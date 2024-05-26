import socket
import threading

# 로그인 서버 주소와 포트
# 10.30.113.204
host = '192.168.219.114'
port = 12345

# 등록된 사용자 목록
users = set()
session= {}
id = 0
user_id = {}

def handle_client(conn, addr):
    global id
    while True:
        data = conn.recv(1024).decode()
        if not data:
            break

        # 명령어에 따른 처리
        command, *params = data.split()
        if command == 'LOGIN':
            username = params[0]
            user_id[addr] = username
            if username not in users:
                users.add(username)
                online_users = ', '.join([user for user in users if user != username])
                if not online_users:
                    online_users = "No other users online."
                conn.send(f"LOGIN_SUCCESS: {online_users}".encode())
            else:
                conn.send("USER_ALREADY_LOGGED_IN".encode())
        elif command == 'LOGOUT':
            username = params[0]
            print(f"{username} logged out.")
            users.discard(username)
        elif command == 'HOST':
            username, title, host, port = params
            session[id] = (username, title, host, int(port), conn)
            print(f"{username} is hosting a chat server at {host}:{port} session id = {id}")
            conn.send(f"{id}".encode())
            id += 1
        elif command == 'LIST':
            conn.send(f"SESSIONS {len(session)}".encode())
            for key, value in session.items():
                conn.send(f"{key}: {value[0]} {value[1]}\n".encode())
        elif command == 'JOIN':
            try:
                session_id = int(params[0])
            except ValueError:
                conn.send("JOIN_FAILED, INVALID SESSION ID".encode())
                continue
            if session_id in session:
                username, title, host, port, host_conn = session[session_id]
                conn.send(f"JOIN_TO {username} {title} {host} {port}".encode())
                host_conn.send(f"{user_id[addr]}".encode())
            else:
                conn.send("JOIN_FAILED, SESSION DOESN`T EXIST".encode())
        elif command == "SERVER_CLOSED":
            session_id = int(params[0])
            if session_id in session:
                username, title, host, port, host_conn = session[session_id]
                del session[session_id] 


    conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[STARTING] Login server is running on {host}:{port}")

    while True:
        conn, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected.")
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()
