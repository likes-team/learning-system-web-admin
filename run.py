import os
from app import create_app
from dotenv import load_dotenv


load_dotenv()
config_name = os.getenv('FLASK_ENV')
app = create_app(config_name)
host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
port = int(os.getenv('FLASK_RUN_PORT', 5000))

if __name__ == '__main__':
    app.run(host=host, port=port)
