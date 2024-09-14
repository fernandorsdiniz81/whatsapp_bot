import requests
import os
import time
from dotenv import load_dotenv
from ai_engine import AIEngine
from virtual_assistant import VirtualAssistant
import speech_recon



class Bot:
    def __init__(self, timeout:int=30) -> None:
        load_dotenv()
        self.ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
        self.APP_ID = os.environ["APP_ID"]
        self.APP_SECRET = os.environ["APP_SECRET"]
        self.VERSION = os.environ["VERSION"]
        self.PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]
        self.MY_NUMBER = os.environ["MY_NUMBER"]
        self.ON_OFF_COMMAND = os.environ["ON_OFF_COMMAND"]
        self.human_message = dict()
        self.bot_message = dict()
        self.bot_status = True
        self.bot_intelligence = AIEngine()
        self.virtual_assistant = VirtualAssistant()
        self.audio_downloader = speech_recon.AudioDownload()
        self.speech_recognition = speech_recon.SpeechRecognition()
    

    def normalize_recipient(self, recipient: str) -> str:
        if len(recipient) == 13:
            return recipient
        else:
            return recipient[0:4]+"9"+recipient[4:13]
        

    def send_template_message(self, recipient:str, template:str="hello_world") -> None:
        recipient = self.normalize_recipient(recipient)
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

        # print(response.status_code)
        # print(response.json())


    def send_message(self, recipient:str, text:str) -> int:
        recipient = self.normalize_recipient(recipient)
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

        # print(response.status_code)
        # print(response.json())

        return response.status_code


    def login(self, wa_id, text): # comando para ligar/desligar o bot
        if wa_id == self.MY_NUMBER and text == self.ON_OFF_COMMAND.lower():
            if self.bot_status is True:
                self.bot_status = False
            else:
                self.bot_status = True
            self.send_message(wa_id, "😴" if self.bot_status is False else "🤓")
            print(f"status do bot: {self.bot_status}")
        

    def read_message(self, response: dict) -> tuple:
        name = response["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
        wa_id = response["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
        timestamp = response["entry"][0]["changes"][0]["value"]["messages"][0]["timestamp"]
        message_id = response["entry"][0]["changes"][0]["value"]["messages"][0]["id"]
        message_type = response["entry"][0]["changes"][0]["value"]["messages"][0]["type"]

        if message_type == "text":
            text = response["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
            audio_id = None
        else:
            text = None
            audio_id = response["entry"][0]["changes"][0]["value"]["messages"][0]["audio"]["id"]

        question = text if audio_id is None else f'audio enviado (audio_id): {audio_id}'
        self.log_recorder(name, wa_id, timestamp, question, bot=False)
        print(f"\nmensagem de {name} ({wa_id}, {timestamp}):\n{question}\n")
        return name, wa_id, timestamp, message_id, text, audio_id


    def read_confirmation(self, message_id: str) -> None:
        url = f"https://graph.facebook.com/{self.VERSION}/{self.PHONE_NUMBER_ID}/messages"
        headers = {
            'Authorization': f'Bearer {self.ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }

        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        requests.post(url, headers=headers, json=data)


    def answer_text_message(self, name: str, wa_id: str, timestamp: str, message_id:str, text: str, specific_prompt=None) -> None:
        self.login(wa_id, text) # Verificação se houve comando para alterar o status do bot
        if self.bot_status is True and text != self.ON_OFF_COMMAND:
            self.read_confirmation(message_id)
            answer = self.virtual_assistant.user_question(name, wa_id, text)
            response_status_code = self.send_message(wa_id, answer)
            if response_status_code == 200:
                print(f"mensagem do bot ({timestamp}):\n{answer}\n")
                self.log_recorder(name, wa_id, timestamp, answer, bot=True)
            else:
                print(f"Falha no envio da mensagem: {response_status_code}")
    
    
    def answer_audio_message(self, name: str, wa_id: str, timestamp: str, message_id:str, audio_id:str) -> None:
        audio_path = self.audio_downloader.audio_download(audio_id)
        transcription = self.speech_recognition.speech_recognition(audio_path)
        self.log_recorder(name, wa_id, timestamp, f"Transcrição do áudio: {transcription}")
        self.answer_text_message(name, wa_id, timestamp, message_id, transcription)
        


    def log_recorder(self, name: str, wa_id: str, timestamp: str, message: str, bot: bool = False) -> None:
        my_time = time.localtime(int(timestamp))
        day = my_time.tm_mday
        month = my_time.tm_mon
        year = my_time.tm_year
        hour = my_time.tm_hour
        minute = my_time.tm_min
        second = my_time.tm_sec
        my_time = f"{day}/{month}/{year} {hour}h{minute}min{second}\"" # conversão do timestamp em tempo real

        with open(f"log/log_{name.split()[0]}_{wa_id[2:]}.txt", "a+") as file:
            if bot is False:
                dialog = f"{my_time}\n{name}({wa_id[2:]}):\n{message}\n\n"
            else:
                dialog = f"eu(bot):\n{message}\n\n\n"
            file.write(dialog)