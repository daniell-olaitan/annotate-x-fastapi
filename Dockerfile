FROM python:3.12.10-slim

# Install psycopg2 dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev

WORKDIR /annotate_app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

COPY . .

CMD ["uvicorn", "fastapi_main:app", "--host", "0.0.0.0", "--port", "8000"]
