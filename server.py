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

HOST = 'localhost'
PORT = 5000  

def multiply_matrices(sub_A, B):
    return np.dot(sub_A, B)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Servidor rodando na porta {PORT}...")

    conn, addr = s.accept()
    with conn:
        print(f"Conectado por {addr}")
        data = b""
        while True:
            packages = conn.recv(4096)
            if not packages:
                break
            data += packages
        
        sub_A, B = pickle.loads(data)
        result = multiply_matrices(sub_A, B)
        conn.sendall(pickle.dumps(result))