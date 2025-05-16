import socket
import pyautogui
import io

SERVER_IP = '192.168.29.147'
PORT = 5000

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