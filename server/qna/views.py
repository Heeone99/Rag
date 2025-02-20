from django.core.cache import cache  # 캐싱을 위한 모듈 추가
from django.contrib.sessions.backends.db import SessionStore
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from langchain.chains.question_answering import load_qa_chain
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from .models import ChatLog
from accounts.models import User
import json
import os
import logging

logging.basicConfig(level=logging.DEBUG)

# ChromaDB 설정
CHROMADB_DIR = os.getenv("CHROMADB_DIR", "./chroma_db/promotion")
CHROMADB_COLLECTION = os.getenv("CHROMADB_COLLECTION", "promotion")


@csrf_exempt
def qna(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get("question")
            session_id = data.get("session_id")

            if not question or not session_id:
                return JsonResponse({"error": "질문과 세션 ID를 입력해주세요."}, status=400)

            # 세션 검증 및 사용자 가져오기
            try:
                session = Session.objects.get(session_key=session_id)
                user_id = session.get_decoded().get('user_id')
                user = User.objects.get(id=user_id)
            except Session.DoesNotExist:
                return JsonResponse({"error": "유효하지 않은 세션 ID입니다."}, status=401)
            except User.DoesNotExist:
                return JsonResponse({"error": "사용자를 찾을 수 없습니다."}, status=404)

            # 캐시에서 확인
            cached_answer = cache.get(question)
            if cached_answer:
                logging.info(f"캐시된 응답 반환: {cached_answer}")
                return JsonResponse({"answer": cached_answer}, status=200)

            # ChromaDB
            db = Chroma(
                collection_name=CHROMADB_COLLECTION,
                persist_directory=CHROMADB_DIR,
                embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")
            )
            retriever = db.as_retriever(search_kwargs={"k": 5})

            # Chaining
            prompt = PromptTemplate(
                input_variables=["context", "question"],
                template="Context: {context}\n\nQuestion: {question}\n\nAnswer: ",
            )
            chain = load_qa_chain(
                llm=ChatOpenAI(model_name="gpt-4o-mini", temperature=0),
                chain_type="stuff",
                prompt=prompt
            )

            # 답변 생성
            documents = retriever.get_relevant_documents(question)
            if not documents:
                return JsonResponse({"error": "관련 정보를 찾을 수 없습니다."}, status=404)

            answer = chain.run(input_documents=documents, question=question)

            # 캐시에 응답 저장
            cache.set(question, answer, timeout=300)

            # 대화 저장
            ChatLog.objects.create(
                user=user,
                user_input=question,
                chatbot_reply=answer
            )

            return JsonResponse({"answer": answer}, status=200)

        except Exception as e:
            logging.error(f"Error in Q&A: {str(e)}")
            return JsonResponse({"error": "서버 내부 오류가 발생했습니다."}, status=500)

    return JsonResponse({"error": "잘못된 요청입니다."}, status=400)





@csrf_exempt
def save_chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get("session_id")
            user_input = data.get("user_input")
            chatbot_reply = data.get("chatbot_reply")

            # 입력 데이터 확인
            if not session_id or not user_input or not chatbot_reply:
                return JsonResponse({"error": "필수 데이터가 누락되었습니다."}, status=400)

            # 세션 검증 및 사용자 가져오기
            session = Session.objects.get(session_key=session_id)
            user_id = session.get_decoded().get('user_id')
            user = User.objects.get(id=user_id)

            # 대화 저장
            ChatLog.objects.create(
                user=user,
                user_input=user_input,
                chatbot_reply=chatbot_reply
            )

            return JsonResponse({"message": "채팅 기록이 저장되었습니다."}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "잘못된 요청입니다."}, status=400)


@csrf_exempt
def get_chat_history(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get("session_id")

            # 세션 검증 및 사용자 가져오기
            session = Session.objects.get(session_key=session_id)
            user_id = session.get_decoded().get('user_id')
            user = User.objects.get(id=user_id)

            # 대화 확인
            chat_logs = ChatLog.objects.filter(user=user).order_by('timestamp')

            # 질문-응답 형태로 데이터 정렬
            history = []
            for log in chat_logs:
                history.append({"sender": "user", "message": log.user_input})
                history.append({"sender": "bot", "message": log.chatbot_reply})

            return JsonResponse({"history": history}, status=200)

        except Session.DoesNotExist:
            return JsonResponse({"error": "세션이 유효하지 않습니다."}, status=401)
        except User.DoesNotExist:
            return JsonResponse({"error": "사용자를 찾을 수 없습니다."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "잘못된 요청입니다."}, status=400)

