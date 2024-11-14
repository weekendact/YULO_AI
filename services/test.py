import subprocess

# 변환할 비디오 파일 경로
input_video = r'output/result_video/20241113_221303_47_person_detection.mp4'
output_video = r'output/b.mp4'

# ffmpeg 명령어를 리스트로 작성
command = [
    'ffmpeg',
    '-i', input_video,     # 입력 파일 경로
    '-c:v', 'libx264',      # 비디오 코덱
    '-preset', 'fast',      # 인코딩 속도
    '-c:a', 'aac',          # 오디오 코덱
    '-strict', 'experimental',  # 실험적인 기능 허용
    '-r', '30',             # 프레임 속도 설정 (예: 30fps)
    '-vsync', '2',          # 프레임 동기화 설정
    output_video            # 출력 파일 경로
]

# subprocess로 명령어 실행
try:
    subprocess.run(command, check=True)
    print(f"비디오 변환 완료: {output_video}")
except subprocess.CalledProcessError as e:
    print(f"비디오 변환 중 오류 발생: {e}")
