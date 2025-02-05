import json


def send_json(sock, obj):
    """Send a JSON object over the socket, appending a newline as delimiter."""
    try:
        msg = json.dumps(obj) + "\n"
        sock.sendall(msg.encode('utf-8'))
    except Exception as e:
        return f"Error sending JSON: {e}"


def recv_json(sock):
    """Receive a JSON object from the socket assuming each message is newline delimited."""
    try:
        # Create a file-like object to read one line at a time
        f = sock.makefile('r')
        line = f.readline()
        if not line:
            return None
        return json.loads(line)
    except Exception as e:
        return f"Error receiving JSON: {e}"
