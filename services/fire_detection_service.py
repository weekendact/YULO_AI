from services.base_detection_service import BaseDetectionService
import cv2

class FireDetectionService(BaseDetectionService):
    def __init__(self, camera_info):
        super().__init__(camera_info, "fire")
        self.fire_count_threshold = 1

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"[오류] 비디오 파일을 열 수 없습니다: {video_path}")
            return

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = self.model(frame)

            boxes = results[0].boxes
            names = results[0].names

            fire_count = 0
            for box in boxes:
                label = names[int(box.cls)]
                if label == "fire":
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0]

                    if conf > 0.5:
                        fire_count += 1
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f'{label} {conf:.2f}', (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if fire_count > 0:
                self.save_detection_clip(frame, "fire", fire_count)

        cap.release()
        print(f"[정보] {video_path} 처리가 완료되었습니다.")
