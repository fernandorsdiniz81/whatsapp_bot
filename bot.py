import requests
import os
import time
from dotenv import load_dotenv
from ai_engine import AIEngine
from virtual_assistant import VirtualAssistant
import speech_recon
import log_recorder


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
        self.ELEVEN_KEY = os.environ["ELEVEN_KEY"]
        self.human_message = dict()
        self.bot_message = dict()
        self.bot_status = True
        self.bot_intelligence = AIEngine()
        self.virtual_assistant = VirtualAssistant()
        self.audio_downloader = speech_recon.AudioDownload()
        self.speech_recognition = speech_recon.SpeechRecognition()
        self.log_recorder = log_recorder.LogRecorder()
    

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


    def login(self, wa_id:str, text:str) -> None: # comando para ligar/desligar o bot
        if wa_id == self.MY_NUMBER and text.lower() == self.ON_OFF_COMMAND.lower():
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

        message = text #if audio_id is None else audio_id
        
        self.human_message[wa_id] = {"name":name, "timestamp":timestamp, "message":message}

        print(f"\nmensagem de {name} ({wa_id}), {timestamp}):\n{message}\n")
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
        if self.bot_status is True and text != self.ON_OFF_COMMAND: # Além do status do bot, verifico se o texto não é o ON_OFF_COMMAND para evitar respostas desnecessárias quando o bot é ligado.
            self.read_confirmation(message_id)
            answer = self.virtual_assistant.user_question(name, wa_id, text)
            response_status_code = self.send_message(wa_id, f"_{answer}_")
            if response_status_code == 200:
                timestamp = round(time.time())
                print(f"mensagem do bot ({timestamp}):\n{answer}\n")
                
                self.bot_message[wa_id] = {"timestamp":timestamp, "message":answer}
                self.log_recorder.log_recorder(wa_id, self.human_message[wa_id], self.bot_message[wa_id])

            else:
                print(f"Falha no envio da mensagem: {response_status_code}")
    
    
    def answer_audio_message(self, name: str, wa_id: str, timestamp: str, message_id:str, audio_id:str) -> None:
        audio_path = self.audio_downloader.audio_download(audio_id)
        transcription = self.speech_recognition.speech_recognition(audio_path)
        self.human_message[wa_id]["message"] = f"Transcrição do audio {audio_id}: {transcription}"
        self.answer_text_message(name, wa_id, timestamp, message_id, transcription)
        

    def text_to_speech(self, wa_id:str, timestamp:str, text:str) -> None:
        VOICE_ID = "EXAVITQu4vr4xnSDxMaL" # Vozes disponíveis: https://api.elevenlabs.io/v1/voices
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

        headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": self.ELEVEN_KEY
        }

        data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
        }

        response = requests.post(url, json=data, headers=headers)
        with open(f"audio/answer_{wa_id}_{timestamp}.mp3", "wb") as audio_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    audio_file.write(chunk)

