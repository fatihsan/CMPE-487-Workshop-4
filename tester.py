import json
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
goodbyeMessage = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "GOODBYE", "PAYLOAD": ""})
payloadBytes = json.dumps((payload)).encode('utf-8')
responseBytes = json.dumps((response)).encode('utf-8')
goodbyeBytes = json.dumps((goodbyeMessage)).encode('utf-8')
message_to_send=""



#DISCOVER
def discover():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #sock.sendto(payloadBytes, ('<broadcast>', PORT))
    sock.sendto(payloadBytes, ('25.255.255.255', PORT))

    print("Discover Broadcast sent")

#Goodbye
def goodbye():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #sock.sendto(goodbyeBytes, ('<broadcast>', PORT))
    sock.sendto(goodbyeBytes, ('25.255.255.255', PORT))

if(len(discoveredUsers)!=0):
    print("We've found "+ str(len(discoveredUsers)) +" chat partner")
    for key in discoveredUsers:
            print(key)


def respond(incomingData):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((incomingData["MY_IP"], PORT))
        s.send(responseBytes)
        #print("Response sent to " + (incomingData["MY_IP"]))
        # data = s.recv(1024)
        # print(data)
        s.close()



def send_Message(name, messagePayload):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((discoveredUsers[name]["IP"], PORT))
            message["PAYLOAD"]= messagePayload
            messageBytes = json.dumps((message)).encode('utf-8')
            s.send(messageBytes)
            print("ME: "+ messagePayload)
            s.close()
    except ConnectionRefusedError:
        print("unexpected offline client detected")


def receiveTCP():
    print("listening to any TCP messages")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()

        while True:
            conn, addr = s.accept()
            with conn:
                #print('Connected by', addr)
                data = conn.recv(1024)
                #print("receiving message")
                #print(data)

                if data:
                    dataDecoded = data.decode('utf-8')
                    incomingData = json.loads(dataDecoded)
                    if (incomingData["TYPE"] == "MESSAGE"):
                        print("\n"+incomingData["NAME"] +":" + incomingData["PAYLOAD"])
                    if (incomingData["TYPE"] == "RESPOND"):
                        discoveredUsers[incomingData["NAME"]] = {"IP":incomingData["MY_IP"], "STATUS":"online"}
                        print("New Chat Partner found!" + "Name:" + incomingData["NAME"])

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
                if (incomingData["TYPE"]=="DISCOVER"):
                    if ((incomingData["NAME"] in discoveredUsers)):
                        print("")
                    else:
                        discoveredUsers[incomingData["NAME"]] = {"IP":incomingData["MY_IP"], "STATUS":"online"}
                        print("New Chat Partner found!"+ "---- Name: "+ incomingData["NAME"])
                        respond(incomingData)
                if (incomingData["TYPE"] == "GOODBYE"):
                    try:
                        if (discoveredUsers[incomingData["NAME"]]["STATUS"]=="offline"):
                            print("")
                        else:
                            discoveredUsers[incomingData["NAME"]] = {"IP": incomingData["MY_IP"], "STATUS": "offline"}
                            print(" Chat Partner " + incomingData["NAME"]+ " is now OFFLINE")
                    except KeyError:
                        print("")





t1 = Thread(target=receiveTCP, args=(),daemon=True)
t1.start()
t2 = Thread(target=receiveUDP, args=(),daemon=True)
t2.start()

discover()
discover()
discover()

def checkIfGoodbye(user_input):
    if (user_input == "GOODBYE"):

        goodbye()
        goodbye()
        goodbye()
        print("GOODBYE SENT")
        time.sleep(5)
        exit()

def showPartners(user_input):
    if (user_input == "SHOW"):
        print("following User are available/online:")
        for user in discoveredUsers:
            if(discoveredUsers[user]['STATUS']=="online"):
                print(user)
partnerName =""
while(True):
    if (len(discoveredUsers)==0):
        print("no chat partner found yet")
        time.sleep(10)
        continue

    showPartners("SHOW")
    message_to_send =""
    print("to exit/stop Chat client at any time please type GOODBYE")
    print("to show available partners type in SHOW")
    partnerName = input("To send a Message type in the Name of a Chat partner")
    checkIfGoodbye(partnerName)
    #print("this is his NAme: "+partnerName)
    if partnerName in discoveredUsers:
        print(("please type in your message (to go back to the menu typ in EXIT)"))
        while(message_to_send!="EXIT"):

            message_to_send = input("your message to: "+ partnerName)
            checkIfGoodbye(message_to_send)
            if(message_to_send=="EXIT"):
                continue
            send_Message(partnerName,message_to_send)
    else:
        print("Couldn't find Chat-Partner. Please choose one of the following Names")
        #checkIfGoodbye(partnerName)








# SPLIT IMAGE APART
# Maximum chunk size that can be sent
CHUNK_SIZE = 1500

# Location of source image
image_file = 'images/001.jpg'

# This file is for dev purposes. Each line is one piece of the message being sent individually
chunk_file = open('chunkfile.txt', 'wb+')

with open(image_file, 'rb') as infile:
    while True:
        # Read 430byte chunks of the image
        chunk = infile.read(CHUNK_SIZE)
        if not chunk: break

        # Do what you want with each chunk (in dev, write line to file)
        chunk_file.write(chunk)

chunk_file.close()

# STITCH IMAGE BACK TOGETHER
# Normally this will be in another location to stitch it back together
read_file = open('chunkfile.txt', 'rb')

# Create the jpg file
with open('images/stitched_together.jpg', 'wb') as image:
    for f in read_file:
        image.write(f)
