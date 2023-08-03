# syntax=docker/dockerfile:1
FROM python:3.5
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
RUN pip install --upgrade pip
RUN pip install pip-tools
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
CMD ["python", "manage.py"]
