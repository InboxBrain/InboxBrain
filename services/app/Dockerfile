FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends     build-essential default-libmysqlclient-dev pkg-config ca-certificates curl     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
