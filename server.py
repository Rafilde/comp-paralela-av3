import socket
import pickle
import numpy as np
import struct

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

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    start_server('localhost', port)