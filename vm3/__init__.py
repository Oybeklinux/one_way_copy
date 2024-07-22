import json

with open('config.json', 'r') as file:
    config: dict = json.load(file)

# read config file
DIRECTORY = config['DIRECTORY']
TARGETS = list(config['VM_LIST'].values())
PC = config['THIS_VM']
HOST = config["VM_LIST"][PC][0]
PORT = config["VM_LIST"][PC][1]
TIME_THRESHOLD = config['TIME_THRESHOLD']
TOKEN_MESSAGE = config['TOKEN_MESSAGE']
I_HAVE_TOKEN = config['I_HAVE_TOKEN']
SERVER_IP = "localhost"
SERVER_PORT = 12345

# VM files state
STATE_FILE = "state.json"
client_apps = {}
