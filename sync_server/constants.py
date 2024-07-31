import json
import os.path
from datetime import datetime


def create_abs_path(file_name):
    current_file_path = os.path.abspath(__file__)
    current_dir_path = os.path.dirname(current_file_path)
    return os.path.join(current_dir_path, file_name)


def get_config(key=None):
    path = create_abs_path('config.json')

    with open(path, 'r') as file:
        obj = json.load(file)
        if not key:
            return obj
        else:
            try:
                return obj[key]
            except KeyError:
                return None


def get_settings(key=None):
    path = create_abs_path('state.json')
    with open(path, 'r') as file:
        obj = json.load(file)
        if not key:
            return obj
        else:
            try:
                return obj[key]
            except KeyError:
                return None



config = get_config()
settings = get_settings()

# read config file
DIRECTORY = config['DIRECTORY']
TARGETS = list(config['VM_LIST'].values())
PC = config['THIS_VM']
THIS_HOST = config["VM_LIST"][PC][0]
THIS_PORT = config["VM_LIST"][PC][1]
TIME_THRESHOLD = config['TIME_THRESHOLD']
SERVER_IP = "127.0.0.1"
SERVER_PORT = 12345
TOKEN = ''
TOKEN_STATUS = settings['TOKEN_STATUS']

# VM files state
STATE_FILE = "state.json"
client_apps = settings['VMLIST']
TOKEN_TYPE_SEND = 1
TOKEN_TYPE_ACCEPT = 2
TOKEN_STATUS_SEND = 1
TOKEN_STATUS_TOKEN_PASS = 2
TOKEN_STATUS_IDLE = 3
BEGIN_DATETIME = datetime.strptime("2024-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
