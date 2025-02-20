from dotenv import load_dotenv
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain import hub
from langchain.chat_models import ChatOpenAI
from langchain.schema import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

# 환경변수 로드
load_dotenv()



# db1 = Chroma(
#             persist_directory="../chroma_db/db1",
#             embedding_function=OpenAIEmbeddings(),
#             collection_name="mjc_db"
#         )

# db2 = Chroma(
#             persist_directory="../chroma_db/db2",
#             embedding_function=OpenAIEmbeddings(),
#             collection_name="mjc_db2"
#         )

db = Chroma(
            persist_directory="../chroma_db/combinded",
            embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
            collection_name="combinded"
        )


# numDimensions 확인 추가
# try:
#     collection = db3._client.get_collection("mjc_db3")
#     if collection.metadata and "numDimensions" in collection.metadata:
#         print(f"numDimensions: {collection.metadata['numDimensions']}")
#     else:
#         print("numDimensions 메타데이터가 설정되어 있지 않습니다.")
# except Exception as e:
#     print("컬렉션 점검 중 오류:", e)

# Retriever 설정
retriever = db.as_retriever(
    # search_type="mmr", 
    # search_kwargs={
    #     "k": 3, "fetch_k": 10, "lambda_mult": 0.3
    #     }
)

# Chain 설정
prompt = hub.pull("rlm/rag-prompt")
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=1)

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)


#테스트 쿼리
print(chain.invoke("게임 개발과 관련된 게시물 내용 요약해줄래"))

# # db3 메타데이터 확인
# print(db3._collection_metadata)
