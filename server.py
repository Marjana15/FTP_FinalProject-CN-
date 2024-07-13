import os
import socket
import threading
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
from ttkthemes import ThemedTk

def handle_client(conn, addr, log_area, info_label, client_addresses, file_list):
    client_addresses.append(addr)
    info_label.config(text=f"{len(client_addresses)}")
    log_area.insert(END, f"[NEW CONNECTION]: {addr} connected\n")
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            command, _, param = data.partition(' ')
            
            if command == 'LIST':
                files = '\n'.join(os.listdir('serverdata'))
                conn.sendall(files.encode('utf-8'))
            elif command == 'GET':
                file_path = os.path.join('serverdata', param)
                if os.path.isfile(file_path):
                    conn.sendall(b'OK')
                    with open(file_path, 'rb') as file:
                        while True:
                            bytes_read = file.read(1024)
                            if not bytes_read:
                                break
                            conn.sendall(bytes_read)
                    log_area.insert(END, f"Sent {param} to {addr}\n")
                else:
                    conn.sendall(b'ERROR')
            elif command == 'UPLOAD':
                file_path = os.path.join('serverdata', param)
                with open(file_path, 'wb') as f:
                    while True:
                        bytes_read = conn.recv(1024)
                        if bytes_read == b'DONE':
                            break
                        f.write(bytes_read)
                log_area.insert(END, f"Received {param} from {addr}\n")
                conn.sendall(b'OK')  # Send confirmation after upload
            elif command == 'DEL':
                file_path = os.path.join('serverdata', param)
                try:
                    os.remove(file_path)
                    conn.sendall(b'OK')
                    log_area.insert(END, f"Deleted {param}\n")
                except FileNotFoundError:
                    conn.sendall(b'ERROR')
                except Exception as e:
                    log_area.insert(END, f"Failed to delete {param}: {e}\n")
                    conn.sendall(b'ERROR')
    finally:
        client_addresses.remove(addr)
        info_label.config(text=f"{len(client_addresses)}")
        log_area.insert(END, f"[DISCONNECTED]: {addr}\n")
        conn.close()

def start_server(ip, port, log_area, info_label, client_addresses, file_list):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip, int(port)))
    server_socket.listen(5)
    log_area.insert(END, f"[STARTING]: Server is starting\n")
    log_area.insert(END, f"[LISTENING]: Server is listening on {ip} : {port}\n")
    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr, log_area, info_label, client_addresses, file_list))
        thread.start()


client_addresses = []

root = ThemedTk(theme="yaru")
root.title("FTP Server")
root.geometry("600x400")

# Add style to the widgets
style = ttk.Style()
style.configure('TLabel', background='#EEE', foreground='#000')
style.configure('TButton', background='#EEE', foreground='#000')
style.configure('TEntry', background='#FFF', foreground='#000')

ttk.Label(root, text="IP Address:").pack(pady=(10,0))
ip_entry = ttk.Entry(root)
ip_entry.pack()

ttk.Label(root, text="Port:").pack(pady=(10,0))
port_entry = ttk.Entry(root)
port_entry.pack()

start_button = ttk.Button(root, text="Start Server", command=lambda: threading.Thread(target=start_server, args=(ip_entry.get(), port_entry.get(), log_area, info_label, client_addresses, file_list)).start())
start_button.pack(pady=10)

stop_button = ttk.Button(root, text="Stop Server", command=root.quit)
stop_button.pack(pady=10)

info_label = ttk.Label(root, text="0")
info_label.pack()

file_list = ttk.Frame(root)
file_list.pack(fill=BOTH, expand=True, padx=10, pady=10)

log_area = ScrolledText(root, height=10, bg="#FFF", fg="#000")
log_area.pack(fill=BOTH, expand=True)

root.mainloop()
