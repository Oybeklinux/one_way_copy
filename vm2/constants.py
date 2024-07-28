import json


def get_config():
    with open('config.json', 'r') as file:
        return json.load(file)


def get_settings():
    with open('state.json', 'r') as file:
        return json.load(file)


config = get_config()
settings = get_settings()

# read config file
DIRECTORY = config['DIRECTORY']
TARGETS = list(config['VM_LIST'].values())
PC = config['THIS_VM']
HOST = config["VM_LIST"][PC][0]
PORT = config["VM_LIST"][PC][1]
TIME_THRESHOLD = config['TIME_THRESHOLD']
SERVER_IP = "localhost"
SERVER_PORT = 12345
TOKEN = ''
TOKEN_STATUS = settings['TOKEN_STATUS']

# VM files state
STATE_FILE = "state.json"
client_apps = settings['VMLIST']
