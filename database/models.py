from sqlalchemy import Column, BigInteger, String, DateTime, Integer
from database.session import Base
from datetime import datetime

class Camera(Base):
    __tablename__ = "camera"
    camera_seq = Column(BigInteger, primary_key=True, index=True)
    building_seq = Column(BigInteger)
    model_seq = Column(BigInteger)
    camera_url = Column(String(255))
    reg_date = Column(DateTime, default=datetime.now)
    update_date = Column(DateTime, default=datetime.now)
    camera_name = Column(String(255))

class Detection(Base):
    __tablename__ = "detection"
    detection_seq = Column(BigInteger, primary_key=True, index=True)
    building_seq = Column(BigInteger)
    camera_seq = Column(BigInteger)
    model_seq = Column(BigInteger)
    reg_date = Column(DateTime, default=datetime.now)
    update_date = Column(DateTime, default=datetime.now)
    detection_data = Column(Integer)
    detection_name = Column(String(255))

class Model(Base):
    __tablename__ = "model"
    model_seq = Column(BigInteger, primary_key=True, index=True)
    reg_date = Column(DateTime, default=datetime.now)
    update_date = Column(DateTime, default=datetime.now)
    model_name = Column(String(255))
