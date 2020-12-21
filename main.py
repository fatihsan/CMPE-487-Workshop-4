import json
import os
import socket
import time
from threading import Thread
import ast
import select
import hashlib
import shutil
import random
import base64

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

HOST = get_ip_address()
#FOR HAMACHI
#HOST = "25.82.175.84"
print(HOST)

PORT = 12345

greeting = "Hi, welcome to our chat client! Please type in your Name:"
MYNAME = input(greeting)

discoveredUsers = dict()
payload = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "DISCOVER", "PAYLOAD":""})
response = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "RESPOND", "PAYLOAD":""})
message = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "MESSAGE", "PAYLOAD":""})
filePackage = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "FILE", "PAYLOAD":"", "SERIAL":""})
chunkPackage = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "CHUNK", "PAYLOAD":"", "SERIAL": ""})
AckPackage = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "ACK", "PAYLOAD":"", "SERIAL":"", "RWND": ""})

goodbyeMessage = dict({"NAME":MYNAME, "MY_IP": HOST, "TYPE": "GOODBYE", "PAYLOAD": ""})
payloadBytes = json.dumps((payload)).encode('utf-8')
responseBytes = json.dumps((response)).encode('utf-8')
goodbyeBytes = json.dumps((goodbyeMessage)).encode('utf-8')
message_to_send=""
acks_received = []
chunk_amounts = {}
chunk_amounts_user = {}
is_transfer_done = {}
list_of_chunks_transfered = {}
chunk_sent = 0

#DISCOVER
def discover():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(payloadBytes, ('<broadcast>', PORT))
    #sock.sendto(payloadBytes, ('25.255.255.255', PORT))

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

# every client should have a list of serial numbers of chunks that they have.

# client 1 has all the chunks.
# client 2 asks for the file, but is halfway there. he has half of them right now.
# client 3 asks for the same file.

# client 1 says I have all 10
# client 2 says I have 0 to 4
# client 3 asks 0 to 4 from client 2, 4 to 10 from client 1.


# a client asks for seperate chunks of a file in broadcast mode.
# available senders send the chunk in question.
# receiver listens all the time.
# if 

def get_cwd():
    return str(os.getcwd())

def get_hash(data):
    sha1 = hashlib.sha1(data)
    result = sha1.hexdigest()
    return result

def generate_packet(type_, payload_, serial_, rwnd_, filename_):
    packet = dict({
        "NAME":MYNAME, 
        "MY_IP": HOST, 
        "TYPE": type_, 
        "PAYLOAD": payload_
        })
    if serial_:
        packet["SERIAL"] = serial_
    if len(rwnd_) > 0:
        packet["RWND"] = rwnd_
    if type_ == "FILE" or type_ == "CHUNK" or type_ == "FILEREQ":
        packet["FILENAME"] = filename_
    return packet

def read_in_chunks(file_object, chunk_size):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def create_temp(filename):
    if os.path.isfile('{}'.format(str(filename))):
        with open('{}'.format(str(filename)), "rb") as f:
            if (os.path.exists('{}_temp'.format(filename))):
                shutil.rmtree('{}/{}_temp'.format(get_cwd(), str(filename)))
            os.mkdir('{}_temp'.format(str(filename)))
            os.chdir('{}/{}_temp'.format(get_cwd(), str(filename)))
            index = 0
            for chunk in read_in_chunks(f, 1000):
                hash_ = get_hash(chunk)
                chunk_file = open('{}.txt'.format(index), 'wb+')
                chunk_file.write(chunk)
                chunk_file.close()
                index = index + 1
            os.chdir("..")
        return True
    else:
        return False


def request_chunk_info(filename):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #sock.sendto(payloadBytes, ('<broadcast>', PORT))
    packet = generate_packet("CHUNK", "", -1, "", filename)
    chunk_amounts_user[filename] = []
    packetBytes = json.dumps(packet).encode('utf-8')
    sock.sendto(packetBytes, ('<broadcast>', PORT))

def request_chunk(filename, destination_ip, serial):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    #sock.sendto(payloadBytes, ('<broadcast>', PORT))
    packet = generate_packet("FILEREQ", "", serial, "", filename)
    packetBytes = json.dumps(packet).encode('utf-8')
    sock.sendto(packetBytes, (destination_ip, PORT))

def request_file():
    print("If you want to abort file request, type in ABORT")
    filename = input("Name of the file:")
    file_type = ""
    if filename == "ABORT":
        pass
    else:
        while ("." not in filename):
            filename = input("Please type in the correct format.")
        temp = filename.split(".")
        file_type = temp[1]

        chunk_amounts[filename] = 0
        request_chunk_info(filename)
        time.sleep(1)
        list_of_chunks_to_request = []
        list_of_users_with_chunks = chunk_amounts_user[filename]
        list_of_chunks_transfered[filename] = []
        is_transfer_done[filename] = False

        for user in list_of_users_with_chunks:
            for chunk_id in user[1]:
                list_of_chunks_to_request.append((user[0], chunk_id))
        

        while not is_transfer_done[filename]:
            #print("possible chunks to request :  "+ str(len(list_of_chunks_to_request)) )
            for pair in list_of_chunks_to_request:
                if pair[1] in list_of_chunks_transfered:
                    list_of_chunks_to_request.remove(pair)
            
            random_request = random.choice(list_of_chunks_to_request)
            request_chunk(filename, random_request[0], random_request[1])
    time.sleep(1)
    putFileTogether(file_type, filename)


def send_chunk(incomingData):
    f = open('{}_temp/{}.txt'.format(incomingData["FILENAME"], incomingData["SERIAL"]), "rb")
    data = f.read()
    data_base64 = base64.encodebytes(data)

    decoded = data_base64.decode('utf-8')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    
    packet = generate_packet("FILE", decoded, incomingData["SERIAL"], "", incomingData["FILENAME"])
    packetBytes = json.dumps(packet).encode('utf-8')
    print("acks received:  "+str(len(acks_received)))

    sock.sendto(packetBytes, (incomingData["MY_IP"], PORT))

            

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


def sendACK(incomingData, leftBuffer):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # sock.sendto(payloadBytes, ('<broadcast>', PORT))
    AckPackage['SERIAL'] = incomingData["SERIAL"]
    AckPackage['RWND'] = leftBuffer
    AckPackage['FILENAME'] = incomingData['FILENAME']
    AckPackageBytes = json.dumps((AckPackage)).encode('utf-8')
    sock.sendto(AckPackageBytes, (incomingData["MY_IP"], PORT))

    print("ack senttt!!!!")
    

def send_chunk_info(packet, receiver_ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    packetBytes = json.dumps((packet)).encode('utf-8')
    sock.sendto(packetBytes, (receiver_ip, PORT))
    #sock.sendto(payloadBytes, ('25.255.255.255', PORT))

    print("chunk info sent!!!")


def putFileTogether(dataformat, filename):
    temp_file = open('{}.txt'.format(filename), 'wb+')
    chunk_list = os.listdir('{}/{}_temp/'.format(get_cwd(), filename))  # dir is your directory path
    number_files = len(chunk_list)
    os.chdir('{}/{}_temp/'.format(get_cwd(), filename))
    for i in range(number_files):
        chunk_file = open('{}.txt'.format(str(i)), 'rb')
        data = chunk_file.read()
        print(type(data))
        temp_file.write(data)



def receiveUDP():
    bufferSize = 1500
    print("listening to any UDP messages")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', PORT))
        #s.setblocking(0)

        while True:
            result = select.select([s], [], [])
            data = result[0][0].recv(bufferSize)
            #print(data)
            if data:
                #print("data::   "+str(type(data)))
                dataDecoded = data.decode('utf-8')
                #print(data)
                incomingData = json.loads(dataDecoded)
                if(incomingData["MY_IP"]== HOST):
                    continue 
                #print("receiving message")
                if incomingData["TYPE"] == "CHUNK":
                    if incomingData["SERIAL"] == -1:
                        list_of_chunks = []
                        if (os.path.exists('{}'.format(incomingData["FILENAME"]))):
                            create_temp(incomingData["FILENAME"])
                            for filename in os.listdir('{}/{}_temp/'.format(get_cwd(), incomingData["FILENAME"])):
                                list_of_chunks.append(filename[:-4])
                        elif (os.path.exists('{}/{}_temp/'.format(get_cwd(), incomingData["FILENAME"]))):
                            for filename in os.listdir('{}/{}_temp/'.format(get_cwd(), incomingData["FILENAME"])):
                                list_of_chunks.append(filename[:-4])
                        else:
                            pass
                        sender_ip = incomingData["MY_IP"]
                        respPackage = chunkPackage
                        respPackage["PAYLOAD"] = list_of_chunks
                        respPackage["SERIAL"] = len(list_of_chunks)   
                        respPackage["FILENAME"] = incomingData["FILENAME"]                          

                        send_chunk_info(respPackage, sender_ip)

                    elif incomingData["SERIAL"] > 0:
                        temp_list = chunk_amounts_user[incomingData["FILENAME"]]
                        temp_list.append((incomingData["MY_IP"], incomingData["PAYLOAD"]))
                        chunk_amounts_user[incomingData["FILENAME"]] = temp_list
                        chunk_amounts[incomingData["FILENAME"]] = max(incomingData["SERIAL"], chunk_amounts[incomingData["FILENAME"]])
                
                if incomingData["TYPE"] == "FILEREQ":
                    if (os.path.exists('{}_temp/{}.txt'.format(incomingData["FILENAME"], incomingData["SERIAL"]))):
                        send_chunk(incomingData)
                    else:
                        pass
                if incomingData["TYPE"] == "ACK":
                    acks_received.append((incomingData["MY_IP"], incomingData["FILENAME"], incomingData["SERIAL"]))
                if (incomingData["TYPE"]=="FILE"):
                    if (os.path.exists('{}/{}_temp/{}.txt'.format(get_cwd(), incomingData["FILENAME"], incomingData["SERIAL"]))):
                        print("ALREADY HAVE THIS CHUNK")
                    else:
                        if incomingData["SERIAL"] == -314235:
                            putFileTogether("img")
                        else:
                            if not os.path.exists('{}/{}_temp/'.format(get_cwd(), incomingData["FILENAME"])):
                                os.mkdir('{}/{}_temp/'.format(get_cwd(), incomingData["FILENAME"]))
                            print("we are here "+ str(incomingData["SERIAL"]))
                            os.chdir('{}/{}_temp/'.format(get_cwd(), incomingData["FILENAME"]))
                            chunk_file = open('{}.txt'.format(incomingData["SERIAL"]), 'wb+')
                            encoded = incomingData["PAYLOAD"].encode('utf-8')
                            decoded_base64 = base64.decodebytes(encoded)
                            chunk_file.write(decoded_base64)
                            chunk_file.close()
                            temp_list = list_of_chunks_transfered[incomingData["FILENAME"]]
                            temp_list.append(incomingData["SERIAL"])
                            list_of_chunks_transfered[incomingData["FILENAME"]] = temp_list
                            os.chdir('..')
                            #respond with ACK inclusing remaining buffer --> here hardcoded
                            sendACK(incomingData,1500)
                    if len(os.listdir('{}/{}_temp/'.format(get_cwd(), incomingData["FILENAME"]))) == chunk_amounts[incomingData["FILENAME"]]:
                        is_transfer_done[incomingData["FILENAME"]] = True
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

def display_help():
    print("to exit/stop Chat client at any time please type GOODBYE")
    print("to show available partners type in SHOW")
    print("to request a file type in FILE")
    print("to get the command list, type in HELP")


partnerName =""
display_help()

while(True):
    if (len(discoveredUsers)==0):
        print("no chat partner found yet")
        time.sleep(1)
        continue
    showPartners("SHOW")
    message_to_send =""
    partnerName = input("To send a Message type in the Name of a Chat partner")
    checkIfGoodbye(partnerName)
    #print("this is his NAme: "+partnerName)
    if partnerName == "FILE":
        request_file()
    elif partnerName == "HELP":
        display_help()
    elif partnerName in discoveredUsers:
        print(("please type in your message (to go back to the menu type in EXIT)"))
        print(("to request a file, please go back to the menu and type in REQUEST"))
        while(message_to_send!="EXIT"):

            message_to_send = input("your message to: "+ partnerName)
            checkIfGoodbye(message_to_send)
            if(message_to_send=="EXIT"):
                continue
            send_Message(partnerName,message_to_send)
    else:
        print("Couldn't find Chat-Partner. Please choose one of the following Names")
        #checkIfGoodbye(partnerName)

