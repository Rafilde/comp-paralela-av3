import socket 
import pickle
import numpy as np

'''
socket: Biblioteca padrão do Python usada para comunicação entre computadores via rede.
         Permite criar conexões cliente-servidor usando o protocolo TCP/IP.

pickle: Biblioteca para serialização de objetos Python. Transforma objetos (como listas ou matrizes)
         em bytes para envio via rede ou armazenamento, e depois reconstrói esses objetos.

numpy: Biblioteca poderosa para computação numérica em Python.
        Usada para criar e manipular matrizes e arrays, e realizar operações matemáticas como multiplicação de matrizes.
'''

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

        print("\n Matriz A ({}x{}):".format(ROW_A, COLUMNS_A))
        print(A)

        print("\n Matriz B ({}x{}):".format(COLUMNS_A, COLUMNS_B))
        print(B)

        return A, B, ROW_A

    except ValueError as e:
        print(f"Erro: {e}")
        return None, None, None

def generate_host(A, TOTAL_ROWS):
    try:
        NUMBER_OF_HOST = int(input(f"\nQuantos servidores (hosts) você quer usar? (1 até {TOTAL_ROWS}): "))
        if NUMBER_OF_HOST < 1  or NUMBER_OF_HOST > TOTAL_ROWS:
            raise ValueError("Número de hosts deve estar entre 1 e o total de linhas da matriz A.")
    except ValueError as e:
        print(f"Erro: {e}")
        return None, None
    
    HOSTS = [("localhost", 5000 + i) for i in range(NUMBER_OF_HOST)]

    PARTS_OF_MATRIX = np.array_split(A,NUMBER_OF_HOST, axis=0)

    return HOSTS, PARTS_OF_MATRIX

def distributed_multiplication(HOSTS, PARTS_OF_MATRIX_A, MATRIX_B):
    results = []

    for i, (host, port) in enumerate(HOSTS):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            SUB_A = PARTS_OF_MATRIX_A[i]
            pacote = pickle.dumps((SUB_A, MATRIX_B))
            s.sendall(pacote)
            dados = b""
            while True:
                pacote = s.recv(4096)
                if not pacote:
                    break
                dados += pacote
            resultado_parcial = pickle.loads(dados)
            results.append(resultado_parcial)

    C = np.vstack(results)

    return C

if __name__  == "__main__":
    A, B, ROWS_A= create_matrix()
    if A is not None and B is not None:
        HOSTS, PARTS_OF_MATRIX_A = generate_host(A, ROWS_A)
        distributed_multiplication(HOSTS, PARTS_OF_MATRIX_A, B)


