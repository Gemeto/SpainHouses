import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import logging
import json
import time
import os
import sys
sys.path.append("../")
from configuration import projectSettings

def extract_features(image_path, model):
    try:
        img = load_img(image_path, target_size=(224, 224))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = tf.keras.applications.resnet50.preprocess_input(img_array)
        features = model.predict(img_array)
        return features.flatten()
    except Exception as e:
        logging.error(f"Error processing {image_path}: {e}")
        return None
 
def list_dir_with_retry(directory, max_retries=3, wait_time=5):
    retries = 0
    while retries < max_retries:
        try:
            return os.listdir(directory)
        except Exception as e:
            logging.warning(f"Error accessing {directory}: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            retries += 1
    logging.error(f"Failed to access {directory} after {max_retries} retries.")
    return None
        
def append_to_npy(file_path, new_data):
    if new_data.size == 0:
        logging.warning(f"No new data to append to {file_path}. Skipping.")
        return

    if os.path.exists(file_path):
        existing_data = np.load(file_path)
        
        combined_data = np.concatenate((existing_data, new_data))
    else:
        combined_data = new_data

    np.save(file_path, combined_data)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Paths and settings
output_features_file = 'features.npy'
output_ids_file = 'ids.npy'
checkpoint_file = 'checkpoint.json'

# Define the base path where the image feature file is stored
base_image_features_path = "../" + projectSettings.IMAGE_FEATURES_PATH
features_path = f'{base_image_features_path}/{output_features_file}'
feature_ids_path = f'{base_image_features_path}/{output_ids_file}'
checkpoint_file_path = f'{base_image_features_path}/{checkpoint_file}'

# Define the base path where the image folders are stored
base_image_path = "../" + projectSettings.IMAGES_PATH

features_list = []
ids_list = []

images_to_process = 10000
processed_images = 0

# Load the saved features and IDs
features = np.load(features_path) if os.path.exists(features_path) else np.array([])
ids = np.load(feature_ids_path) if os.path.exists(feature_ids_path) else np.array([])

# List all folder names (IDs)
folder_ids = set(os.listdir(base_image_path))

# Convert the unique IDs from the ids array into a set
vector_ids = set(np.unique(ids))

# Find the IDs that are in the folder but not in the vector IDs
missing_ids = folder_ids - vector_ids

print(f"Total number of folders: {len(folder_ids)}")
print(f"Total number of unique IDs in vectors: {len(vector_ids)}")
print(f"Number of missing IDs: {len(missing_ids)}")

# Initialize the model (ensure your TensorFlow is configured to use the GPU)
base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
model = tf.keras.models.Model(inputs=base_model.input, outputs=base_model.output)

# Load checkpoint if it exists and is valid
if os.path.exists(checkpoint_file_path):
    try:
        with open(checkpoint_file_path, 'r') as f:
            checkpoint = json.load(f)
        start_folder = checkpoint.get('last_folder', None)
        start_image = checkpoint.get('last_image', None)
    except (json.JSONDecodeError, ValueError) as e:
        logging.warning(f"Checkpoint file is empty or corrupted: {e}. Starting from the beginning.")
        checkpoint = {}
        start_folder = None
        start_image = None
else:
    checkpoint = {}
    start_folder = None
    start_image = None

# Process only the missing folders
missing_ids.add(start_folder) if start_folder else None
missing_folders = sorted(list(missing_ids))
start_index = missing_folders.index(start_folder) if start_folder else 0

for folder_index in range(start_index, len(missing_folders)):
    folder_name = missing_folders[folder_index]
    folder_path = os.path.join(base_image_path, folder_name)
    if os.path.isdir(folder_path):
        logging.info(f"Processing folder {folder_index + 1}/{len(missing_folders)}: {folder_name}")
        images = list_dir_with_retry(folder_path)
        # Skip this folder if it couldn't be accessed
        if images is None:
            continue
        start_img_index = images.index(start_image) if folder_name == start_folder and start_image else 0
        for image_index in range(start_img_index, len(images)):
            image_name = images[image_index]
            image_path = os.path.join(folder_path, image_name)
            logging.info(f"Processing image {image_name} in folder {folder_name}...")
            features = extract_features(image_path, model)
            if features is not None:
                features_list.append(features)
                ids_list.append(folder_name)
                processed_images += 1

        # Save checkpoint and stop if the limit is reached
        if processed_images >= images_to_process:
            checkpoint = {'last_folder': folder_name, 'last_image': image_name}
            with open(checkpoint_file_path, 'w') as f:
                json.dump(checkpoint, f)
            logging.info(f"Processed {processed_images} images. Checkpoint saved. Exiting.")

            # Convert to numpy arrays for appending
            features_array = np.array(features_list)
            ids_array = np.array(ids_list)

            # Append new features and IDs to existing files
            append_to_npy(features_path, features_array)
            append_to_npy(feature_ids_path, ids_array)

            break # Exit the loop after saving the checkpoint
    if processed_images >= images_to_process:
        break # Exit the outer loop if processing limit is reached

# Convert to numpy arrays for appending
features_array = np.array(features_list)
ids_array = np.array(ids_list)

# Append the final batch of features and IDs to existing files
append_to_npy(features_path, features_array)
append_to_npy(feature_ids_path, ids_array)
logging.info(f"Final save after processing {processed_images} images.")
logging.info("Feature extraction completed.")