import cv2
import threading
import time
import subprocess

class CameraConnectionManager:
    def __init__(self, camera_url):
        self.camera_url = camera_url
        self.cap = None
        self.lock = threading.Lock()
        self.connected = False

    def connect(self):
        attempt = 0
        max_attempts = 5
        while attempt < max_attempts:
            self.cap = cv2.VideoCapture(self.camera_url)
            time.sleep(1)
            if self.cap.isOpened():
                self.connected = True
                print(f"카메라 연결 성공: {self.camera_url}")
                return
            else:
                print(f"카메라 연결 실패, 재시도 {attempt + 1}/{max_attempts}: {self.camera_url}")
                self.cap.release()
                time.sleep(5)
            attempt += 1
        self.connected = False
        print(f"카메라 연결 실패: {self.camera_url}")

    def reconnect(self):
        print(f"카메라 재연결 시도 중: {self.camera_url}")
        self.connect()

    def get_frame(self):
        with self.lock:
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    return frame
                else:
                    print(f"프레임 읽기 실패: {self.camera_url}")
                    self.connected = False
                    self.reconnect()
            return None

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.connected = False
            print(f"카메라 연결 해제: {self.camera_url}")
