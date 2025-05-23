import socket
from PIL import Image, ImageTk
import io
import sys
import tkinter as tk
import threading
import json

SERVER_IP = sys.argv[1]

def send_message(message):
    msg_client_socket.sendall((message+"\n").encode())

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

def receive_images(conn):
    while True:
        # Receive image size first
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

        img = Image.open(io.BytesIO(data))
        resized_img = img.resize((1280, 720))
        tk_img = ImageTk.PhotoImage(resized_img)

        label.config(image=tk_img)
        label.image = tk_img

def monitor():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))  # Connect to a public DNS to get the right interface
    HOST = s.getsockname()[0]
    s.close()
    PORT = 5000
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    conn, addr = server_socket.accept()
    threading.Thread(target=receive_images, args=(conn,)).start()

root = tk.Tk()
root.title("LANDesk")
root.minsize(width=1280, height=720)
label = tk.Label(root,bg="lightblue")
label.place(x=0, y=0, width=1280, height=720)

# Bind press events
label.bind("<Button-1>", on_click)
label.bind("<Button-2>", on_click)
label.bind("<Button-3>", on_click)

# Bind release events
label.bind("<ButtonRelease-1>", on_release)
label.bind("<ButtonRelease-2>", on_release)
label.bind("<ButtonRelease-3>", on_release)

# Mouse movement
label.bind("<Motion>", on_move)

#Scroll movement
label.bind("<MouseWheel>", on_scroll)

msg_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
msg_client_socket.connect((SERVER_IP, 12000))

threading.Thread(target=monitor, daemon=True).start()
root.mainloop()