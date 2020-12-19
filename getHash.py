import hashlib
import sys
CHUNK_SIZE = 8000
image_file = r"C:\Users\asdf\PycharmProjects\pythonProject\1.jpg"
data_frame = [image_file]
i = 1
chunk_file = open('chunkfile.txt', 'wb+')
chunk_filel = open('chunkfilel.txt', 'wb+')
with open(image_file, 'rb') as infile:
    new = r"C:\Users\asdf\PycharmProjects\pythonProject\myfile.txt"
    with open(new, "rb+") as f:
        while True:
            chunk = infile.read(CHUNK_SIZE)
            sha1 = hashlib.sha1(chunk)
            result = sha1.hexdigest()
            # to sure hash works right
            result += "000000"+str(i) 
            #print(result)
            #print(i)
            i += 1
            hsh = result.encode('utf-8')
            if chunk:
                chunk_filel.write(hsh)
                chunk_file.write(chunk)
            if not chunk:
                chunk_filel.write(hsh)
                #print(hsh)
                break
