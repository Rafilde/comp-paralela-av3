import socket
import pickle
import numpy as np
from multiprocessing import Process
import time
import struct

"""
socket: comunicação via rede usando TCP/IP
pickle: serialização e desserialização de objetos Python
numpy: operações com arrays e matrizes numéricas
multiprocessing.Process: criação de processos paralelos para execução simultânea
time: controle e manipulação de tempo (ex: sleep, marcações)
struct: empacotamento/desempacotamento seguro de dados binários, como inteiros em bytes
"""

# Função: create_matrix
# ---------------------------------------------
# Esta função é responsável por gerar duas matrizes aleatórias (A e B),
# que podem ser multiplicadas entre si.
# 
# Passos:
# 1. Solicita ao usuário as dimensões da matriz A (número de linhas e colunas),
#    e o número de colunas da matriz B (lembrando que o número de linhas da matriz B
#    precisa ser igual ao número de colunas da matriz A para que a multiplicação seja possível).
# 2. Solicita também um número inteiro N que define o valor máximo dos elementos gerados
#    aleatoriamente nas matrizes (valores entre 0 e N-1).
# 3. Verifica se todos os valores inseridos são válidos (maiores que zero),
#    e em caso negativo, levanta um erro.
# 4. Gera as matrizes A (de tamanho ROW_A x COLUMNS_A) e B (de tamanho COLUMNS_A x COLUMNS_B)
#    utilizando a função `np.random.randint`.
# 5. Exibe as matrizes A e B no terminal.
# 6. Retorna as matrizes A, B e o número de linhas da matriz A, que geralmente é usado
#    para dividir os dados entre servidores em paralelização.
#
# Se ocorrer algum erro na entrada (por exemplo, se o usuário digitar uma letra),
# a função captura a exceção, imprime a mensagem de erro e retorna `None` para todos os valores.
def create_matrix():
    print("=== Gerador de Matrizes Aleatórias ===")
    try:
        ROW_A = int(input("Informe o número de LINHAS da matriz A: "))
        COLUMNS_A = int(input("Informe o número de COLUNAS da matriz A: "))
        COLUMNS_B = int(input("Informe o número de COLUNAS da matriz B: "))
        N = int(input("Informe um valor máximo a ser gerado randomicamente: "))

        if ROW_A <= 0 or COLUMNS_A <= 0 or COLUMNS_B <= 0 or N <= 0:
            raise ValueError("Número deve ser maior que zero")
        
        A = np.random.randint(0, N, (ROW_A, COLUMNS_A))
        B = np.random.randint(0, N, (COLUMNS_A, COLUMNS_B))

        print("\nMatriz A ({}x{}):".format(ROW_A, COLUMNS_A))
        print(A)
        print("\nMatriz B ({}x{}):".format(COLUMNS_A, COLUMNS_B))
        print(B)

        return A, B, ROW_A

    except ValueError as e:
        print(f"Erro: {e}")
        return None, None, None
    
# Função: generate_host
# ---------------------------------------------
# Esta função tem como objetivo configurar os servidores (hosts) que irão
# processar partes da matriz A de forma paralela.
#
# Passos:
# 1. Pergunta ao usuário quantos servidores deseja utilizar para o processamento.
#    O número de servidores deve ser pelo menos 1 e no máximo igual ao número
#    de linhas da matriz A (já que cada servidor receberá ao menos uma linha).
# 2. Se o número informado for inválido, a função lança um erro e retorna `None`.
# 3. Caso seja válido, a função cria uma lista de tuplas `HOSTS`, onde cada tupla
#    representa um servidor rodando localmente (localhost) com uma porta diferente
#    iniciando em 5000 (ex: (localhost, 5000), (localhost, 5001), etc.).
# 4. A matriz A é então dividida em partes iguais (ou quase iguais) entre os hosts
#    usando `np.array_split`, que divide a matriz em `NUMBER_OF_HOST` pedaços ao longo
#    das linhas (axis=0).
# 5. Por fim, a função retorna:
#     - a lista de hosts (endereços dos servidores),
#     - a lista de partes da matriz A que cada servidor irá receber.
def generate_host(A, TOTAL_ROWS):
    try:
        NUMBER_OF_HOST = int(input(f"\nQuantos servidores (hosts) você quer usar? (1 até {TOTAL_ROWS}): "))
        if NUMBER_OF_HOST < 1 or NUMBER_OF_HOST > TOTAL_ROWS:
            raise ValueError("Número de hosts deve estar entre 1 e o total de linhas da matriz A.")
    except ValueError as e:
        print(f"Erro: {e}")
        return None, None
    
    HOSTS = [("localhost", 5000 + i) for i in range(NUMBER_OF_HOST)]
    PARTS_OF_MATRIX = np.array_split(A, NUMBER_OF_HOST, axis=0)

    return HOSTS, PARTS_OF_MATRIX

# Função: start_server_process
# ------------------------------------------------
# Esta função inicia um processo de servidor em uma porta específica.
#
# Explicação detalhada:
# - A função recebe um parâmetro `port`, que representa a porta na qual o servidor será iniciado.
# - Dentro da função:
#   1. Importa os módulos `os` e `sys`:
#      - `os` permite a execução de comandos no terminal/shell.
#      - `sys.executable` retorna o caminho do interpretador Python em uso (ex: C:\Python39\python.exe).
#   2. Usa `os.system()` para executar um comando no terminal que inicia o script `server.py`
#      passando a porta como argumento. Por exemplo:
#         python server.py 5000
#      Isso faz com que o servidor comece a escutar na porta especificada.
#
# Observação:
# - Essa função é usada dentro de um processo separado (por exemplo, usando `multiprocessing.Process`)
#   para iniciar múltiplos servidores simultaneamente em diferentes portas.
def start_server_process(port):
    import os
    import sys
    os.system(f"{sys.executable} server.py {port}")

# Função: client_send_receive
# ------------------------------------------------------------
# Esta função representa o comportamento de um cliente que:
# 1. Se conecta a um servidor via socket TCP;
# 2. Envia uma parte da matriz A e a matriz B serializadas (com pickle);
# 3. Aguarda a resposta do servidor (o resultado da multiplicação parcial);
# 4. Recebe e desserializa os dados;
# 5. Retorna o resultado recebido (C_chunk).
#
# Parâmetros:
# - host: endereço do servidor (ex: 'localhost')
# - port: porta do servidor (ex: 5000)
# - A_chunk: parte da matriz A que será enviada ao servidor
# - B: matriz B inteira que será usada na multiplicação
#
# Etapas detalhadas:
# - Cria um socket TCP/IP.
# - Conecta ao servidor especificado.
# - Serializa (com pickle) o par (A_chunk, B).
# - Envia o tamanho dos dados serializados como um inteiro de 4 bytes (com `struct.pack`)
#   para garantir que o servidor saiba quanto deve esperar.
# - Envia os dados serializados.
# - Aguarda os primeiros 4 bytes da resposta, que indicam o tamanho da resposta serializada.
# - Lê do socket até receber todos os bytes esperados.
# - Desserializa os dados recebidos (resultado da multiplicação parcial).
# - Fecha a conexão e retorna a matriz resultante parcial (C_chunk).
#
# Em caso de erro de conexão ou interrupção na comunicação, a função trata a exceção
# e retorna `None`.

def client_send_receive(host, port, A_chunk, B):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))

        data = pickle.dumps((A_chunk, B))
        client_socket.sendall(struct.pack('>I', len(data)))
        client_socket.sendall(data)

        size_data = client_socket.recv(4)
        if not size_data:
            raise ConnectionError("Nenhum dado recebido do servidor")
        data_size = struct.unpack('>I', size_data)[0]

        received_data = b""
        while len(received_data) < data_size:
            chunk = client_socket.recv(4096)
            if not chunk:
                raise ConnectionError("Conexão interrompida durante recebimento")
            received_data += chunk

        C_chunk = pickle.loads(received_data)

        client_socket.close()
        return C_chunk
    except Exception as e:
        print(f"Erro ao se conectar a {host}:{port}: {e}")
        return None
    
# Bloco principal do programa
# ------------------------------------------------------------
# Este bloco é executado apenas quando o script é executado diretamente,
# e não quando importado como módulo.
#
# Etapas executadas:
#
# 1. Cria duas matrizes aleatórias A e B com a função `create_matrix`.
#    Também retorna o número de linhas da matriz A (ROWS_A).
#
# 2. Realiza a multiplicação serial (convencional, sem distribuição) com `np.dot`
#    e mede o tempo que essa operação leva (`start_serial` e `end_serial`).
#
# 3. Chama a função `generate_host` para:
#    - Perguntar ao usuário quantos servidores (hosts) deseja usar;
#    - Dividir a matriz A em partes iguais para distribuição;
#    - Criar uma lista com os endereços dos servidores.
#
# 4. Inicia um processo separado para cada servidor, executando o script `server.py`
#    com a porta correspondente (função `start_server_process`).
#    Adiciona um pequeno atraso entre o início de cada servidor (`time.sleep(1)`).
#
# 5. Realiza a multiplicação distribuída:
#    - Envia cada parte da matriz A (A_chunk) junto com a matriz B para o respectivo servidor;
#    - Aguarda o resultado da multiplicação parcial (C_chunk);
#    - Armazena os resultados recebidos em uma lista.
#
# 6. Finaliza todos os processos de servidor usando `p.terminate()`.
#
# 7. Se todos os resultados foram recebidos corretamente:
#    - Une os pedaços (linhas) da matriz resultante C com `np.vstack`;
#    - Imprime a matriz C final;
#    - Exibe o tempo da multiplicação serial e o tempo da multiplicação distribuída.
#
# 8. Caso ocorra algum problema (como não receber resultado dos servidores), imprime um aviso.
if __name__ == "__main__":
    A, B, ROWS_A = create_matrix()
    if A is not None and B is not None:

        start_serial = time.time()
        C_serial = np.dot(A, B)
        end_serial = time.time()

        HOSTS, PARTS_OF_MATRIX_A = generate_host(A, ROWS_A)
        if HOSTS is None or PARTS_OF_MATRIX_A is None:
            print("Erro ao gerar hosts ou partes da matriz.")
            exit(1)

        server_processes = []
        for host, port in HOSTS:
            p = Process(target=start_server_process, args=(port,))
            p.start()
            server_processes.append(p)
            time.sleep(1)  

        start_distributed = time.time()

        results = []
        for i, ((host, port), A_chunk) in enumerate(zip(HOSTS, PARTS_OF_MATRIX_A)):
            print(f"Enviando parte {i+1} para {host}:{port}")
            C_chunk = client_send_receive(host, port, A_chunk, B)
            if C_chunk is not None:
                results.append(C_chunk)
        
        end_distributed = time.time()

        for p in server_processes:
            p.terminate()

        if results:
            C = np.vstack(results)
            print("\nMatriz C (resultado da multiplicação):")
            print(C)
            print(f"Tempo serial: {end_serial - start_serial:.4f} segundos")
            print(f"\nTempo distribuído: {end_distributed - start_distributed:.4f} segundos")
        else:
            print("Nenhum resultado recebido dos servidores.")