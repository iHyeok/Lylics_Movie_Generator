# Lylics_Movie_Generator

결혼식 영상을 위한 노래방 스타일 자막 영상 자동 생성기

## 프로젝트 개요

MP3/WAV 오디오 파일과 가사 텍스트를 입력하면, Whisper AI를 활용해 자동으로 타이밍을 추출하고 배경 사진과 함께 노래방 스타일의 영상을 생성합니다.

## 주요 기능

- **자동 타이밍 추출**: Whisper를 통해 word-level 타임스탬프 자동 생성
- **구간별 배경 전환**: 가사 구간마다 다른 배경 사진 표시
- **가사 정제**: (Verse), (Chorus) 등 라벨 자동 제거
- **유연한 이미지 처리**: 이미지 부족 시 자동 반복 사용

## 입력 요구사항

### 1. 오디오 파일
- 형식: WAV (권장) 또는 MP3
- 위치: `audio.wav` 또는 `audio.mp3`

### 2. 가사 파일 (`lyrics.txt`)
- 형식: 일반 텍스트
- 구조:
  - 한 줄 = 한 화면에 표시할 텍스트
  - 더블 엔터 (빈 줄) = 배경 이미지 전환 구간
  - (Verse), (Chorus) 등 라벨은 자동 제거됨

**예시:**
```
(Verse 1)
수줍게 마주 보는 그대 눈 속에
우리가 함께한 시간이 빛나죠

(Chorus)
오늘, 우리, 영원을 약속해요
세상 가장 빛나는 멜로디로
```

### 3. 배경 이미지
- 위치: `images/` 폴더
- 형식: JPG, PNG
- 명명: 숫자 순서 (예: `01.jpg`, `02.jpg`, ...)
- 개수: 구간 수만큼 권장 (부족 시 자동 반복)

## 디렉토리 구조
```
wedding-karaoke/
├── README.md
├── requirements.txt
├── karaoke_maker.py      # 메인 스크립트
├── audio.wav             # 입력: 오디오 파일
├── lyrics                # 입력: 가사 파일
│   ├── lyrics1.txt       
├── images/               # 입력: 배경 이미지 (보안상 ignore 처리)
│   ├── 01.jpg
│   ├── 02.jpg
│   └── ...
├── sample_images/               # 입력: 배경 이미지 (클로드 코드 테스트 용 샘플)
│   ├── 01.jpg
│   ├── 02.jpg
│   └── ...
└── output/               # 출력: 생성된 영상
    └── wedding_karaoke.mp4
```

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 파일 준비
- `audio.wav`: 노래 파일
- `lyrics.txt`: 가사 파일
- `images/`: 배경 사진들

### 3. 실행
```bash
python karaoke_maker.py
```

### 4. 결과 확인
`output/wedding_karaoke.mp4` 파일 생성됨

## 출력 사양

- 해상도: 1920x1080 (Full HD)
- 코덱: H.264
- 프레임레이트: 30fps
- 자막: 중앙 정렬, 화면 하단

## 기술 스택

- **Whisper**: 음성 인식 및 타이밍 추출
- **MoviePy**: 영상 생성 및 편집
- **Pillow**: 이미지 처리
- **Python 3.8+**

## 처리 흐름

1. Whisper로 오디오 분석 → word-level 타임스탬프 추출
2. 가사 파싱 → 라벨 제거, 구간 분리
3. Whisper 결과와 가사 매칭
4. 각 구간별로 이미지 + 자막 조합
5. 최종 영상 렌더링

## 개발 환경

- Python 3.8 이상
- 충분한 메모리 (Whisper 모델 로딩 시 필요)
- GPU 권장 (CPU도 가능하나 느림)

## 라이선스

MIT License

## 개발자

KYXI - Wedding Video Automation Project