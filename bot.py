import os
import re
import requests
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
        self.human_message = dict()
        self.bot_message = dict()
        self.bot_status = True
        self.bot_intelligence = AIEngine()
        self.virtual_assistant = VirtualAssistant()
        self.audio_downloader = speech_recon.AudioDownload()
        self.speech_recognition = speech_recon.SpeechRecognition()
        self.log_recorder = log_recorder.LogRecorder()
    

    def normalize_recipient(self, recipient: str) -> str:
        '''Alguns wa_id do Brasil possuem o "9" na frente, outros não. Recebe-se mensagem de qualquer um deles, mas para envio, devemos utilizar o número completo.'''
        br_wa_id_pattern = r"^55\d{2}9\d{8}$"
        if re.fullmatch(br_wa_id_pattern, recipient):
            return recipient
        else:
            normalized_recipient = recipient[0:4]+"9"+recipient[4:13]
            return normalized_recipient
        

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

        return response.status_code
        

    def send_message(self, data) -> int:
        '''https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages/'''
        
        url = f"https://graph.facebook.com/{self.VERSION}/{self.PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = data

        response = requests.post(url, headers=headers, json=data)
        return response.status_code


    def login(self, wa_id:str, text:str) -> None: # comando para ligar/desligar o bot
        if wa_id == self.MY_NUMBER and text.lower() == self.ON_OFF_COMMAND.lower():
            if self.bot_status is True:
                self.bot_status = False
                emoji = "😴"
            else:
                self.bot_status = True
                emoji = "🤓"
            data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": wa_id,
                    "type": "text",
                    "text": {
                    "body": emoji
                    }
                }
            self.send_message(data)
            print(f"status do bot: {self.bot_status}")
        

    def read_message(self, response: dict, name=None, wa_id=None, timestamp=None, message_id=None, message_type=None, text=None, audio_id=None) -> tuple:
        # As variáveis name, wa_id, timestamp, message_id, message_type, text e audio_id são atribuídas 
        # como "None" por padrão, porque o Flask requer um retorno HTTP válido e um erro ocorreria
        # a depender do tipo de mensagem (image, text, audio, etc...)
        name = str(response["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"])
        wa_id = str(response["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"])
        timestamp = str(response["entry"][0]["changes"][0]["value"]["messages"][0]["timestamp"])
        message_id = str(response["entry"][0]["changes"][0]["value"]["messages"][0]["id"])
        message_type = str(response["entry"][0]["changes"][0]["value"]["messages"][0]["type"])

        if message_type == "text":
            text = response["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
            audio_id = None
        elif message_type == "audio":
            text = f"Áudio: {audio_id}"
            audio_id = response["entry"][0]["changes"][0]["value"]["messages"][0]["audio"]["id"]

        # Algumas normalizações:
        name = name.split(" ")[0] # chamar o cliente apelas pelo primeiro nome é mais natural
        wa_id = self.normalize_recipient(wa_id) # acrescenta o "9" caso necessário

        self.human_message[wa_id] = {"name":name, "timestamp":timestamp, "message":text}

        print(f"\nmensagem de {name} ({wa_id}):\n{text}\n")
        
        return name, wa_id, timestamp, message_id, message_type, text, audio_id


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
            if answer[:8] == "location".lower():
                self.send_location(wa_id)
                return
            elif answer[:6].lower() == "thanks":
                self.send_media(wa_id, "sticker", "1612991982960989")
                return
            else:
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": wa_id,
                    "type": "text",
                    "text": {
                    "body": f"_{answer}_" # itálico
                    }
                }

            response_status_code = self.send_message(data)
            
            if response_status_code == 200:
                timestamp = round(time.time())
                self.bot_message[wa_id] = {"timestamp":timestamp, "message":answer}
                self.log_recorder.log_recorder(wa_id, self.human_message[wa_id], self.bot_message[wa_id])
                print(f"mensagem do bot:\n{answer}\n")
            else:
                print(f"Falha no envio da mensagem para {wa_id}: {response_status_code}")
    
    
    def answer_audio_message(self, name: str, wa_id: str, timestamp: str, message_id:str, audio_id:str) -> None:
        audio_path = self.audio_downloader.audio_download(audio_id)
        transcription = self.speech_recognition.speech_recognition(audio_path)
        self.human_message[wa_id]["message"] = f"Transcrição do audio {audio_id}: {transcription}"
        prompt = "Transcrição do áudio do cliente, utilizando o Whisper (em caso de dúvida, solicite gentilmente ao cliente para digitar ao invés de enviar áudio): "
        self.answer_text_message(name, wa_id, timestamp, message_id, prompt+transcription)


    def send_media(self, wa_id:str, msg_type:str, media_id:str) -> None:
        '''https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages/#media-object\n
        Exemplos de msg_type: "audio", "document", "image", "sticker", "video")'''
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": wa_id,
            "type": msg_type,
            msg_type: {
            "id": media_id
            }
        }

        response_status_code = self.send_message(data)

        if response_status_code == 200:
            timestamp = round(time.time())
            self.bot_message[wa_id] = {"timestamp":timestamp, "message":msg_type}
            self.log_recorder.log_recorder(wa_id, self.human_message[wa_id], self.bot_message[wa_id])
            print(f"mensagem do bot ({timestamp}):\n{msg_type}\n")
        else:
            print(f"Falha no envio da mensagem: {response_status_code}")


    def send_location(self, wa_id:str):
        '''https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages/#location-messages'''
        
        data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": wa_id,
                "type": "text",
                "text": {
                "body": "Vou enviar a localização:"
                }
            }
        
        self.send_message(data)
        
        data = {
            "messaging_product": "whatsapp",
            "to": wa_id,
            "type": "location",
            "location": {
                "longitude": "-44.2022776194688", 
                "latitude": "-19.958501126246528",
                "name": "Rua Francisco Ricardo da Silva 781A, Angola Betim",
                "address": "Oficina Sonhar"
                }
            }
        
        response_status_code = self.send_message(data)
        
        if response_status_code == 200:
            timestamp = round(time.time())
            self.bot_message[wa_id] = {"timestamp":timestamp, "message":"Localização"}
            self.log_recorder.log_recorder(wa_id, self.human_message[wa_id], self.bot_message[wa_id])
            print(f"mensagem do bot ({timestamp}):\nLocalização\n")
        else:
            print(f"Falha no envio da mensagem: {response_status_code}")


#### TESTE ####
# bot = Bot()
# wa_id = "5531920016652"
# # media_id = "795107592832128" #robozinho
# # msg_type = "image"
# # media_id = "512747994877905" # sticker dog
# media_id = "476103735405941" # sticker valeu
# msg_type = "sticker"
# teste.send_media(wa_id, msg_type, media_id)

# data = {
#     "messaging_product": "whatsapp",
#     "recipient_type": "individual",
#     "to": wa_id,
#     "type": "text",
#     "text": {
#     "body": "_Desculpe, mas só entendo texto e áudio... não entendo imagens (ainda)!_" # itálico
#     }
# }
# bot.send_message(data)