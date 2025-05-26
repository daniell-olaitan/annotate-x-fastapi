import { InputPopup } from './InputPopup.js';
import { Popup } from './Popup.js';
import { ColorSelector, Drawer } from '../utils.js';

import htm from 'https://esm.sh/htm';
import { h } from 'https://esm.sh/preact';
import { useRef, useState, useEffect } from 'https://esm.sh/preact/hooks';
import { v4 as uuidv4 } from 'https://jspm.dev/uuid';

const html = htm.bind(h);

export function Annotator({
  project,
  setProject,
  image,
  annotations,
  setAnnotations,
}) {
  const imageAnnotationsRef = useRef([]);

  const containerWidth = 900;
  const containerHeight = 400;

  const annotationColor = 'red';

  const drawerRef = useRef(new Drawer());

  const [scale, setScale] = useState(null);

  const imageRef = useRef(null);
  const canvasRef = useRef(null);

  const [labels, setLabels] = useState([]);

  const isDrawingRef = useRef(false);
  const startPoint = useRef({ x: 0, y: 0 });
  const currentPoint = useRef({ x: 0, y: 0 });

  const [popupPos, setPopupPos] = useState(null);
  const [inputPopupPos, setInputPopupPos] = useState(null);

  useEffect(() => {
    const canvas = canvasRef.current;

    if (!image || !canvas || !annotations) return;

    const scaleX = containerWidth / image.width;
    const scaleY = containerHeight / image.height;

    imageAnnotationsRef.current = annotations[image.id];
    setScale({ x: scaleX, y: scaleY });
    drawerRef.current.ctx = canvas.getContext('2d');
    drawAnnotations(scaleX, scaleY);
  }, [image]);

  useEffect(() => {
    if (!annotations || !scale || !image) return;

    imageAnnotationsRef.current = annotations[image.id];
    drawAnnotations(scale.x, scale.y);
  }, [annotations]);

  useEffect(() => {
    if (!project) return;

    const labelItems = project.categories.map(cls => ({id: cls.name, value: cls}));

    labelItems.push({id: 'Add New', value: '__new__'})
    setLabels(labelItems);
  }, [project]);

  const getCurrentAnnotation = (startPoint, currentPoint) => {
    return {
      id: uuidv4(),
      x: Math.min(startPoint.x, currentPoint.x) / scale.x,
      y: Math.min(startPoint.y, currentPoint.y) / scale.y,
      width: Math.abs(currentPoint.x - startPoint.x) / scale.x,
      height: Math.abs(currentPoint.y - startPoint.y) / scale.y,
      category: {
        id: uuidv4(),
        name: null,
        color: annotationColor
      }
    };
  };

  const drawAnnotations = (scaleX, scaleY) => {
    const drawer = drawerRef.current;
    const categories = {};
    const labels = [];

    annotations[image.id].forEach(a => {
      const category = a.category.name;

      if (category) {
        if (category in categories) {
          categories[category] += 1;
        } else {
          categories[category] = 1;
        }

        labels.push(`${category}${categories[category]}`);
      }
    });

    const drawAnnotation = (annotatn, text) => {
      drawer.color = annotatn.category.color;
      drawer.drawRect(annotatn, scaleX, scaleY);

      if (annotatn.category.name) {
        const label = {
          x: annotatn.x,
          y: annotatn.y,
          text: text
        };

        drawer.drawLabel(label, scaleX, scaleY);
      }
    };

    if (!drawer.ctx) return;
    drawer.clearRect({
      x: 0,
      y: 0,
      width: containerWidth,
      height: containerHeight
    });

    imageAnnotationsRef.current.forEach((annotatn, index) => {
      const text = labels[index];
      drawAnnotation(annotatn, text);
    });

    // Draw active box
    if (isDrawingRef.current) {
      const currentAnnotion = getCurrentAnnotation(startPoint.current, currentPoint.current);
      drawAnnotation(currentAnnotion, null);
    }
  };

  const handleClassSelect = (cls, e) => {
    const annotatn = imageAnnotationsRef.current.pop();

    if (cls) {
      if (cls === '__new__') {
        imageAnnotationsRef.current.push(annotatn);
        setAnnotations({...annotations, [image.id]: imageAnnotationsRef.current});

        e.preventDefault();

        const x = e.clientX;
        const y = e.clientY;
        setInputPopupPos({
          x: (annotatn.x + annotatn.width) * scale.x,
          y: (annotatn.y + annotatn.height) * scale.y
        });
      } else {
        annotatn.category.name = cls.name;
        annotatn.category.color = cls.color;

        imageAnnotationsRef.current.push(annotatn);
        setAnnotations({...annotations, [image.id]: imageAnnotationsRef.current});
      }
    }

    drawAnnotations(scale.x, scale.y);
    setPopupPos(null);
  };

  const handleCategoryInput = (category, e) => {
    const annotatn = imageAnnotationsRef.current.pop();
    const categoryNames = project.categories.map(cls => cls.name);

    if (category && category.trim()) {
      if (categoryNames.includes(category.toLowerCase())) {
        const cls = project.categories.find(c => c.name === category.toLowerCase());

        if (cls) {
          annotatn.category.name = cls.name;
          annotatn.category.color = cls.color;
        }
      } else {
        const colorSelector = new ColorSelector();
        const categoryColors = project.categories.map(cls => cls.color);

        annotatn.category.name = category.toLowerCase();
        annotatn.category.color = colorSelector.selectColor(categoryColors);

        setProject(prev => ({...prev, categories: [...prev.categories, annotatn.category]}));
      }

      console.log(annotatn);

      imageAnnotationsRef.current.push(annotatn);
      setAnnotations({...annotations, [image.id]: imageAnnotationsRef.current});
    }

    drawAnnotations(scale.x, scale.y);
    setInputPopupPos(null);
  };

  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();

    startPoint.current = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };

    currentPoint.current = startPoint.current;
    isDrawingRef.current = true;
  };

  const handleMouseMove = (e) => {
    if (!isDrawingRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();

    currentPoint.current = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };

    drawAnnotations(scale.x, scale.y);
  };

  const handleMouseUp = () => {
    if (!isDrawingRef.current) return;
    isDrawingRef.current = false;

    const currentAnnotion = getCurrentAnnotation(
      startPoint.current,
      currentPoint.current
    );

    // Ignore very small boxes
    if (currentAnnotion.width < 5 || currentAnnotion.height < 5) {
      drawAnnotations(scale.x, scale.y);
      return;
    }

    imageAnnotationsRef.current.push(currentAnnotion);
    setAnnotations({...annotations, [image.id]: imageAnnotationsRef.current});

    setPopupPos({
      x: (currentAnnotion.x + currentAnnotion.width) * scale.x,
      y: (currentAnnotion.y + currentAnnotion.height) * scale.y
    });
  };

  useEffect(() => {
    const img = imageRef.current;
    const canvas = canvasRef.current;

    if (!img || !canvas) return;

    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      canvas.removeEventListener('mousedown', handleMouseDown);
      canvas.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [scale, image]);

  return html`
    ${!image
      ? html`<p class="py-16 px-32 h2-c font-semibold">add an image for annotation</p>`
      : html`
          <div class="relative" style="width: ${containerWidth}px; height: ${containerHeight}px;">
            <img
              src=${image.url}
              ref=${imageRef}
              alt="annotatable"
              class="absolute top-0 left-0 w-full h-full object-contain z-10"
            />

            <canvas
              ref=${canvasRef}
              width=${containerWidth}
              height=${containerHeight}
              class="absolute top-0 left-0 cursor-crosshair z-20"
            />

            ${popupPos &&
              html`
                <${Popup}
                  labels=${labels}
                  popupPos=${popupPos}
                  title="select a class"
                  onSelect=${handleClassSelect}
                />
              `
            }

            ${inputPopupPos &&
              html`
                <${InputPopup}
                  popupPos=${inputPopupPos}
                  onSubmit=${handleCategoryInput}
                />
              `
            }
          </div>
        `
    }
  `;
}
