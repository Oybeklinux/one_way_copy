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
    client_app_socket_list = [server_socket]

    file_name_list = {}

    while client_app_socket_list:
        # Use select to wait for I/O events
        readable, _, exceptional = select.select(client_app_socket_list, [], client_app_socket_list)

        for vm_soket in readable:
            if vm_soket is server_socket:
                # A readable server socket means a new connection
                client_socket, client_address = vm_soket.accept()
                print(f"Connected by {client_address}")
                client_socket.setblocking(0)
                client_app_socket_list.append(client_socket)
                file_path = os.path.join(SAVE_DIRECTORY, f"received_file_{client_address[0]}_{client_address[1]}.py")
                file_name_list[client_socket] = file_path

            else:
                # Read from a client socket
                data = vm_soket.recv(BUFFER_SIZE)
                if data:
                    save_file_chunk(file_name_list[vm_soket], data)
                else:
                    # Interpret empty result as closed connection
                    print(f"Closing connection to {vm_soket.getpeername()}")
                    client_app_socket_list.remove(vm_soket)
                    vm_soket.close()
                    file_path = file_name_list.pop(vm_soket)

                    print(f"Saved file: {file_path}")

        for vm_soket in exceptional:
            # Handle exceptional conditions
            print(f"Handling exceptional condition for {vm_soket.getpeername()}")
            client_app_socket_list.remove(vm_soket)
            vm_soket.close()
            file_path = file_name_list.pop(vm_soket, None)
            if file_path:
                print(f"Saved file: {file_path}")



if __name__ == "__main__":
    main()
