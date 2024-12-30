FROM tensorflow/tensorflow:2.16.1-gpu
WORKDIR /imageFeatureExtractor
COPY ./imageFeatureExtractor /imageFeatureExtractor
COPY ./data /data
COPY ./configuration /configuration
RUN pip install -r requirements.txt