#!/usr/bin/env python
# coding: utf-8


import subprocess
import socket
import select
import json
import threading
import shlex
import time
import random
import string

# to break loops on exit command
global shutdown
shutdown = False

# default ports to be used for sending & listening
default_port_tcp = 12345
default_port_udp = 12345

# for udp broadcasts
broadcast_channel = "<broadcast>"

# history file, initialized empty at each startup
history_file = "histor.y"

# initialize empty history file
f = open(history_file, "w")
f.close()


# returns text of indicated color to be printed on the terminal
def color(s, c):
    cdic = {
        "red": u"\u001b[31m",
        "blue": u"\u001b[34m",
        "green": u"\u001b[32m",
        "cyan": u"\u001b[36m",
        "yellow": u"\u001b[33m",
        "magenta": u"\u001b[35m",
        "default": "",
        "-reset": u"\u001b[0m",
    }
    return (cdic[c] + s + cdic["-reset"])


# for creating an exit token (just a design choice)
def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


exit_token = get_random_string(16)


# returns a packet dictionary with the desired values
def get_packet(name, sender_ip, packet_type, payload=''):
    packet = {
        'NAME': name,
        'MY_IP': sender_ip,
        'TYPE': packet_type,
        'PAYLOAD': payload,
    }

    return packet


# listen to a port, write incoming into `history_file`
def listen_port_tcp(local_ip, port=default_port_tcp, history_file=history_file, verbose=False):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((local_ip, port))
        s.listen()
        try:
            conn, addr = s.accept()
        except:
            return
        with conn:
            if verbose:
                print("Connected by", addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break

                f = open(history_file, "a+")
                f.write(data.decode())
                f.close()


# send packet to receiver_ip:port
def send_packet_tcp(packet, receiver_ip, port=default_port_tcp, verbose=False):
    the_json = json.dumps(packet) + "\n"
    pkt = the_json.encode()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(1.5)
        s.connect((receiver_ip, port))

        s.sendall(pkt)


# listen to a port (UDP), write incoming into `history_file`
def listen_port_udp(local_ip, packet_processor, port=default_port_udp, history_file=history_file, verbose=False):
    port = port
    bufferSize = 1024
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', port))
    s.setblocking(0)
    result = select.select([s], [], [])

    data = result[0][0].recv(bufferSize)
    if verbose:
        print(color("(UDP) received message: %s" % data, 'green'))
    try:
        packet_json = json.loads(data)
    # if loading packet to json fails, display the broken packet to the user
    except:
        print(color(f"(UDP) non-json packet received:<{data}>", 'red'))
        pass

    if packet_json['TYPE'] == 'GOODBYE' and packet_json['PAYLOAD'] == exit_token:
        return "exit"
    else:
        packet_processor(packet_json)
        return "continue"


# send packet to receiver_ip:port (UDP)
def send_packet_udp(packet, port=default_port_udp, verbose=False):
    the_json = json.dumps(packet)
    pkt = the_json.encode()

    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(pkt, (broadcast_channel, port))


# has two functionalities
# 1. send "DISCOVER" packet to all IPs in host_ips
# 2. send "RESPOND" packet to a specified IP
# also sends to self, to add self to online users list (good for test purposes)
def greet(sender_ip, receiver_ip=None, greet_type='DISOVER', verbose=False):
    local = sender_ip[:sender_ip.rfind('.') + 1]
    local = local[:local.rfind('.') + 1]

    packet = get_packet(name, sender_ip, greet_type)

    if greet_type == "DISCOVER":
        print("Sending discover to hosts on the LAN...", end="\n")
        send_packet_udp(packet)
        send_packet_udp(packet)
        send_packet_udp(packet)
        print("Done.\n")
    elif greet_type == "RESPOND":
        send_packet_tcp(packet, receiver_ip)
    else:
        return


# send goodbye packets to users that aren't the current user
def say_goodbye(users):
    goodbye_packet = get_packet(name, local_ip, packet_type='GOODBYE', payload=exit_token)
    send_packet_udp(goodbye_packet)


# send a packet of type "MESSAGE", with given text as payload
def send_msg(text, receiver_ip, sender_ip):
    packet = get_packet(name, sender_ip, 'MESSAGE', text)
    send_packet_tcp(packet, receiver_ip)


# check for new packets
# return (boolean indicating change in history file since last check, all content of the file, new content on the file)
def new_packets(history, history_file, verbose=False):
    f = open(history_file, "r")
    readings = f.read()
    f.close()

    new = readings[len(history):]

    different = readings != history

    if verbose:
        print(different, new)

    return different, readings, new


# print welcome logo
print(color(u"""

             .)/     )/,
              /`-._,-'`._,@`-,
       ,  _,-=\\,-.__,-.-.__@/
      (_,'    )\\`    '(`                          
                     _       
         ___ ___ ___| |_ ___ 
        | . | -_|  _| '_| . |
        |_  |___|___|_,_|___|
        |___|                       
     _       _          _ _         _   
 ___| |_ ___| |_    ___| |_|___ ___| |_ 
|  _|   | .'|  _|  |  _| | | -_|   |  _|
|___|_|_|__,|_|    |___|_|_|___|_|_|_| 

""", "default"))

# get available host IP addresses for the current user
cmd_get_ip = "ifconfig | grep netmask"
out, err = subprocess.Popen(cmd_get_ip, shell=True, stdout=subprocess.PIPE).communicate()
ifconfig_lines = out.decode("utf-8").split("\n")[:-1]
ifconfig_ips = [line.split()[1] for line in ifconfig_lines if line.split()[1] != "127.0.0.1"]

# if more than one host IP address is available, take prompt from user as to which one should be used
if len(ifconfig_ips) > 1:
    print("Available IP adresses:")
    for i, ip in enumerate(ifconfig_ips):
        print(f"* {i}: {color(ip, 'cyan')}")
    print(f"Please choose an ip address by specifying its list number above (0-{len(ifconfig_ips) - 1}).")

    while True:
        choice = input("choose>:")
        try:
            choice = int(choice)
        except:
            pass
        if choice in range(len(ifconfig_ips)):
            local_ip = ifconfig_ips[choice]
            break
        else:
            continue
else:
    local_ip = ifconfig_ips[0]

if local_ip.split(".")[0] == "25":
    broadcast_channel = "25.255.255.255"

print()
print(f"Using ip {color(local_ip, 'cyan')}")
print()

###################################################################

print(f"• Please enter your message in the following format:'{color('recipient_name|msg', 'cyan')}'.")
print(f"• To get a list of all online users, type '{color('$online', 'cyan')}'.")
print()
print(f"• {color('Cyan', 'cyan')} indicates that the user is in your online contacts list.")
print(f"• {color('Yellow', 'yellow')} indicates that the user is not in online contacts list.")
print(
    f"• {color('Red', 'red')} indicates that the user is trying to use the display name of someone in your online contacts list.")
print()
print(f"• To see all commands and indicator, type '{color('$help', 'cyan')}'.")

print()

# prompt user for display name
name = ""
while True:
    name = input("To start, enter your display name:\n>:")
    if len(name) <= 16 and "|" not in name and ":" not in name and "$" not in name and " " not in name:
        break
    else:
        print(color(
            "Your display name should be at most 16 characters. It can't contain blank spaces, '|', '$' and/or ':'.\n",
            'red'))

print(f"Welcome {name}!")
print()

# dictonary of online users (<display_name>:<ip_address> pairs)
users = {}

# initial readings for the history file (to not take into account the existing packets if file not reinitialized)
_, history, new = new_packets('', history_file)


def process_udp_packet(packet_json, verbose=False):
    try:
        packet_json

        # if packet type is "DISCOVER", add user to `users` (if not already in) and send a "RESPOND" packet
        if packet_json["TYPE"] == "DISCOVER":
            greet(sender_ip=local_ip, greet_type='RESPOND', receiver_ip=packet_json["MY_IP"])
            if packet_json["MY_IP"] not in users.values():
                users[packet_json["NAME"]] = packet_json["MY_IP"]
                print(color(f"{packet_json['NAME']} is now online! ({packet_json['MY_IP']})\n", "green"))

        # if packet type is "GOODBYE", remove user from online users dictionary if they are in it
        elif packet_json["TYPE"] == "GOODBYE":
            if packet_json["NAME"] in users.keys() and packet_json["MY_IP"] == users[packet_json["NAME"]]:
                users.pop(packet_json["NAME"], None)
                print(color(f"{packet_json['NAME']} is now offline!\n", "yellow"))

        # any other type
        else:
            print(color("unexpected packet of type", "red"), packet_json["TYPE"])

    except Exception as e:
        if verbose:
            print(color("unexpected packet behavior: ", "red"), packet_json)
            print(str(e))
        else:
            pass


def check_packets_udp():
    while True:
        if listen_port_udp(local_ip, process_udp_packet) == "exit":
            break


# process newly read packets and listen for new packets, repeat.
def check_packets_tcp(history=history):
    global shutdown
    while not shutdown:

        change, history, new = new_packets(history, history_file)

        if change:
            # get new packets into a list
            packets = new.split("\n")[:-1]

            for packet in packets:
                try:
                    packet_json = json.loads(packet)

                    # exit packet
                    if packet_json["TYPE"] == "EXIT":
                        # removeprint(color(">>>DEBUG>>> mt packet", "red"))
                        if packet_json["PAYLOAD"] == exit_token:
                            shutdown = True
                            break

                    # if packet type is "RESPOND", add user to `users` (if not already in)
                    elif packet_json["TYPE"] == "RESPOND":
                        if packet_json["MY_IP"] not in users.values():
                            users[packet_json["NAME"]] = packet_json["MY_IP"]
                            print(color(f"{packet_json['NAME']} is now online! ({packet_json['MY_IP']})\n", "green"))

                    # if packet type is "MESSAGE", display payload with the sender's display name
                    # display name will be colored to indicate their relationship with the current user's online users list
                    elif packet_json["TYPE"] == "MESSAGE":
                        if packet_json['NAME'] in users.keys():
                            if users[packet_json['NAME']] == packet_json['MY_IP']:
                                print(f"{color(packet_json['NAME'], 'cyan')}:\n{packet_json['PAYLOAD']}\n")
                            else:
                                print(f"{color(packet_json['NAME'], 'red')}:\n{packet_json['PAYLOAD']}\n")
                        else:
                            print(f"{color(packet_json['NAME'], 'yellow')}:\n{packet_json['PAYLOAD']}\n")

                # if loading packet to json fails, display the broken packet to the user
                except:
                    print(color(f"(TCP) non-json packet received:<{packet}>", 'red'))

        # listen for new changes
        if shutdown:
            break
        # removeprint(color(">>>DEBUG>>> b4 listen", "red"))
        listen_port_tcp(local_ip=local_ip, history_file=history_file)
        # removeprint(color(">>>DEBUG>>> after listen", "red"))


# get input from user
def get_input():
    msg = input("")

    # let the user clean their workspace by pressing return
    if msg == "":
        pass

    # if the message starts with a $, its a command
    elif msg[0] == "$":

        # $online : displays the current `users` dictionary
        if msg == "$online":
            if bool(users):
                for user in users.keys():
                    print(f"* {user} : {users[user]}")
                print()
            else:
                print("- there are no online users")
                print()

        # $add : manually add a new user (sends them a "DISCOVER" packet and adds them to `users`)
        elif msg == "$add":
            new_username = input("enter name: ")
            new_user_ip = input("enter ip: ")
            users[new_username] = new_user_ip
            print()
            greet(sender_ip=local_ip, greet_type='DISCOVER', receiver_ip=new_user_ip)

        # $ipof:<username> : prints the requested user's IP address (if user exists)
        elif msg.startswith("$ipof:"):
            username = msg.split(":")[1]
            if username not in users.keys():
                print(f"User not in list. Enter '{color('$online', 'cyan')}' to list online users.\n")
            else:
                print(f"The IP address of {color(username, 'cyan')} is {color(users[username], 'cyan')}.\n")

        # $help : displays all commands and indicators
        elif msg == "$help":
            print(f"• Please enter your message in the following format:'{color('recipient_name|msg', 'cyan')}'.")
            print(f"• To get a list of all online users, type '{color('$online', 'cyan')}'.")
            print(f"• To add a user manually using their ip address, type '{color('$add', 'cyan')}'.")
            print(f"• To learn the IP address of a user in your online list, type '{color('$ipof:username', 'cyan')}'.")
            print(f"• To quit gecko, type '{color('$exit', 'cyan')}'.")
            print(f"• {color('Cyan', 'cyan')} indicates that the user is in your online contacts list.")
            print(f"• {color('Yellow', 'yellow')} indicates that the user is not in online contacts list.")
            print(
                f"• {color('Red', 'red')} indicates that the user is trying to use the display name of someone in your online contacts list.")
            print()

        # $exit : exits the client (problematic w/ check_packets thread)
        elif msg == "$exit":
            say_goodbye(users)
            # removeprint(color(">>>DEBUG>>> exit called", "red"))
            send_packet_tcp({'TYPE': 'EXIT', 'PAYLOAD': exit_token}, local_ip)
            # removeprint(color(">>>DEBUG>>> tcp exit sent", "red"))
            # send_packet_udp({'TYPE': 'EXIT', 'PAYLOAD':exit_token})
            # removeprint(color(">>>DEBUG>>> udp exit sent", "red"))
            tcp_check.join()
            # removeprint(color(">>>DEBUG>>> tcp join done", "red"))
            udp_check.join()
            # removeprint(color(">>>DEBUG>>> udp join done", "red"))
            exit()

        else:
            pass

    # otherwise, the input should be a message in the format 'recipient_name|msg'
    else:
        msg_data = msg.split("|")
        if len(msg_data) == 2:
            recipient_name, msg_body = msg_data
            if recipient_name in users.keys():
                try:
                    send_msg(msg_body, users[recipient_name], local_ip)
                    print()
                except:
                    print(color(f"Unexpected offline client detected. ({recipient_name})\n", 'red'))
                    users.pop(recipient_name, None)
            else:
                print("User is not online!\n")
        else:
            print(f"Please enter your message in the following format:'{color('recipient_name|msg', 'cyan')}'.\n")


def get_indefinite_input():
    while True:
        while get_input():
            pass


tcp_check = threading.Thread(name='check_packets_tcp', target=check_packets_tcp)
tcp_check.start()

udp_check = threading.Thread(name='check_packets_udp', target=check_packets_udp)
udp_check.start()

greet(sender_ip=local_ip, greet_type='DISCOVER')

get_indefinite_input()
