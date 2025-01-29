from flask import Flask, render_template, request, send_from_directory
from spainhouses.image_comparator import load_image_features, process_similar_offers
from spainhouses.db import get_offer, get_paginated_offers, get_offers_by_ref, get_offer_historic
import numpy as np
from pathlib import Path
import sys
import os
sys.path.append("../../")
from configuration import projectPaths

def create_app():
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    STATIC_FOLDER = os.path.join(APP_DIR, 'build/static')
    TEMPLATE_FOLDER = os.path.join(APP_DIR, 'build')
    app = Flask(__name__, static_folder=STATIC_FOLDER, template_folder=TEMPLATE_FOLDER)

    # Static files route
    @app.route('/statics/<directory>/<filename>')
    def offer_img_static(directory, filename):
        return send_from_directory(f"{projectPaths.IMAGES_PATH}/{directory}", filename)

    # Offers list route
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def announcements_list(path):
        paginated_offers = get_paginated_offers(request.args, page=int(request.args.get('page', 1)), offers_per_page=21)

        for offer in paginated_offers["docs"]:
            offer["main_image"] = get_main_image(offer['ref'])
        
        return render_template('templates/announcement/announcements_list.html', get=request.args, paginated_offers=paginated_offers)
    
    # Offer detail route
    @app.route('/announcement/<ref>')
    def announcement_detail(ref):
        image_features_path = f'{projectPaths.IMAGE_FEATURES_PATH}/features.npy'
        image_ids_path = f'{projectPaths.IMAGE_FEATURES_PATH}/ids.npy'
        offer = get_offer(ref)

        if os.path.exists(image_features_path) and os.path.exists(image_ids_path):
            features = load_image_features(image_features_path)
            ids = np.load(Path(image_ids_path), mmap_mode='r')
            offer["similar_offers"] = get_similar_offers(process_similar_offers(offer, features, ids))

        image_path = f"{projectPaths.IMAGES_PATH}/{offer['ref']}"
        if os.path.exists(image_path):
            offer["images"] = os.listdir(image_path)

        offer["historic"] = get_offer_historic(ref)
        offer["main_image"] = get_main_image(offer['ref'])

        return render_template('templates/announcement/announcement_detail.html', offer=offer)

    return app

def get_main_image(ref):
    image_path = f"{projectPaths.IMAGES_PATH}/{ref}"
    if os.path.exists(image_path):
        image_urls = os.listdir(image_path)
        return image_urls[0] if image_urls else None
    return None

def get_similar_offers(refs):
    similar_offers = get_offers_by_ref(refs)
    for similar in similar_offers:
        similar["main_image"] = get_main_image(similar['ref'])
    return similar_offers