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
        loader = TextLoader(file_path="/home/fernando/Python/Whatsapp_bot/faq.txt")
        content = loader.load() # Load data into Document objects.
        embeddings = OpenAIEmbeddings()
        self.vector_store = FAISS.from_documents(content, embeddings)
        self.ai_engine = ai_engine.AIEngine()
        end = time()
        print(f"Base carregada em {round(end - start, ndigits=2)} segundos!")

    
    def user_question(self, name, wa_id: str, human_message: str, specific_prompt=None) -> str:
        similar_response = self.vector_store.similarity_search(human_message, k=3)
        documents = [document.page_content for document in similar_response]
        specific_prompt = f"You should use a 14 years old content language. At first, when the client salute you, you should salute him back and say something like 'Bem vindo à Oficina Sonhar'. Answer all the questions with the best of your ability, always in portuguese from Brazil. The client's name is {name}. You should formulate your answer by using only the content of {documents}. If the client asks something about the address or location to withdraw the products, just answer the word 'location'. But if the client asks something about the time of the day he could withdraw the products, you will formulate the answer. If the client thanks, or says something about goodbye, just answer the word 'thanks'. " if specific_prompt is None else specific_prompt

        # If {human_message} appears to be confused, maybe it's because it's a transcription done by an audio. In these cases, asks the user what did he mean, always in the client's language (normally portuguese from Brazil).

        answer = self.ai_engine.answer_messages_with_ai(name, wa_id, human_message, specific_prompt) # -> LangChain object
        return answer