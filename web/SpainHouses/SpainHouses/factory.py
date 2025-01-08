from flask import Flask, render_template, request, send_from_directory
from flask_cors import CORS
from spainhouses.db import get_offer, get_paginated_offers, get_offers_by_ref, get_offer_historic
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
from bson import json_util, ObjectId
from json import JSONEncoder
from datetime import datetime
import numpy as np
from pathlib import Path
from typing import Dict
import sys
import os
sys.path.append("../../../")
from configuration import projectSettings

class MongoJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_util.CANONICAL_JSON_OPTIONS)
    
class MultiNumpyMMAPHandler:
    _instance = None
    _arrays: Dict[str, dict] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MultiNumpyMMAPHandler, cls).__new__(cls)
        return cls._instance

    def load_array(self, file_path):
        try:
            self._arrays[file_path] = np.load(Path(file_path), mmap_mode='r')
            return self._arrays[file_path]
        except Exception as e:
            raise Exception(f"Error al cargar el archivo numpy {file_path}: {str(e)}")
        
    def set_array(self, identifier, array):
        self._arrays[identifier] = array

    def get_array(self, file_path):
        if file_path not in self._arrays:
            return self.load_array(file_path)
        
        return self._arrays[file_path]
    
    def exist_array(self, file_path):
        return file_path in self._arrays

    def get_slice(self, file_path, indices):
        array = self.get_array(file_path)
        if array is None:
            return None
        return array[indices]

    def remove_array(self, file_path):
        if file_path in self._arrays:
            del self._arrays[file_path]
            return True
        return False

    def clear_all(self) -> None:
        for file_path in list(self._arrays.keys()):
            self.remove_array(file_path)


def create_app():

    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    STATIC_FOLDER = os.path.join(APP_DIR, 'build/static')
    TEMPLATE_FOLDER = os.path.join(APP_DIR, 'build')

    app = Flask(__name__, static_folder=STATIC_FOLDER,
                template_folder=TEMPLATE_FOLDER,
                )
    CORS(app)
    app.json_encoder = MongoJsonEncoder

    @app.route('/statics/<directory>/<filename>')
    def offers_img_static(directory, filename):
        return send_from_directory(f"{projectSettings.IMAGES_PATH}/{directory}", filename)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def announcements_list(path):
        paginated_offers = get_paginated_offers(request.args, page=int(request.args.get('page', 1)), offers_per_page=21)

        for offer in paginated_offers["docs"]:
            offer["main_image"] = get_main_image(offer['ref'])
        
        return render_template('templates/announcement/announcements_list.html', get=request.args, paginated_offers=paginated_offers)
    
    @app.route('/announcement/<ref>')
    def announcements_detail(ref):
        image_features_path = f'{projectSettings.IMAGE_FEATURES_PATH}/features.npy'
        image_ids_path = f'{projectSettings.IMAGE_FEATURES_PATH}/ids.npy'
        offer = get_offer(ref)

        if os.path.exists(image_features_path) and os.path.exists(image_ids_path):
            mem_array_handler = MultiNumpyMMAPHandler()
            features = load_image_features(mem_array_handler, image_features_path)
            ids = mem_array_handler.get_array(image_ids_path)
            offer["similar_offers"] = process_similar_offers(offer, features, ids)

        image_path = f"{projectSettings.IMAGES_PATH}/{offer['ref']}"
        if os.path.exists(image_path):
            offer["images"] = os.listdir(image_path)

        offer["historic"] = get_offer_historic(ref)
        offer["main_image"] = get_main_image(offer['ref'])

        return render_template('templates/announcement/announcement_detail.html', offer=offer)

    return app

def load_image_features(mem_array_handler, image_features_path):
            features = mem_array_handler.get_array(image_features_path)
            if not mem_array_handler.exist_array(image_features_path):
                features = normalize(features)
                mem_array_handler.set_array(image_features_path, features)
            return features

def get_main_image(ref):
    image_path = f"{projectSettings.IMAGES_PATH}/{ref}"
    if os.path.exists(image_path):
        image_urls = os.listdir(image_path)
        return image_urls[0] if image_urls else None
    return None

def process_similar_offers(offer, features, ids):
    similars = find_similar_offer_images(offer['ref'], features, ids)
    similar_offers = get_offers_by_ref(similars)
    for similar in similar_offers:
        similar["main_image"] = get_main_image(similar['ref'])
    return similar_offers

def find_similar_offer_images(selected_id, features, ids, top_n=3):
    unique_similar_ids = {}
    similarities = None
    similar_indices = None
    image_features_index = np.where(ids == selected_id)[0]

    if len(image_features_index) > 0:
        #Solo usamos la primera mitad del array porque se repiten
        for features_index in np.array_split(image_features_index, 2)[0]:
            image_features = features[features_index]

            #Calculate cosine similarity
            similarities = cosine_similarity(image_features.reshape(1, -1), features)

            #Sort matches by similarity in desc order
            similar_indices = similarities[0].argsort()[::-1]

            for idx in similar_indices:
                similar_id = ids[idx]

                #Setting simiar ids dict
                if similar_id != selected_id and similar_id not in unique_similar_ids:
                    if float(similarities[0][idx]) < 0.77:
                        break
                    unique_similar_ids[similar_id] = similarities[0][idx]
                if len(unique_similar_ids) >= top_n:
                    break

            if len(unique_similar_ids) >= top_n:
                break
    
    return list(unique_similar_ids.keys())