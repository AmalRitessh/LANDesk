import sys
import io
import json
import socket
import pyautogui
import threading
from pynput.mouse import Button, Controller

mouse_controller = Controller()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))  # Connect to a public DNS to get the right interface
HOST_IP = s.getsockname()[0]
s.close()

def message_listener():
    msg_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    msg_server_socket.bind((HOST_IP, 12000))
    msg_server_socket.listen()
    conn, addr = msg_server_socket.accept()

    buffer = ""

    with conn:
        while True:
            try:
                data = conn.recv(1024).decode()
                if not data:
                    break

                buffer += data
                while '\n' in buffer:
                    json_str, buffer = buffer.split('\n', 1)
                    if json_str.strip():
                        execute_mouse_action(json_str.strip())
            except Exception as e:
                print(f"[ERROR] {e}")
                break

    conn.close()

def execute_mouse_action(json_data):
    data = json.loads(json_data)

    if data["event"] == "move":
        mouse_controller.position = (round(data["x"]*WIDTH_SCALE_FACTOR), round(data["y"]*HEIGHT_SCALE_FACTOR))

    elif data["event"] == "click":
        mouse_controller.position = (round(data["x"]*WIDTH_SCALE_FACTOR), round(data["y"]*HEIGHT_SCALE_FACTOR))
        button = Button.left if data["button"] == "Button.left" else Button.right

        if data["action"] == "pressed":
            mouse_controller.press(button)
        else:
            mouse_controller.release(button)

SERVER_IP = sys.argv[1]
PORT = 5000
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
WIDTH_SCALE_FACTOR = SCREEN_WIDTH/1280
HEIGHT_SCALE_FACTOR = SCREEN_HEIGHT/720

message_thread = threading.Thread(target=message_listener, daemon=True)
message_thread.start()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

while True:
    screenshot = pyautogui.screenshot()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='JPEG', quality=80)
    data = img_byte_arr.getvalue()

    # Send length first
    size = len(data).to_bytes(4, 'big')
    client_socket.sendall(size + data)