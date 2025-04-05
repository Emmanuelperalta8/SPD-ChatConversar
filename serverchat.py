import socket                    # Biblioteca para comunicação de rede (sockets TCP)
import multiprocessing           # Permite execução de múltiplos processos simultaneamente
import datetime                  # Para gerar timestamps nos logs

# Limites do servidor
MAX_CLIENTS = 10                 # Número máximo de clientes conectados
MAX_MSG_LENGTH = 200            # Tamanho máximo permitido por mensagem

# Função para log com horário
def log(message):
    timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")  # Formata o horário atual
    print(f"{timestamp} {message}")                             # Exibe log com timestamp

# Função que trata as mensagens e ações de cada cliente
def process_request(client_socket, addr, all_clients, nicknames, lock):
    try:
        # Solicita o apelido do usuário
        client_socket.send("Digite seu apelido: ".encode())
        nickname = client_socket.recv(1024).decode().strip()

        if not nickname:
            nickname = f"{addr[0]}:{addr[1]}"  # Usa IP:porta como apelido padrão

        # Salva o apelido na lista de apelidos (com proteção de acesso)
        with lock:
            nicknames[client_socket.fileno()] = nickname

        log(f"{nickname} ({addr}) conectado.")
        client_socket.send("Conectado ao servidor. Você pode começar a conversar.".encode())

        # Loop principal para receber mensagens
        while True:
            message = client_socket.recv(1024).decode().strip()
            if not message:
                break

            # Verifica se mensagem excede o limite de caracteres
            if len(message) > MAX_MSG_LENGTH:
                client_socket.send(f"⚠️ Sua mensagem ultrapassou {MAX_MSG_LENGTH} caracteres.".encode())
                continue

            # Cliente deseja sair
            if message.lower() == "sair":
                log(f"{nickname} desconectou.")
                break

            log(f"{nickname}: {message}")

            # Envia a mensagem para todos os outros clientes conectados
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
        # Remove o cliente desconectado da lista e fecha a conexão
        with lock:
            if client_socket in all_clients:
                all_clients.remove(client_socket)
            nicknames.pop(client_socket.fileno(), None)
        client_socket.close()

# Função que inicia o servidor
def start_server(host='0.0.0.0', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))        # Liga o servidor ao IP e porta
    server.listen(5)                 # Começa a escutar conexões
    log(f"Servidor ouvindo em {host}:{port}")

    # Objetos compartilhados entre processos
    manager = multiprocessing.Manager()
    all_clients = manager.list()     # Lista de clientes conectados
    nicknames = manager.dict()       # Mapeia cliente → apelido
    lock = manager.Lock()            # Lock para evitar problemas de concorrência

    # Loop principal do servidor: aceita conexões
    while True:
        client_socket, addr = server.accept()

        with lock:
            # Verifica se o servidor está cheio
            if len(all_clients) >= MAX_CLIENTS:
                log(f"Servidor cheio! Recusando {addr}")
                try:
                    client_socket.send("Servidor cheio. Tente novamente mais tarde.".encode())
                except:
                    pass
                client_socket.close()
                continue
            all_clients.append(client_socket)

        # Cria um processo separado para atender esse cliente
        client_process = multiprocessing.Process(
            target=process_request,
            args=(client_socket, addr, all_clients, nicknames, lock)
        )
        client_process.daemon = True
        client_process.start()

# Ponto de entrada do programa
if __name__ == "__main__":
    start_server()
