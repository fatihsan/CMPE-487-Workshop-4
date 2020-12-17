import json
import socket
import sys
import time
from threading import Thread
import ast
import select

CHUNK_SIZE = 500

# Location of source image
image_file = 'images/cover.jpg'
#filePackage = dict({"index":"i", "hash": "xx", "chunk": "MESSAGE"})
filePackage = dict({"NAME":"MYNAME", "MY_IP": "HOST", "TYPE": "FILE", "PAYLOAD":"", "serial":""})



PORT = 12345
#DISCOVER
def discover():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    #chunk_file = open('chunkfile.txt', 'wb+')
    i = 0
    with open(image_file, 'rb') as infile:
        while True:
            i = i+1
            # Read 430byte chunks of the image
            chunk = infile.read(CHUNK_SIZE)
            filePackage["serial"]= i
            print(type(chunk))
            print(sys.getsizeof(chunk))
            filePackage["PAYLOAD"] = chunk.decode('utf-8')
            packageEncoded= json.dumps(filePackage).encode('utf-8')

            sock.sendto(packageEncoded, ('<broadcast>', PORT))
            if not chunk:
                filePackage["serial"] = 0
                filePackage["PAYLOAD"] = ""
                packageEncoded = json.dumps(filePackage).encode('utf-8')
                sock.sendto(packageEncoded, ('<broadcast>', PORT))
                break


    #sock.sendto("payloadBytes".encode(), ('25.255.255.255', PORT))

    print("Discover Broadcast sent")

discover()

