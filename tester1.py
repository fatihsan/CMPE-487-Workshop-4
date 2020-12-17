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





chunk_file = open('chunkfile.txt', 'wb+')
list = {}
list = []
def receiveUDP():
    bufferSize = 1533
    print("listening to any UDP messages")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', PORT))
        #s.setblocking(0)
        while True:
            result = select.select([s], [], [])
            data = result[0][0].recv(bufferSize)

            #print(data)
            if data:
                #datadecoded = data.decode()
                #print(datadecoded)

                list.insert(i, x)
                chunk_file.write(data)
                print(data)

                if data == "end".encode():
                    chunk_file.close()
                    read_file = open('chunkfile.txt', 'rb')
                    with open('images/stitched_together.jpg', 'wb') as image:
                        for f in read_file:
                            image.write(f)




t2 = Thread(target=receiveUDP, args=(),daemon=True)
t2.start()

time.sleep(200)





# # SPLIT IMAGE APART
# # Maximum chunk size that can be sent
# CHUNK_SIZE = 1500
#
# # Location of source image
# image_file = 'images/001.jpg'
#
# # This file is for dev purposes. Each line is one piece of the message being sent individually
# chunk_file = open('chunkfile.txt', 'wb+')
#
# with open(image_file, 'rb') as infile:
#     while True:
#         # Read 430byte chunks of the image
#         chunk = infile.read(CHUNK_SIZE)
#         if not chunk: break
#
#         # Do what you want with each chunk (in dev, write line to file)
#         chunk_file.write(chunk)
#
# chunk_file.close()
#
# # STITCH IMAGE BACK TOGETHER
# # Normally this will be in another location to stitch it back together
# read_file = open('chunkfile.txt', 'rb')
#
# # Create the jpg file
# with open('images/stitched_together.jpg', 'wb') as image:
#     for f in read_file:
#         image.write(f)
