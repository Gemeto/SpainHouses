from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
from pathlib import Path
import numpy as np

def load_image_features(image_features_path):
    features = np.load(Path(image_features_path), mmap_mode='r')
    return normalize(features) #TODO check if this is necessary

def process_similar_offers(offer, features, ids):
    refs = find_similar_offer_images(offer['ref'], features, ids)
    return refs

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