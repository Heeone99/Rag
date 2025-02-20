import os
import requests
import json
import subprocess
import yt_dlp
import re
import uuid  # UUID를 생성하기 위한 라이브러리
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings

# 환경변수 로드
load_dotenv()

# 고유한 이름 생성
def generate_unique_name(prefix="file"):
    """UUID를 사용하여 고유한 이름 생성"""
    unique_id = uuid.uuid4().hex[:8]  # 8자리 고유 ID 생성
    return f"{prefix}_{unique_id}"

# FFmpeg로 파일 변환
def convert_to_mp4(input_path, output_path):
    """FFmpeg를 사용하여 .webm 파일을 .mp4로 변환"""
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-c:v", "copy",
            "-c:a", "aac",
            output_path
        ]
        subprocess.run(command, check=True)
        print(f"Converted {input_path} to {output_path} successfully.")
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Error during FFmpeg conversion: {e}")

# FFmpeg로 오디오 추출
def extract_audio_with_ffmpeg(input_path, output_path):
    """FFmpeg를 사용하여 .mp4 파일에서 오디오를 추출"""
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-vn",  # 비디오 제외
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            output_path
        ]
        subprocess.run(command, check=True)
        print(f"Audio extracted: {output_path}")
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Error during audio extraction: {e}")

# yt-dlp를 사용한 동영상 다운로드 및 오디오 추출
def download_and_process_video(video_url, video_dir, audio_dir):
    """yt-dlp를 사용하여 동영상을 다운로드하고 처리"""
    try:
        # 동영상 다운로드 옵션 설정
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{video_dir}/%(id)s.webm",  # 유튜브 ID로 저장
            'quiet': False,
        }

        # yt-dlp로 다운로드 및 정보 추출
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            video_id = info_dict.get('id', 'unknown_id')

        # 임의의 파일 이름 생성
        unique_name = generate_unique_name("lecture")
        webm_path = os.path.join(video_dir, f"{video_id}.webm")
        mp4_path = os.path.join(video_dir, f"{unique_name}.mp4")
        audio_path = os.path.join(audio_dir, f"{unique_name}.wav")

        # 디렉토리 생성
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        # .webm 파일을 .mp4로 변환
        convert_to_mp4(webm_path, mp4_path)

        # FFmpeg로 오디오 추출
        extract_audio_with_ffmpeg(mp4_path, audio_path)

        return mp4_path, audio_path, unique_name
    except Exception as e:
        raise ValueError(f"Error during video/audio processing: {e}")

# CLOVA Speech API로 음성을 텍스트로 변환
def transcribe_audio_to_text(media_file_path, api_url, api_key):
    """음성을 텍스트로 변환하는 함수"""
    headers = {'X-CLOVASPEECH-API-KEY': api_key}
    files = {'media': open(media_file_path, 'rb')}
    params = {
        "language": "ko-KR",
        "completion": "sync",
        "callback": "",
        "fullText": True
    }
    data = {'params': json.dumps(params), 'type': "application/json"}
    response = requests.post(api_url, headers=headers, files=files, data=data)
    
    # 예외 처리
    if response.status_code != 200:
        raise ValueError(f"API 요청 실패: {response.status_code}, {response.text}")
    
    response_data = response.json()
    return response_data.get("text", "")

# 텍스트를 ChromaDB에 저장
def save_to_chromadb(text, db_path, collection_name):
    """텍스트 데이터를 ChromaDB에 저장하는 함수"""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    documents = [Document(page_content=chunk) for chunk in text_splitter.split_text(text)]
    
    # ChromaDB 생성 및 데이터 추가
    db = Chroma(
        persist_directory=db_path,  # 데이터를 저장할 디렉토리
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
        collection_name=collection_name
    )
    db.add_documents(documents)  # 문서 추가
    return db

# 실행 코드
if __name__ == "__main__":
    API_URL = os.getenv('API_URL')
    API_KEY = os.getenv('API_KEY')
    VIDEO_URL = 'https://www.youtube.com/watch?v=O3qFWRObAXw'
    VIDEO_DIR = '../data/video'
    AUDIO_DIR = '../data/audio'
    DB_PATH = '../chroma_db/lecture_summary'

    try:
        # 1. 동영상 다운로드 및 오디오 추출
        video_path, audio_path, unique_name = download_and_process_video(VIDEO_URL, VIDEO_DIR, AUDIO_DIR)

        # 2. 텍스트 변환 및 저장
        lecture_text = transcribe_audio_to_text(audio_path, API_URL, API_KEY)

        # ChromaDB에 저장할 임의의 컬렉션 이름 생성
        collection_name = generate_unique_name("collection")
        db = save_to_chromadb(lecture_text, DB_PATH, collection_name)

        print(f"Processing complete. MP4: {video_path}, WAV: {audio_path}, Collection Name: {collection_name}")
    except Exception as e:
        print(f"Error occurred: {e}")
