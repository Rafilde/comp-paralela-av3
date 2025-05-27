import socket
import pickle
import numpy as np

def start_server(host='localhost', port=5000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Servidor escutando em {host}:{port}")

    try:
        while True:
            conn, addr = server_socket.accept()
            print(f"Conectado a {addr}")

            data = conn.recv(4096)
            A_chunk, B = pickle.loads(data)

            C_chunk = np.dot(A_chunk, B)

            conn.sendall(pickle.dumps(C_chunk))
            conn.close()

    except Exception as e:
        print(f"Erro no servidor: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    start_server('localhost', port)