"""
    Sample code for Multi-Threaded Server
    Python 3
    Usage: python3 TCPserver3.py localhost 12000
    coding: utf-8
    
    Author: Wei Song (Tutor for COMP3331/9331)
"""
import os
import signal
import sys
import fcntl
from threading import Thread

from utils import *

log = Log("Server")

# acquire server host and port from command line parameter
if len(sys.argv) != 2:
    log.i("Error usage, python3 TCPServer3.py SERVER_PORT")
    exit(0)
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(serverAddress)

# maintain users
users = []
for line in open('credentials.txt'):
    users.append({
        'username': line.split(' ')[0],
        'password': line.split(' ')[1].replace('\n', ''),
        'isLogin': False,
        'address': ('0.0.0.0', 0)
    })


def find_user_by_name(name: str):
    for u in users:
        if u["username"] == name:
            return u
    return None


def quit(signum, frame):
    print('You pressed Ctrl + C!')
    sys.exit(0)


THREAD_DIR = "./threads"

socketTcp = socket(AF_INET, SOCK_STREAM)
socketTcp.bind(serverAddress)


def establish_tcp_connection():
    try:
        socketTcp.listen(20)
    except:
        log.i("Listen failed.")
    client_socket, client_addr = socketTcp.accept()
    return client_socket, client_addr


def create_threads_dir_if_not_exist():
    if not os.path.exists(THREAD_DIR):
        os.makedirs(THREAD_DIR)


def rewrite_dicts_to_thread_file(thread_title: str, dicts_in: list):
    with open(f"{THREAD_DIR}/{thread_title}", mode='a+') as file:
        fcntl.flock(file.fileno(), fcntl.LOCK_EX)
        file.seek(0)
        file.truncate(0)
        file.write(dicts_in[0]['creator'] + '\n')
        start = 1
        for i in dicts_in:
            if i['type'] == "file":
                file.write(f"{i['user']} uploaded {i['filename']}\n")
            else:
                file.write(f"{start} {i['user']}: {i['message']}\n")
            start += 1


def convert_thread_to_dicts(thread_title: str):
    result = []
    with open(f"{THREAD_DIR}/{thread_title}") as file:
        fcntl.flock(file.fileno(), fcntl.LOCK_EX)
        is_first_line = True
        creator = ""
        for lin in file.readlines():
            if is_first_line:
                creator = lin.strip()
                is_first_line = False
                continue
            sp1 = lin.strip().split(maxsplit=1)
            thread_num = sp1[0]
            if not thread_num.isdigit():
                sp0 = lin.strip().split()
                result.append({
                    "type": "file",
                    "creator": creator,
                    "user": sp0[0],
                    "filename": sp0[2]
                })
                continue
            sp2 = sp1[1].split(":")
            user = sp2[0]
            message = sp2[1].strip()

            result.append({
                "type": "message",
                "creator": creator,
                "thread_number": thread_num,
                "user": user,
                "message": message,
            })
    return result


class ClientThread(Thread):

    def __init__(self, clientAddress, soc, request):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.soc = soc
        self.request = request
        self.current_user = find_user_by_name(request.user)
        create_threads_dir_if_not_exist()

    def send_back(self, response: Response):
        self.soc.sendto(self.clientAddress, response, False)

    def run(self):
        if self.request.command == "LOGIN":
            log.i(f"{self.clientAddress[0]} is trying to login with the username: <{self.request.user}>.")
            query_user = find_user_by_name(self.request.user)
            if query_user is None:
                self.send_back(Response(code=3,
                                        message="Creating new account for: {}.".format(self.request.user)))
            elif not query_user["isLogin"]:
                self.send_back(Response(code=1, message="You can login."))
            elif query_user["isLogin"]:
                self.send_back(Response(code=0,
                                        message=f"{query_user['username']} s already logged in, please do not log in again."))
            return

        try:
            log.i(f"{self.request.user} issued {self.request.command}.")
            if self.request.command == "CRT":
                self.CRT(self.request.parameters["threadtitle"])
            elif self.request.command == "MSG":
                self.MSG(thread_title=self.request.parameters["threadtitle"],
                         messages=self.request.parameters["message"])
            elif self.request.command == 'DLT':
                self.DLT(thread_title=self.request.parameters["threadtitle"],
                         message_number=self.request.parameters["messagenumber"])
            elif self.request.command == 'EDT':
                self.EDT(thread_title=self.request.parameters['threadtitle'],
                         messages=self.request.parameters['message'],
                         message_number=self.request.parameters['messagenumber'])
            elif self.request.command == 'LST':
                self.LST()
            elif self.request.command == 'RDT':
                self.RDT(thread_title=self.request.parameters['threadtitle'])
            elif self.request.command == 'UPD':
                self.UPD(thread_title=self.request.parameters['threadtitle'],
                         file_name=self.request.parameters['filename'],
                         size=self.request.parameters['size'])
            elif self.request.command == 'DWN':
                self.DWN(thread_title=self.request.parameters['threadtitle'],
                         file_name=self.request.parameters['filename'])
            elif self.request.command == 'RMV':
                self.RMV(thread_title=self.request.parameters['threadtitle'])
            elif self.request.command == 'RMV_CONFIRM':
                self.RMV_CONFIRM(thread_title=self.request.parameters['threadtitle'],
                                 selection=self.request.parameters['selection'])
            elif self.request.command == 'XIT':
                self.XIT()
            elif self.request.command == 'LOGIN_CONFIRM':
                self.LOGIN_CONFIRM(password=self.request.parameters['password'],
                                   new_user=self.request.parameters['new'])
        except Exception as e:
            self.send_back(
                Response(code=0, message=f"Cannot understand the command: '{self.request.command}'; {e.__str__()}"))
            log.e('Cannot understand the command.')

    def LOGIN_CONFIRM(self, password: str, new_user: bool):
        try:
            if new_user:
                users.append({
                    'username': self.request.user,
                    'password': password,
                    'isLogin': True,
                    'address': ('0.0.0.0', 0)
                })
                with open("credentials.txt", mode="a+") as file:
                    fcntl.flock(file.fileno(), fcntl.LOCK_EX)
                    file.write(f"{self.request.user} {password}\n")
                self.send_back(Response(
                    code=1,
                    message=f"Created a new account: {self.request.user}"
                ))
            else:
                if self.current_user['password'] == password:
                    self.send_back(Response(
                        code=1,
                        message="Login successfully."
                    ))
                else:
                    self.send_back(Response(code=2, message="Invalided password."))
        except Exception as e:
            self.send_back(Response(
                code=0,
                message=e.__str__()
            ))

    def CRT(self, thread_title: str):
        try:
            if os.path.exists(f"{THREAD_DIR}/{thread_title}"):
                self.send_back(Response(
                    code=0,
                    message=f"{thread_title} already exists."
                ))
                return
            with open(f"{THREAD_DIR}/{thread_title}", "w") as file:
                fcntl.flock(file.fileno(), fcntl.LOCK_EX)
                file.write(self.current_user['username'] + "\n")
                self.send_back(Response(
                    code=1,
                    message=f"Thread {thread_title} created by {self.current_user['username']}."
                ))
                log.i(f"{self.current_user['username']} created a new thread: {thread_title}")
        except Exception as e:
            self.send_back(Response(
                code=0,
                message=e.__str__()
            ))

    def MSG(self, thread_title: str, messages: str):
        try:
            if not self.check_if_thread_exist(thread_title):
                return
            with open(f"{THREAD_DIR}/{thread_title}", mode="a+") as file:
                fcntl.flock(file.fileno(), fcntl.LOCK_EX)
                file.seek(0)
                lines = file.readlines()
                last_number = len(lines) - 1
                file.seek(0, 2)
                file.write(f"{last_number + 1} {self.current_user['username']}: {messages}\n")

                self.send_back(Response(
                    code=1,
                    message=f"Insert a new message in {thread_title}."
                ))
                log.i(f"<{self.current_user['username']}> insert a new message in <{thread_title}>")
        except Exception as e:
            self.send_back(Response(
                code=0,
                message=e.__str__()
            ))

    def DLT(self, thread_title: str, message_number: str):
        try:
            if not self.check_if_thread_exist(thread_title):
                return
            dicts = convert_thread_to_dicts(thread_title)
            query = None
            for item in dicts:
                if item["type"] == "message":
                    if item["thread_number"] == message_number:
                        query = item
            if query is None:
                self.send_back(Response(
                    code=0,
                    message=f"No message found by <{message_number}>"
                ))
                return
            if query["user"] != self.current_user["username"]:
                self.send_back(Response(
                    code=0,
                    message="Cannot delete the message that doesn't belong to you."
                ))
                return
            dicts.remove(query)
            rewrite_dicts_to_thread_file(thread_title, dicts)
            self.send_back(Response(
                code=1,
                message=f"You deleted a message from <{thread_title}>."
            ))
            log.i(f"<{self.current_user['username']}> deleted a message from <{thread_title}>.")
        except Exception as e:
            self.send_back(Response(
                code=0,
                message=e.__str__()
            ))

    def EDT(self, thread_title: str, message_number: str, messages: str):
        try:
            if not self.check_if_thread_exist(thread_title):
                return
            dicts = convert_thread_to_dicts(thread_title)
            query = None
            pos = 0
            i = 0
            for item in dicts:
                if item["type"] == "message":
                    if item["thread_number"] == message_number:
                        query = item
                        pos = i
                i += 1
            if query is None:
                self.send_back(Response(
                    code=0,
                    message=f"No message found by <{message_number}>"
                ))
                return
            if query["user"] != self.current_user["username"]:
                self.send_back(Response(
                    code=0,
                    message="Cannot delete the message that doesn't belong to you."
                ))
                return
            dicts[pos]['message'] = messages
            rewrite_dicts_to_thread_file(thread_title, dicts)
            self.send_back(Response(
                code=1,
                message=f"You edited a message from <{thread_title}>."
            ))
            log.i(f"<{self.current_user['username']}> edited a message from <{thread_title}>.")
            pass
        except Exception as e:
            self.send_back(Response(
                code=0,
                message=e.__str__()
            ))

    def LST(self):
        files = os.listdir(THREAD_DIR)
        result = ""
        for i in files:
            result += i + "\n"
        self.send_back(Response(
            code=1,
            message=result
        ))
        pass

    def RDT(self, thread_title: str):
        try:
            if not self.check_if_thread_exist(thread_title):
                return
            with open(f"{THREAD_DIR}/{thread_title}") as file:
                fcntl.flock(file.fileno(), fcntl.LOCK_EX)
                lines = file.readlines()
                result = f"{thread_title}: \n\n"
                for i in range(1, len(lines)):
                    result += lines[i]
                self.send_back(Response(
                    code=1,
                    message=result
                ))
        except Exception as e:
            self.send_back(Response(
                code=0,
                message=e.__str__()
            ))

    def UPD(self, thread_title: str, file_name: str, size: int):
        try:
            if not self.check_if_thread_exist(thread_title):
                return
            files = os.listdir("./")
            if thread_title + "-" + file_name in files:
                self.send_back(Response(
                    code=0,
                    message=f"File '{file_name}' already exists in '{thread_title}'."
                ))
                return

            self.send_back(Response(
                code=1,
                message="Verified!!"
            ))
            client_socket, client_addr = establish_tcp_connection()

            try:
                log.i(f"Accept connection from {client_addr[0]}  ({self.current_user['username']})")

                with open(f"./{thread_title}-{file_name}", "ab") as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    remain = size
                    log.i(f"Total size: {size / 1024.0} KB")
                    while remain > 0:
                        file_data = client_socket.recv(1024)
                        f.write(file_data)
                        remain -= len(file_data)
                with open(f"{THREAD_DIR}/{thread_title}", mode="a+") as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    f.write(f"{self.current_user['username']} uploaded {file_name}\n")
                log.i(f"<{self.current_user['username']}> uploaded a file <{thread_title}-{file_name}>")
            except Exception as e:
                log.e(e.__str__())

            client_socket.close()
            log.i(f"Closed tcp connection from <{self.current_user['username']}>")
        except Exception as e:
            self.send_back(Response(
                code=0,
                message=e.__str__()
            ))

    def DWN(self, thread_title: str, file_name: str):
        try:
            if not self.check_if_thread_exist(thread_title):
                return
            files = os.listdir("./")
            if thread_title + "-" + file_name not in files:
                self.send_back(Response(
                    code=0,
                    message=f"File '{file_name}' doesn't exists in '{thread_title}'."
                ))
                return
            self.send_back(Response(
                code=1,
                message=str(os.path.getsize(f"{thread_title}-{file_name}"))
            ))
            client_socket, client_add = establish_tcp_connection()

            try:
                with open(f"{thread_title}-{file_name}", "rb") as file:
                    fcntl.flock(file.fileno(), fcntl.LOCK_EX)
                    while True:
                        file_data = file.read(1024)
                        if file_data:
                            client_socket.send(file_data)
                        else:
                            break
                    self.send_back(Response(
                        code=1,
                        message="Transmission completed."
                    ))
            except Exception as e:
                self.send_back(Response(
                    code=0,
                    message=f"Some errors occurred during the transmission.\n({e.__str__()})"
                ))
            client_socket.close()
            log.i(f"Closed tcp connection from <{self.current_user['username']}>")
        except Exception as e:
            self.send_back(Response(
                code=0,
                message=e.__str__()
            ))

    def RMV(self, thread_title: str):
        try:
            if not self.check_if_thread_exist(thread_title):
                return
            with open(f"{THREAD_DIR}/{thread_title}") as file:
                fcntl.flock(file.fileno(), fcntl.LOCK_EX)
                first_line = file.readlines()[0].strip()
                if first_line != self.current_user["username"]:
                    self.send_back(Response(
                        code=2,
                        message="You cannot delete threads that don't belong to you!"
                    ))
                    return
            self.send_back(Response(
                code=1,
                message=""
            ))
        except Exception as e:
            self.send_back(Response(
                code=0,
                message=e.__str__()
            ))

    def RMV_CONFIRM(self, thread_title: str, selection: str):
        try:
            if selection == "yes":
                message_dicts = convert_thread_to_dicts(thread_title)
                for item in message_dicts:
                    if item["type"] == "file":
                        os.remove(f"./{thread_title}-{item['filename']}")
                os.remove(f"{THREAD_DIR}/{thread_title}")
                self.send_back(Response(
                    code=1,
                    message=f"Delete {thread_title} successfully."
                ))
            else:
                self.send_back(Response(
                    code=1,
                    message="You cancel the deletion."
                ))

        except Exception as e:
            self.send_back(Response(
                code=0,
                message=e.__str__()
            ))

    def XIT(self):
        if self.current_user['isLogin']:
            self.current_user['isLogin'] = False
        self.send_back(Response(
            code=1,
            message="Logout"
        ))
        log.i(f"{self.current_user['username']} logged out.")

    def check_if_thread_exist(self, thread_title: str):
        if not os.path.exists(f"{THREAD_DIR}/{thread_title}"):
            self.send_back(Response(
                code=0,
                message=f"Thread {thread_title} does not exit."
            ))
            return False
        return True


socketHelper = SocketHelper(serverSocket)
log.i("Server is running...")
log.i("Waiting for connection request from clients...")
signal.signal(signal.SIGINT, quit)
while True:
    try:
        data, clientAddress = serverSocket.recvfrom(1024)
        request = json2Request(data.decode())
        clientThread = ClientThread(clientAddress, socketHelper, request)
        clientThread.start()
    except timeout:
        continue
    except KeyboardInterrupt:
        break

socketTcp.close()
serverSocket.close()
