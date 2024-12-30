FROM python:3.12

# Use a smaller base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Istanbul
ENV LC_ALL=tr_TR.UTF-8
ENV LANG=tr_TR.UTF-8

WORKDIR /crawler
COPY ./crawler /crawler
COPY ./constants /constants
COPY ./configuration /configuration

# Install dependencies and Chrome in one layer to keep image size smaller
RUN apt-get update && apt-get install -y \
     wget \
     gnupg \
     unzip \
     curl \
     ca-certificates \
     fonts-liberation \
     libappindicator3-1 \
     libasound2 \
     libatk-bridge2.0-0 \
     libatk1.0-0 \
     libcups2 \
     libdbus-1-3 \
     libgdk-pixbuf2.0-0 \
     libnspr4 \
     libnss3 \
     libx11-xcb1 \
     libxcomposite1 \
     libxdamage1 \
     libxrandr2 \
     xdg-utils \
     locales \
     --no-install-recommends \
     && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
     && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
     && apt-get install ./google-chrome-stable_current_amd64.deb --yes \
     && apt-get clean \
     && rm -rf /var/lib/apt/lists/*

# Configure locale settings for Türkiye
RUN echo "LC_ALL=tr_TR.UTF-8" >> /etc/environment \
     && echo "LANG=tr_TR.UTF-8" >> /etc/environment \
     && locale-gen tr_TR.UTF-8

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose the ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Command to run FastAPI and Streamlit
CMD ["scrapy", "crawl", "habitaclia"]