from inputs import get_gamepad, SYNCHRONIZATION_EVENTS
from numpy import interp
import numpy as np
import cv2
import socket
import struct
import pickle
import multiprocessing

JOY_DEADZONE = 20
JOY_MAX =  32768
JOY_MIN = -32768

TRILO_MAX =  1
TRILO_MIN = -1


def Camerafeed():
    HOST_IP = socket.gethostbyname(socket.gethostname())
    PORT    = 9999

    cam_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cam_sock.connect((HOST_IP, PORT))

    data = b""
    payload_size = struct.calcsize("Q")

    try:
        while True:
            while len(data) < payload_size:
                data += cam_sock.recv(4*1024)

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            unpacked_msg_size = struct.unpack("L", packed_msg_size)[0]
            
            while len(data) < unpacked_msg_size:
                data += cam_sock.recv(4*1024)
            
            frame_data = data[:unpacked_msg_size]
            data = data[unpacked_msg_size:]
            
            # extract the video frame
            frame_data = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)

            cv2.imshow("frame", frame)
            cv2.waitKey(1)

    except socket.error as e:  # try triggered when connection timed out
        print("ERROR: Connection to Server lost...")
        print('-----> Exception: ' + str(e)) 
    finally:
        cam_sock.close()
        cv2.destroyAllWindows()



def Trilo_joy_map(joy_x, joy_y):
    trilo_x, trilo_y = 0,0

    trilo_x = interp(joy_x, [JOY_MIN, JOY_MAX], [TRILO_MIN, TRILO_MAX])
    trilo_y = interp(joy_y, [JOY_MIN, JOY_MAX], [TRILO_MIN, TRILO_MAX])

    return trilo_x, trilo_y

def Deadzone_Check(deadzone_threshold, value):
    return True if (value < deadzone_threshold and value > -deadzone_threshold) else False

def Controller_Input():
    left_x  = 0
    left_y  = 0
    right_x = 0
    right_y = 0
    btn_A = False
    btn_B = False
    btn_X = False
    btn_Y = False


    # data to send to trilobot
    trilo_x, trilo_y = 0,0

    while True:
        events = get_gamepad()
        for event in events:
            if not str(event.code) == "SYN_REPORT":
                if str(event.code) == "ABS_X"     : left_x  = event.state
                if str(event.code) == "ABS_Y"     : left_y  = event.state
                if str(event.code) == "ABS_RX"    : right_x = event.state
                if str(event.code) == "ABS_RY"   : right_y = event.state
                if str(event.code) == "BTN_SOUTH" : btn_A   = event.state
                if str(event.code) == "BTN_EAST"  : btn_B   = event.state
                if str(event.code) == "BTN_NORTH" : btn_X   = event.state
                if str(event.code) == "BTN_WEST"  : btn_Y   = event.state

                print(f"LEFT_JOY: ({left_x}, {left_y}) | RIGHT_JOY: ({right_x}, {right_y}) | A:{btn_A} B:{btn_B} X:{btn_X} Y:{btn_Y}") 

        trilo_x, trilo_y = Trilo_joy_map(joy_x=left_x, joy_y=left_y)
        print(f"TRILO XY: ({trilo_x}, {trilo_y})")
        

camera_process = multiprocessing.Process(target=Camerafeed)
controller_process = multiprocessing.Process(target=Controller_Input)

if __name__ == "__main__":
    camera_process.daemon = True
    camera_process.start()
    controller_process.start()
    controller_process.join()
