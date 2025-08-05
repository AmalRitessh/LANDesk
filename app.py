import os
import tkinter as tk
import socket
import threading
import subprocess
import ipaddress
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import base64

# Generating asymmetric key pair
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

class LANDesk:
    def __init__(self):
        self.received_pem_bytes = b''
        self.key = b''
        self.nonce = b''

        self.root = tk.Tk()
        self.root.title("LANDesk")
        self.root.config(bg="lightblue")
        self.root.minsize(853,480)
        self.root.maxsize(853,480)
        self.root.geometry("640x360+450+200")

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to a public DNS to get the right interface
        self.HOST_IP = s.getsockname()[0]
        s.close()

        tk.Label(text="LANDesk",bg="lightblue",font=("Comic Sans MS",30,"bold")).pack()
        tk.Label(text=self.HOST_IP,bg="lightblue",font=("Comic Sans MS",10,"bold")).pack()
        connectToIp = tk.Entry(self.root, font=("Arial", 15))
        connectToIp.pack()
        tk.Button(text="submit",bg="lightblue", font=("Comic Sans MS",14,"bold"),command=lambda: self.access_request(connectToIp.get().strip())).pack()


        tk.Label(self.root,text="request:",bg = "lightblue", font=("Comic Sans MS",14,"bold")).place(x=10,y=160)
        self.requestFrame = tk.Frame(self.root)
        self.requestFrame.config(bg="green")
        self.requestFrame.place(x=1, y=200, width=425, height=280)

        tk.Label(self.root,text="view:",bg = "lightblue", font=("Comic Sans MS",14,"bold")).place(x=437,y=160)
        self.viewFrame = tk.Frame(self.root)
        self.viewFrame.config(bg="red")
        self.viewFrame.place(x=427, y=200, width=425, height=280)

        message_thread = threading.Thread(target=self.message_listener, daemon=True)
        message_thread.start()
        
        self.root.mainloop()

    def message_listener(self):
        msg_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        msg_server_socket.bind((self.HOST_IP, 12345))
        msg_server_socket.listen()

        while True:
            conn, addr = msg_server_socket.accept()
            data = conn.recv(1024)
            if not data:
                break
            print(f"{addr[0]}: {data[0:17].decode()}")
            if data[0:17] == b"REQUESTING ACCESS":
                self.received_pem_bytes = data[17:]
                self.root.after(0, lambda: self.add_request(addr[0]))
            elif data[0:17] == b"ACCEPTING REQUEST":
                encrypted = data[17:]
                decrypted = private_key.decrypt(
                    encrypted,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                self.key = decrypted[:32]
                self.nonce = decrypted[32:] 

                self.root.after(0, lambda: self.add_view(addr[0]))
            elif data[0:17] == b"CONNECT TO SERVER":
                self.root.after(0, lambda: self.initiate_client(addr[0]))
        conn.close()

    def generate_chacha20_key_nonce(self):
        key = os.urandom(32)
        nonce = os.urandom(16)
        return key, nonce
    
    def is_valid_ip(self,ip_str):
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False

    def initiate_client(self,IP):
        subprocess.Popen(["python3", "client.py", IP, self.key.hex(), self.nonce.hex()], text=True)

    def initiate_server(self,IP,frame):
        try:
            frame.destroy()
            msg_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            msg_client_socket.settimeout(2)
            msg_client_socket.connect((IP, 12345))
            subprocess.Popen(["python3", "server.py", IP, self.key.hex(), self.nonce.hex()], text=True)

            message = "CONNECT TO SERVER"
            msg_client_socket.sendall(message.encode())
            msg_client_socket.close()
        except:
            print("can't connect: initiate_server")

    def access_request(self,IP):
        if self.is_valid_ip(IP):
            try:
                msg_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                msg_client_socket.settimeout(2)
                msg_client_socket.connect((IP, 12345))

                message = b"REQUESTING ACCESS" + public_pem
                msg_client_socket.sendall(message)
                msg_client_socket.close()
            except:
                print("can't connect: access_request")
        else:
            print("invalid ip: access_request")

    def accept_response(self,IP,frame):
        try:
            frame.destroy()
            msg_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            msg_client_socket.settimeout(2)
            msg_client_socket.connect((IP, 12345))

            # Generating symmetric key and nonce
            self.key, self.nonce = self.generate_chacha20_key_nonce()
            key_pair = self.key + self.nonce
            loaded_public_key = serialization.load_pem_public_key(
                self.received_pem_bytes,
                backend=default_backend()
            )

            # Encrypt the key+nonce with the public key
            encrypted = loaded_public_key.encrypt(
                key_pair,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            message = b"ACCEPTING REQUEST" + encrypted
            msg_client_socket.sendall(message)
            msg_client_socket.close()
        except:
            print("can't connect: accept_response")

    def add_request(self,IP):
        requestObjectFrame = tk.Frame(self.requestFrame)
        requestObjectFrame.config(bg="yellow",height=50,width=425)
        requestObjectFrame.pack(pady=2)

        tk.Label(requestObjectFrame,text=IP,font=("Comic Sans MS",13)).place(x=65,y=10)
        accept = tk.Button(requestObjectFrame,text="Accept",font=("Comic Sans MS",12), command=lambda f=requestObjectFrame: self.accept_response(IP,f))
        accept.place(x=250,y=5)

        reject = tk.Button(requestObjectFrame,text="Reject",font=("Comic Sans MS",12),command=lambda f=requestObjectFrame: self.remove(f))
        reject.place(x=340,y=5)

    def add_view(self,IP):
        viewObjectFrame = tk.Frame(self.viewFrame)
        viewObjectFrame.config(bg="yellow",height=50,width=425)
        viewObjectFrame.pack(pady=2)

        tk.Label(viewObjectFrame,text=IP,font=("Comic Sans MS",13)).place(x=65,y=10)
        view = tk.Button(viewObjectFrame,text="View",font=("Comic Sans MS",12), command=lambda f=viewObjectFrame: self.initiate_server(IP,f))
        view.place(x=250,y=5)

        reject = tk.Button(viewObjectFrame,text="Reject",font=("Comic Sans MS",12),command=lambda f=viewObjectFrame: self.remove(f))
        reject.place(x=340,y=5)

    def remove(self,frame):
        frame.destroy()

LANDesk()