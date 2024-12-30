from pathlib import Path

ENV_FILE_PATH = Path(__file__).resolve().parent.parent.joinpath('.env')
IMAGES_PATH = Path(__file__).resolve().parent.parent.joinpath('data/images')
IMAGE_FEATURES_PATH = Path(__file__).resolve().parent.parent.joinpath('data/image_embeddings')