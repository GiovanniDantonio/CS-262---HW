import socket
import struct

# Custom wire protocol
HEADER_SIZE = 4

def send_packet(sock, data):
    encoded_data = data.encode('utf-8')
    packet = struct.pack(f'!I{len(encoded_data)}s', len(encoded_data), encoded_data)
    sock.sendall(packet)

def recv_packet(sock):
    header = sock.recv(HEADER_SIZE)
    if not header:
        return None
    data_length = struct.unpack('!I', header)[0]
    data = sock.recv(data_length).decode('utf-8')
    return data
