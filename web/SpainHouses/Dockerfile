FROM python:3.12
WORKDIR /SpainHouses
COPY ./web /
COPY ./data /data
COPY ./constants /constants
COPY ./configuration /configuration
COPY .env /
RUN pip install -r requirements.txt