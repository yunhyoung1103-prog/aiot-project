```python
import sys                               # 시스템 관련 모듈 불러오기
import face_recognition_models           # 얼굴 인식 모델 라이브러리 불러오기
sys.modules['face_recognition_models'] = face_recognition_models  # 모듈 등록

import cv2                               # OpenCV 라이브러리 불러오기
import face_recognition                  # 얼굴 인식 라이브러리 불러오기
import requests                          # HTTP 요청 라이브러리 불러오기
import time                              # 시간 측정 라이브러리 불러오기

TELEGRAM_TOKEN = "8615131870:..."         # 텔레그램 봇 토큰
CHAT_ID = "8528356776"                   # 메시지를 받을 채팅 ID
MASTER_IMAGE_PATH = "photo.jpg"          # 등록된 사용자 얼굴 사진 경로

def send_telegram_message(text):          # 텔레그램 메시지 전송 함수 정의
    """텔레그램으로 메시지를 보내는 함수"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"  # API 주소 생성
    payload = {"chat_id": CHAT_ID, "text": text}                       # 전송할 데이터 구성
    try:
        requests.post(url, json=payload)   # 텔레그램 서버로 메시지 전송
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")  # 오류 발생 시 메시지 출력

print("시스템을 초기화 중입니다... 잠시만 기다려주세요.")  # 시스템 초기화 안내

try:
    master_image = face_recognition.load_image_file(MASTER_IMAGE_PATH)  # 등록된 얼굴 사진 불러오기
    master_encoding = face_recognition.face_encodings(master_image)[0]  # 얼굴 특징값 추출
    known_face_encodings = [master_encoding]                            # 얼굴 특징값 저장

    video_capture = cv2.VideoCapture(0)  # 기본 웹캠 연결
    print("시스템이 시작되었습니다! (종료: 카메라 창에서 'q' 누르기 또는 터미널에서 Ctrl+C)")

    last_check_time = time.time()  # 마지막 얼굴 인식 시간 저장

    last_face_locations = []       # 얼굴 위치 저장 리스트
    last_face_names = []           # 얼굴 이름 저장 리스트

    while True:                    # 무한 반복 시작

        ret, frame = video_capture.read()  # 웹캠 영상 읽기
        if not ret:                        # 영상 읽기에 실패한 경우
            print("웹캠을 찾을 수 없습니다.")
            break                          # 반복문 종료

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)  # 영상 크기를 1/4로 축소
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)  # BGR → RGB 변환

        current_time = time.time()         # 현재 시간 저장

        if current_time - last_check_time > 3:  # 3초마다 얼굴 인식 수행
            last_check_time = current_time

            last_face_locations = face_recognition.face_locations(rgb_small_frame)  # 얼굴 위치 검출
            face_encodings = face_recognition.face_encodings(
                rgb_small_frame,
                last_face_locations
            )  # 얼굴 특징값 추출

            last_face_names = []           # 얼굴 이름 리스트 초기화

            for face_encoding in face_encodings:  # 검출된 얼굴마다 반복
                matches = face_recognition.compare_faces(
                    known_face_encodings,
                    face_encoding,
                    tolerance=0.5
                )  # 등록된 얼굴과 비교

                name = "Unknown"           # 기본값은 외부인

                if True in matches:        # 등록된 사용자일 경우
                    name = "Authorized"
                    print("결과: 인증되었습니다.")
                    send_telegram_message("인증되었습니다.")  # 인증 메시지 전송
                else:
                    print("결과: 외부인입니다.")
                    send_telegram_message("외부인입니다.")   # 외부인 메시지 전송

                last_face_names.append(name)  # 결과 저장

        for (top, right, bottom, left), name in zip(last_face_locations, last_face_names):

            top *= 4      # 위쪽 좌표 원래 크기로 복원
            right *= 4    # 오른쪽 좌표 복원
            bottom *= 4   # 아래쪽 좌표 복원
            left *= 4     # 왼쪽 좌표 복원

            color = (0, 255, 0)  # 기본 색상(초록색)

            if name == "Unknown":
                color = (0, 0, 255)  # 외부인일 경우 빨간색 사용

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)  # 얼굴 사각형 표시

            cv2.rectangle(frame, (left, bottom - 35), (right, bottom),
                          color, cv2.FILLED)  # 텍스트 배경 표시

            font = cv2.FONT_HERSHEY_DUPLEX  # 글꼴 설정

            display_name = "certify" if name == "Authorized" else "unknown"  # 화면에 표시할 이름 설정

            cv2.putText(frame, display_name,
                        (left + 6, bottom - 6),
                        font,
                        1.0,
                        (255, 255, 255),
                        1)  # 이름 출력

        cv2.imshow('CCTV Camera', frame)  # 실시간 영상 출력

        if cv2.waitKey(1) & 0xFF == ord('q'):  # q 키 입력 시
            break                              # 반복문 종료

except KeyboardInterrupt:
    print("\n시스템을 종료합니다.")  # Ctrl+C 입력 시 종료

except IndexError:
    print(f"\n[오류] {MASTER_IMAGE_PATH} 파일에서 얼굴을 찾을 수 없습니다.")  # 얼굴 사진 오류

except Exception as e:
    print(f"\n[알림] 예기치 않은 에러 발생: {e}")  # 기타 예외 처리

finally:
    if 'video_capture' in locals() and video_capture.isOpened():
        video_capture.release()  # 웹캠 자원 해제

    cv2.destroyAllWindows()      # 모든 창 닫기
```
