import os
import tkinter as tk
from tkinter import filedialog, messagebox
import socket
import threading
from ttkthemes import ThemedTk
from tkinter import ttk

client_socket = None  # Global socket variable

def connect_to_server(ip, port):
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, int(port)))
        status_label.config(text="[SUCCESS]: Connected to the File Server")
        connect_button.config(text="Disconnect")
        refresh_file_list()
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect: {e}")

def disconnect_from_server():
    global client_socket
    if client_socket:
        client_socket.close()
        client_socket = None
        status_label.config(text="Disconnected")
        connect_button.config(text="Connect")
        for widget in button_frame.winfo_children():
            widget.destroy()

def refresh_file_list():
    def task():
        global client_socket
        if client_socket:
            try:
                client_socket.sendall("LIST".encode('utf-8'))
                data = client_socket.recv(4096).decode('utf-8')
                files = data.split('\n')
                for widget in button_frame.winfo_children():
                    widget.destroy()
                for file in files:
                    if file:  # Avoid inserting empty strings
                        add_file_row(file)
            except Exception as e:
                messagebox.showerror("Network Error", f"Failed to refresh file list: {e}")

    threading.Thread(target=task).start()

def add_file_row(filename):
    row_frame = ttk.Frame(button_frame)
    row_frame.pack(fill="x", pady=2)

    file_label = ttk.Label(row_frame, text=filename, anchor="w")
    file_label.pack(side="left", padx=10)

    download_button = ttk.Button(row_frame, text="Download", command=lambda: download_file(filename))
    download_button.pack(side="right", padx=5)

    delete_button = ttk.Button(row_frame, text="Delete", command=lambda: delete_file(filename))
    delete_button.pack(side="right", padx=5)

def upload_file():
    filepath = filedialog.askopenfilename()
    if filepath:
        filename = os.path.basename(filepath)
        def task():
            try:
                client_socket.sendall(f"UPLOAD {filename}".encode('utf-8'))
                with open(filepath, 'rb') as f:
                    while True:
                        data = f.read(1024)
                        if not data:
                            break
                        client_socket.sendall(data)
                # Ensure the file is closed before checking for the response
                response = client_socket.recv(1024).decode('utf-8')
                if response == 'OK':
                    status_label.config(text=f"Upload Successful: {filename}")
                    refresh_file_list()
                else:
                    status_label.config(text="Upload Failed: Failed to upload file")
                    refresh_file_list()
            except Exception as e:
                status_label.config(text=f"Network Error: Failed to upload file: {e}")
        threading.Thread(target=task).start()

def download_file(filename):
    def task():
        try:
            client_socket.sendall(f"GET {filename}".encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            if response == 'OK':
                file_extension = os.path.splitext(filename)[1]
                file_types = [(f"{file_extension} files", f"*{file_extension}"), ("All files", "*.*")]
                save_path = filedialog.asksaveasfilename(defaultextension=file_extension, filetypes=file_types, initialfile=filename)
                if save_path:
                    with open(save_path, 'wb') as f:
                        while True:
                            data = client_socket.recv(1024)
                            if not data:
                                break
                            f.write(data)
                    status_label.config(text=f"Download Successful: {filename}")
            else:
                status_label.config(text="Download Failed: Could not download the file")
        except Exception as e:
            status_label.config(text=f"Network Error: Failed to download file: {e}")

    threading.Thread(target=task).start()

def delete_file(filename):
    def task():
        try:
            client_socket.sendall(f"DEL {filename}".encode('utf-8'))
            response = client_socket.recv(1024)
            if response == b'OK':
                status_label.config(text=f"Delete Successful: {filename}")
                refresh_file_list()
            else:
                status_label.config(text="Delete Failed: Could not delete the file")
        except Exception as e:
            status_label.config(text=f"Network Error: Failed to delete file: {e}")

    threading.Thread(target=task).start()

def toggle_connection(ip, port):
    if connect_button.config('text')[-1] == 'Connect':
        threading.Thread(target=connect_to_server, args=(ip, port)).start()
    else:
        disconnect_from_server()

def create_client_gui():
    global status_label, button_frame, connect_button

    root = ThemedTk(theme="yaru")
    root.title("FTP Client")

    style = ttk.Style()
    style.configure('Accent.TButton', background='#A020F0', foreground='#A020F0')  # Changed foreground to black

    ttk.Label(root, text="IP Address:").grid(row=0, column=0, padx=10, pady=10)
    ip_entry = ttk.Entry(root)
    ip_entry.grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(root, text="Port:").grid(row=0, column=2, padx=10, pady=10)
    port_entry = ttk.Entry(root)
    port_entry.grid(row=0, column=3, padx=10, pady=10)
    port_entry.insert(0, '65432')

    connect_button = ttk.Button(root, text="Connect", style="Accent.TButton", command=lambda: toggle_connection(ip_entry.get(), port_entry.get()))
    connect_button.grid(row=0, column=4, padx=10, pady=10)

    ttk.Button(root, text="Upload", style="Accent.TButton", command=upload_file).grid(row=1, column=0, columnspan=5, padx=10, pady=10)

    server_files_label = ttk.Label(root, text="Server Files")
    server_files_label.grid(row=2, column=0, columnspan=5, pady=10)
    server_files_label.configure(font=("Helvetica", 24))

    button_frame = ttk.Frame(root)
    button_frame.grid(row=3, column=0, columnspan=5, sticky="nsew", padx=10, pady=10)

    root.grid_rowconfigure(3, weight=1)
    root.grid_columnconfigure(1, weight=1)

    status_label = ttk.Label(root, text="Disconnected")
    status_label.grid(row=4, column=0, columnspan=5, pady=10)

    root.mainloop()

create_client_gui()
