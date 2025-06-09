import socket
import threading

class GameServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.clients = []
        self.rooms = {}
        self.lock = threading.Lock()
        print(f"Server listening on {self.host}:{self.port}")

    def handle_client(self, conn, addr):
        print(f"New connection from {addr}")
        try:
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break
                parts = data.split('|')
                command = parts[0]
                if command == 'CREATE_ROOM':
                    with self.lock:
                        room_id = len(self.rooms) + 1
                        num_players = int(parts[1])
                        password = parts[2] if len(parts) > 2 else ""
                        self.rooms[room_id] = {
                            'num_players': num_players,
                            'players': [conn],
                            'max_players': num_players,
                            'password': password
                        }
                        conn.sendall(f"ROOM_CREATED|{room_id}".encode('utf-8'))
                        # 若玩家数为 1，直接发送游戏开始消息
                        if num_players == 1:
                            conn.sendall("GAME_START".encode('utf-8'))
                elif command == 'JOIN_ROOM':
                    room_id = int(parts[1])
                    password = parts[2] if len(parts) > 2 else ""
                    if room_id in self.rooms and len(self.rooms[room_id]['players']) < self.rooms[room_id]['max_players'] and self.rooms[room_id]['password'] == password:
                        self.rooms[room_id]['players'].append(conn)
                        conn.sendall("ROOM_JOINED".encode('utf-8'))
                        if len(self.rooms[room_id]['players']) == self.rooms[room_id]['max_players']:
                            with self.lock:
                                for client in self.rooms[room_id]['players']:
                                    client.sendall("GAME_START".encode('utf-8'))
                    else:
                        conn.sendall("ROOM_FULL_OR_NOT_EXIST".encode('utf-8'))
                else:
                    with self.lock:
                        for room_id, room in self.rooms.items():
                            if conn in room['players']:
                                for client in room['players']:
                                    if client != conn:
                                        client.sendall(data.encode('utf-8'))
                                break
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            with self.lock:
                for room_id, room in list(self.rooms.items()):
                    if conn in room['players']:
                        room['players'].remove(conn)
                        if not room['players']:
                            del self.rooms[room_id]
            conn.close()
            print(f"Connection closed with {addr}")

    def start(self):
        while True:
            conn, addr = self.server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    server = GameServer()
    server.start()