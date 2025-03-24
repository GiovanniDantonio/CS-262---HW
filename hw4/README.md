
#### **Usage**

- Open the client interface.
- Register or log in.
- Send messages to other registered users.
- Read unread messages when logging in.

## Installation
1. Clone the repository:
   git clone [repo name]
   cd into repo folder
   cd cs2620/hw/hw2

   source venv/bin/activate
   cd reg
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto
   python3 server.py
   python3 client.py


## Running the Script

python3 benchmark_serialization.py

