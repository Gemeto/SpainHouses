
from spainhouses.webapp import create_app
import os

if __name__ == "__main__":
    app = create_app()
    app.config['DEBUG'] = True
    app.config['MONGO_URI'] = f"mongodb://{os.getenv('MONGO_USER', 'root')}:{os.getenv('MONGO_PASS', 'root')}@{os.getenv('MONGO_HOST', 'localhost')}/{os.getenv('MONGO_DB', 'spainhouses')}?authSource=admin"

    app.run(host='0.0.0.0')
