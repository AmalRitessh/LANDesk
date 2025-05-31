import socket
from PIL import Image, ImageTk
import io
import sys
import tkinter as tk
import threading
import json
import keyboard

SERVER_IP = sys.argv[1]
hook = None
lock = threading.Lock()

def send_message(message):
    try:
        msg_client_socket.sendall((message + "\n").encode())
    except Exception as e:
        print(f"Error sending message: {e}")

def on_click(event):
    button_map = {1: "Left", 2: "Middle", 3: "Right"}
    data = {
        "event": "click",
        "x": event.x,
        "y": event.y,
        "button": button_map.get(event.num, f"Button-{event.num}"),
        "action": "pressed"
    }
    send_message(json.dumps(data))

def on_release(event):
    button_map = {1: "Left", 2: "Middle", 3: "Right"}
    data = {
        "event": "click",
        "x": event.x,
        "y": event.y,
        "button": button_map.get(event.num, f"Button-{event.num}"),
        "action": "released"
    }
    send_message(json.dumps(data))

def on_move(event):
    data = {
        "event": "move",
        "x": event.x,
        "y": event.y
    }
    send_message(json.dumps(data))

def on_scroll(event):
    data = {
        "event": "scroll",
        "x": event.x,
        "y": event.y,
        "direction": "up" if event.delta > 0 else "down",
        "amount": 1
    }
    send_message(json.dumps(data))

def on_key(event):
    key_data = {
        "event": "key",
        "key": event.name,
        "action": "pressed" if event.event_type == keyboard.KEY_DOWN else "released"
    }
    send_message(json.dumps(key_data))

def start_hook():
    global hook
    with lock:
        if hook is None:
            try:
                hook = keyboard.hook(on_key, suppress=True)
            except Exception as e:
                print(f"Error starting keyboard hook: {e}")

def stop_hook():
    global hook
    with lock:
        if hook is not None:
            try:
                keyboard.unhook(hook)
            except Exception as e:
                print(f"Error stopping keyboard hook: {e}")
            hook = None

def on_focus_in(event=None):
    start_hook()

def on_focus_out(event=None):
    stop_hook()

def on_closing():
    stop_hook()
    msg_client_socket.sendall(("CLOSEING FROM SERVER\n").encode())
    server_socket.close()
    msg_client_socket.close()
    root.destroy()

def receive_images(conn):
    while True:
        try:
            size_data = conn.recv(4)
            if not size_data:
                break
            size = int.from_bytes(size_data, 'big')

            data = b''
            while len(data) < size:
                packet = conn.recv(size - len(data))
                if not packet:
                    break
                data += packet

            if data == b'CLOSED FROM CLIENT':
                print("CLOSED FROM CLIENT")
                on_closing()

            img = Image.open(io.BytesIO(data))
            resized_img = img.resize((1280, 720))
            tk_img = ImageTk.PhotoImage(resized_img)

            label.config(image=tk_img)
            label.image = tk_img
        except Exception as e:
            print(f"Error receiving or processing image: {e}")

# GUI Setup
root = tk.Tk()
root.title("LANDesk")
root.minsize(width=1280, height=720)
label = tk.Label(root, bg="lightblue")
label.place(x=0, y=0, width=1280, height=720)

# Bind press events
label.bind("<Button-1>", on_click)
label.bind("<Button-2>", on_click)
label.bind("<Button-3>", on_click)
# Bind release events
label.bind("<ButtonRelease-1>", on_release)
label.bind("<ButtonRelease-2>", on_release)
label.bind("<ButtonRelease-3>", on_release)

# Mouse movement and scroll bindings
label.bind("<Motion>", on_move)
label.bind("<MouseWheel>", on_scroll)

root.bind("<FocusIn>", on_focus_in)
root.bind("<FocusOut>", on_focus_out)
root.protocol("WM_DELETE_WINDOW", on_closing)

# Message channel socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
HOST = s.getsockname()[0]
s.close()
PORT = 5000
try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    conn, addr = server_socket.accept()
    threading.Thread(target=receive_images, args=(conn,), daemon=True).start()
except Exception as e:
    print(f"Error connecting to server socket: {e}")

try:
    msg_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    msg_client_socket.connect((SERVER_IP, 12000))
except Exception as e:
    print(f"Error connecting to message socket: {e}")

# Start the GUI loop
root.mainloop()