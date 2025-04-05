import socket             # Biblioteca para comunicação via rede (TCP/IP)
import threading          # Biblioteca para trabalhar com threads (execução simultânea)
import curses             # Biblioteca para criar interfaces de terminal interativas
import time               # Para manipular tempo (pausas, etc.)

# Função para receber mensagens do servidor de forma contínua
def receive_messages(client_socket, chat_win, lock):
    while True:
        try:
            # Recebe mensagens do servidor
            message = client_socket.recv(1024).decode()
            if message:
                # Atualiza a janela do chat com a nova mensagem, com proteção contra threads simultâneas
                with lock:
                    chat_win.addstr(f"{message}\n")   # Adiciona a mensagem na janela
                    chat_win.scrollok(True)           # Permite rolagem
                    chat_win.refresh()                # Atualiza a interface
        except:
            break   # Se der erro (ex: desconexão), encerra o loop

# Função principal da interface de bate-papo com curses
def chat_interface(stdscr, client_socket):
    curses.curs_set(1)     # Mostra o cursor no terminal
    stdscr.clear()         # Limpa a tela
    height, width = stdscr.getmaxyx()  # Obtém tamanho da tela

    # Cria duas janelas: uma para o chat e outra para digitação
    chat_win = curses.newwin(height - 3, width, 0, 0)
    input_win = curses.newwin(3, width, height - 3, 0)

    input_win.addstr(0, 0, "Digite sua mensagem (digite 'sair' para encerrar):")
    input_win.refresh()

    lock = threading.Lock()  # Cria um bloqueio para evitar conflito entre threads

    # Inicia uma thread que ficará recebendo mensagens do servidor
    recv_thread = threading.Thread(target=receive_messages, args=(client_socket, chat_win, lock))
    recv_thread.daemon = True   # Finaliza junto com o programa principal
    recv_thread.start()

    # Loop principal para ler entrada do usuário e enviar para o servidor
    while True:
        input_win.move(1, 0)      # Move o cursor para a linha de entrada
        input_win.clrtoeol()      # Limpa a linha
        curses.echo()             # Mostra o que o usuário digita
        msg = input_win.getstr(1, 0).decode()  # Lê a string digitada
        curses.noecho()           # Desliga a exibição automática do texto

        if msg.lower() == 'sair':
            client_socket.send(msg.encode())  # Envia a mensagem para o servidor
            break
        else:
            client_socket.send(msg.encode())  # Envia qualquer outra mensagem

    client_socket.close()  # Encerra o socket após sair do loop

# Função para conectar ao servidor
def start_client(server_host='172.29.28.20', server_port=12345):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria um socket TCP

    try:
        client.connect((server_host, server_port))  # Tenta conectar ao servidor
    except ConnectionRefusedError:
        print("Erro: O servidor não está disponível.")
        return

    # Recebe a primeira mensagem do servidor (pode ser mensagem de boas-vindas ou erro)
    initial_msg = client.recv(1024).decode()
    if "Servidor cheio" in initial_msg:
        print(f"⚠️ {initial_msg}")
        client.close()
        return

    print(initial_msg)

    # Solicita o apelido do usuário e envia para o servidor
    nickname = input("Digite seu apelido: ")
    client.send(nickname.encode())

    time.sleep(0.5)  # Dá tempo pro servidor processar o apelido

    # Inicia a interface de chat usando curses
    curses.wrapper(chat_interface, client)

# Ponto de entrada do programa
if __name__ == "__main__":
    start_client()
