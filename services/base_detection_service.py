import cv2
from ultralytics import YOLO
import threading
from datetime import datetime
import os
import logging
import subprocess

logging.getLogger("ultralytics").setLevel(logging.WARNING) # YOLO 그만 얘기해

class BaseDetectionService:
    def __init__(self, camera_info, model_name):
        self.camera_info = camera_info
        self.model = self.load_model(model_name) 
        self.output_dir = f"/home/kkw/Inhatc/project/YULO_model/output/result_video"
        self.detection_count = 0
        self.lock = threading.Lock()

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
    # 모델 로딩 메서드
    def load_model(self, model_name):
        model_path = f'/home/kkw/Inhatc/project/YULO_model/data/{model_name}.pt'
        return YOLO(model_path)

    # 감지 클립 저장 메서드
    def save_detection_clip(self, frame, model_name, detected_count):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"{timestamp}_{model_name}_detection.mp4")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 30.0
        frame_width = frame.shape[1]
        frame_height = frame.shape[0]
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

        label = f"Model: {model_name}, Detected: {detected_count}"
        cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        out.write(frame)
        out.release()
        print(f"[정보] 감지된 비디오 저장 완료: {output_path}")
        return output_path

    # 각 모델 서비스에서 구현하는 진짜 detect 
    def process_video(self, video_path):
        raise NotImplementedError("`process_video`는 각 모델 클래스에서 구현해야 합니다.")
    import subprocess


    # 왜 안되는지 모르겠는 mp4 를 mp4로 바꾸는 로직 - 이것 때문에 bbox 안보이는 것 같음
    def convert_mp4(self, input_path, output_path):
        """MP4 파일을 변환하는 메서드"""
        command = [
            'ffmpeg',
            '-y',
            '-i', input_path,               # 입력 파일
            '-c:v', 'libx264',              # 비디오 코덱 설정 (H.264)
            '-preset', 'fast',              # 인코딩 프리셋 (속도 선택)
            '-c:a', 'aac',                  # 오디오 코덱 설정 (AAC)
            '-strict', 'experimental',      # 실험적인 AAC 코덱 지원
            output_path                      # 출력 파일
       ]
        
        try:
            subprocess.run(command, check=True)
            print(f"[정보] 비디오 변환 완료: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"[오류] 변환 실패: {e}")


