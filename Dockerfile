FROM python:2.7-slim

COPY requirements.txt /tmp
WORKDIR /tmp
RUN pip install -r requirements.txt

COPY ./src /src
WORKDIR /src
EXPOSE 5000

ENTRYPOINT ["python", "bind-api.py"]
