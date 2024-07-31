import os
import socket
import threading
import time
from datetime import datetime, timedelta
from random import choice
from time import sleep
import json
from sync_server.constants import config, TARGETS, THIS_HOST, THIS_PORT, SERVER_PORT, SERVER_IP, DIRECTORY, PC, \
    TIME_THRESHOLD, \
    client_apps, get_settings
from sync_server.constants import TOKEN_TYPE_SEND, TOKEN_TYPE_ACCEPT, TOKEN_STATUS_SEND, TOKEN_STATUS_TOKEN_PASS, \
    TOKEN_STATUS_IDLE

from sync_server.settings import save_files_state, remove_file_name
from sync_server.settings import get_state
from sync_server.constants import settings
from sync_server.settings import save_token_status
from sync_server.log import get_logger
from sync_server.sender import send_file

logger = get_logger(__name__)

TOKEN = ''
TOKEN_STATUS = settings['TOKEN_STATUS']


def get_file_info(directory):
    total_files = 0
    total_size = 0
    state = get_state()
    filenames = state['send_files']

    for filename in filenames:
        try:
            total_size += os.path.getsize(os.path.join(os.path.abspath(directory), filename))
            total_files += 1
        except FileNotFoundError:
            continue

    return total_files, total_size


def receive_broadcast(host, port):
    global TOKEN, TOKEN_STATUS
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    while True:
        data, addr = sock.recvfrom(1024)
        data = data.decode()
        data = json.loads(data)
        # check if it is file info or token_passing
        if 'TOKEN' in data:
            sender_address = tuple(data["SENDER"])
            if data['TYPE'] == TOKEN_TYPE_SEND:
                TOKEN = data['TOKEN']
                TOKEN = data['TOKEN']
                TOKEN_STATUS = TOKEN_STATUS_SEND
                save_token_status(TOKEN_STATUS)
                logger.info(f"Token received from {sender_address}")
                send_accept_token(sender_address)

            elif data['TYPE'] == TOKEN_TYPE_ACCEPT:
                TOKEN_STATUS = TOKEN_STATUS_IDLE
                save_token_status(TOKEN_STATUS)
                logger.info(f"Accept token received. from {sender_address}")
        else:
            save_files_state(data)
            for vm, value in data.items():
                logger.info(f"Received from {vm}: Total files: {value['files']}, Total size: {value['size']} bytes")


def broadcast_file_info():
    while True:
        file_info = get_file_info(DIRECTORY)

        data = {
            PC: {
                "files": file_info[0],
                "size": file_info[1],
            }
        }
        data = json.dumps(data)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        for ip, port in TARGETS:
            if ip != THIS_HOST or port != THIS_PORT:
                logger.info(f"Sending file info to ... {ip} {port}")
                sock.sendto(data.encode(), (ip, port))

        sock.close()
        time.sleep(5)  # Broadcast every 10 seconds


# Function to send a file to server A via TCP


def send_files():

    for dirpath, dirnames, filenames in os.walk(DIRECTORY):
        print(f"Total {len(filenames)} files: {filenames}")

        for filename in filenames:
            # continue if file belongs to another VM
            files_to_be_sent = get_settings('send_files')
            if filename not in files_to_be_sent:
                continue
            try:
                file, ext = filename.split(".")
                file_time = datetime.strptime(file, '%Y-%m-%d-%H-%M-%S')
            except ValueError:
                continue

            file_path = os.path.join(DIRECTORY, filename)
            if (datetime.utcnow() - file_time) > timedelta(minutes=TIME_THRESHOLD):
                os.remove(file_path)
                remove_file_name(filename)
                logger.info(f"Deleted old file: {filename}")
            else:
                try:
                    send_file(file_path, SERVER_IP, SERVER_PORT)
                    logger.info(f"Sent file to server A: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to send file {filename} to server: {e}")
                    return False

        return True


def get_random_vm():
    vm_list = []
    for vm in client_apps:
        if client_apps[vm]['files'] > 0:
            vm_list.append(vm)
    if not vm_list:
        return None

    vm = choice(vm_list)
    return tuple(config['VM_LIST'][vm])


def send_accept_token(address):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        token = {"TOKEN": TOKEN, "TYPE": TOKEN_TYPE_ACCEPT, "SENDER": config["VM_LIST"][PC]}
        token = json.dumps(token)
        s.sendto(token.encode(), address)
    logger.info(f"Accept token was sent to {address[0]}:{address[1]} ")


def pass_token():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        address = get_random_vm()
        if not address:
            return None

        token = {"TOKEN": TOKEN, "TYPE": TOKEN_TYPE_SEND, "SENDER": config["VM_LIST"][PC]}
        token = json.dumps(token)
        s.sendto(token.encode(), address)
    logger.info(f"Token passed to {address[0]}:{address[1]}")
    return True


def generate_token():
    return "sdfdsfsaf"


def send_files_or_pass_token():
    global TOKEN, TOKEN_STATUS
    while True:
        logger.info(f"TOKEN STATUS: {TOKEN_STATUS}")
        if TOKEN_STATUS == TOKEN_STATUS_SEND or TOKEN_STATUS == TOKEN_STATUS_TOKEN_PASS:
            logger.info("Sending files")
            if not send_files():
                logger.warning("Error during sending")
            else:
                logger.info("Sending files finished")
                TOKEN_STATUS = TOKEN_STATUS_TOKEN_PASS
                save_token_status(TOKEN_STATUS)

        if TOKEN_STATUS == TOKEN_STATUS_TOKEN_PASS:
            logger.info("Sending token")
            if pass_token() is None:
                logger.warning(f"No files to copy {datetime.now()}")
            logger.info(f"Sending token finished {datetime.now()}")
            # else:
            #     TOKEN_STATUS = TOKEN_STATUS_IDLE
            sleep(4)  # wait for the token to come back

        if TOKEN_STATUS == TOKEN_STATUS_IDLE:
            logger.info(f"Waiting for token {datetime.now()}")


if __name__ == "__main__":
    TOKEN = generate_token()
    # watchdog
    # watch_files()
    # watch_files_thread = threading.Thread(target=watch_files())

    # Start broadcasting in a separate thread
    broadcast_thread = threading.Thread(target=broadcast_file_info)

    # send file
    send_file_thread = threading.Thread(target=send_files_or_pass_token)

    # receive file info and token
    receive_thread = threading.Thread(target=receive_broadcast, args=(THIS_HOST, THIS_PORT))

    # watch_files_thread.start()
    broadcast_thread.start()

    receive_thread.start()
    send_file_thread.start()

    # Start receiving in the main thread
    # watch_files_thread.join()
    broadcast_thread.join()
    receive_thread.join()
    send_file_thread.join()

    print("THE END")
