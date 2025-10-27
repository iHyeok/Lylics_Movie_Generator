#!/bin/bash
# 한글 폰트 설치 스크립트 (Ubuntu/Debian)

echo "한글 폰트 설치를 시작합니다..."

# Nanum 폰트 설치
if [ -f /etc/debian_version ]; then
    echo "Nanum 폰트 설치 중..."
    sudo apt-get update
    sudo apt-get install -y fonts-nanum fonts-nanum-coding fonts-nanum-extra
elif [ -f /etc/redhat-release ]; then
    echo "Nanum 폰트 설치 중..."
    sudo yum install -y google-noto-sans-cjk-fonts
elif [ "$(uname)" == "Darwin" ]; then
    echo "macOS에서는 Nanum 폰트를 수동으로 설치해주세요."
    echo "https://hangeul.naver.com/2017/nanum 에서 다운로드"
else
    echo "지원하지 않는 운영체제입니다."
    exit 1
fi

# 폰트 캐시 업데이트
echo "폰트 캐시 업데이트 중..."
fc-cache -f -v

echo "폰트 설치가 완료되었습니다!"
echo "설치된 Nanum 폰트 확인:"
fc-list | grep -i nanum
