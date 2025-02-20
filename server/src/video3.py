import os
from moviepy.editor import VideoFileClip
import requests
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain import hub
from langchain.chat_models import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 환경 변수 로드
load_dotenv()

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "../data/audio")
TEXT_DIR = os.path.join(BASE_DIR, "../data/txt")
VIDEO_DIR = os.path.join(BASE_DIR, "../data/video")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "../chroma_db/video")


# 폴더 생성 함수
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# 1. 동영상에서 음성 추출
def extract_audio(video_path, output_audio_path):
    """Extract audio from video and save as a .wav file."""
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(output_audio_path)
    print(f"Audio saved to {output_audio_path}")

# 2. 클로바 스피치 API를 통해 음성을 텍스트로 변환
def clova_speech_to_text(api_url, secret_key, audio_path):
    """Convert audio to text using Clova Speech API."""
    headers = {
        "X-NCP-APIGW-API-KEY-ID": secret_key['id'],
        "X-NCP-APIGW-API-KEY": secret_key['key'],
        "Content-Type": "application/octet-stream",
    }
    with open(audio_path, "rb") as audio_file:
        audio_data = audio_file.read()

    response = requests.post(api_url, headers=headers, data=audio_data)
    if response.status_code == 200:
        result = response.json()
        text = result['text']  # 클로바 API 응답에 따라 키 수정
        print("Speech to Text result:", text)
        return text
    else:
        print("Error:", response.status_code, response.text)
        return None

# 3. 텍스트 데이터 저장
def save_text_to_file(text, output_file):
    """Save the text data to a file."""
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(text)
    print(f"Text data saved to {output_file}")

# 4. LangChain 설정
def create_chain():
    """Create a LangChain chain for text summarization."""
    # ChromaDB 설정
    db = Chroma(
        persist_directory=os.path.join(CHROMA_DB_DIR, "lecture_db"),
        embedding_function=OpenAIEmbeddings(model="text-embedding-ada-002"),
        collection_name="lecture_data"
    )

    # Retriever 설정
    retriever = db.as_retriever()

    # Chain 설정
    prompt = hub.pull("rlm/rag-prompt")
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=1)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain

# 5. 전체 워크플로우
def main():
    # 입력 파일 경로
    video_name = "lecture.mp4"  # 처리할 동영상 파일 이름
    video_path = os.path.join(VIDEO_DIR, video_name)
    audio_path = os.path.join(AUDIO_DIR, "lecture_audio.wav")
    text_file = os.path.join(TEXT_DIR, "lecture_text.txt")
    summary_file = os.path.join(TEXT_DIR, "lecture_summary.txt")

    # API 키
    api_url = "https://your_clova_api_url"
    secret_key = {"id": "YOUR_API_ID", "key": "YOUR_API_SECRET"}

    # 동영상에서 음성 추출
    extract_audio(video_path, audio_path)

    # 클로바 스피치 API를 통해 음성을 텍스트로 변환
    text_data = clova_speech_to_text(api_url, secret_key, audio_path)
    if text_data is not None:
        save_text_to_file(text_data, text_file)

        # 텍스트를 LangChain에 저장하고 요약
        chain = create_chain()

        # Chain을 통해 요약 수행
        summary = chain.invoke("강의 내용을 요약해 주세요")
        print("Summary:", summary)

        # 요약된 텍스트를 저장
        save_text_to_file(summary, summary_file)

if __name__ == "__main__":
    main()
