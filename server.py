# version 1.0 identify each car with their port number
import pickle
import random
import socket
# import sys
import threading
import time
import PVIS
import json
import data_class
import GPS
from distance_calculator import calculate_distance
import TOF_sensor
HOST = '' #change this to the ad hoc connection IP
PORT = 12345
svis=PVIS.PVIS(stop_mark=20,Nmax=53, Kmax=9, alphaD=0.0267, alphaV=0.0102, ehg=2.5)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print('server started，waiting for client connection...')
client_connections = []
client_addresses = []
lock = threading.Lock()
lock2 = threading.Lock()
lock3 = threading.Lock()
GPS_info_dict={}
GPS_info_dict["n"] = []
GPS_info_dict["k"] = []
GPS_info_dict["Ego GPS time"] = []
GPS_info_dict["V2V GPS time"] = []
GPS_info_dict["Sensor time"] = []
GPS_info_dict["PVIS time"] = []
sensor_info=[]
data_for_server=None
speed_from_TOF=None
distance_from_TOF=None
time_sensor_recv = None
time_GPS = None
time_sensor = None
time_PIVS = None
flag = False
time_start = time.time()


# def read_gps_data():
#     global data_for_server
#     try:
#         code_for_testing.setup()
#     except KeyboardInterrupt:
#         code_for_testing.destroy()
#     while True:
#         data_for_server=code_for_testing.calculate_data()
#         if data_for_server==None:
#             continue

def read_gps_data():
    global data_for_server
    global time_GPS
    while True:
        data_for_server=GPS.run()
        if data_for_server==None:
            continue
        time_GPS = time.time() - time_start


def read_TOF_data():
    global speed_from_TOF
    global distance_from_TOF
    global time_sensor
    while True:
        distance_from_TOF,speed_difference_from_TOF=TOF_sensor.get_speed_and_distance()
        if distance_from_TOF==None:
            continue
        if data_for_server == None:
            continue
        speed_from_TOF=speed_difference_from_TOF+data_for_server.speed
        time_sensor = time.time() - time_start


def generate_noise():
    speedGPS=random.uniform(11, 20)
    distanceGPS=random.uniform(11, 20)
    GPS_noise=[distanceGPS,speedGPS]
    return GPS_noise


def handle_client(client_socket, client_address):
    global data_from_client
    global GPS_info_dict
    list_GPS=[]
    list_handle=[]
    while True:
        if distance_from_TOF == None:
            continue
        try:
            # data = client_socket.recv(1024).decod
            with lock:
                data_rev = client_socket.recv(1024)
                if not data_rev:
                    continue
                time_final_GPS_recv = time.time()
                data = pickle.loads(data_rev)
            if data_for_server is not None:
                x=calculate_distance(data.latitude,data.longitude,data_for_server.latitude, data_for_server.longitude)
                port_number=client_address
                speed=data.speed
                GPS_info=[x,speed]
                with lock3:
                    if GPS_info_dict.__contains__(port_number):
                        GPS_info_dict[port_number].append(GPS_info)
                    else:
                        GPS_info_dict[port_number]=[GPS_info]
                    GPS_noise=generate_noise()
                    if GPS_info_dict.__contains__(1):
                        GPS_info_dict[1].append(GPS_noise)
                    else:
                        GPS_info_dict[1]=[GPS_noise]
                    sensor_info.append([distance_from_TOF, speed_from_TOF])

                flag,n,k =svis.run_step(GPS_info_dict,sensor_info)

                time_PVIS = time.time() - time_start
                print("Ego GPS data receive time: ", time_GPS)
                print("V2V GPS data receive time: ", time_final_GPS_recv-time_start)
                print("Sensor data receive time: ", time_sensor)
                print("PVIS iteration time: ", time_PVIS, "\n")

                GPS_info_dict["n"].append(n)
                GPS_info_dict["k"].append(k)
                GPS_info_dict["Ego GPS time"].append(time_GPS)
                GPS_info_dict["V2V GPS time"].append(time_final_GPS_recv-time_start)
                GPS_info_dict["Sensor time"].append(time_sensor)
                GPS_info_dict["PVIS time"].append(time_PVIS)
                if flag==True:
                    print("ALL DONE")
                    num = random.randint(0,100)
                    file_path = f"./output_{num}.csv"
                    GPS_info_dict["Sensor_info_list"]=sensor_info
                    # results = pd.DataFrame.from_dict(GPS_info_dict) 
                    with open(file_path, "w") as file:
                        json.dump(GPS_info_dict,file)
                    
                    # results.to_csv(f'test-{num}.csv')    
                    print(f"Successfully write in Test {num}！")
                    return



            # main thread： loop over and over to wait for clients to connect
            # thread 1(could be 1 to n, n is how many client has connected): run handle client for each client connected, which contains receiving GPS data from that client
            # thread 2: run GPS reader for server
            # thread 3: run TOF reader for server


        except Exception as e:
            print(e)
            raise Exception("error is here")
            # break

    with lock2:
        index = client_connections.index(client_socket)
        client_connections.remove(client_socket)
        client_addresses.pop(index)
        client_socket.close()


GPS.setup()
server_gps= threading.Thread(target=read_gps_data)
server_gps.start()

TOF_sensor.setUp()
server_TOF=threading.Thread(target=read_TOF_data)
server_TOF.start()


while True:
    client_socket, addr = server_socket.accept()
    print('connection established:', addr[1])

    with lock2:
        client_connections.append(client_socket)
        client_addresses.append(addr[1])

    client_thread = threading.Thread(target=handle_client, args=(client_socket, addr[1]))
    client_thread.start()
