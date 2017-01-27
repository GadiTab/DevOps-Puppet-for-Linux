#!/usr/bin/python

# Import Libraries
from time import sleep
from os import system, path
from datetime import datetime
from socket import *
import fcntl, struct, subprocess, shlex, threading
# Extended Library
try:
    from netaddr import *
except:
    system("apt-get install python-netaddr -y")
    from netaddr import *


# *START* Network calculations *START*
#--------------------------------------------------------------------------------------------------------------------
strs = subprocess.check_output(shlex.split('ip r l'))  # Get Default Gateway
gateway = strs.split('default via')[-1].split()[0]  # Get Default Gateway
hostIP = strs.split('src')[-1].split()[0]  # Get Server IP Address
iface = "eth0"  # Get Subnet Mask
mask=inet_ntoa(fcntl.ioctl(socket(AF_INET, SOCK_DGRAM), 35099, struct.pack('256s', iface))[20:24])  # Get Subnet Mask
segment = str(IPNetwork(('{}/{}').format(hostIP,mask)).cidr)  # Calculate Segment
server_dns = getfqdn()  # Server DNS name
port = 51234
#---------------------------------------------------------------------------------------------------------------------
# *END* Network Calculations *END*


# Set global clients connections lists
clients_connections = []
clients_addresses = []


# Open & bind socket
def open_socket():
    global sock
    try:
        sock = socket()
        sock.bind((hostIP, port))
        sock.listen(5)
        accept_connections()
        close_socket()
    except error as message:
        print "Socket error: " + str(message)
        sleep(5)
        close_socket()


# Accept connections thread job
def accept_connections():
    while True:
        try:
            client_conn, client_address = sock.accept()
            client_conn.setblocking(1)
            clients_connections.append(client_conn)
            clients_addresses.append(client_address)
            print "\nConnections has been established: " + client_address[0]
        except:
            print "Error accepting connections"
            close_socket()
            break


# Check clients connections
def check_clients():
    global clients
    clients = []
    for i, client_conn in enumerate(clients_connections):
        try:
            client_conn.send("hostname")
            hostname = client_conn.recv(1024)
        except:
            print "Connection lost with: " + clients_addresses[i][0]
            del clients_connections[i]
            del clients_addresses[i]
            continue
        clients.append([clients_addresses[i][0],hostname])


# Print Clients
def print_clients():
    global clients
    i = 0
    print "Clients:"
    for client in clients:
        i += 1
        print "{}. {} - {}".format(i, client[0], client[1])


# Creating a thread to open and accept connections
def threads():
    thread_clients = threading.Thread(target=open_socket)
    thread_clients.setDaemon(True)
    thread_clients.start()


# (1) Show clients menu
def show_clients():
    system("clear")
    for i in range (3):
        check_clients()
    print_clients()
    enter_to_continue()


# (2) Command the clients menu
def command_clients_menu():
    system("clear")
    global client_pick
    print "Send commands to a client [client - number or 0 to all] (Type 'back' to return)\n"
    for i in range (3):
        check_clients()
    print_clients()
    client_pick = raw_input("\nClient Number: ")
    while len(client_pick) == 0:
        client_pick = raw_input("Client Number: ")
    if client_pick == 'back':
        print_menu()
    elif client_pick == '0':
        command_all_clients()
    else:
        single_client_to_command()


# (2) Pick a client to send commands.
def single_client_to_command():
    global client_pick
    try:
        client_pick = int(client_pick)
        i = 0
        for client_con in clients_connections:
            i += 1
            if client_pick == i:
                print "Type commands to the client (Type 'back' to return):"
                command_a_single_client(client_con)
                return
        if client_pick > i:
            print "There is no such a client."
            raw_input("Press enter to continue...\n")
            command_clients_menu()
    except:
        print "You can't input a character"
        raw_input("Press enter to continue...\n")
        command_clients_menu()


# (2) Send commands to a single client.
def command_a_single_client(client_con):
    while True:
        client_con.send("Cmd")
        cmd = raw_input("> ")
        while len(cmd) == 0:
            cmd = raw_input("> ")
        if cmd == "back":
            client_con.send("back")
            command_clients_menu()
            return
        else:
            try:
                client_con.send(cmd)
                client_response = client_con.recv(1024)
                print "\n{}\n".format(client_response)
            except:
                print "connection lost with the client"
                command_clients_menu()
    return


# (2) Send commands to all clients ('0' at command_clients_menu)
def command_all_clients():
    print "Type commands to all clients (Type 'back' to return):"
    while True:
        cmd = raw_input("> ")
        if cmd == "back":
            command_clients_menu()
            return
        elif len(cmd) == 0:
            continue
        else:
            for i, client_con in enumerate(clients_connections):
                client_con.send("Cmd")
                sleep(0.1)
                try:
                    client_con.send(cmd)
                    print clients_addresses[i][0] + " - Success"
                except:
                    print clients_connections[i][0] + " - Failed to receive."
            print ""


# (3) Send files menu
def send_file_menu():
    system("clear")
    global client_pick
    print "Send a file to a client [client - number or 0 to all] (Type 'back' to return):\n"
    for i in range (3):
        check_clients()
    print_clients()
    client_pick = raw_input("\nClient Number: ")
    while len(client_pick) == 0:
        client_pick = raw_input("Client Number: ")
    if client_pick == 'back':
        print_menu()
        return
    elif client_pick == '0':
        send_to_all_clients_mode()
    else:
        send_file_to_single_client()


# (3) Pick a client to transfer files.
def send_file_to_single_client():
    global client_pick
    try:
        client_pick = int(client_pick)
        i = 0
        for client_con in clients_connections:
            i += 1
            if client_pick == i:
                print "Type the destination path (Type 'back' to return):"
                client_con.send("SC-File")
                send_file_destination(client_con)
                return
        if client_pick > i:
            print "There is no such a client"
            raw_input("\nPress enter to continue...\n")
            send_file_menu()
    except:
        print "You can't input a character"
        raw_input("\nPress enter to continue...\n")
        send_file_menu()


# (3) Choose a destination path
def send_file_destination(client_con):
    check_path_answer = "Path is NOT existed"
    dst_file_path = raw_input("Destination Path > ")
    if dst_file_path == "back":
        client_con.send("back")
        send_file_menu()
        return
    while len(dst_file_path) == 0:
        dst_file_path = raw_input("Destination Path > ")
    sleep(0.1)
    while check_path_answer == "Path is NOT existed":
        client_con.send(dst_file_path)
        check_path_answer = client_con.recv(1024)
        print "client says: {}".format(check_path_answer)
        if check_path_answer == "Path is NOT existed":
            send_file_destination(client_con)
    send_file_source(client_con)


# (3) Choose a source file
def send_file_source(client_con):
    while True:
        src_file_path = raw_input("Source File > ")
        if src_file_path == "back":
            client_con.send("back")
            send_file_destination(client_con)
            return
        while len(src_file_path) == 0:
            src_file_path = raw_input("Source File > ")
        if not path.isfile(src_file_path):
            print "There is no such a file."
            continue
        src_file_name = path.basename(src_file_path)
        client_con.send(src_file_name)
        sleep(0.1)
        client_con.send(str(path.getsize(src_file_path)))
        sleep(0.1)
        try:
            with open(src_file_path, 'rb') as chosen_file:
                bytes_to_send = chosen_file.read(1024)
                client_con.send(bytes_to_send)
                while len(bytes_to_send) > 0:
                    sleep(0.1)
                    bytes_to_send = chosen_file.read(1024)
                    client_con.send(bytes_to_send)
            result = sock.recv(1024)
            print "Client says: {}".format(result)
        except:
            print "Sending file failed. Probably internet connection has lost."


# (3) Tell all clients to get in multi clients file transfer mode.
def send_to_all_clients_mode():
    for i, client_con in enumerate(clients_connections):
        client_con.send("MC-File")
    dst_file_to_all()


# (3) Choose destination path in multi clients mode.
def dst_file_to_all():
    print "Type the destination path (Type 'back' to return):"
    dst_file_path = raw_input("Destination Path > ")
    while len(dst_file_path) == 0:
        dst_file_path = raw_input("Destination Path > ")
    for i, client_con in enumerate(clients_connections):
        if dst_file_path == "back":
            client_con.send("back")
            continue
        else:
            client_con.send(dst_file_path)
            check_path_answer = client_con.recv(1024)
            print "{} says: {}".format(clients_addresses[i][0], check_path_answer)
    if dst_file_path == "back":
        send_file_menu()
        return
    else:
        source_file_to_all()
        return


# (3) Choose a file source in multi clients mode.
def source_file_to_all():
    while True:
        src_file_path = raw_input("Source File > ")
        while len(src_file_path) == 0:
            src_file_path = raw_input("Source File > ")
        if not path.isfile(src_file_path) and src_file_path != "back":
            print "There is no such a file."
            continue
        for i, client_con in enumerate(clients_connections):
            if src_file_path == "back":
                client_con.send("back")
                client_con.recv(1024)
                continue
            else:
                src_file_name = path.basename(src_file_path)
                client_con.send(src_file_name)
                relevant_check = client_con.recv(1024)
                if relevant_check == "Out of scope":
                    continue
                else:
                    client_con.send(str(path.getsize(src_file_path)))
                    sleep(0.1)
                    try:
                        with open(src_file_path, 'rb') as chosen_file:
                            bytes_to_send = chosen_file.read(1024)
                            client_con.send(bytes_to_send)
                            while len(bytes_to_send) > 0:
                                sleep(0.1)
                                bytes_to_send = chosen_file.read(1024)
                                client_con.send(bytes_to_send)
                        print "{} says: File transferring completed".format(clients_addresses[i][0])
                    except:
                        print "Sending file to {} has failed. Probably internet connection has lost.".format(clients_addresses[i][0])
        if src_file_path == "back":
            dst_file_to_all()
            return


# (4) Remote install menu.
def remote_install_menu():
    system("clear")
    global target_client
    print "Install a package to a client [client - number or 0 to all] (Type 'back' to return):\n"
    for i in range (3):
        check_clients()
    print_clients()
    target_client = raw_input("\nClient number: ")
    while len(target_client) == 0:
        target_client = raw_input("Client number: ")
    if target_client == "back":
        print_menu()
        return
    elif target_client == "0":
        remote_install_all()
    else:
        single_client_remote_install()


# (4) Pick a client for remote install.
def single_client_remote_install():
    global target_client
    try:
        target_client = int(target_client)
        i = 0
        for client_con in clients_connections:
            i += 1
            if target_client == i:
                client_con.send("Install")
                remote_install_command(client_con)
                return
        if target_client > i:
            print "There is no such a client"
            remote_install_menu()
    except:
        print "You can't input a character"
        raw_input("\nPress enter to continue...\n")
        remote_install_menu()


# (4) Remote install command
def remote_install_command(client_con):
    while True:
        package_name = raw_input("Type the package name you would like to install remotely (Type 'back' to return): ")
        if package_name == "back":
            client_con.send("back")
            remote_install_menu()
            return
        cmd = "apt-get install {} -y".format(package_name)
        client_con.send(cmd)


# (4) Remote install to all clients.
def remote_install_all():
    while True:
        package_name = raw_input("Type the package name you would like to install remotely (Type 'back' to return): ")
        for client_con in clients_connections:
            client_con.send("Install")
            sleep(0.1)
            if package_name == "back":
                client_con.send("back")
            cmd = "apt-get install {} -y".format(package_name)
            client_con.send(cmd)
        if package_name == "back":
            remote_install_menu()
            return


# (5) Remote uninstall menu
def remote_uninstall_menu():
    system("clear")
    global victim_client
    print "Remove a package from a client [client - number or 0 to all] (Type 'back' to return)\n"
    for i in range(3):
        check_clients()
    print_clients()
    victim_client = raw_input("\nClient number: ")
    while len(victim_client) == 0:
        victim_client = raw_input("Client number: ")
    if victim_client == "back":
        print_menu()
        return
    elif victim_client == "0":
        remote_uninstall_all()
    else:
        single_client_remote_uninstall()


# (5) Pick a client for remote uninstall
def single_client_remote_uninstall():
    global victim_client
    try:
        victim_client = int(victim_client)
        i = 0
        for client_con in clients_connections:
            i += 1
            if victim_client == i:
                client_con.send("UnInstall")
                remote_uninstall_command(client_con)
                return
        if victim_client > i:
            print "There is no such a client"
            remote_uninstall_menu()
    except:
        print "You can't input a character"
        raw_input("\nPress enter to continue...\n")
        remote_uninstall_menu()


# (5) Remote uninstall command.
def remote_uninstall_command(client_con):
    while True:
        package_name = raw_input("Type the package name you would like to remove remotely (Type 'back' to return): ")
        if package_name == "back":
            client_con.send("back")
            remote_uninstall_menu()
            return
        cmd = "apt-get remove {} -y".format(package_name)
        client_con.send(cmd)
        client_con.recv(1024)
        cmd = "apt-get remove --purge {} -y".format(package_name)
        client_con.send(cmd)

# (5) Remote uninstall to all clients
def remote_uninstall_all():
    while True:
        package_name = raw_input("Type the package name you would like to remove remotely (Type 'back' to return): ")
        for client_con in clients_connections:
            client_con.send("UnInstall")
            sleep(0.1)
            if package_name == "back":
                client_con.send("back")
            cmd = "apt-get remove {} -y".format(package_name)
            client_con.send(cmd)
            client_con.recv(1024)
            cmd = "apt-get remove --purge {} -y".format(package_name)
            client_con.send(cmd)
        if package_name == "back":
            remote_uninstall_menu()
            return


# (6) Netcat menu
def netcat_menu():
    system("clear")
    global chat_mate
    print "Chat with a client [client - number or 0 to SEND ONLY to all] (Type 'back' to return)\n"
    for i in range(3):
        check_clients()
    print_clients()
    chat_mate = raw_input("\nClient number: ")
    while len(chat_mate) == 0:
        chat_mate = raw_input("Client number: ")
    if chat_mate == "back":
        print_menu()
        return
    elif chat_mate == "0":
        netcat_all()
    else:
        netcat_single()

# (6) Pick a client for netcat
def netcat_single():
    global chat_mate
    try:
        chat_mate = int(chat_mate)
        i = 0
        for client_con in clients_connections:
            i += 1
            if chat_mate == i:
                client_con.send("NetCat")
                netcat_chat_single()
                return
        if chat_mate > i:
            print "There is no such a client"
            netcat_menu()
    except:
        print "You can't input a character"
        raw_input("\nPress enter to continue...\n")
        netcat_menu()


# (6) Start netcat chat with the chosen client.
def netcat_chat_single():
    print "Opening a Netcan session with the client, please Hold patiently. To stop chatting type Ctrl+C."
    cmd = "nc -lvp 54321"
    system(cmd)
    netcat_menu()


# (6) Send chat (messages) to all connected clients.
def netcat_all():
    print "You are now sending messages to all connected clients. Type 'stop chat' to exit."
    you_said = " "
    for client_con in clients_connections:
        client_con.send("NetCatAll")
    while you_said != "stop chat":
        you_said = raw_input("> ")
        print "You: {}".format(you_said)
        for client_con in clients_connections:
            client_con.send(you_said)
            if you_said == "stop chat":
                client_con.send("stop chat")
                sleep(0.5)
    netcat_menu()


# Exit
def exit_program():
    close_socket()
    print "Master of Puppets Server is... Closed :)"


# User typed an unexisting option
def invalid_option():
    print "Invalid option"
    enter_to_continue()


# Getting back to main menu
def enter_to_continue():
    raw_input("\nPress enter to continue...\n")
    print_menu()


# Closing the socket
def close_socket():
    global sock
    for connection in clients_connections:
        connection.send("close")
    sock.close()


# Main menu INPUT
def select_menu():
    user_selection = raw_input("Action: ")
    menu_options = {
        "1": show_clients,
        "2": command_clients_menu,
        "3": send_file_menu,
        "4": remote_install_menu,
        "5": remote_uninstall_menu,
        "6": netcat_menu,
        "7": exit_program,
    }
    menu_options.get(user_selection, invalid_option)()


# Main menu OUTPUT
def print_menu():
    system("clear")
    time = datetime.now().strftime('%H:%M')
    print """
##############################################################################

Python 102              Name: Gadi Tabak                    {}

##############################################################################

Segment: {}

Your DNS: {}

Your gateway: {}

#####################################

            Menu
            ----

1. Show all clients
2. Send commands to all clients
3. Transfer files to all clients
4. Install something on all clients
5. Remove something from all clients
6. Open Netcat (Chat) Session.
7. Exit
    """.format(time, segment, server_dns, gateway)
    select_menu()


# Main function
def main():
    threads()
    print_menu()

# Let's start (and make sure the socket will be closed in case of an error)
try:
    main()
except:
    print "Something wrong happend and the program had to be closed."
    for client_conn in clients_connections:
        client_conn.send("close")
    close_socket()
