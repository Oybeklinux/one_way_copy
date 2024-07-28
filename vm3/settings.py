from constants import STATE_FILE
import json


def json_edit(callback):
    def wrapper(arg):
        with open(STATE_FILE, 'r') as file:
            try:
                settings = json.load(file)
            except:
                settings = {}

        callback(arg, settings)

        with open(STATE_FILE, 'w') as file:

            json.dump(settings, file, indent=4)

    return wrapper


@json_edit
def save_file_name(file_name: str, data: dict = None):
    if isinstance(data, dict):
        if 'send_files' not in data:
            data['send_files'] = []
        data['send_files'].append(file_name)


@json_edit
def save_files_state(state: dict, data: dict = None):
    if isinstance(data, dict):
        data.update(state)


def get_state():
    with open(STATE_FILE, 'r') as file:
        return json.load(file)
