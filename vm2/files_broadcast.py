import os
import socket
import threading
import time
from datetime import datetime, timedelta
from random import choice
from time import sleep

from vm1 import *


def get_file_info(directory):
    total_files = 0
    total_size = 0

    for dirpath, dirnames, filenames in os.walk(directory):
        total_files += len(filenames)
        total_size += sum(os.path.getsize(os.path.join(dirpath, file)) for file in filenames)

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
        # check if it is file info or token_passing
        if 'token' in data:
            print('I got token')
            send_files()
            time.sleep(2)  # Simulate some processing time
            pass_token()
            break
        else:

            client_apps.update(data)
            save_state_to_json(client_apps)
            for vm, value in data.items():
                print(f"Received from {vm}: Total files: {value['files']}, Total size: {value['size']} bytes")


def broadcast():
    while True:
        file_info = get_file_info(DIRECTORY)
        broadcast_file_info(file_info, TARGETS)
        time.sleep(10)  # Broadcast every 10 seconds


# Function to send a file to server A via TCP
def send_file_to_server_a(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, SERVER_PORT))
        s.send(data)


def send_files():
    print('I have token. I am sending')
    for dirpath, dirnames, filenames in os.walk(DIRECTORY):

        for filename in filenames:
            try:
                file, ext = filename.split(".")
                file_time = datetime.strptime(file, '%Y-%m-%d-%H-%M-%S')
            except ValueError:
                continue

            file_path = os.path.join(DIRECTORY, filename)
            if (datetime.utcnow() - file_time) > timedelta(minutes=TIME_THRESHOLD):
                os.remove(file_path)
                print(f"Deleted old file: {filename}")
            else:
                try:
                    send_file_to_server_a(file_path)
                    print(f"Sent file to server A: {filename}")
                except Exception as e:
                    print(f"Failed to send file {filename} to server A: {e}")


def get_random_vm():
    vm_list = []
    for vm in client_apps:
        if client_apps[vm]['files'] > 0:
            vm_list.append(vm)
    return choice(vm_list) if vm_list else None


def pass_token():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        address = get_random_vm()
        if not address:
            return None

        token = {"token": TOKEN_MESSAGE}
        token = json.dumps(token)
        s.sendto(token.encode(), address)
    print(f"Token passed to {address[0]}:{address[1]}")


def send_files_or_pass_token():
    while True:
        if I_HAVE_TOKEN:
            send_files()
        if pass_token():

            break

        # simulate copying
        sleep(5)


if __name__ == "__main__":

    # Start broadcasting in a separate thread
    broadcast_thread = threading.Thread(target=broadcast)
    broadcast_thread.start()
    # send file
    send_file_thread = threading.Thread(target=send_files_or_pass_token())
    send_file_thread.start()
    # Start receiving in the main thread
    receive_broadcast(HOST, PORT)
