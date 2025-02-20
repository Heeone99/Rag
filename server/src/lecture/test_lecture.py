import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# 환경변수 로드
load_dotenv()

# 강의 요약 실행 함수
def summarize_lecture(db, query):
    """강의 요약을 수행하는 함수"""
    retriever = db.as_retriever()

    # 템플릿 생성
    prompt_template = ChatPromptTemplate.from_template(
        """
        Please summarize the following lecture content using the provided structure:

        **Lecture Topic**:
        - Topic: (Summarize the main topic or theme of the lecture)

        **Core Content**:
        - Provide a detailed summary of the core content in the lecture text.
        - Include key points, important arguments, or discussions.

        **Key Points**:
        - List the major points discussed in the lecture using bullet points.
        - For each point, include the timestamp in minutes and seconds (e.g., "10:30" for 10 minutes and 30 seconds).
        - Example: 
          - [10:30] Point 1: Description.
          - [15:45] Point 2: Description.

        **Conclusion and Takeaways**:
        - Summarize the overall conclusion or the key insights from the lecture.
        - Highlight any actionable recommendations or implications.

        **Glossary of Important Terms**:
        - Provide a glossary of technical terms, jargon, or specific terminology used in the lecture.
        - For each term, include a brief explanation or definition to help the reader understand the context.

        TASK:
        Summarize the text provided below and return it in Korean.

        BEGIN TEXT
        {context}
        END TEXT

        FORMAT:
        Markdown
        """
    )

    # LLM 및 체인 정의
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=1)
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt_template},
        return_source_documents=False,  # 요약만 반환
        verbose=True
    )

    return chain.run(query)

# 실행 코드
if __name__ == "__main__":
    # ChromaDB 경로 및 컬렉션 이름 설정
    DB_PATH = '../chroma_db/lecture_summary'
    COLLECTION_NAME = 'collection_3fd4c5e1'

    try:
        # 1. DB 존재 여부 확인 및 로드
        if os.path.exists(DB_PATH):
            print(f"Loading existing collection: {COLLECTION_NAME}")
            db = Chroma(
                persist_directory=DB_PATH,
                embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
                collection_name=COLLECTION_NAME
            )
            print("Database loaded successfully.")
        else:
            raise FileNotFoundError(f"Collection '{COLLECTION_NAME}' not found in the database path.")

        # 2. 강의 요약 실행
        query = "Please summarize the lecture content."
        print("Generating summary of the lecture...")
        summary = summarize_lecture(db, query)
        print("Summary Result:")
        print(summary)

    except Exception as e:
        print(f"Error occurred: {e}")
