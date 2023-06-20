"""
    Python 3
    Usage: python3 TCPClient3.py localhost 12000
    coding: utf-8
    
    Author: Wei Song (Tutor for COMP3331/9331)
"""
from socket import *
import sys, os
from utils import *
import fcntl
from base64 import b64encode

log = Log("Client")

# Server would be running on the same host as Client
if len(sys.argv) != 3:
    print("\n===== Error usage, python3 TCPClient3.py SERVER_IP SERVER_PORT ======\n")
    exit(0)
serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
serverAddress = (serverHost, serverPort)

# define a socket for the client side, it would be used to communicate with the server
clientSocket = socket(AF_INET, SOCK_DGRAM)

# build connection with the server and send message to it
clientSocket.connect(serverAddress)

socket_helper = SocketHelper(clientSocket)


def print_commands():
    print("""
        Enter one of the following commands:
            CRT <threadtitle>: Create Thread
            MSG <threadtitle> <message>: Post Message
            DLT <threadtitle> <messagenumber>: Delete Message
            EDT <threadtitle> <messagenumber> <message>: Edit Message
            LST: List Threads
            RDT <threadtitle>: Read Thread 
            UPD <threadtitle> <filename>: Upload file 
            DWN <threadtitle> <filename>: Download file 
            RMV <threadtitle>: Remove Thread
            XIT: Exit
        """)


# user = {"name": input("Enter username: "), "password": input("Enter password: "), "is_login": False}
user = {"name": input("Username: "), "password": "", "is_login": False}
username = user['name']


def upload_file(filename):
    tcp_socket = socket(AF_INET, SOCK_STREAM)
    tcp_socket.connect(serverAddress)
    try:
        with open(filename, "rb") as f:
            while True:
                file_data = f.read(1024)
                if file_data:
                    tcp_socket.send(file_data)
                else:
                    print("Transmission completed.")
                    break
    except Exception as e:
        print(f"Transmission failed.\n{e.__str__()}")
    tcp_socket.close()


def download_file(file_name, size):
    tcp_socket = socket(AF_INET, SOCK_STREAM)
    tcp_socket.connect(serverAddress)
    try:
        with open(file_name, "ab") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            remain = size
            while remain > 0:
                file_data = tcp_socket.recv(1024)
                print("\r[{:.2f} %]".format((1 - (remain / size)) * 100), end="")
                sys.stdout.flush()
                f.write(file_data)
                remain -= len(file_data)
        print(f"\n{file_name} download complete.")
    except Exception as e:
        print(f"Transmission failed.\n{e.__str__()}")
    rep = json2Response(clientSocket.recv(1024).decode())
    tcp_socket.close()
    print(rep.message)


def CRT(thread_title: str):
    response_crt = socket_helper.sendall(Request(
        command="CRT",
        user=username,
        parameters={
            "threadtitle": thread_title
        }
    ).to_json().encode())
    if response_crt.code == 1:
        print(response_crt.message)
    else:
        print(f"FAILED: {response_crt.message}")


def MSG(thread_title: str, messages: str):
    response_crt = socket_helper.sendall(Request(
        command="MSG",
        user=username,
        parameters={
            "threadtitle": thread_title,
            "message": messages
        }
    ).to_json().encode())
    if response_crt.code == 1:
        print(response_crt.message)
    else:
        print(f"FAILED: {response_crt.message}")


def DLT(thread_title: str, message_number: str):
    response_crt = socket_helper.sendall(Request(
        command="DLT",
        user=username,
        parameters={
            "threadtitle": thread_title,
            "messagenumber": message_number
        }
    ).to_json().encode())
    if response_crt.code == 1:
        print(response_crt.message)
    else:
        print(f"FAILED: {response_crt.message}")


def EDT(thread_title: str, message_number: str, messages: str):
    response_crt = socket_helper.sendall(Request(
        command="EDT",
        user=username,
        parameters={
            "threadtitle": thread_title,
            "messagenumber": message_number,
            "message": messages
        }
    ).to_json().encode())
    if response_crt.code == 1:
        print(response_crt.message)
    else:
        print(f"FAILED: {response_crt.message}")


def LST():
    response_crt = socket_helper.sendall(Request(
        command="LST",
        user=username,
        parameters={
        }
    ).to_json().encode())
    if response_crt.code == 1:
        print(response_crt.message)
    else:
        print(f"FAILED: {response_crt.message}")


def RDT(thread_title: str):
    resp = socket_helper.sendall(Request(
        command="RDT",
        user=username,
        parameters={
            "threadtitle": thread_title,
        }
    ).to_json().encode())
    if resp.code == 1:
        print(resp.message)
    else:
        print(f"FAILED: {resp.message}")


def UPD(thread_title: str, file_name: str):
    length_of_encoded = 0
    with open(file_name, "rb") as f:
        length_of_encoded = len(f.read())
    response_crt = socket_helper.sendall(Request(
        command="UPD",
        user=username,
        parameters={
            "threadtitle": thread_title,
            "filename": file_name,
            "size": length_of_encoded
        }
    ).to_json().encode())
    if response_crt.code == 1:
        print(response_crt.message)
        print("Start to uploading...")
        upload_file(file_name)
    else:
        print(f"FAILED: {response_crt.message}")


def DWN(thread_title: str, file_name: str):
    response_crt = socket_helper.sendall(Request(
        command="DWN",
        user=username,
        parameters={
            "threadtitle": thread_title,
            "filename": file_name
        }
    ).to_json().encode())
    if response_crt.code == 1:
        download_file(file_name, int(response_crt.message))
    else:
        print(f"FAILED: {response_crt.message}")


def RMV(thread_title: str):
    response_crt = socket_helper.sendall(Request(
        command="RMV",
        user=username,
        parameters={
            "threadtitle": thread_title,
        }
    ).to_json().encode())
    if response_crt.code == 1:
        selection = ""
        while True:
            selection = input(f"Are you sure to delete {thread_title}?(yes or no): ")
            if selection == "yes" or selection == "no":
                break
        resp = socket_helper.sendall(Request(
            command=f"RMV_CONFIRM",
            user=username,
            parameters={
                "threadtitle": thread_title,
                "selection": selection
            }
        ).to_json().encode())
        print(resp.message)
    else:
        print(f"FAILED: {response_crt.message}")


def XIT():
    response_xit = socket_helper.sendall(Request(
        command='XIT',
        user=user['name'],
        parameters={}
    ).to_json().encode())
    if response_xit.code == 1:
        print("Log out successfully.\n")
        print("Bye Bye ~~")
        exit(0)
    else:
        print(response_xit.message)
        print("Exit failed, cannot log out.")


def command_selected(command_line: str):
    try:
        line_tokens = command_line.split()
        first = line_tokens[0]
        if first == "CRT":
            CRT(line_tokens[1])
        elif first == "MSG":
            temp = command_line.split(maxsplit=2)
            MSG(temp[1], temp[2])
        elif first == 'DLT':
            DLT(line_tokens[1], line_tokens[2])
        elif first == 'EDT':
            temp = command_line.split(maxsplit=3)
            EDT(temp[1], temp[2], temp[3])
        elif first == 'LST':
            LST()
        elif first == 'RDT':
            RDT(line_tokens[1])
        elif first == 'UPD':
            UPD(line_tokens[1], line_tokens[2])
        elif first == 'DWN':
            DWN(line_tokens[1], line_tokens[2])
        elif first == 'RMV':
            RMV(line_tokens[1])
        elif first == 'XIT':
            XIT()
        else:
            print(f"Unknown command: {first}, using h for help.")
    except Exception as e:
        print("Cannot understand your command, using h for help.\n\n" + e.__str__())


def login_confirm(new_user: bool):
    user['password'] = input('Password: ')
    resp = socket_helper.sendall(
        Request(
            command="LOGIN_CONFIRM",
            user=username,
            parameters={
                "password": user['password'],
                "new": new_user
            }
        ).to_json().encode()
    )
    if resp.code != 1:
        print(resp.message)
        return False
    else:
        return True


while True:
    # login logic
    if not user["is_login"]:
        response = socket_helper.sendall(
            Request(
                command="LOGIN",
                user=user["name"],
                parameters={

                }
            ).to_json().encode()
        )
        if response.code == 1:
            ok = login_confirm(False)
            if not ok:
                break
        elif response.code == 3:
            print(response.message)
            ok = login_confirm(True)
            if not ok:
                break
        else:
            break
        print("Welcome to the forum!")
        user["is_login"] = True

    message = input(f"[{username}] => (h for help): ")
    if message == "h":
        print_commands()
    command_selected(message)

# close the socket·
clientSocket.close()
