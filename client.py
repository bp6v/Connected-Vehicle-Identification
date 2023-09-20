import pickle
import socket
import threading
import time
import GPS

HOST = '' #change this to the ad hoc connection IP
PORT = 12345
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
print('connection started')
count=0
while True:
    message = GPS.run()
    if message == None:
        continue
    message_wrap = pickle.dumps(message)
    client_socket.sendall(message_wrap)



client_socket.close()
