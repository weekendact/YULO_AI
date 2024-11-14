from services.base_detection_service import BaseDetectionService
import cv2
from database.session import SessionLocal
from database import crud
from datetime import datetime
import os

class PersonDetectionService(BaseDetectionService):
    def __init__(self, camera_info):
        super().__init__(camera_info, "person")
        self.person_count_threshold = 4
        self.saved = False 

    def save_detection_data_to_db(self, video_path, person_count):
        detection_name = os.path.basename(video_path)
        detection_name = os.path.splitext(detection_name)[0]

        with SessionLocal() as db:
            detection_data = {
                "building_seq": self.camera_info.building_seq,
                "camera_seq": self.camera_info.camera_seq,
                "model_seq": self.camera_info.model_seq,
                "reg_date": datetime.now(),
                "update_date": datetime.now(),
                "detection_data": person_count,
                "detection_name": detection_name
            }
            crud.create_detection(db, detection_data)
            print(f"[정보] 데이터베이스에 감지 데이터 저장 완료: {detection_name}, person Count: {person_count}")
            
            self.saved = True

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"[오류] 비디오 파일을 열 수 없습니다: {video_path}")
            return

        frame_count = 0
        person_detected = False
        output_video_path = None
        output_writer = None
        person_count = 0
        start_time = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            results = self.model(frame)  # 모델을 통해 프레임 처리
            boxes = results[0].boxes
            names = results[0].names

            person_count = 0
            
            for box in boxes:
                label = names[int(box.cls)]
                if label == "person":
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # 좌상단 x1, y1, 우하단 x2, y2
                    conf = box.conf[0]  # 신뢰도 추출

                    if conf > 0.5:  # 신뢰도가 0.5 이상일 때만
                        person_count += 1
                        print(f"[디버그] person detected: {x1}, {y1}, {x2}, {y2}, {conf}")

                        # 경계 상자 그리기
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # 경계 상자 그리기
                        cv2.putText(frame, f'{label} {conf:.2f}', (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)  # 텍스트 추가

                        # 화면에서 확인하기 위해 디버그로 프레임 저장 (임시로 저장한 후 확인)

                        person_detected = True


            if person_detected and person_count >= self.person_count_threshold and output_writer is None:
                output_video_path = self.save_detection_clip(frame, "person", person_count)
                output_writer = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (frame.shape[1], frame.shape[0]))
                start_time = frame_count
                print(f"[정보] 새로운 클립 시작: {output_video_path}")

            if start_time is not None:
                if output_writer is not None and frame_count - start_time < 15 * 20:  # 15초 동안만 저장
                    output_writer.write(frame)

                if frame_count - start_time >= 15 * 20:
                    break

        cap.release()

        if output_writer is not None and person_detected and person_count >= self.person_count_threshold:
            output_writer.release()
            self.convert_mp4(video_path, output_video_path)
            print(f"[정보] {video_path} 비디오 저장 완료: {output_video_path}")
            self.save_detection_data_to_db(output_video_path, person_count)

        if not person_detected or person_count < self.person_count_threshold:
            print(f"[정보] {video_path}에는 {self.person_count_threshold}명 이상의 person이 감지되지 않아 저장하지 않았습니다.")

        print(f"[정보] {video_path} 처리가 완료되었습니다.")


# class PersonDetectionService(BaseDetectionService):
#     def __init__(self, camera_info):
#         super().__init__(camera_info, "person")
#         self.person_count_threshold = 1
#         self.saved = False 

#     def save_detection_data_to_db(self, video_path, person_count):
#         detection_name = os.path.basename(video_path)
#         detection_name = os.path.splitext(detection_name)[0]

#         with SessionLocal() as db:
#             detection_data = {
#                 "building_seq": self.camera_info.building_seq,
#                 "camera_seq": self.camera_info.camera_seq,
#                 "model_seq": self.camera_info.model_seq,
#                 "reg_date": datetime.now(),
#                 "update_date": datetime.now(),
#                 "detection_data": person_count,
#                 "detection_name": detection_name
#             }
#             crud.create_detection(db, detection_data)
#             print(f"[정보] 데이터베이스에 감지 데이터 저장 완료: {detection_name}, person Count: {person_count}")

#     def convert_video(self, input_video_path, output_video_path):
#         """
#         FFmpeg 명령어를 사용하여 비디오를 변환하는 함수
#         """
#         command = [
#             'ffmpeg',
#             '-i', input_video_path,       # 입력 비디오
#             '-c:v', 'libx264',            # 비디오 코덱
#             '-preset', 'fast',            # 빠른 인코딩
#             '-c:a', 'aac',                # 오디오 코덱
#             '-strict', 'experimental',    # 실험적 기능 사용
#             output_video_path             # 출력 비디오
#         ]

#         try:
#             subprocess.run(command, check=True)
#             print(f"[정보] 비디오 변환 완료: {output_video_path}")
#         except subprocess.CalledProcessError as e:
#             print(f"[오류] 비디오 변환 중 오류 발생: {e}")

#     def process_video(self, video_path):
#         cap = cv2.VideoCapture(video_path)
#         if not cap.isOpened():
#             print(f"[오류] 비디오 파일을 열 수 없습니다: {video_path}")
#             return

#         frame_count = 0
#         person_detected = False
#         output_video_path = None
#         output_writer = None
#         person_count = 0
#         start_time = None

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             frame_count += 1
#             results = self.model(frame)  # 모델을 통해 프레임 처리
#             boxes = results[0].boxes
#             names = results[0].names

#             person_count = 0
            
#             for box in boxes:
#                 label = names[int(box.cls)]
#                 if label == "person":
#                     x1, y1, x2, y2 = map(int, box.xyxy[0])  # 좌상단 x1, y1, 우하단 x2, y2
#                     conf = box.conf[0]  # 신뢰도 추출

#                     if conf > 0.5:  # 신뢰도가 0.5 이상일 때만
#                         person_count += 1
#                         print(f"[디버그] person detected: {x1}, {y1}, {x2}, {y2}, {conf}")

#                         # 경계 상자 그리기
#                         cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # 경계 상자 그리기
#                         cv2.putText(frame, f'{label} {conf:.2f}', (x1, y1 - 10),
#                                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)  # 텍스트 추가

#                         person_detected = True

#             if person_detected and person_count >= self.person_count_threshold and output_writer is None:
#                 # 비디오 파일 경로 설정
#                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 output_video_path = os.path.join(self.output_dir, f"{timestamp}_{str(self.camera_info.camera_seq)}_person_detection.mp4")
#                 output_writer = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), 15.0, (frame.shape[1], frame.shape[0]))
#                 # output_writer = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), 30.0, (frame.shape[1], frame.shape[0]))

#                 start_time = frame_count
#                 print(f"[정보] 새로운 클립 시작: {output_video_path}")

#             if start_time is not None:
#                 if output_writer is not None and frame_count - start_time < 15 * 20:  # 15초 동안만 저장
#                     output_writer.write(frame)

#                 if frame_count - start_time >= 15 * 20:
#                     break

#         cap.release()

#         if output_writer is not None and person_detected and person_count >= self.person_count_threshold:
#             output_writer.release()
#             print(f"[정보] {video_path} 비디오 저장 완료: {output_video_path}")
#             self.save_detection_data_to_db(output_video_path, person_count)

#             # 비디오 변환 명령어 실행
#             converted_video_path = os.path.splitext(output_video_path)[0] + "_converted.mp4"
#             self.convert_video(output_video_path, converted_video_path)

#         if not person_detected or person_count < self.person_count_threshold:
#             print(f"[정보] {video_path}에는 {self.person_count_threshold}명 이상의 person이 감지되지 않아 저장하지 않았습니다.")

#         print(f"[정보] {video_path} 처리가 완료되었습니다.")