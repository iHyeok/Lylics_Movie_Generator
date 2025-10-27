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
├── audio
│   ├── audio1.wav             # 입력: 오디오 파일
│   └── ...
├── lyrics                # 입력: 가사 파일
│   ├── lyrics1.txt       
│   └── ...
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

### 2. 한글 폰트 설치 (Linux)
```bash
chmod +x install_fonts.sh
./install_fonts.sh
```

macOS나 Windows에서는 Nanum 폰트를 수동으로 설치해주세요:
- **macOS**: https://hangeul.naver.com/2017/nanum
- **Windows**: https://hangeul.naver.com/2017/nanum

### 3. 파일 준비
프로젝트 디렉토리에 다음 파일들을 준비합니다:

```bash
# 오디오 파일을 audio 폴더에 복사
cp /path/to/your/song.wav audio/

# 가사 파일을 lyrics 폴더에 복사
cp /path/to/your/lyrics.txt lyrics/

# 배경 이미지들을 images 폴더에 복사
cp /path/to/your/images/*.jpg images/
```

### 4. 실행
```bash
# 기본 사용법
python karaoke_maker.py audio/song.wav lyrics/lyrics.txt

# 출력 파일명 지정
python karaoke_maker.py audio/song.wav lyrics/lyrics.txt output/my_video.mp4

# 이미지 폴더 지정 (기본값: images/)
python karaoke_maker.py audio/song.wav lyrics/lyrics.txt output/my_video.mp4 sample_images
```

### 5. 결과 확인
지정한 출력 경로에 영상 파일이 생성됩니다 (기본값: `output/karaoke_video.mp4`)

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

## 주요 기능 상세

### Whisper 모델 선택

스크립트는 기본적으로 `base` 모델을 사용합니다. 필요에 따라 모델을 변경할 수 있습니다:

- **tiny**: 가장 빠름, 정확도 낮음
- **base**: 균형 잡힌 성능 (기본값)
- **small**: 더 나은 정확도
- **medium**: 높은 정확도, 느림
- **large**: 최고 정확도, 매우 느림

모델 변경은 `karaoke_maker.py`의 `WhisperTimingExtractor` 초기화 부분에서 수정:
```python
extractor = WhisperTimingExtractor(model_name="small")  # 또는 medium, large
```

### 가사 포맷 가이드

최적의 결과를 위한 가사 작성 팁:

1. **한 줄 = 한 화면**: 너무 긴 줄은 화면에 맞게 나눠주세요
2. **빈 줄 = 장면 전환**: 배경 이미지가 바뀔 구간에 빈 줄 추가
3. **라벨 자동 제거**: (Verse), (Chorus) 등은 자동으로 제거됨
4. **특수문자 주의**: 이모지나 특수문자는 폰트에 따라 표시되지 않을 수 있음

## 문제 해결

### 한글이 표시되지 않는 경우

1. 한글 폰트가 설치되어 있는지 확인:
   ```bash
   fc-list | grep -i nanum
   ```

2. 폰트가 없다면 설치:
   ```bash
   ./install_fonts.sh
   ```

3. 다른 폰트 사용하려면 `karaoke_maker.py`에서 폰트명 변경:
   ```python
   font='NanumGothic-Bold'  # 원하는 폰트명으로 변경
   ```

### Whisper 타이밍이 맞지 않는 경우

1. **더 큰 모델 사용**: small 또는 medium 모델 시도
2. **가사 수정**: Whisper가 인식한 텍스트와 가사 파일을 비교하여 수정
3. **오디오 품질**: 노이즈가 적고 명확한 오디오 사용

### 메모리 부족 오류

1. **더 작은 모델**: tiny 또는 base 모델 사용
2. **이미지 크기**: 배경 이미지를 미리 리사이즈 (권장: 1920x1080)
3. **프로세스 수**: MoviePy의 threads 옵션 조정

### 영상 생성이 느린 경우

1. **Whisper 모델**: base 또는 tiny 모델 사용
2. **MoviePy preset**: 'ultrafast' 또는 'veryfast'로 변경
3. **해상도 조정**: 1280x720으로 낮추기

## 고급 사용법

### 커스터마이징

`karaoke_maker.py`를 직접 수정하여 다음을 변경할 수 있습니다:

- 자막 크기, 색상, 위치
- 영상 해상도 및 프레임레이트
- 이미지 전환 효과
- 폰트 스타일

### 배치 처리

여러 곡을 한 번에 처리하는 간단한 쉘 스크립트:

```bash
#!/bin/bash
for audio in audio/*.wav; do
    name=$(basename "$audio" .wav)
    python karaoke_maker.py "$audio" "lyrics/${name}.txt" "output/${name}.mp4"
done
```

## 라이선스

MIT License

## 개발자

KYXI - Wedding Video Automation Project