from fastapi import FastAPI
from api.routes import stream, bbox_stream
from database.session import engine
from database import models
from services.camera_dispatcher import CameraDispatcher
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

BASE_VIDEO_PATH = "/home/kkw/Inhatc/project/YULO_model/output"
HLS_DIRECTORY = os.path.join(BASE_VIDEO_PATH, "hls")

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

# FastAPI 인스턴스 생성
app = FastAPI()

# 서버 시작 시 모든 카메라 스트림 및 감지 시작
@app.on_event("startup")
def startup_event():
    dispatcher = CameraDispatcher()
    dispatcher.start_all_streams_and_recordings()  # 모든 카메라의 HLS 스트림 시작

# 라우터 등록
app.include_router(stream.router)
app.include_router(bbox_stream.router)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HLS 스트리밍 파일을 제공하는 경로
app.mount("/output/hls", StaticFiles(directory=HLS_DIRECTORY), name="hls")
