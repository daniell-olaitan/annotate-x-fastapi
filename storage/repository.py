from src.models import User, Project, Image, Annotation, Category
from storage.orm import UserORM, ProjectORM, ImageORM, AnnotationORM, CategoryORM, DemoORM
from sqlmodel import Session, select
from abc import ABC, abstractmethod
from pathlib import Path

NOT_IMPLEMENTED_ERROR = NotImplementedError('Method must be implemented')


## Abstract Model Repositories
class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> str:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get(self, username: str) -> User | None:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get_by_id(self, id: str) -> User | None:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get_usernames(self) -> list[str]:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def remove(self, id: str) -> None:
        raise NOT_IMPLEMENTED_ERROR


class ProjectRepository(ABC):
    @abstractmethod
    def add(self, project: Project, user_id: str) -> str:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get(self, name: str) -> Project | None:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get_by_id(self, id: str) -> Project | None:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get_with_relationships(self, id: str) -> Project | None:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get_project_image_names(self, id: str) -> list[str]:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def list(self, user_id: str) -> list[Project]:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def remove(self, id: str) -> None:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def export_project_data(self, id: str) -> dict:
        raise NOT_IMPLEMENTED_ERROR


class AnnotationRepository(ABC):
    @abstractmethod
    def add(self, annotation: Annotation, image_id: str, category_id: str) -> str:
        raise NOT_IMPLEMENTED_ERROR


class CategoryRepository(ABC):
    @abstractmethod
    def add(self, category: Category, project_id: str) -> str:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get(self, name: str) -> Category | None:
        raise NOT_IMPLEMENTED_ERROR


class ImageRepository(ABC):
    @abstractmethod
    def add(self, image: Image, project_id: str) -> str:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get_by_id(self, id: str) -> Image | None:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def remove(self, id: str) -> None:
        raise NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def remove_image_annotations(self, id: str) -> None:
        raise NOT_IMPLEMENTED_ERROR


class DemoRepository(ABC):
    @abstractmethod
    def get_image_urls(self) -> list[str]:
        raise NOT_IMPLEMENTED_ERROR


## Implementations of the Model Repositories
class BaseSQLAlchemyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        super().__init__()


class SQLAlchemyUserRepsitory(BaseSQLAlchemyRepository, UserRepository):
    def add(self, user: User) -> str:
        import bcrypt

        password_hash = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
        user_orm = UserORM(password=password_hash, **user.to_dict())
        self._session.add(user_orm)

        return user_orm.id

    def get(self, username: str) -> User | None:
        statement = select(UserORM).where(UserORM.username == username)
        try:
            user_orm = self._session.exec(statement).one()
        except Exception:
            return None

        return User(**user_orm.model_dump())

    def get_by_id(self, id: str) -> User | None:
        user_orm = self._session.get(UserORM, id)
        if user_orm:
            return User(**user_orm.model_dump())

        return None

    def get_usernames(self) -> list[str]:
        return [
            user.username
            for user in self._session.exec(select(UserORM)).all()
        ]

    def remove(self, id: str) -> None:
        statement = select(UserORM).where(UserORM.id == id)
        user_orm = self._session.exec(statement).first()
        if user_orm:
            self._session.delete(user_orm)


class SQLAlchemyProjectRepository(BaseSQLAlchemyRepository, ProjectRepository):
    def add(self, project: Project, user_id: str) -> str:
        project_orm = ProjectORM(user_id=user_id, **project.to_dict())
        self._session.add(project_orm)

        return project_orm.id

    def get(self, name: str) -> Project | None:
        statement = select(ProjectORM).where(ProjectORM.name == name)
        try:
            project_orm = self._session.exec(statement).one()
        except Exception:
            return None

        return Project(**project_orm.model_dump())

    def get_by_id(self, id: str) -> Project | None:
        project_orm = self._session.get(ProjectORM, id)
        if project_orm:
            return Project(**project_orm.model_dump())

        return None

    def get_project_image_names(self, id: str) -> list[str]:
        return [
            Path(img.url).stem
            for img in self._session.exec(select(ImageORM).where(ImageORM.project_id == id)).all()
        ]

    def get_with_relationships(self, id: str) -> Project | None:
        project_orm = self._session.get(ProjectORM, id)
        if project_orm is None:
            return None

        project = Project(**project_orm.model_dump())
        categories = [
            Category(**category.model_dump())
            for category in project_orm.categories
        ]

        images = [
            Image(**image.model_dump())
            for image in project_orm.images
        ]

        for image, image_orm in zip(images, project_orm.images):
            annotations = [
                Annotation(**annotation.model_dump())
                for annotation in image_orm.annotations
            ]

            for a, a_orm in zip(annotations, image_orm.annotations):
                a.category = Category(**a_orm.category.model_dump())

            image.annotations = annotations

        project.categories = categories
        project.images = images

        return project

    def list(self, user_id: str = None) -> list[Project]:
        if user_id:
            user_orm = self._session.get(UserORM, user_id)
            if not user_orm:
                return []

            return [
                Project(**project_orm.model_dump())
                for project_orm in self._session.exec(
                    select(ProjectORM).where(ProjectORM.user_id == user_id)
                ).all()
            ]

        return [
            Project(**project_orm.model_dump())
            for project_orm in self._session.exec(select(ProjectORM)).all()
        ]

    def remove(self, id: str) -> None:
        project_orm = self._session.get(ProjectORM, id)
        if project_orm:
            self._session.delete(project_orm)

    def export_project_data(self, id: str) -> dict:
        project = {}
        project_orm = self._session.get(ProjectORM, id)
        if project_orm:
            categories = [
                {'id': category_orm.id, 'name': category_orm.name}
                for category_orm in project_orm.categories
            ]

            images = []
            image_urls = []
            annotations = []
            for image_orm in project_orm.images:
                image_dict = image_orm.model_dump()
                image_urls.append(image_dict.pop('url'))
                images.append(image_dict)

                for annotation_orm in image_orm.annotations:
                    annotation = {
                        'id': annotation_orm.id,
                        'image_id': annotation_orm.image_id,
                        'category_id': annotation_orm.category_id,
                        'iscrowd': 0,
                        'area': annotation_orm.width * annotation_orm.height,
                        'bbox': [
                            annotation_orm.x,
                            annotation_orm.y,
                            annotation_orm.width,
                            annotation_orm.height
                        ]
                    }

                    annotations.append(annotation)

            project.update(
                name=project_orm.name.lower(),
                images=images,
                categories=categories,
                image_urls=image_urls,
                annotations=annotations
            )

        return project


class SQLAlchemyImageRepository(BaseSQLAlchemyRepository, ImageRepository):
    def add(self, image: Image, project_id: str) -> str:
        image_orm = ImageORM(project_id=project_id, **image.to_dict())
        self._session.add(image_orm)

        return image_orm.id

    def get_by_id(self, id: str) -> Image | None:
        image_orm = self._session.get(ImageORM, id)
        if image_orm:
            return Image(**image_orm.model_dump())

        return None

    def remove(self, id: str) -> None:
        image_orm = self._session.get(ImageORM, id)
        if image_orm:
            self._session.delete(image_orm)

    def remove_image_annotations(self, id: str) -> None:
        image_orm = self._session.get(ImageORM, id)
        if image_orm:
            for a in image_orm.annotations:
                self._session.delete(a)

        self._session.commit()


class SQLAlchemyAnnotationRepository(AnnotationRepository, BaseSQLAlchemyRepository):
    def add(self, annotation: Annotation, image_id: str, category_id: str) -> str:
        annotation_orm = AnnotationORM(category_id=category_id, image_id=image_id, **annotation.to_dict())
        self._session.add(annotation_orm)

        return annotation_orm.id


class SQLAlchemyCategoryRepository(CategoryRepository, BaseSQLAlchemyRepository):
    def add(self, category: Category, project_id: str) -> str:
        category_orm = CategoryORM(project_id=project_id, **category.to_dict())
        self._session.add(category_orm)

        return category_orm.id

    def get(self, name: str) -> Category | None:
        statement = select(CategoryORM).where(CategoryORM.name == name)
        try:
            category_orm = self._session.exec(statement).one()
        except Exception:
            return None

        return Category(**category_orm.model_dump())


class SQLAlchemyDemoRepository(DemoRepository, BaseSQLAlchemyRepository):
    def get_image_urls(self) -> list[str]:
        return [
            demo.url
            for demo in self._session.exec(select(DemoORM)).all()
        ]
