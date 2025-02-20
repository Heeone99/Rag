import os
import uuid
import subprocess
import requests
import json
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
from .models import LectureSummary

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
 
def generate_unique_name(prefix="file"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

# 클로바 API 호출을 통해 텍스트 변환
def transcribe_audio_to_text(media_file_path, api_url, api_key):
    headers = {'X-CLOVASPEECH-API-KEY': api_key}
    with open(media_file_path, 'rb') as media_file:
        files = {'media': media_file}
        params = {
            "language": "ko-KR",
            "completion": "sync",
            "callback": "",
            "fullText": True
        }
        data = {'params': json.dumps(params), 'type': "application/json"}
        response = requests.post(api_url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json().get("text", "")


def create_chroma_db(persist_directory, collection_name):
    """Create or load a ChromaDB."""
    return Chroma(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding_function=embeddings
    )

# 프롬프트
def load_prompt(prompt_file):
    with open(prompt_file, 'r', encoding='utf-8') as file:
        return file.read()

# 동영상 요약
def summarize_lecture(db, query):
    retriever = db.as_retriever()
    prompt_file = './data/prompt/lecture_summary_prompt.txt'
    prompt_template_text = load_prompt(prompt_file)
    prompt_template = ChatPromptTemplate.from_template(prompt_template_text)

    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=1)
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt_template},
        verbose=True
    )
    return chain.run(query)

# 동영상 요약 바탕 qa
def answer_question(db, question):
    retriever = db.as_retriever()
    prompt_file = './data/prompt/lecture_qa_prompt.txt'
    prompt_template_text = load_prompt(prompt_file)
    prompt_template = ChatPromptTemplate.from_template(prompt_template_text)

    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt_template},
        verbose=True
    )
    return qa_chain.run(question)


class LectureSummaryView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        api_url = os.getenv('API_URL')
        api_key = os.getenv('API_KEY')
        video_dir = './data/video'
        audio_dir = './data/audio'
        db_base_path = './chroma_db/lecture_summary'

        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        video_url = request.data.get('video_url')
        video_file = request.FILES.get('video_file')

        try:
            unique_key = video_url.strip() if video_url else video_file.name

            lecture_summary = LectureSummary.objects.filter(unique_name=unique_key).first()
            if lecture_summary:
                db = create_chroma_db(
                    persist_directory=lecture_summary.db_path,
                    collection_name=lecture_summary.collection_name
                )
                return JsonResponse({
                    "unique_name": lecture_summary.unique_name,
                    "summary": lecture_summary.summary
                }, status=200)

            collection_name = generate_unique_name("collection")
            db_path = os.path.join(db_base_path, collection_name)
            video_input_path = None
            mp4_path = os.path.join(video_dir, f"{collection_name}.mp4")

            if video_url:

                video_input_path = os.path.join(video_dir, f"{collection_name}.%(ext)s")
                subprocess.run(["yt-dlp", "-o", video_input_path, video_url], check=True)
  
                if os.path.exists(video_input_path.replace("%(ext)s", "webm")):
                    video_input_path = video_input_path.replace("%(ext)s", "webm")
                elif os.path.exists(video_input_path.replace("%(ext)s", "mkv")):
                    video_input_path = video_input_path.replace("%(ext)s", "mkv")
                else:
                    raise ValueError("Downloaded video file not found.")

            elif video_file:
                ext = os.path.splitext(video_file.name)[-1].lower()
                video_input_path = os.path.join(video_dir, f"{collection_name}{ext}")
                with open(video_input_path, 'wb') as out_file:
                    for chunk in video_file.chunks():
                        out_file.write(chunk)

            # 동영상 -> 음성파일 변환
            subprocess.run(["ffmpeg", "-i", video_input_path, "-c:v", "copy", "-c:a", "aac", mp4_path], check=True)


            audio_path = os.path.join(audio_dir, f"{collection_name}.wav")
            subprocess.run(["ffmpeg", "-i", mp4_path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", audio_path], check=True)

            
            lecture_text = transcribe_audio_to_text(audio_path, api_url, api_key)


            db = create_chroma_db(persist_directory=db_path, collection_name=collection_name)
            db.add_documents([Document(page_content=lecture_text)])


            summary = summarize_lecture(db, "Summarize the lecture content.")

            LectureSummary.objects.create(
                unique_name=unique_key,
                collection_name=collection_name,
                db_path=db_path,
                summary=summary
            )

            return JsonResponse({"unique_name": unique_key, "summary": summary}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)



class LectureQAView(APIView):
    def post(self, request):
        unique_name = request.data.get('unique_name')
        question = request.data.get('question')

        if not unique_name or not question:
            return JsonResponse({"error": "unique_name and question are required."}, status=400)

        try:
            lecture_summary = LectureSummary.objects.filter(unique_name=unique_name).first()
            if not lecture_summary:
                return JsonResponse({"error": "Lecture summary not found."}, status=404)

            db = create_chroma_db(
                persist_directory=lecture_summary.db_path,
                collection_name=lecture_summary.collection_name
            )
            answer = answer_question(db, question)
            return JsonResponse({"answer": answer}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
