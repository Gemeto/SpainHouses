
from spainhouses.webapp import create_app
import sys
import os
from dotenv import load_dotenv
sys.path.append("../")
from configuration import projectPaths

if __name__ == "__main__":
    app = create_app()
    app.config['DEBUG'] = True
    host = os.getenv('MONGO_HOST')
    user = os.getenv('MONGO_USER')
    password = os.getenv('MONGO_PASS')
    db = os.getenv('MONGO_DB')
    if os.getenv('MONGO_HOST') is None:
        host = 'localhost'
        load_dotenv(dotenv_path=projectPaths.ENV_FILE_PATH) #When reading env file this way the connection url doesn't work properly on windows
        user = os.getenv('MONGO_USER')
        password = os.getenv('MONGO_PASS')
        db = os.getenv('MONGO_DB')
    app.config['MONGO_URI'] = f"mongodb://{user}:{password}@{host}/{db}?authSource=admin"

    app.run(host='0.0.0.0')
