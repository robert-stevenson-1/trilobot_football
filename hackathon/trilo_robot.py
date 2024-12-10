import cv2
import socket
import struct
import pickle
import base64
import multiprocessing
import picamera2

# TRILO_IP = socket.gethostbyname(socket.gethostname())
TRILO_IP = '10.82.0.108'
CAM_PORT     = 9999
CONTROLLER_PORT = 9998

print(TRILO_IP)

def Trilo_cam():
    cam_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cam_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # enable address reuse
    cam_sock.bind((TRILO_IP, CAM_PORT))
    # cam_sock.connect((TRILO_IP, PORT))

    cam_sock.listen(1)
    print(f"Camera server listening on {TRILO_IP}:{CAM_PORT}")

    while True:
        try:
            client_socket, addr = cam_sock.accept()
            print("Connection from:", addr)
            
            if client_socket:
            # LOCAL DEV
            #     cam = cv2.VideoCapture(0)
            #     cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Try 640x480 or lower
            #     cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            #     cam.set(cv2.CAP_PROP_FPS, 15)           # Use a lower frame rate, like 15 FPS

            #     print(cam.isOpened())
            #     while cam.isOpened():
            #         img, frame = cam.read()
            #         if frame is not None:
            #             f_buffer = cv2.imencode('.jpg', frame)[1]
            #             video_data = base64.b64encode(f_buffer)

            #             f_buffer = f_buffer.tobytes()
            #             msg_size = struct.pack("!L", len(f_buffer)) + f_buffer
            #             try:
            #                 # print('msg_size len: ' + str(len(msg_size)) 
            #                 #     + ' | video_data len: ' + str(len(video_data)) 
            #                 #     + ' | encoded_frame len: ' + str(len(f_buffer)))
            #                 client_socket.sendall(msg_size)
            #             except socket.error as e:
            #                 print(f"> SOCKET ERROR: {e}")
            #                 break
            #         else:
            #             print("frame empty")

            # DEPLOYMENT DEV
                picam2 = picamera2.Picamera2()
                picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (640, 480)})) # opencv works in BGR not RGB
                picam2.start()

                while True:
                    frame = picam2.capture_array()
                    if frame is not None:
                        f_buffer = cv2.imencode('.jpg', frame)[1]
                        video_data = base64.b64encode(f_buffer)

                        f_buffer = f_buffer.tobytes()
                        msg_size = struct.pack("!L", len(f_buffer)) + f_buffer
                        try:
                            print('msg_size len: ' + str(len(msg_size)) 
                                + ' | video_data len: ' + str(len(video_data)) 
                                + ' | encoded_frame len: ' + str(len(f_buffer)))
                            print(f"Server: Sending frame of size {len(f_buffer)}")
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
            if 'picam2' in locals():
                picam2.close()
                print("Camera closed.")
            if 'client_socket' in locals():
                client_socket.close()
                print("Client socket closed.")

# Take controller data recieved over a socket and control the trilobot
def control():
    controller_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    controller_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Enable address reuse
    controller_sock.bind((TRILO_IP, CONTROLLER_PORT))
    controller_sock.listen(1)
    print(f"Controller server listening on {TRILO_IP}:{CONTROLLER_PORT}")

    try:
        while True:
            client_socket, addr = controller_sock.accept()
            print(f"Controller client connected from {addr}")
            try:
                while True:
                    # Receive controller data
                    data = client_socket.recv(8)  # 2 floats (4 bytes each)
                    if not data:
                        print("Controller client disconnected.")
                        break  # Break the inner loop to accept a new client connection

                    # Unpack and process the data
                    trilo_x, trilo_y = struct.unpack("ff", data)
                    print(f"Received Controller Data: X={trilo_x}, Y={trilo_y}")

            except Exception as e:
                print(f"Controller handler error: {e}")
            finally:
                client_socket.close()
                print("Controller client connection closed.")

    except Exception as e:
        print(f"Controller server error: {e}")
    finally:
        controller_sock.close()
        print("Controller socket closed.")



if __name__ == "__main__":
    camera_process = multiprocessing.Process(target=Trilo_cam)
    controller_process = multiprocessing.Process(target=control)
    camera_process.daemon = True
    controller_process.start()
    camera_process.start()
    controller_process.join()