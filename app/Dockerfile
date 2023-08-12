FROM python:3.8.6-slim-buster

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN python3 -m pip install --upgrade pip

COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

COPY . /app

