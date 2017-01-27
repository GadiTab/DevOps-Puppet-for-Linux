#!/usr/bin/python
# Import Libraries
from socket import socket, getfqdn
from subprocess import PIPE, Popen
from os import chdir, path, mkdir, getcwd, system
from time import sleep

# Set Global Variables
hostname = getfqdn()
sock = socket()


# Connect to the server socket
def connect():
    try:
        sock.connect(('10.0.0.4', 51234))
        print "Connected."
    except:
        print "Connection failed"
        sock.close()


# Client is waiting for a command from the server.
def waiting_for_commands():
    data = "   "
    while data != "close":
        data = sock.recv(1024)
        receive_options = {
            "hostname": send_hostname,
            "Cmd": recv_commands,
            "SC-File": single_recv_dst_path,
            "MC-File": multi_recv_dst_path,
            "Install": apt_install,
            "UnInstall": apt_remove,
            "NetCat": net_cat_single,
            "NetCatAll": net_cat_recv_all,
        }
        receive_options.get(data, out_of_scope)()
    sock.close()
    print "socket closed."


# Send client hostname
def send_hostname():
    sock.send(hostname)


# (2) Receive shell commands
def recv_commands():
    data_cmd = sock.recv(1024)
    if data_cmd == "back":
        return
    if data_cmd == 'cd':
        chdir(data_cmd)
        sock.send(getcwd())
    if len(data_cmd) > 0:
        cmd = Popen(data_cmd, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        output_bytes = cmd.stdout.read() + cmd.stderr.read()
        output_str = str(output_bytes)
        sock.send(str.encode(output_str))
        print(output_str)


# (3) Check if path existed on transfer file single client mode
def single_recv_dst_path():
    while True:
        dir_path_data = sock.recv(1024)
        if dir_path_data == "back":
            return
        elif not path.isdir(dir_path_data):
            sock.send("Path is NOT existed")
            continue
        else:
            sock.send("Path Existed")
            receive_file(dir_path_data)


# (3) Receive file data in single client mode
def receive_file(dir_path_data):
    while True:
        file_name = sock.recv(1024)
        if file_name == "back":
            return
        else:
            file_size = long(sock.recv(1024))
            new_file = open(dir_path_data + file_name, 'wb')
            file_data = sock.recv(1024)
            file_recv_size = len(file_data)
            new_file.write(file_data)
            while file_size > file_recv_size:
                file_data = sock.recv(1024)
                file_recv_size += len(file_data)
                new_file.write(file_data)
            result = "Received File: {}{}".format(dir_path_data, file_name)
            sock.send(result)


# (3) Check if path existed on transfer file multi clients mode
def multi_recv_dst_path():
    while True:
        dir_path_data = sock.recv(1024)
        if dir_path_data == "back":
            return
        if not path.isdir(dir_path_data):
            try:
                mkdir(dir_path_data)
                sock.send("Path is NOT existed. Directory was created.")
            except:
                sock.send("Creating a Directory Failed. Existing the program. Try lower directory level next time.")
                return
        sock.send("Path exists")
        multi_receive_file(dir_path_data)


# (3) Receive file data in multi clients mode
def multi_receive_file(dir_path_data):
    while True:
        file_name = sock.recv(1024)
        if file_name == "back":
            sock.send(" ")
            return
        else:
            sock.send(" ")
            file_size = long(sock.recv(1024))
            new_file = open(dir_path_data + file_name, 'wb')
            file_data = sock.recv(1024)
            file_recv_size = len(file_data)
            new_file.write(file_data)
            while file_size > file_recv_size:
                file_data = sock.recv(1024)
                file_recv_size += len(file_data)
                new_file.write(file_data)
            print "Received File: {}{}".format(dir_path_data, file_name)


# (4) Install a program
def apt_install():
    while True:
        cmd = sock.recv(1024)
        if cmd == "back":
            return
        system(cmd)


# (5) Remove a program
def apt_remove():
    while True:
        cmd_remove = sock.recv(1024)
        if cmd_remove == "back":
            return
        system(cmd_remove)
        sock.send(" ")
        cmd_remove_purge = sock.recv(1024)
        system(cmd_remove_purge)


# (6) Start netcat chat
def net_cat_single():
    print "Netcat session opened."
    sleep(0.5)
    cmd = "nc 10.0.0.4 54321"
    system(cmd)
    print "Netcat session closed."
    return


# (6) Receive messages from the server
def net_cat_recv_all():
    print "Server is about to send important messages:"
    msg_recv = " "
    while msg_recv != "stop chat":
        msg_recv = sock.recv(1024)
        print "Server: {}".format(msg_recv)
    return


# When client receive unfimiliar data (like can happen in transfer file multi clients mode)
def out_of_scope():
    sock.send("Out of scope")


# Main function
def main():
    connect()
    waiting_for_commands()
    sock.close()


# Let's begin :)
main()
