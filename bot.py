# WhatsApp com uso da API oficial

import requests
import os
from dotenv import load_dotenv
from ai_engine import AIEngine
from virtual_assistant import VirtualAssistant



class Bot:
    def __init__(self, timeout:int=30) -> None:
        load_dotenv()
        self.ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
        self.APP_ID = os.environ["APP_ID"]
        self.APP_SECRET = os.environ["APP_SECRET"]
        self.VERSION = os.environ["VERSION"]
        self.PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]
        self.COMMAND = os.environ["COMMAND"]
        self.bot_status = True
        self.bot_intelligence = AIEngine()
        self.virtual_assistant = VirtualAssistant()
    

    def send_template_message(self, recipient:str, template:str="hello_world") -> None:
        url = f"https://graph.facebook.com/{self.VERSION}/{self.PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template,
                "language": {
                    "code": "en_US"
                }
            }
        }
      
        response = requests.post(url, headers=headers, json=data)

        print(response.status_code)
        print(response.json())


    def send_message(self, recipient:str, text:str) -> int:
        url = f"https://graph.facebook.com/{self.VERSION}/{self.PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {
            "body": text
            }
        }

        response = requests.post(url, headers=headers, json=data)

        print(response.status_code)
        print(response.json())

        return response.status_code


    def read_message(self, response: dict) -> tuple:
        name = response["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
        wa_id = response["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
        timestamp = response["entry"][0]["changes"][0]["value"]["messages"][0]["timestamp"]
        text = response["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
        print(f"\nmensagem de {name} ({wa_id}, {timestamp}):\n{text}\n")
        return name, wa_id, timestamp, text


    def login(self, text): # Serve para ligar/desligar o bot
        if text == self.COMMAND.lower():
            if self.bot_status == True:
                self.bot_status = False
            else:
                self.bot_status = True
        print(self.bot_status)

     
    def answer_message(self, name: str, wa_id: str, timestamp: str, text: str) -> None:
        self.login(text)
        if self.bot_status == True and text != self.COMMAND:
            answer = self.virtual_assistant.user_question(name, wa_id, text)
            response = self.send_message(wa_id, answer)
            if response == 200:
                print(f"mensagem do bot ({timestamp}):\n{answer}\n")
            else:
                print(f"Falha no envio da mensagem: {response}")
    

    def log_record():
        pass


# Enviando mensagem template para meus números:        
# bot = Bot()
# recipients = ["5531987772280", "5531920016652"]
# for recipient in recipients:
#     # bot.send_template_message(recipient)
