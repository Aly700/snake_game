import pygame
import json
import socket
import threading
import time
import rsa
import base64
import select

# Configuration variables
HOST = 'localhost'
PORT = 5555
CELL_SIZE = 20
GRID_SIZE = 20
REQUEST_INTERVAL = 0.1
CUSTOM_EVENT = pygame.USEREVENT + 1

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode([CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE])

# Define predefined messages and their corresponding hotkeys
predefined_messages = {
    pygame.K_z: "Congratulations!",
    pygame.K_x: "It works!",
    pygame.K_c: "Ready?"
}

# Generate RSA keys for the client
(public_key, private_key) = rsa.newkeys(1024)  # 1024-bit keys

# Helper functions for sending and receiving data
def send_data(sock, data):
    if isinstance(data, str):
        data = data.encode('utf-8')

    data_length = len(data)
    sock.sendall(data_length.to_bytes(4, 'big') + data)

def recvall(sock, n):
    data = bytearray()
    while len(data) < n:
        try:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        except BlockingIOError:
            time.sleep(0.1)
    return data

def draw_game_state(screen, game_state):
    # Fill the background with black
    screen.fill((0, 0, 0))

    # Draw all snakes
    for snake_info in game_state['snakes'].values():
        snake_positions = snake_info['positions']
        snake_color = tuple(snake_info['color'])  # Ensure color is a tuple

        for i, pos in enumerate(snake_positions):
            pygame.draw.rect(screen, snake_color, [pos[0]*CELL_SIZE, pos[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE])

            # Draw eyes for the head of the snake
            if i == 0:  # Head of the snake
                centre = CELL_SIZE // 2
                radius = 3
                eye1 = (pos[0]*CELL_SIZE + centre - radius, pos[1]*CELL_SIZE + 8)
                eye2 = (pos[0]*CELL_SIZE + CELL_SIZE - radius * 2, pos[1]*CELL_SIZE + 8)

                # Eyes color - white or another contrasting color
                eye_color = (255, 255, 255) if snake_color != (255, 255, 255) else (0, 0, 0)
                pygame.draw.circle(screen, eye_color, eye1, radius)
                pygame.draw.circle(screen, eye_color, eye2, radius)

    # Draw snacks
    for pos in game_state['snacks']:
        pygame.draw.rect(screen, (125, 125, 125), [pos[0]*CELL_SIZE, pos[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE])

    # Draw grid lines
    for row in range(GRID_SIZE):
        for column in range(GRID_SIZE):
            rect = pygame.Rect(column * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (25, 25, 25), rect, 1)


def parse_game_state(state_str):
    # Parse the JSON string into a Python dictionary
    game_state = json.loads(state_str)
    return game_state

def encrypt_message(message, server_public_key):
    encrypted = rsa.encrypt(message.encode(), server_public_key)
    return base64.b64encode(encrypted).decode()

def decrypt_message(encrypted_message, private_key):
    decoded_message = base64.b64decode(encrypted_message)
    return rsa.decrypt(decoded_message, private_key).decode()



def handle_server_messages(s, server_public_key):
    global running
    while running:
        try:
            raw_msg_length = recvall(s, 4)
            if not raw_msg_length:
                time.sleep(0.1)
                continue

            msg_length = int.from_bytes(raw_msg_length, byteorder='big')
            data = recvall(s, msg_length)
            if data:
                message = data.decode()

                # Check if the message is a game state message
                if message.startswith("game_state:"):
                    game_state_json = message[len("game_state:"):]
                    try:
                        game_state = json.loads(game_state_json)
                        event = pygame.event.Event(CUSTOM_EVENT, game_state=game_state)
                        pygame.event.post(event)
                    except json.JSONDecodeError:
                        print("")
                else:
                    # For encrypted messages
                    try:
                        decrypted_message = rsa.decrypt(base64.b64decode(message), private_key).decode()
                        chat_message = decrypted_message[len("msg:"):].strip()
                        event = pygame.event.Event(CUSTOM_EVENT, message=chat_message)
                        pygame.event.post(event)
                    except Exception as e:
                        print(f"")
            else:
                time.sleep(0.1)
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"")
            break



# Main game loop setup
running = True
last_request_time = 0


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.setblocking(False)

    # Wait for server's public key
    print("[Client] Waiting for server's public key...")
    server_pub_key_data = None
    while not server_pub_key_data:
        ready_to_read, _, _ = select.select([s], [], [], 5.0)  # 5 seconds timeout
        if s in ready_to_read:
            server_pub_key_data = s.recv(2048)

    server_public_key = rsa.PublicKey.load_pkcs1(server_pub_key_data)
    print("[Client] Received server's public key.")

    # Send client's public key to the server
    client_public_key_pem = public_key.save_pkcs1(format='PEM')
    s.sendall(client_public_key_pem)
    print("[Client] Client's public key sent.")

    threading.Thread(target=handle_server_messages, args=(s, server_public_key)).start()

  
    print("Chat:")

    # Main loop
    while running:
        current_time = time.time()
        event_processed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == CUSTOM_EVENT:
                if hasattr(event, 'game_state'):
                    # Handle game state
                    draw_game_state(screen, event.game_state)
                    event_processed = True
                elif hasattr(event, 'message'):
                    # Handle other messages
                    chat_message = event.message
                    print(f"User: {chat_message}")
                    event_processed = True

            elif event.type == pygame.KEYDOWN:
                if event.key in predefined_messages:
                    message = predefined_messages[event.key]
                    encrypted_message = encrypt_message(f"msg:{message}", server_public_key)
                    send_data(s, encrypted_message)
                    print(f"You: {message}")
                    event_processed = True
                elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_r]:
                    control_message = pygame.key.name(event.key)
                    encrypted_control_message = encrypt_message(control_message, server_public_key)
                    send_data(s, encrypted_control_message)
                    event_processed = True
                elif event.key == pygame.K_q:
                    encrypted_quit_message = encrypt_message("quit", server_public_key)
                    send_data(s, encrypted_quit_message)
                    running = False
                    event_processed = True

        if not event_processed and current_time - last_request_time > REQUEST_INTERVAL:
            encrypted_get_message = encrypt_message("get", server_public_key)
            send_data(s, encrypted_get_message)
            last_request_time = current_time

        pygame.display.flip()

    pygame.quit()
    print("Exiting Game")