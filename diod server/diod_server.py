import json
import socket
import hashlib
import os
import threading
from datetime import datetime, timedelta

from sync_server.log import get_logger

logger = get_logger(__name__)
# Define constants
PACKET_SIZE = 1460
IP_LENGTH = 2
OFFSET_LENGTH = 4
FILE_TYPE_LENGTH = 1
TOTAL_CHUNKS_LENGTH = 3
CHUNK_INDEX_LENGTH = 3
HASH_LENGTH = 32
CHUNK_SIZE = 1415
BIT_ARRAY_SIZE = 2 ** 24 // 8  # 2MB bit array to hold 2**24 bits

# Example file extensions mapping
FILE_EXTENSIONS = {
    1: '.txt',
    2: '.jpg',
    3: '.png',
    # Add more file types as needed
}


def create_empty_file(file_path, total_size):
    with open(file_path, 'wb') as f:
        f.seek(total_size - 1)
        f.write(b'\0')


def handle_payload(ip, offset, file_type, total_chunks, chunk_index, chunk_hash, chunk_data, file_data):
    folder_path = f"./resource/{ip}"
    os.makedirs(folder_path, exist_ok=True)
    file_extension = FILE_EXTENSIONS.get(file_type, '.bin')
    file_path = os.path.join(folder_path, f"{offset}.{file_extension}")
    bit_array_path = file_path + '.bitarray'

    if not os.path.exists(file_path):
        create_empty_file(file_path, total_chunks * CHUNK_SIZE)
        with open(bit_array_path, 'wb') as f:
            f.write(bytearray(BIT_ARRAY_SIZE))

    with open(bit_array_path, 'r+b') as f:
        bit_array = bytearray(f.read())
        byte_index = chunk_index // 8
        bit_index = chunk_index % 8
        if not (bit_array[byte_index] & (1 << bit_index)):
            with open(file_path, 'r+b') as file:
                file.seek(chunk_index * CHUNK_SIZE)
                file.write(chunk_data)
                bit_array[byte_index] |= (1 << bit_index)
                f.seek(0)
                f.write(bit_array)
                f.flush()
                bit_array = bytearray(f.read())

            if all((bit_array[i // 8] & (1 << (i % 8))) for i in range(total_chunks)):
                with open(file_path, 'rb') as file:
                    complete_data = file.read()
                    if hashlib.sha256(complete_data).digest() == chunk_hash:
                        print(f"File {file_path} received completely and verified.")
                        os.remove(bit_array_path)
                    else:
                        print(f"File {file_path} hash mismatch. Waiting for re-transmission.")
                        os.remove(file_path)
                        os.remove(bit_array_path)
        else:
            print(f"Chunk {chunk_index} already received, ignoring...")


def bytes_2_int(data):
    if isinstance(data, int):
        return int.from_bytes(data, byteorder='little')


def unpack(packet: bytes):
    start_index = 0
    ip_b = packet[start_index:IP_LENGTH]
    ip = socket.inet_ntoa(ip_b)

    start_index += IP_LENGTH
    offset_b = packet[start_index: OFFSET_LENGTH]
    offset = bytes_2_int(offset_b)

    start_index += OFFSET_LENGTH
    file_type_b = packet[start_index: FILE_TYPE_LENGTH]
    file_type = bytes_2_int(file_type_b)

    start_index += FILE_TYPE_LENGTH
    total_chunks_b = packet[start_index: TOTAL_CHUNKS_LENGTH]
    total_chunks = bytes_2_int(total_chunks_b)

    start_index += TOTAL_CHUNKS_LENGTH
    chunk_index_b = packet[start_index: CHUNK_INDEX_LENGTH]
    chunk_index = bytes_2_int(chunk_index_b)

    start_index += CHUNK_INDEX_LENGTH
    chunk_hash = packet[start_index: HASH_LENGTH]

    start_index += HASH_LENGTH
    chunk_data = packet[start_index: CHUNK_SIZE]

    return ip, offset, file_type, total_chunks, chunk_index, chunk_hash, chunk_data


def handle_client_connection(client_socket):
    while True:
        packet = client_socket.recv(PACKET_SIZE)
        if not packet:
            break
        ip, offset, file_type, total_chunks, chunk_index, chunk_hash, chunk_data = unpack(packet)

        if chunk_hash != hashlib.sha256(chunk_data).digest():
            logger.error(f"Hash value is wrong. Hash: {chunk_hash}. Chunk index: {chunk_index}")
            continue
        if file_type not in FILE_EXTENSIONS:
            logger.error(f"There is no such file extension: {file_type}. Chunk index: {chunk_index}")
            continue
        if ip not in TARGETS:
            logger.error(f"No such ip address. IP: {ip}")
            continue

        now = datetime.utcnow()
        time_10m_before = now - timedelta(minutes=TIME_THRESHOLD)
        if not (time_10m_before < offset < now):
            logger.error(f"Invalid offset. Offset{offset}")
            continue
        if chunk_index >= total_chunks:
            logger.error("Chunk_index can not be larger then total_indeks")
            continue

        handle_payload(ip, offset, file_type, total_chunks, chunk_index, chunk_hash, chunk_data, packet)

    client_socket.close()


def start_server(server_ip, server_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    print(f"Server listening on {server_ip}:{server_port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
        client_handler.start()


def get_config():
    with open('sync_server/config.json', 'r') as file:
        return json.load(file)


if __name__ == "__main__":

    config = get_config()
    TIME_THRESHOLD = config['TIME_THRESHOLD']
    # get all ip address
    TARGETS = [ip[0] for ip in config['VM_LIST'].values()]
    start_server('127.0.0.1', 12345)
