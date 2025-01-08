
from spainhouses.factory import create_app
import os

if __name__ == "__main__":
    app = create_app()
    app.config['DEBUG'] = True
    app.config['MONGO_URI'] = f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASS')}@{os.getenv('MONGO_HOST')}/{os.getenv('MONGO_DB')}?authSource=admin"

    app.run(host='0.0.0.0')
