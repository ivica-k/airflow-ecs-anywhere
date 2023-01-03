FROM  python:3.9.16-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 --no-cache-dir install -r requirements.txt

COPY etl_scripts/*.py /app/