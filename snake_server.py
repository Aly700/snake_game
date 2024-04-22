import socket
import threading
import time
import uuid
import rsa
import base64
from snake import SnakeGame  # Import SnakeGame logic

# Server configuration
server = "localhost"
port = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen()
print("Server Started. Waiting for a connection...")

# RSA Key generation for the server
(public_key, private_key) = rsa.newkeys(2048)


# Serialize server's public key
pem_public_key = public_key.save_pkcs1(format='PEM')


# Game settings
rows = 20
game = SnakeGame(rows)
interval = 0.2

# Client management
clients = {}
moves_queue = {}
client_public_keys = {}
last_directions = {}

def send_data(conn, data):
    print(f"[Server] Sending data: {data}")
    if isinstance(data, str):
        data = data.encode('utf-8')

    data_length = len(data)
    conn.sendall(data_length.to_bytes(4, 'big') + data)
    print("[Server] Data sent.")

def recvall(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def broadcast_message(message, sender_id):
    for client_id, conn in clients.items():
        if client_id != sender_id and client_id in client_public_keys:
            try:
                # Append '\n' before encryption
                encrypted_message = (f"msg:{message}\n")
                encrypted_msg = rsa.encrypt(encrypted_message.encode(), client_public_keys[client_id])
                encoded_msg = base64.b64encode(encrypted_msg)
                send_data(conn, encoded_msg)
            except Exception as e:
                print(f"Error sending message to client {client_id}: {e}")


def client_thread(conn, user_id):
    global game, moves_queue

    last_directions[user_id] = "down"

    try:
        print(f"[Server] Sending server public key to client {user_id}")
        conn.sendall(pem_public_key)

        print(f"[Server] Receiving client's public key from {user_id}")
        client_pub_key_data = conn.recv(1024)  # Correctly receiving from the client connection
        if not client_pub_key_data:
            raise Exception(f"No public key received from client {user_id}")
        client_public_key = rsa.PublicKey.load_pkcs1(client_pub_key_data)
        client_public_keys[user_id] = client_public_key
        print(f"[Server] Client's public key received and loaded for {user_id}")

        while True:
            encrypted_data_length = conn.recv(4)
            if not encrypted_data_length:
                break

            data_length = int.from_bytes(encrypted_data_length, byteorder='big')
            encrypted_data = conn.recv(data_length)
            decrypted_data = rsa.decrypt(base64.b64decode(encrypted_data), private_key).decode()
            print("Decrypted data: {decrypted_data}")

            if decrypted_data.startswith("msg:"):
                chat_message = decrypted_data[4:]
                print("Chat message: {chat_message}")
                broadcast_message(f"{user_id}: {chat_message}", user_id)
            elif decrypted_data in ["left", "right", "up", "down"]:
                moves_queue[user_id] = decrypted_data

            # Send game state without encryption
            game_state = game.get_state()
            game_state_message = "game_state:" + game_state
            send_data(conn, (game_state_message + "\n").encode())
    except Exception as e:
        print(f"[Server] Error with client {user_id}: {e}")
    finally:
        game.remove_player(user_id)
        conn.close()
        if user_id in clients:
            del clients[user_id]
        if user_id in client_public_keys:
            del client_public_keys[user_id]
        if user_id in last_directions:
            del last_directions[user_id]
        if user_id in moves_queue:
            del moves_queue[user_id]
        print(f"Client {user_id} disconnected")

def game_thread():
    global game, moves_queue, last_directions
    while True:
        try:
            for user_id in last_directions:
                move = moves_queue.get(user_id, last_directions[user_id])
                game.move_player(user_id, move)
                last_directions[user_id] = move  # Update the last direction
            moves_queue.clear()
            time.sleep(interval)
        except Exception as e:
            print("Error in game_thread:", e)
            break



threading.Thread(target=game_thread, daemon=True).start()

while True:
    conn, addr = s.accept()
    user_id = str(uuid.uuid4())
    game.add_player(user_id)
    clients[user_id] = conn
    print(f"Connected to: {addr}, assigned ID: {user_id}")
    threading.Thread(target=client_thread, args=(conn, user_id)).start()

s.close()
