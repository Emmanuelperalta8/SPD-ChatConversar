import socket
import multiprocessing
import datetime

MAX_CLIENTS = 10
MAX_MSG_LENGTH = 200  # limite de caracteres por mensagem

def log(message):
    timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
    print(f"{timestamp} {message}")

def process_request(client_socket, addr, all_clients, nicknames, lock):
    try:
        client_socket.send("Digite seu apelido: ".encode())
        nickname = client_socket.recv(1024).decode().strip()

        if not nickname:
            nickname = f"{addr[0]}:{addr[1]}"

        with lock:
            nicknames[client_socket.fileno()] = nickname

        log(f"{nickname} ({addr}) conectado.")

        client_socket.send("Conectado ao servidor. Você pode começar a conversar.".encode())

        while True:
            message = client_socket.recv(1024).decode().strip()
            if not message:
                break

            if len(message) > MAX_MSG_LENGTH:
                client_socket.send(f"⚠️ Sua mensagem ultrapassou {MAX_MSG_LENGTH} caracteres.".encode())
                continue

            if message.lower() == "sair":
                log(f"{nickname} desconectou.")
                break

            log(f"{nickname}: {message}")

            with lock:
                for c in all_clients:
                    if c != client_socket:
                        try:
                            c.send(f"{nickname}: {message}".encode())
                        except Exception as e:
                            log(f"Erro ao enviar para {c.getpeername()}: {e}")

    except Exception as e:
        log(f"Erro com {addr}: {e}")

    finally:
        with lock:
            if client_socket in all_clients:
                all_clients.remove(client_socket)
            nicknames.pop(client_socket.fileno(), None)
        client_socket.close()

def start_server(host='0.0.0.0', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    log(f"Servidor ouvindo em {host}:{port}")

    manager = multiprocessing.Manager()
    all_clients = manager.list()
    nicknames = manager.dict()
    lock = manager.Lock()

    while True:
        client_socket, addr = server.accept()

        with lock:
            if len(all_clients) >= MAX_CLIENTS:
                log(f"Servidor cheio! Recusando {addr}")
                try:
                    client_socket.send("Servidor cheio. Tente novamente mais tarde.".encode())
                except:
                    pass
                client_socket.close()
                continue
            all_clients.append(client_socket)

        client_process = multiprocessing.Process(
            target=process_request,
            args=(client_socket, addr, all_clients, nicknames, lock)
        )
        client_process.daemon = True
        client_process.start()

if __name__ == "__main__":
    start_server()
