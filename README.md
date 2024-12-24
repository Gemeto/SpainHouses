Project that covers the tasks of extracting, analyzing and visualizing real estate offers data.

Required:
1. Python3
2. Docker

Installation:
1. Create a file named 'secrets.py' inside the folder named 'configuration' and set the following fields:
POSTGRES_DB = "db_name"
POSTGRES_USERNAME = "your_postgres_username"
POSTGRES_PASSWORD = "your_postgres_pass"
POSTGRES_HOSTNAME = "your_postgres_hostname"
POSTGRES_PORT = "your_postgres_port"

2. Create a Python venv with the command "python -m venv env" and activate it with the command "./env/scripts/activate" (Recommended)
   
3. Install all the requirements with the command "pip -r requirements.txt"

4. Run the modules:
   Crawler -> "python crawler/main.py" (To extract data from various webs)
   ImageFeatureExtractor -> "python ImageFeatureExtractor/imageFeatureExtractor.py" (To extract features of the extracted images, in order to compare them on the SpainHouses website)
   Web -> "python web/SpainHouses/manage.py runserver"
