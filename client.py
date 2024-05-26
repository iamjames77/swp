import socket
import threading
import sys

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
choice = ''

def connect_to_server(host, port):
    try:
        client.connect((host, port))
        login()
        select_option()
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        sys.exit(1)
    finally:
        disconnect()

def disconnect():
    try:
        client.send(f"LOGOUT {username}".encode())
        client.close()
    except socket.error as e:
        print(f"Error disconnecting from server: {e}")

def select_option():
    global choice
    choice = input("Host a session (H)\nJoin a session (J)\nLogout (L)\n>").upper()
    if choice == 'H':
        title = input("Enter a title for your session: ")
        IP = get_local_ip()
        new_server = ChatServer(host=IP, port=0)
        host, port = new_server.server.getsockname()
        client.send(f"HOST {username} {title} {host} {port}".encode())
        id = client.recv(1024).decode()
        print(f"Server hosted at {host} on port {port} id = {id}")
        new_server.id = int(id)
        new_server.run()
    elif choice == 'J':
        client.send("LIST".encode())
        list_size = client.recv(1024).decode()
        if list_size == "SESSIONS 0":
            print("No sessions available.")
            select_option()
        print("id | username | title")
        response = client.recv(1024).decode()
        print(response)
        choice = input("Enter the id of the session you want to join: ")
        client.send(f"JOIN {choice}".encode())
        response = client.recv(1024).decode()
        print(response)
        if "JOIN_TO" in response:
            host, port = response.split()[3:]
            new_client = ChatClient(host, int(port))
            new_client.run()
        else:
            select_option()
    elif choice == 'L':
        disconnect()

def login():
    while True:
        global username
        username = input("Enter your username: ")
        client.send(f"LOGIN {username}".encode())
        response = client.recv(1024).decode()
        if "LOGIN_SUCCESS" in response:
            print("Logged in successfully!")
            online_users = response.split(' ', 1)[1]
            print("Online users:", online_users)
            break
        elif response == "USER_ALREADY_LOGGED_IN":
            print("This user is already logged in. Try another username.")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 이 주소는 접속되지 않아도 되며, 라우팅 테이블만 확인하기 위한 것입니다.
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class ChatServer:
    def __init__(self, host= '0.0.0.0', port=0):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        self.clients = []
        self.addresses = []
        self.id = 0
        
        print(f"[STARTING] Server starting, host {host} at port {self.server.getsockname()[1]}")

    def handle_clients(self, conn, addr):
        user_id = client.recv(1024).decode()
        print(f"[CONNECTION] {user_id} connected.\n> ", end='')
        while True:
            try:
                msg = conn.recv(1024).decode()
                if msg:
                    print(f"{user_id}: {msg}\n> ",end='')
                    self.broadcast_messages(f"{user_id}: {msg}", conn)
                else:
                    break
            except:
                continue

    def broadcast_messages(self, msg, sender):
        for client in self.clients:
            if client != sender:
                try:
                    client.send(msg.encode())
                except:
                    client.close()
                    self.remove_client(client)

    def remove_client(self, client):
        if client in self.clients:
            self.clients.remove(client)

    def accept_connections(self):
        while True:
            client, client_address = self.server.accept()
            client.send("Connected to the server!".encode())
            self.addresses.append(client_address)
            self.clients.append(client)
            threading.Thread(target=self.handle_clients, args=(client, client_address)).start()

    def send_message(self):
        while True:
            print('> ', end='')
            message = input()
            if message == "!QUIT":
                self.server.close()
                client.send(f"SERVER_CLOSED {self.id}".encode())
                select_option()
            else:
                self.broadcast_messages(f"{username}: {message}", None)

    def run(self):
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.start()
        self.send_message()
    

class ChatClient:
    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.client.connect((host, port))

    def send_message(self, msg):
        self.client.send(msg.encode())

    def receive_messages(self):
        while True:
            try:
                msg = self.client.recv(1024).decode()
                print(msg+'\n> ', end='')
            except:
                print("Connection closed by the server.")
                self.client.close()
                select_option()

    def run(self):
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()
        while True:
            print("> ", end='')
            msg = input()
            if msg == "!QUIT":
                self.client.send(msg.encode())
                self.client.close()
                select_option()
            else:
                self.send_message(msg)

if __name__ == "__main__":
    login_host, login_port = '192.168.219.117', 12345
    connect_to_server(login_host, login_port)
    
