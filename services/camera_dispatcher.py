import threading
import os
import subprocess
import time
from datetime import datetime
from database.session import SessionLocal
from database import crud
# from services.smoke_detection_service import SmokeDetectionService  
# from services.fire_detection_service import FireDetectionService
from services.person_detection_service import PersonDetectionService
from threading import Lock

BASE_VIDEO_PATH = "/home/kkw/Inhatc/project/YULO_model/output"
SEGMENT_DURATION = 1 * 15  # 클립 길이를 15초로 설정
WAIT_DURATION = 30     # 각 클립 녹화 후 30초 대기

class CameraDispatcher:
    def __init__(self):
        self.camera_threads = []
        self.file_delete_lock = Lock()
        self.clear_directories()

    # first_cut_video, hls 디렉토리에 있는 모든 파일 삭제 
    # hls 이전 파일이 있으면 전에 시간으로 보임
    # first_cut_video 이전 파일이 있으면 detect가 또 돌아감
    def clear_directories(self):
        first_cut_path = os.path.join(BASE_VIDEO_PATH, "first_cut_video")
        hls_path = os.path.join(BASE_VIDEO_PATH, "hls")

        for path in [first_cut_path, hls_path]:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                print(f"[정보] {path} 디렉토리의 모든 파일이 삭제되었습니다.")
            else:
                os.makedirs(path)
                print(f"[정보] {path} 디렉토리가 생성되었습니다.")

    # 모든 카메라 정보 갖고오기 RTSP URL
    def load_camera_info(self):
        with SessionLocal() as db:
            return crud.get_all_cameras_with_urls(db)

    # 모든 카메라 HLS 스트리밍, 감지용 5분 (지금은 15초) 녹화 시작
    def start_all_streams_and_recordings(self):
        cameras = self.load_camera_info()
        # HLS 랑 감지용 비디오 녹화 합치고 싶은데 왜 에러나..
        for camera in cameras:
            # HLS 스트리밍 시작
            stream_thread = threading.Thread(target=self.start_hls_stream,
                                             args=(camera.camera_url, 
                                                   camera.camera_seq))
            stream_thread.daemon = True
            stream_thread.start()
            self.camera_threads.append(stream_thread)
            
            # 감지용 비디오 녹화 시작
            record_thread = threading.Thread(target=self.record_stream, 
                                             args=(camera,))
            record_thread.daemon = True
            record_thread.start()
            self.camera_threads.append(record_thread)

    # FFmpeg 를 이용해 HLS 스트림 생성
    def start_hls_stream(self, camera_url, camera_seq):
        output_dir = os.path.join(BASE_VIDEO_PATH, f"hls/camera_{camera_seq}")
        hls_file = os.path.join(output_dir, "index.m3u8")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        command = [
            "ffmpeg", "-rtsp_transport", "tcp", "-i", camera_url,
            "-c:v", "libx264", "-preset", "veryfast",
            "-f", "hls",
            "-hls_time", "10",
            "-hls_list_size", "5",
            "-hls_flags", "delete_segments+round_durations",
            "-hls_segment_filename", os.path.join(output_dir, "segment_%03d.ts"),
            hls_file
        ]

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(f"[정보] HLS 인덱스 파일 생성 완료: {hls_file}")
            else:
                print(f"[오류] HLS 파일 생성 실패. 오류 로그: {stderr.decode()}")
                print(f"[stdout] : {stdout.decode()}")

        except Exception as e:
            print(f"[오류] 스트림 기록 중 예외 발생했습니다.: {str(e)}")


    # FFmpeg를 이용해 카메라 스트림을 15초 동안 저장한 후, 30초 대기
    def record_stream(self, camera_info):
        output_dir = os.path.join(BASE_VIDEO_PATH, f"first_cut_video/camera_{camera_info.camera_seq}")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        while True:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = os.path.join(output_dir, f"{timestamp}_camera_{camera_info.camera_seq}.mp4")

            command = [
                "ffmpeg", "-fflags", "+genpts", "-flags", "+low_delay", "-use_wallclock_as_timestamps", "1",
                "-rtsp_flags", "prefer_tcp", "-rtsp_transport", "tcp", "-i", camera_info.camera_url,
                "-t", str(SEGMENT_DURATION),
                "-c:v", "libx264", "-preset", "ultrafast", output_filename
           ]

            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    print(f"[정보] 비디오 저장 완료: {output_filename}")
                    self.run_detection(output_filename, camera_info.model_seq, camera_info)
                else:
                    print(f"[오류] 비디오 저장 실패. 오류 로그: {stderr.decode()}")

            except Exception as e:
                print(f"[오류] 스트림 기록 중 예외 발생: {str(e)}")

            print(f"[정보] {WAIT_DURATION}초 대기 시작...")
            time.sleep(WAIT_DURATION)
            print(f"[정보] 대기 종료, 다음 비디오 클립 녹화 시작...")

    def run_detection(self, video_path, model_seq, camera_info):
        """저장된 비디오 파일에 대해 모델 감지 실행"""
        print(f"[카메라 인포] : {camera_info}")
        with SessionLocal() as db:
            model_info = crud.get_model_info(db, model_seq)
            model_name = model_info.model_name if model_info else None

        if model_name == "smoke":
            detection_service = SmokeDetectionService(camera_info)
        elif model_name == "fire":
            detection_service = FireDetectionService(camera_info)
        elif model_name == "person":
            detection_service = PersonDetectionService(camera_info)
        else:
            print(f"[경고] 알 수 없는 모델: {model_name}")
            return

        if detection_service:
            print(f"[정보] 감지 서비스 활성화: {model_name} 모델로 {video_path} 처리 중")
            detection_service.process_video(video_path)
                
            with self.file_delete_lock:
                try:
                    os.remove(video_path)
                    print(f"[정보] 감지 완료 후 파일 삭제 : {video_path}")
                except Exception as e:
                    print(f"[오류] 파일 삭제 실패 : {str(e)}")


if __name__ == "__main__":
    dispatcher = CameraDispatcher()
    dispatcher.start_all_streams_and_recordings()
