from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
import gemini_engine
from time import time
from dotenv import load_dotenv
import os

# Este módulo é responsável por carregar as informações (embeddings) a serem 
# utilizadas pelo modelo de LLM na elaboração de suas respostas por meio do 
# módulo gemini_engine.py


class VirtualAssistant:
    def __init__(self) -> None:
        load_dotenv()
        GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
        start = time()
        print("Carregando base...")
        loader = TextLoader(file_path="/home/fernando/Python/Whatsapp_bot/faq.txt")
        content = loader.load() # Load data into Document objects.
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
        self.vector_store = FAISS.from_documents(content, embeddings)
        self.ai_engine = gemini_engine.AIEngine()
        end = time()
        print(f"Base carregada em {round(end - start, ndigits=2)} segundos!")

    
    def user_question(self, name:str, wa_id: str, human_message: str, specific_prompt:str=None) -> str:
        similar_response = self.vector_store.similarity_search(human_message, k=3)
        documents = [document.page_content for document in similar_response]
        specific_prompt = f"You should use a 14 years old content language. At first, when the client salute you, you should salute him back and say something like 'Bem vindo à Oficina Sonhar' and identify youself as a virtual assistant in order to the client don't confuse you with the onwer. Answer all the questions with the best of your ability, always in portuguese from Brazil. The client's name is {name}. You should formulate your answer by using only the content of {documents}. If the client asks something about the address or location to withdraw the products, just answer the word 'location'. But if the client asks something about the time of the day he could withdraw the products, you will formulate the answer. If the client thanks, or says something about goodbye, just answer the word 'thanks'. " if specific_prompt is None else specific_prompt

        answer = self.ai_engine.answer_messages_with_ai(name, wa_id, human_message, specific_prompt) # -> LangChain object
        return answer
    

    def user_image(self, name:str, wa_id: str, specific_prompt:str=None) -> str:
        human_message = self.ai_engine.parse_image()
        specific_prompt = f"Descrição da imagem enviada pelo cliente: {human_message}. Faça uma inferência entre esta descrição e os serviços oferecidos pela Oficina Sonhar para tentar entender o que o cliente quis dizer. Sempre analise a resposta anterior."
        answer = self.user_question(name, wa_id, human_message, specific_prompt)
        return answer