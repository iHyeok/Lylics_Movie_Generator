#!/usr/bin/env python3
"""
Karaoke-style Video Generator with Auto-timing using Whisper AI

MP3/WAV 오디오 파일과 가사 텍스트를 입력받아,
Whisper AI로 타이밍을 추출하고 배경 사진과 함께 노래방 스타일 영상을 생성합니다.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import whisper
import numpy as np

# MoviePy 2.x import
try:
    # MoviePy 2.x
    from moviepy import (
        VideoClip,
        AudioFileClip,
        ImageClip,
        CompositeVideoClip,
        TextClip,
        concatenate_videoclips
    )
except ImportError:
    # MoviePy 1.x fallback
    from moviepy.editor import (
        VideoClip,
        AudioFileClip,
        ImageClip,
        CompositeVideoClip,
        TextClip,
        concatenate_videoclips
    )

from PIL import Image, ImageDraw, ImageFont


class LyricsParser:
    """가사 파일을 파싱하고 정제하는 클래스"""

    def __init__(self, lyrics_file: str):
        self.lyrics_file = lyrics_file
        self.sections = []

    def parse(self) -> List[Dict[str, any]]:
        """
        가사 파일을 파싱하여 구간별로 분리

        Returns:
            List[Dict]: [{'lines': ['line1', 'line2'], 'section_num': 0}, ...]
        """
        with open(self.lyrics_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 구간 분리 (빈 줄 기준)
        sections = content.split('\n\n')

        parsed_sections = []
        for i, section in enumerate(sections):
            if not section.strip():
                continue

            # 각 구간의 라인들
            lines = section.strip().split('\n')

            # 라벨 제거 (Verse), (Chorus) 등
            cleaned_lines = []
            for line in lines:
                # 괄호로 시작하는 라벨 제거
                cleaned_line = re.sub(r'^\([^)]+\)\s*', '', line)
                if cleaned_line.strip():
                    cleaned_lines.append(cleaned_line.strip())

            if cleaned_lines:
                parsed_sections.append({
                    'lines': cleaned_lines,
                    'section_num': i,
                    'text': ' '.join(cleaned_lines)  # Whisper 매칭용 전체 텍스트
                })

        self.sections = parsed_sections
        return parsed_sections


class WhisperTimingExtractor:
    """Whisper를 사용하여 오디오에서 타이밍을 추출하는 클래스"""

    def __init__(self, model_name: str = "base"):
        """
        Args:
            model_name: Whisper 모델 이름 (tiny, base, small, medium, large)
        """
        print(f"Whisper 모델 로딩 중: {model_name}")
        self.model = whisper.load_model(model_name)

    def extract_timing(self, audio_file: str) -> Dict:
        """
        오디오 파일에서 word-level 타임스탬프 추출

        Args:
            audio_file: 오디오 파일 경로

        Returns:
            Dict: Whisper 결과 (segments, text 포함)
        """
        print(f"오디오 분석 중: {audio_file}")
        result = self.model.transcribe(
            audio_file,
            language='ko',  # 한국어
            word_timestamps=True,  # word-level 타임스탬프
            verbose=True
        )
        return result


class TimingMatcher:
    """가사와 Whisper 타임스탬프를 매칭하는 클래스"""

    @staticmethod
    def match_lyrics_to_timing(sections: List[Dict], whisper_result: Dict) -> List[Dict]:
        """
        가사 구간과 Whisper 결과를 매칭

        Args:
            sections: 파싱된 가사 구간들
            whisper_result: Whisper 분석 결과

        Returns:
            List[Dict]: 타이밍 정보가 추가된 구간들
        """
        segments = whisper_result.get('segments', [])

        # 전체 텍스트에서 단어별 타이밍 추출
        all_words = []
        for segment in segments:
            if 'words' in segment:
                all_words.extend(segment['words'])

        # 각 구간에 타이밍 할당
        timed_sections = []
        word_idx = 0

        for section in sections:
            section_text = section['text']
            words_in_section = section_text.split()

            # 이 구간의 시작/종료 시간 찾기
            start_time = None
            end_time = None

            if word_idx < len(all_words):
                start_time = all_words[word_idx].get('start', 0)

                # 구간의 단어 수만큼 진행
                end_idx = min(word_idx + len(words_in_section), len(all_words) - 1)
                end_time = all_words[end_idx].get('end', start_time + 5)

                word_idx = end_idx + 1

            timed_sections.append({
                **section,
                'start_time': start_time if start_time is not None else 0,
                'end_time': end_time if end_time is not None else 5,
                'duration': (end_time - start_time) if (start_time and end_time) else 5
            })

        return timed_sections


class VideoGenerator:
    """노래방 스타일 영상을 생성하는 클래스"""

    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps

    def load_images(self, images_dir: str, num_sections: int) -> List[str]:
        """
        배경 이미지 로드 (부족하면 반복)

        Args:
            images_dir: 이미지 디렉토리
            num_sections: 필요한 이미지 수

        Returns:
            List[str]: 이미지 파일 경로 리스트
        """
        image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
        image_files = []

        for ext in image_extensions:
            image_files.extend(Path(images_dir).glob(f'*{ext}'))

        # 파일명으로 정렬
        image_files = sorted(image_files, key=lambda x: x.name)

        if not image_files:
            raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {images_dir}")

        # 이미지가 부족하면 반복
        images = []
        for i in range(num_sections):
            images.append(str(image_files[i % len(image_files)]))

        return images

    def create_text_clip(self, text: str, duration: float, font_size: int = 60):
        """
        자막 클립 생성 (Pillow 사용)

        Args:
            text: 표시할 텍스트
            duration: 지속 시간
            font_size: 폰트 크기

        Returns:
            ImageClip: 생성된 자막 클립
        """
        # Pillow로 텍스트 이미지 생성
        text_width = self.width - 200

        # 폰트 로드 (시스템 폰트 경로에서 찾기)
        font = None
        font_paths = [
            '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf',
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
            'C:\\Windows\\Fonts\\malgun.ttf',  # Windows
            '/System/Library/Fonts/AppleSDGothicNeo.ttc',  # macOS
            '/Library/Fonts/NanumGothicBold.ttf',  # macOS
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue

        if font is None:
            # 기본 폰트 사용
            font = ImageFont.load_default()

        # 텍스트를 여러 줄로 분리
        lines = text.split('\n')

        # 각 줄의 크기 계산
        line_heights = []
        line_widths = []
        for line in lines:
            bbox = font.getbbox(line)
            line_widths.append(bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])

        # 전체 텍스트 이미지 크기
        total_height = sum(line_heights) + (len(lines) - 1) * 10  # 줄 간격 10px
        max_width = max(line_widths) if line_widths else text_width

        # 투명 배경 이미지 생성
        img = Image.new('RGBA', (max_width + 20, total_height + 20), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 텍스트 그리기 (외곽선 + 텍스트)
        y_offset = 10
        for line, line_width in zip(lines, line_widths):
            x_offset = (max_width - line_width) // 2 + 10  # 중앙 정렬

            # 외곽선 (검은색)
            for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2), (-2,0), (2,0), (0,-2), (0,2)]:
                draw.text((x_offset + dx, y_offset + dy), line, font=font, fill='black')

            # 텍스트 (흰색)
            draw.text((x_offset, y_offset), line, font=font, fill='white')

            y_offset += line_heights[lines.index(line)] + 10

        # NumPy 배열로 변환
        img_array = np.array(img)

        # ImageClip 생성
        return ImageClip(img_array).set_duration(duration).set_position(('center', self.height - 200))

    def create_section_clip(self, image_path: str, text: str, duration: float) -> CompositeVideoClip:
        """
        구간별 클립 생성 (배경 이미지 + 자막)

        Args:
            image_path: 배경 이미지 경로
            text: 자막 텍스트
            duration: 지속 시간

        Returns:
            CompositeVideoClip: 생성된 클립
        """
        # 배경 이미지 클립
        img_clip = ImageClip(image_path).set_duration(duration)
        img_clip = img_clip.resize(height=self.height)  # 1080p에 맞춤

        # 이미지가 화면보다 작으면 중앙 배치, 크면 크롭
        if img_clip.w < self.width:
            img_clip = img_clip.set_position('center')
        else:
            # 중앙 크롭
            x_center = img_clip.w / 2
            x1 = int(x_center - self.width / 2)
            img_clip = img_clip.crop(x1=x1, width=self.width)

        # 자막 클립
        text_clip = self.create_text_clip(text, duration)

        # 합성
        return CompositeVideoClip([img_clip, text_clip], size=(self.width, self.height))

    def generate_video(
        self,
        timed_sections: List[Dict],
        images_dir: str,
        audio_file: str,
        output_file: str
    ):
        """
        최종 영상 생성

        Args:
            timed_sections: 타이밍 정보가 포함된 가사 구간들
            images_dir: 배경 이미지 디렉토리
            audio_file: 오디오 파일
            output_file: 출력 영상 파일
        """
        print("영상 생성 중...")

        # 이미지 로드
        images = self.load_images(images_dir, len(timed_sections))

        # 각 구간별 클립 생성
        clips = []
        for i, section in enumerate(timed_sections):
            text = '\n'.join(section['lines'])
            duration = section['duration']

            clip = self.create_section_clip(images[i], text, duration)
            clips.append(clip)

            print(f"구간 {i+1}/{len(timed_sections)} 생성 완료: {duration:.2f}초")

        # 클립 연결
        final_clip = concatenate_videoclips(clips, method="compose")

        # 오디오 추가
        audio = AudioFileClip(audio_file)
        final_clip = final_clip.set_audio(audio)

        # 영상 출력
        print(f"최종 영상 렌더링 중: {output_file}")
        final_clip.write_videofile(
            output_file,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='medium'
        )

        print(f"영상 생성 완료: {output_file}")


def main():
    """메인 실행 함수"""

    # 파일 경로 설정
    if len(sys.argv) < 3:
        print("사용법: python karaoke_maker.py <audio_file> <lyrics_file> [output_file] [images_dir]")
        print("\n예시:")
        print("  python karaoke_maker.py audio/song.wav lyrics/lyrics.txt")
        print("  python karaoke_maker.py audio/song.mp3 lyrics/lyrics.txt output/my_video.mp4 sample_images")
        sys.exit(1)

    audio_file = sys.argv[1]
    lyrics_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "output/karaoke_video.mp4"
    images_dir = sys.argv[4] if len(sys.argv) > 4 else "images"

    # 파일 존재 확인
    if not os.path.exists(audio_file):
        print(f"오디오 파일을 찾을 수 없습니다: {audio_file}")
        sys.exit(1)

    if not os.path.exists(lyrics_file):
        print(f"가사 파일을 찾을 수 없습니다: {lyrics_file}")
        sys.exit(1)

    if not os.path.exists(images_dir):
        print(f"이미지 디렉토리를 찾을 수 없습니다: {images_dir}")
        sys.exit(1)

    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

    print("=" * 60)
    print("노래방 스타일 영상 생성기")
    print("=" * 60)
    print(f"오디오: {audio_file}")
    print(f"가사: {lyrics_file}")
    print(f"이미지: {images_dir}")
    print(f"출력: {output_file}")
    print("=" * 60)

    # 1. 가사 파싱
    print("\n[1/4] 가사 파싱 중...")
    parser = LyricsParser(lyrics_file)
    sections = parser.parse()
    print(f"총 {len(sections)}개 구간 발견")
    for i, section in enumerate(sections):
        print(f"  구간 {i+1}: {section['lines'][0][:30]}...")

    # 2. Whisper 타이밍 추출
    print("\n[2/4] Whisper로 타이밍 추출 중...")
    extractor = WhisperTimingExtractor(model_name="base")
    whisper_result = extractor.extract_timing(audio_file)
    print(f"인식된 텍스트: {whisper_result['text'][:100]}...")

    # 3. 타이밍 매칭
    print("\n[3/4] 가사와 타이밍 매칭 중...")
    timed_sections = TimingMatcher.match_lyrics_to_timing(sections, whisper_result)
    for i, section in enumerate(timed_sections):
        print(f"  구간 {i+1}: {section['start_time']:.2f}s ~ {section['end_time']:.2f}s ({section['duration']:.2f}s)")

    # 4. 영상 생성
    print("\n[4/4] 영상 생성 중...")
    generator = VideoGenerator()
    generator.generate_video(timed_sections, images_dir, audio_file, output_file)

    print("\n" + "=" * 60)
    print("완료! 영상이 생성되었습니다.")
    print(f"출력 파일: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
