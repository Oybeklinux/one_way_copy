import datetime
import socket
import hashlib
import os
import struct
from datetime import datetime

from sync_server.constants import THIS_HOST, BEGIN_DATETIME
from sync_server.log import get_logger

# Define constants
CHUNK_SIZE = 1415
PACKET_SIZE = 1460
IP_LENGTH = 2
OFFSET_LENGTH = 4
FILE_TYPE_LENGTH = 1
TOTAL_CHUNKS_LENGTH = 3
CHUNK_INDEX_LENGTH = 3
HASH_LENGTH = 32

# Example file extensions mapping
FILE_EXTENSIONS = {
    '.txt': 1,
    '.jpg': 2,
    '.png': 3,
    '.pdf': 4,
    '.mkv': 5,
    ".html": 6,
    ".db": 7
    # Add more file types as needed
}

logger = get_logger(__name__)


def get_file_type(file_name):
    _, ext = os.path.splitext(file_name)
    return FILE_EXTENSIONS.get(ext, 0)


def to_bytes(data, size):
    if isinstance(data, int):
        return data.to_bytes(size, byteorder="little")


def create_packet(chunk_data, ip, offset, file_type, total_chunks, chunk_index):
    # Calculate the hash of the chunk
    chunk_hash = hashlib.sha256(chunk_data).digest()

    offset_b = to_bytes(offset, OFFSET_LENGTH)
    file_type_b = to_bytes(file_type, FILE_TYPE_LENGTH)
    total_chunks_b = to_bytes(total_chunks, TOTAL_CHUNKS_LENGTH)
    chunk_index_b = to_bytes(chunk_index, CHUNK_INDEX_LENGTH)
    chunk = ip + offset_b + file_type_b + total_chunks_b + chunk_index_b + chunk_hash + chunk_data
    return chunk


def get_timestamp(file):
    _, file_name = os.path.split(file)
    time_str = file_name.split(".")[0]

    dt = datetime.strptime(time_str, "%Y-%m-%d-%H-%M-%S")
    offset = dt - BEGIN_DATETIME
    if datetime.now() < dt:
        raise Exception('datetime could not be larger then NOW')

    return int(offset.total_seconds())


def send_file(file_name, server_ip, server_port):
    file_size = os.path.getsize(file_name)
    if file_size == 0:
        logger.error(f"File size is 0:{file_name}")
        return
    total_chunks = file_size // CHUNK_SIZE + (1 if file_size % CHUNK_SIZE != 0 else 0)
    file_type = get_file_type(file_name)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    with open(file_name, 'rb') as f:
        for chunk_index in range(total_chunks):
            chunk_data = f.read(CHUNK_SIZE)
            ip = socket.inet_aton(THIS_HOST)[IP_LENGTH:]  # Assuming IP is the same as server for this example
            offset = get_timestamp(file_name)
            packet = create_packet(chunk_data, ip, offset, file_type, total_chunks, chunk_index)
            client_socket.sendall(packet)
            logger.info(f"Sending chunk {chunk_index}. File: {os.path.split(file_name)[1]}")

    client_socket.close()


if __name__ == "__main__":
    send_file('example.txt', '127.0.0.1', 5000)
