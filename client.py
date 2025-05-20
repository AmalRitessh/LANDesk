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

    while True:
        conn, addr = msg_server_socket.accept()
        data = conn.recv(1024)
        if not data:
            break
        execute_mouse_action(data)
    conn.close()

def execute_mouse_action(json_data):
    data = json.loads(json_data)

    if data["event"] == "move":
        mouse_controller.position = (data["x"], data["y"])

    elif data["event"] == "click":
        mouse_controller.position = (data["x"], data["y"])
        button = Button.left if data["button"] == "Button.left" else Button.right

        if data["action"] == "pressed":
            mouse_controller.press(button)
        else:
            mouse_controller.release(button)

SERVER_IP = sys.argv[1]
PORT = 5000

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