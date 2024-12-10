import socket
import struct
import numpy as np
import cv2

# Server connection details
HOST_IP = '10.82.0.108'  # Update with the correct server IP
PORT = 9999

# Create the client socket
cam_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cam_sock.connect((HOST_IP, PORT))

data = b""
payload_size = struct.calcsize("!L")  # Size of the packed header (message size)

try:
    while True:
        # Ensure the header is received
        while len(data) < payload_size:
            packet = cam_sock.recv(4 * 1024)
            if not packet:
                print("Connection closed by server.")
                break
            data += packet
            print("getting data header")

        # Extract the message size
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("!L", packed_msg_size)[0]
        print(f"Client: Expecting frame of size {msg_size}")

        # Receive the actual frame data
        while len(data) < msg_size:
            packet = cam_sock.recv(4 * 1024)
            if not packet:
                print("Connection closed by server during frame reception.")
                break
            data += packet
            # print("getting data of actual frame")

        # Extract the frame data
        frame_data = data[:msg_size]
        data = data[msg_size:]
        print("extracting frame")

        # Decode the frame
        frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            print("Failed to decode frame.")
            continue

        # Display the frame
        cv2.imshow("Receiving Video", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # Exit on 'ESC'
            break

except Exception as e:
    print(f"Client error: {e}")

finally:
    cam_sock.close()
    cv2.destroyAllWindows()
    print("Client connection closed.")
