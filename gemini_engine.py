import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import google.generativeai as genai
import PIL.Image
from dotenv import load_dotenv


class AIEngine:
    def __init__(self) -> None:
        load_dotenv()
        self.GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
        self.store = {}

    
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]


    def answer_messages_with_ai(self, name: str, wa_id: str, human_message: str, specific_prompt=None) -> str:
        default_prompt = f"Answer all questions to the best of your ability, in the same language used by the client. The content must be 14 years old classification. At the first interacton, you should salute the user by it's first name is {name}." if specific_prompt is None else specific_prompt
        prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"'{default_prompt}'",
            ),
            MessagesPlaceholder(variable_name="messages")
        ])
        model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
        chain = prompt | model
        
        with_message_history = RunnableWithMessageHistory(chain, self.get_session_history)
        config = {"configurable": {"session_id": f"{wa_id}"}}

        ai_output = with_message_history.invoke(
            [HumanMessage(content=f"{human_message}")],
            config=config,
        )
        
        return ai_output.content
    

    def parse_image(self) -> str:
        image_path = f"{os.path.dirname(__file__)}/media/image.jpeg"
        genai.configure(api_key = self.GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        image = PIL.Image.open(image_path)
        response = model.generate_content(["Me diga do que se trata esta imagem", image])
        human_message = response.text
        return human_message
    
