import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv


class AIEngine:
    def __init__(self) -> None:
        load_dotenv()
        OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
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
        model = ChatOpenAI(model="gpt-3.5-turbo")
        chain = prompt | model
        
        with_message_history = RunnableWithMessageHistory(chain, self.get_session_history)
        config = {"configurable": {"session_id": f"{wa_id}"}}

        ai_output = with_message_history.invoke(
            [HumanMessage(content=f"{human_message}")],
            config=config,
        )
        
        return ai_output.content