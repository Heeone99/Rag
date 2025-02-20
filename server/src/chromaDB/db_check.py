import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings

# 환경 변수 로드
load_dotenv()

# ChromaDB 관련 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(CURRENT_DIR, "../../chroma_db")  # ChromaDB가 저장된 디렉토리

# ChromaDB 초기화
openAI = OpenAIEmbeddings(model="text-embedding-3-small")
db = Chroma(persist_directory=DB_DIR, embedding_function=openAI)

def list_collections():
    """
    ChromaDB에 저장된 컬렉션 목록을 출력하는 함수
    """
    try:
        collections = db._client.list_collections()
        if collections:
            print("\nChromaDB에 저장된 컬렉션 목록:")
            for collection in collections:
                print(f"- 컬렉션 이름: {collection.name}")
        else:
            print("ChromaDB에 저장된 컬렉션이 없습니다.")
    except Exception as e:
        print(f"오류 발생: {str(e)}")

def check_collection_content(collection_name):
    """
    특정 컬렉션의 문서 내용을 출력하는 함수
    """
    try:
        collection = db._client.get_collection(collection_name)
        if collection:
            print(f"\n컬렉션 '{collection_name}'의 내용:")
            documents = collection.get()
            for doc_id, page_content, metadata in zip(documents['ids'], documents['documents'], documents['metadatas']):
                print(f"- 문서 ID: {doc_id}")
                print(f"  내용: {page_content}...")  # 내용의 앞 100글자만 출력
                print(f"  메타데이터: {metadata}")
        else:
            print(f"컬렉션 '{collection_name}'을(를) 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    # ChromaDB의 모든 컬렉션 목록 출력
    list_collections()

    # 사용자가 특정 컬렉션의 이름을 입력하여 내용 확인
    collection_to_check = input("내용을 확인할 컬렉션 이름을 입력하세요: ")
    if collection_to_check:
        check_collection_content(collection_to_check)
    else:
        print("컬렉션 이름을 입력하지 않았습니다.")
