import sys
import io
import json
import socket
import pyautogui
import threading
from pynput.mouse import Button, Controller
import keyboard
import tkinter as tk

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
                        if json_str.strip() == "CLOSEING FROM SERVER":
                            print("CLOSEING FROM SERVER")
                            on_closing()
                        execute_input(json_str.strip())
            except Exception as e:
                print(f"[ERROR] {e}")
                break

    conn.close()

def execute_input(json_data):
    data = json.loads(json_data)

    if data["event"] == "move":
        mouse_controller.position = (
            round(data["x"]*WIDTH_SCALE_FACTOR), 
            round(data["y"]*HEIGHT_SCALE_FACTOR)
            )

    elif data["event"] == "scroll":
        mouse_controller.position = (
            round(data["x"]*WIDTH_SCALE_FACTOR), 
            round(data["y"]*HEIGHT_SCALE_FACTOR)
            )

        if data["direction"] == "up":
            mouse_controller.scroll(0, data["amount"])
        elif data["direction"] == "down":
            mouse_controller.scroll(0, -data["amount"])
        else:
            print("Unknown direction:", data["direction"])

    elif data["event"] == "click":
        mouse_controller.position = (
            round(data["x"]*WIDTH_SCALE_FACTOR), 
            round(data["y"]*HEIGHT_SCALE_FACTOR)
            )

        button = None
        if data["button"] == "Left":
            button = Button.left
        elif data["button"] == "Right":
            button = Button.right
        elif data["button"] == "Middle":
            button = Button.middle
        else:
            print("Unknown button:", data["button"])

        if button:
            if data["action"] == "pressed":
                mouse_controller.press(button)
            elif data["action"] == "released":
                mouse_controller.release(button)
            else:
                print("Unknown action:", data["action"])
    elif data["event"] == "key":
        try:
            key = data["key"]
            action = data["action"]
            if action == "pressed":
                keyboard.press(key)
            elif action == "released":
                keyboard.release(key)
        except Exception as e:
            print(f"Error processing key event: {e}")

def send_image():
    while True:
        screenshot = pyautogui.screenshot()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='JPEG', quality=80)
        data = img_byte_arr.getvalue()

        # Send length first
        size = len(data).to_bytes(4, 'big')
        try:
            client_socket.sendall(size + data)
        except Exception as e:
            print(f"[ERROR] {e}")
            
def on_closing():
    data = "CLOSED FROM CLIENT"
    size = len(data).to_bytes(4, 'big')
    client_socket.sendall(size + data.encode())
    client_socket.close()
    root.destroy()

SERVER_IP = sys.argv[1]
PORT = 5000
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
WIDTH_SCALE_FACTOR = SCREEN_WIDTH/1280
HEIGHT_SCALE_FACTOR = SCREEN_HEIGHT/720

message_thread = threading.Thread(target=message_listener, daemon=True)
message_thread.start()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

send_image_thread = threading.Thread(target=send_image,daemon=True)
send_image_thread.start()

root = tk.Tk()
root.title("LANDesk - Active")
root.config(bg="lightblue")
root.minsize(height=100, width= 300)
root.protocol("WM_DELETE_WINDOW", on_closing)

label = tk.Label(root,bg="lightblue",font=("Comic Sans MS",17),text=SERVER_IP)
label.pack()

tk.Button(root, bg="lightblue", font=("Comic Sans MS",13), text="Close", command=on_closing).pack()
root.mainloop()
