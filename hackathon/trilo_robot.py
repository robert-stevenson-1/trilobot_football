import cv2
import socket
import struct
import pickle
import base64

TRILO_IP = socket.gethostbyname(socket.gethostname())
# TRILO_IP = '127.0.1.1'
print(TRILO_IP)
PORT     = 9999

cam_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cam_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # enable address reuse
cam_sock.bind((TRILO_IP, PORT))
# cam_sock.connect((TRILO_IP, PORT))

cam_sock.listen(5)

while True:
    try:
        client_socket, addr = cam_sock.accept()
        print("Connection from:", addr)
        
        if client_socket:
            cam = cv2.VideoCapture(0)
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 480) #640
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 320) #480
            
            while cam.isOpened():
                img, frame = cam.read()
                if frame is not None:
                    f_buffer = cv2.imencode('.jpg', frame)[1]
                    video_data = base64.b64encode(f_buffer)

                    f_buffer = f_buffer.tobytes()
                    msg_size = struct.pack("L", len(f_buffer)) + f_buffer
                    try:
                        print('msg_size len: ' + str(len(msg_size)) 
                            + ' | video_data len: ' + str(len(video_data)) 
                            + ' | encoded_frame len: ' + str(len(f_buffer)))
                        client_socket.sendall(msg_size)
                    except socket.error:
                        print("> SOCKET ERROR")
                        break

        else:
            break
    except Exception as e:
        print(f"Server error: {e}")
        break
    finally:
        # Release the camera and close client socket
        if 'cam' in locals() and cam.isOpened():
            cam.release()
            print("Camera released.")
        if 'client_socket' in locals():
            client_socket.close()
            print("Client socket closed.")