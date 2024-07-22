import socket
import select
import os

# Server configuration
SERVER_IP = 'localhost'  # Listen on all interfaces
SERVER_PORT = 12345
SAVE_DIRECTORY = 'downloads'
BUFFER_SIZE = 4096

# Ensure the save directory exists
os.makedirs(SAVE_DIRECTORY, exist_ok=True)


def save_file_chunk(file_path, data):
    with open(file_path, 'ab') as f:  # Append in binary mode
        f.write(data)


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(5)
    server_socket.setblocking(0)
    print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

    # List of sockets to be monitored for incoming connections
    inputs = [server_socket]
    outputs = []
    message_queues = {}
    file_handles = {}

    while inputs:
        # Use select to wait for I/O events
        readable, writable, exceptional = select.select(inputs, outputs, inputs)

        for vm_soket in readable:
            if vm_soket is server_socket:
                # A readable server socket means a new connection
                client_socket, client_address = vm_soket.accept()
                print(f"Connected by {client_address}")
                client_socket.setblocking(0)
                inputs.append(client_socket)
                file_path = os.path.join(SAVE_DIRECTORY, f"received_file_{client_address[0]}_{client_address[1]}.py")
                file_handles[client_socket] = file_path
                message_queues[client_socket] = b""
            else:
                # Read from a client socket
                data = vm_soket.recv(BUFFER_SIZE)
                if data:
                    save_file_chunk(file_handles[vm_soket], data)
                else:
                    # Interpret empty result as closed connection
                    print(f"Closing connection to {vm_soket.getpeername()}")
                    inputs.remove(vm_soket)
                    if vm_soket in outputs:
                        outputs.remove(vm_soket)
                    vm_soket.close()
                    file_path = file_handles.pop(vm_soket)
                    message_queues.pop(vm_soket, None)
                    print(f"Saved file: {file_path}")

        for vm_soket in exceptional:
            # Handle exceptional conditions
            print(f"Handling exceptional condition for {vm_soket.getpeername()}")
            inputs.remove(vm_soket)
            if vm_soket in outputs:
                outputs.remove(vm_soket)
            vm_soket.close()
            file_path = file_handles.pop(vm_soket, None)
            if file_path:
                print(f"Saved file: {file_path}")
            message_queues.pop(vm_soket, None)


if __name__ == "__main__":
    main()
