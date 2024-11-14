from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import crud
from database.session import get_db
from fastapi.responses import FileResponse, RedirectResponse
import os

router = APIRouter()

BASE_VIDEO_PATH = "/home/kkw/Inhatc/project/YULO_model/output/result_video/"
HLS_DIRECTORY = os.path.join(BASE_VIDEO_PATH, "hls")

# 카메라 스트리밍 URL 접속 hls 파일 리다이렉팅
@router.get("/stream/rtsp/{camera_seq}")
def view_camera_stream(camera_seq: int, db: Session = Depends(get_db)):
    camera_info = crud.get_camera(db, camera_seq)
    if not camera_info or not camera_info.camera_url:
        raise HTTPException(status_code=404, detail="카메라 URL이 없음")

    hls_stream_url = f"/output/hls/camera_{camera_seq}/index.m3u8"
    return RedirectResponse(url=hls_stream_url)

# 감지된 비디오 파일 반환
@router.get("/stream/{detection_seq}")
def stream_video(detection_seq: int, db: Session = Depends(get_db)):
    detection_name = crud.get_detection_name(db, detection_seq)
    if not detection_name:
        raise HTTPException(status_code=404, detail="비디오 이름이 테이블에 없음")

    video_file_path = os.path.join(BASE_VIDEO_PATH, f"{detection_name}.mp4")
    print(f"[정보] video_file_path: {video_file_path}")  # 경로 확인 로그 추가

    if not os.path.exists(video_file_path):
        raise HTTPException(status_code=404, detail="비디오 파일이 없음")

    return FileResponse(video_file_path, media_type="video/mp4")
