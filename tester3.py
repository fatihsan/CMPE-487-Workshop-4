import json
import os
import socket
import time
from threading import Thread
import ast
import select

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

HOST = get_ip_address()
#FOR HAMACHI
#HOST = "25.82.175.84"

PORT = 12345

greeting = "Hi, welcome to our chat client! Please type in your Name:"
MYNAME = input(greeting)

discoveredUsers = dict()
payload = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "DISCOVER", "PAYLOAD":""})
response = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "RESPOND", "PAYLOAD":""})
message = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "MESSAGE", "PAYLOAD":""})
filePackage = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "FILE", "PAYLOAD":"", "serial":""})
AckPackage = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "ACK", "PAYLOAD":"", "serial":"", "rwnd": ""})

goodbyeMessage = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "GOODBYE", "PAYLOAD": ""})
payloadBytes = json.dumps((payload)).encode('utf-8')
responseBytes = json.dumps((response)).encode('utf-8')
goodbyeBytes = json.dumps((goodbyeMessage)).encode('utf-8')
message_to_send=""

def sendACK(incomingData, leftBuffer):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # sock.sendto(payloadBytes, ('<broadcast>', PORT))
    AckPackage['serial'] = incomingData["serial"]
    AckPackage['rwnd'] = leftBuffer
    AckPackageBytes = json.dumps((AckPackage)).encode('utf-8')
    sock.sendto(payloadBytes, ('25.255.255.255', PORT))

    print("Discover Broadcast sent")


def putFileTogether(dataformat):
    list = os.listdir("chunks")  # dir is your directory path
    number_files = len(list)
    temp_file = open('temp.txt', 'wb+')
    for i in number_files:
        chunk_file = open(i+'.txt', 'rb')
        temp_file.write(chunk_file)


    if dataformat== "img":
        with open('images/stitched_together.jpg', 'wb') as image:
            for f in temp_file:
                image.write(f)



def receiveUDP():
    bufferSize = 1024
    print("listening to any UDP messages")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', PORT))
        #s.setblocking(0)

        while True:
            result = select.select([s], [], [])
            data = result[0][0].recv(bufferSize)
            #print(data)
            if data:
                dataDecoded = data.decode('utf-8')
                incomingData = json.loads(dataDecoded)
                if(incomingData["MY_IP"]== HOST):
                    continue
                #print("receiving message")
                if (incomingData["TYPE"]=="FILE"):
                    if (os.path. exists('chunks/'+incomingData["serial"]+'.txt')):
                        print("ALREADY HAVE THIS CHUNK")
                    else:
                        if incomingData["serial"] == 0:
                            putFileTogether("img")
                        else:
                            chunk_file = open('chunks/'+incomingData["serial"]+'.txt', 'wb+')
                            chunk_file.write(incomingData["PAYLOAD"].decode())
                            chunk_file.close()
                            #respond with ACK inclusing remaining buffer --> here hardcoded
                            sendACK(incomingData,1500)
                if (incomingData["TYPE"]=="DISCOVER"):
                    if ((incomingData["NAME"] in discoveredUsers)):
                        print("")
                    else:
                        discoveredUsers[incomingData["NAME"]] = {"IP":incomingData["MY_IP"], "STATUS":"online"}
                        print("New Chat Partner found!"+ "---- Name: "+ incomingData["NAME"])
                        #respond(incomingData)
                if (incomingData["TYPE"] == "GOODBYE"):
                    try:
                        if (discoveredUsers[incomingData["NAME"]]["STATUS"]=="offline"):
                            print("")
                        else:
                            discoveredUsers[incomingData["NAME"]] = {"IP": incomingData["MY_IP"], "STATUS": "offline"}
                            print(" Chat Partner " + incomingData["NAME"]+ " is now OFFLINE")
                    except KeyError:
                        print("")


t2 = Thread(target=receiveUDP, args=(),daemon=True)
t2.start()

time.sleep(300)