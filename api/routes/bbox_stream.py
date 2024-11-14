from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import crud
from database.session import get_db
from fastapi.responses import RedirectResponse
from ultralytics import YOLO
import os
import subprocess
from threading import Thread
import cv2
import time

router = APIRouter()

MODEL_PATH = "/home/kkw/Inhatc/project/YULO_model/data/person.pt"
HLS_DIRECTORY = "/home/kkw/Inhatc/project/YULO_model/output/hls"
model = YOLO(MODEL_PATH)

def process_and_stream_bbox_hls(rtsp_url, output_name):
    """BBOX가 추가된 스트리밍을 HLS 형식으로 변환하여 저장"""
    output_path = os.path.join(HLS_DIRECTORY, output_name)
    hls_file = os.path.join(output_path, "index.m3u8")

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # OpenCV로 RTSP 스트림 열기
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise RuntimeError(f"카메라 스트림을 열 수 없습니다: {rtsp_url}")

    # FFmpeg 프로세스로 출력 파이프라인 생성
    command = [
        "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "bgr24",
        "-s", "1920x1080", "-r", "15", "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-f", "hls",
        "-hls_time", "2", "-hls_list_size", "5", "-hls_flags", "delete_segments+round_durations",
        "-hls_segment_filename", os.path.join(output_path, "segment_%03d.ts"),
        hls_file
   ]

    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"[오류] 프레임 읽기 실패: {rtsp_url}")
            break

        # YOLO 모델로 감지 수행
        results = model(frame)
        boxes = results[0].boxes

        # BBox가 감지된 경우 프레임에 그리기
        detected = False
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label = results[0].names[int(box.cls)]
            if label.lower() == "person":  # "person"만 감지
                # BBox 그리기 및 레이블 추가
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                detected = True

        if detected:
            try:
                # FFmpeg 프로세스에 프레임 전달
                process.stdin.write(frame.tobytes())
            except Exception as e:
                print(f"[오류] FFmpeg 프로세스에 프레임 전달 실패: {e}")
                break

    cap.release()
    process.stdin.close()
    process.wait()

    # FFmpeg 프로세스 오류 로그 출력
    stderr = process.stderr.read().decode()
    if stderr:
        print(f"FFmpeg error log: {stderr}")

@router.get("/bbox/stream/{camera_seq}")
def view_bbox_stream(camera_seq: int, db: Session = Depends(get_db)):
    """BBOX가 추가된 특정 카메라의 HLS 스트림을 반환"""
    # camera_seq에 해당하는 카메라 정보를 DB에서 가져옴
    camera_info = crud.get_camera(db, camera_seq)
    if not camera_info or not camera_info.camera_url:
        raise HTTPException(status_code=404, detail="카메라 URL이 없습니다.")

    output_name = f"bbox_camera_{camera_seq}"
    # 감지 스레드를 백그라운드에서 실행
    Thread(target=process_and_stream_bbox_hls, args=(camera_info.camera_url, output_name), daemon=True).start()

    # HLS 스트림 URL로 리디렉션
    hls_stream_url = f"/output/hls/{output_name}/index.m3u8"
    for _ in range(20):  # 최대 20초 대기
        if os.path.exists(os.path.join(HLS_DIRECTORY, output_name, "index.m3u8")):
            return RedirectResponse(url=hls_stream_url)
        time.sleep(1)

    raise HTTPException(status_code=404, detail="스트리밍 파일이 아직 생성되지 않았습니다.")
