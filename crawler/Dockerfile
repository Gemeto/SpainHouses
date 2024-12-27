FROM python:3.12
WORKDIR /crawler
COPY ./crawler /crawler
COPY ./constants /constants
COPY ./configuration /configuration
RUN pip install -r requirements.txt

# Install Chromedriver
RUN wget -q -O chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/113.0.5672.63/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    rm chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/