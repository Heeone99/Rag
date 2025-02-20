from langchain_chroma import Chroma
from langchain.chat_models import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain import hub
import os
from dotenv import load_dotenv

load_dotenv()

class ChromaDBHandler:
    def __init__(self):
        self.db = Chroma(
            persist_directory=os.getenv("CHROMADB_DIR"),
            embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
            collection_name=os.getenv("CHROMADB_COLLECTION")
        )
        self.retriever = self.db.as_retriever()
        self.prompt = hub.pull("rlm/rag-prompt")
        self.llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=1)
        self.chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def query(self, question):
        return self.chain.invoke(question)
