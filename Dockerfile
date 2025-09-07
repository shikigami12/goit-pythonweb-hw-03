FROM python:3.10-slim

WORKDIR /app

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system --deploy --ignore-pipfile

COPY . .

EXPOSE 3000

CMD ["python", "main.py"]
