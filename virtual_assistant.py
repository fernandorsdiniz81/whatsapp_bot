from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import CSVLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import TextLoader
import ai_engine
from time import time


class VirtualAssistant:
    def __init__(self) -> None:
        start = time()
        print("Carregando base...")
        loader = TextLoader(file_path="/home/fernando/Python/Whatsapp_bot/guitarra_cort.txt")
        content = loader.load() # Load data into Document objects.
        embeddings = OpenAIEmbeddings()
        self.vector_store = FAISS.from_documents(content, embeddings)
        self.ai_engine = ai_engine.AIEngine()
        end = time()
        print(f"Base carregada em {round(end - start, ndigits=2)} segundos!")

    
    def user_question(self, name, wa_id: str, human_message: str, specific_prompt=None) -> str:
        similar_response = self.vector_store.similarity_search(human_message, k=3)
        documents = [document.page_content for document in similar_response]
        specific_prompt = f"Answer all the questions with the best of your ability, in the same language used by the client. The client's name is {name}. You should formulate your answer by using only the content of {documents}." if specific_prompt is None else specific_prompt
        answer = self.ai_engine.answer_messages_with_ai(name, wa_id, human_message, specific_prompt) # -> LangChain object
        return answer