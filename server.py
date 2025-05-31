import socket
import pickle
import numpy as np
import struct

"""
socket: comunicação via rede usando TCP/IP
pickle: serialização e desserialização de objetos Python
numpy: operações com arrays e matrizes numéricas
struct: empacotamento/desempacotamento seguro de dados binários, como inteiros em bytes
"""
# Função start_server
# ------------------------------------------------------------
# Esta função inicia um servidor TCP que escuta por conexões de clientes em um endereço e porta específicos.
# Ela é usada como parte de um sistema de multiplicação de matrizes distribuída, onde o cliente envia
# partes da matriz A (A_chunk) e a matriz B inteira para o servidor, que realiza a multiplicação 
# e devolve o resultado correspondente (C_chunk).
#
# Parâmetros:
# - host (str): endereço IP ou hostname onde o servidor irá escutar. Padrão é 'localhost'.
# - port (int): número da porta onde o servidor irá escutar. Padrão é 5000.
#
# Passos da função:
# 1. Cria um socket TCP.
# 2. Associa o socket ao endereço e porta especificados.
# 3. Coloca o socket em modo de escuta, aceitando 1 conexão por vez.
# 4. Entra em um loop infinito, onde:
#    - Aguarda uma conexão do cliente.
#    - Recebe os primeiros 4 bytes indicando o tamanho dos dados a serem recebidos.
#    - Recebe os dados completos em partes (chunks) de até 4096 bytes.
#    - Desserializa os dados usando pickle para obter A_chunk e B.
#    - Realiza a multiplicação de matrizes: C_chunk = A_chunk * B.
#    - Serializa o resultado C_chunk e envia de volta ao cliente, precedido pelo tamanho.
#    - Fecha a conexão atual e volta a escutar outra.
# 5. Se ocorrer qualquer exceção, imprime o erro e fecha o socket no bloco `finally`.

def start_server(host='localhost', port=5000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Servidor escutando em {host}:{port}")

    try:
        while True:
            conn, addr = server_socket.accept()
            print(f"Conectado a {addr}")

            size_data = conn.recv(4)
            if not size_data:
                print("Nenhum dado recebido, fechando conexão")
                conn.close()
                continue
            data_size = struct.unpack('>I', size_data)[0]

            received_data = b""
            while len(received_data) < data_size:
                chunk = conn.recv(4096)
                if not chunk:
                    print("Conexão interrompida durante recebimento")
                    break
                received_data += chunk

            try:
                A_chunk, B = pickle.loads(received_data)
            except Exception as e:
                print(f"Erro ao deserializar dados: {e}")
                conn.close()
                continue

            C_chunk = np.dot(A_chunk, B)

            result_data = pickle.dumps(C_chunk)
            conn.sendall(struct.pack('>I', len(result_data))) 
            conn.sendall(result_data)  

            conn.close()

    except Exception as e:
        print(f"Erro no servidor: {e}")
    finally:
        server_socket.close()

# Bloco principal de execução
# ------------------------------------------------------------
# Este bloco garante que o servidor só será iniciado se este arquivo for executado diretamente
# (ou seja, não será executado se for importado como módulo por outro script).
#
# Funcionalidade:
# - Importa o módulo `sys` para acessar os argumentos da linha de comando.
# - Tenta ler o primeiro argumento passado (índice 1) como número da porta para o servidor.
#   Se nenhum argumento for fornecido, usa a porta padrão 5000.
# - Chama a função `start_server` com o host definido como 'localhost' e a porta obtida.
#
# Isso permite iniciar múltiplos servidores em diferentes portas ao executar, por exemplo:
#   python server.py 5001
#   python server.py 5002
if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    start_server('localhost', port)