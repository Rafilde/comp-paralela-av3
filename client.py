import socket
import pickle
import numpy as np
from multiprocessing import Process
import time

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

def start_server_process(port):
    import os
    import sys
    os.system(f"{sys.executable} server.py {port}")

def client_send_receive(host, port, A_chunk, B):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))

        data = pickle.dumps((A_chunk, B))
        client_socket.sendall(data)

        result = client_socket.recv(4096)
        C_chunk = pickle.loads(result)

        client_socket.close()
        return C_chunk
    except Exception as e:
        print(f"Erro ao se conectar a {host}:{port}: {e}")
        return None

if __name__ == "__main__":
    A, B, ROWS_A = create_matrix()
    if A is not None and B is not None:
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

        results = []
        for i, ((host, port), A_chunk) in enumerate(zip(HOSTS, PARTS_OF_MATRIX_A)):
            print(f"Enviando parte {i+1} para {host}:{port}")
            C_chunk = client_send_receive(host, port, A_chunk, B)
            if C_chunk is not None:
                results.append(C_chunk)

        for p in server_processes:
            p.terminate()

        if results:
            C = np.vstack(results)
            print("\nMatriz C (resultado da multiplicação):")
            print(C)
        else:
            print("Nenhum resultado recebido dos servidores.")