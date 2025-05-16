import socket
from PIL import Image, ImageTk
import io
import tkinter as tk
import threading

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
label.pack(expand=True, fill='both')

threading.Thread(target=monitor, daemon=True).start()
root.mainloop()