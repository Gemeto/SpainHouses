
from spainhouses.webapp import create_app
import os

if __name__ == "__main__":
    app = create_app()
    app.config['DEBUG'] = True
    app.config['MONGO_URI'] = f"mongodb://root:root@localhost/spainhouses?authSource=admin"

    app.run(host='0.0.0.0')
