from sqlalchemy.orm import Session
from datetime import datetime
from . import models
from typing import NamedTuple

now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

class CameraInfo(NamedTuple):
    camera_url: str
    camera_seq: int
    model_seq: int
    building_seq: int

def get_detection_name(db: Session, detection_seq: int):
    detection = db.query(models.Detection).filter(models.Detection.detection_seq == detection_seq).first()
    if detection:
        return detection.detection_name
    return None

def get_model_info(db: Session, model_seq: int):
    return db.query(models.Model).filter(models.Model.model_seq == model_seq).first()

def get_all_cameras_with_urls(db: Session):
    cameras = db.query(models.Camera).filter(models.Camera.camera_url.isnot(None)).all()
    return [
        CameraInfo(
            camera_url=camera.camera_url,
            camera_seq=camera.camera_seq,
            model_seq=camera.model_seq,
            building_seq=camera.building_seq
        ) for camera in cameras
   ]

def get_camera(db: Session, camera_seq: int):
    return db.query(models.Camera).filter(models.Camera.camera_seq == camera_seq).first()

def create_detection(db: Session, detection_data: dict):
    new_detection = models.Detection(
        building_seq=detection_data.get("building_seq"),
        camera_seq=detection_data.get("camera_seq"),
        model_seq=detection_data.get("model_seq"),
        reg_date=detection_data.get("reg_date", datetime.now()),
        update_date=detection_data.get("update_date", datetime.now()),
        detection_data=detection_data.get("detection_data"),
        detection_name=detection_data.get("detection_name")
    )
    db.add(new_detection)
    db.commit()
    db.refresh(new_detection)
    return new_detection
