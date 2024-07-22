import json
import os
import socket
import threading
import time

DIRECTORY = 'dst'
TARGETS = [
    ("localhost", 11111),
    ("localhost", 22222),
    ("localhost", 33333),
    ("localhost", 44444)
]
HOST = "localhost"
PORT = 22222
PC = "VM2"
STATE_FILE = "state.json"
client_apps = {}


def get_file_info(directory):
    total_files = 0
    total_size = 0

    for dirpath, dirnames, filenames in os.walk(directory):
        total_files += len(filenames)
        total_size += sum(os.path.getsize(os.path.join(dirpath, f)) for f in filenames)

    return total_files, total_size


def broadcast_file_info(file_info, targets):
    data = {
        PC: {
            "files": file_info[0],
            "size": file_info[1],
        }
    }

    data = json.dumps(data)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for ip, port in targets:
        if ip != HOST or port != PORT:
            sock.sendto(data.encode(), (ip, port))

    sock.close()


def save_state_to_json(json_data):
    with open(STATE_FILE, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)


def receive_broadcast(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    while True:
        data, addr = sock.recvfrom(1024)
        data = data.decode()
        data = json.loads(data)
        client_apps.update(data)
        save_state_to_json(client_apps)
        for vm, value in data.items():
            print(f"Received from {vm}: Total files: {value['files']}, Total size: {value['size']} bytes")


def broadcast():
    while True:
        file_info = get_file_info(DIRECTORY)
        broadcast_file_info(file_info, TARGETS)
        time.sleep(10)  # Broadcast every 10 seconds


if __name__ == "__main__":
    # Start broadcasting in a separate thread
    broadcast_thread = threading.Thread(target=broadcast)
    broadcast_thread.start()
    # Start receiving in the main thread
    receive_broadcast(HOST, PORT)
