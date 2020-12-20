import json
import os
import signal
import shutil
from pathlib import Path

chunk_size = 100
filename = input("file:")
def read_in_chunks(file_object, chunk_size):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

def handler(signum, frame):
    print ('Ctrl+Z pressed, but ignored')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path1=str(Path(dir_path).parents[0])
    print(dir_path1)
    if os.path.join(dir_path1):
        print("1")
        os.path.dirname(os.path.dirname(dir_path1))
        os.remove('ders_temp')
        shutil.rmtree('{}_temp'.format(str(filename)))
signal.signal(signal.SIGTSTP, handler)

if os.path.isfile('{}'.format(str(filename))):
    print("1")
    with open('{}'.format(str(filename)), "rb") as f:
        #shutil.rmtree('{}_temp'.format(str(filename)))
        os.mkdir('{}_temp'.format(str(filename)))
        os.chdir('{}_temp'.format(str(filename)))
        index = 0
        for chunk in read_in_chunks(f,300):
            #hash_ = get_hash(chunk)
            chunk_file = open('{}.txt'.format(index), 'w+')
            #this will change chunk type byte to str. Otherwise write function does not work
            chunk = str(chunk, 'utf-8')
            chunk_file.write(chunk)
            chunk_file.close()
            index = index + 1
        end = open('{}_end.txt'.format(index), 'w')
        end.close()
    #return True
else:
     print("no")
while True:
    pass
