import asyncio
from dotenv import load_dotenv
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import os

# 환경변수 로드
load_dotenv()

# ChromaDB 초기화
db = Chroma(
    persist_directory="../chroma_db/combinded",
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
    collection_name="combinded"
)

# Retriever 설정
retriever = db.as_retriever()

# Prompt 설정
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
    You are an intelligent assistant specialized in summarizing information.
    Your task is to generate accurate and concise answers based on the provided context.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
)

# LLM 설정
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0,
    streaming=True,
)

async def generate_stream(query):
    """
    비동기 스트림 데이터를 생성합니다.
    """
    try:
        # 문서 검색
        documents = retriever.invoke(query)
        if not documents:
            yield "data: No relevant documents found.\n\n"
            return

        # Context 생성
        context = "\n".join([doc.page_content for doc in documents])

        # Prompt 실행 및 스트림 반환
        inputs = prompt_template.format(context=context, question=query)

        # 비동기 스트림 처리
        loop = asyncio.get_event_loop()
        for chunk in await loop.run_in_executor(None, llm.stream, inputs):  # 동기 -> 비동기 변환
            # AIMessageChunk의 content 속성 사용
            if hasattr(chunk, 'content') and chunk.content:
                yield f"data: {chunk.content}\n\n"
    except Exception as e:
        yield f"data: Error occurred: {str(e)}\n\n"

async def main():
    """
    메인 함수에서 비동기 스트림 실행.
    """
    query = "게임 개발과 관련된 게시물 내용 요약해줄래"
    print("Streaming output:")
    async for output in generate_stream(query):
        print(output, end="")

if __name__ == "__main__":
    asyncio.run(main())
