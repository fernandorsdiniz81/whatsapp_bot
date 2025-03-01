import os
import re
import requests
import time
import budget_recorder
import log_recorder
import speech_recon
from dotenv import load_dotenv
from media_downloader import ImageDownloader
from gemini_engine import AIEngine
from virtual_assistant import VirtualAssistant


class Bot:
    def __init__(self) -> None:
        load_dotenv()
        self.ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
        self.APP_ID = os.environ.get("APP_ID")
        self.APP_SECRET = os.environ.get("APP_SECRET")
        self.VERSION = os.environ.get("VERSION")
        self.PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
        self.MY_NUMBER = os.environ.get("MY_NUMBER")
        self.ON_OFF_COMMAND = os.environ.get("ON_OFF_COMMAND")
        self.human_message = dict()
        self.bot_message = dict()
        self.budget_requests = dict()
        self.bot_status = True
        self.bot_intelligence = AIEngine()
        self.virtual_assistant = VirtualAssistant()
        self.image_downloader = ImageDownloader()
        self.audio_downloader = speech_recon.AudioDownload()
        self.speech_recognition = speech_recon.SpeechRecognition()
        self.log_recorder = log_recorder.LogRecorder()
        self.budget_recorder = budget_recorder.BudgetRecorder()
    
    

    def read_message(self, response: dict, name=None, wa_id=None, timestamp=None, message_id=None, message_type=None, text=None, audio_id=None, media_id=None) -> tuple:
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
        elif message_type == "image":
            media_id = response["entry"][0]["changes"][0]["value"]["messages"][0]["image"]["id"]

        # Algumas normalizações:
        name = name.split(" ")[0] # chamar o cliente apelas pelo primeiro nome é mais natural
        wa_id = self.normalize_recipient(wa_id) # acrescenta o primeiro "9" caso necessário

        self.human_message[wa_id] = {"name":name, "timestamp":timestamp, "message":text}

        print(f"\nmensagem de {name} ({wa_id}):\n{text}\n")
        print(f"\n\nmessage_type: {message_type}\n\n")
        
        # ações condizentes com cada tipo de mensagem:
        if message_type == "text":
            self.answer_text_message(name, wa_id, timestamp, message_id, text)
        elif message_type == "audio":
            self.answer_audio_message(name, wa_id, timestamp, message_id, audio_id)
        elif message_type == "image":
            self.answer_image_message(name, wa_id, timestamp, message_id, media_id)
        else: # somente áudio, texto e imagens são processados, para os demais tipos, uma resposta de erro
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": wa_id,
                "type": "text",
                "text": {
                "body": "_Desculpe, mas só entendo texto, áudio e imagens..._" # itálico
                }
            }
            print(f"\nResponse:\n{response}\n\n")

            self.send_message(data)

        return name, wa_id, timestamp, message_id, message_type, text, audio_id, media_id
    

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


    def answer_text_message(self, name: str, wa_id: str, timestamp: str, message_id:str, text: str) -> None:
        self.login(wa_id, text) # Verificação se houve comando para alterar o status do bot
        if self.bot_status is True and text != self.ON_OFF_COMMAND: # Além do status do bot, verifico se o texto não é o ON_OFF_COMMAND para evitar respostas desnecessárias quando o bot é ligado.
            self.read_confirmation(message_id)
            answer = self.virtual_assistant.user_question(name, wa_id, text)
            if "location".lower() in answer:
                self.send_location(wa_id)
                return
            
            elif "thanks".lower() in answer:
                try:
                    self.send_media(wa_id, "sticker", "1612991982960989") # media_id vale por 30 dias
                except:
                    pass
                return
            
            # elif "budget".lower() in answer:
            #     self.budget_recorder.budget_recorder(wa_id,)
            #     self.send_message()
            #     data = {
            #         "messaging_product": "whatsapp",
            #         "recipient_type": "individual",
            #         "to": wa_id,
            #         "type": "text",
            #         "text": {
            #         "body": f"_Seu pedido de orçamento foi registrado! Em breve te responderei!_ 😉" # itálico
            #         }
            #     }
            
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
        prompt = "Transcrição do áudio do cliente, utilizando o Whisper (em caso de dúvida, solicite gentilmente ao cliente para digitar ao invés de enviar áudio). "
        self.answer_text_message(name, wa_id, timestamp, message_id, prompt+transcription)


    def answer_image_message(self, name: str, wa_id: str, timestamp: str, message_id:str, media_id:str) -> None:
        print("midia_id:", media_id)
        self.image_downloader.download_image(media_id) # salva a imagem recebida em /media/image.jpeg
        answer = self.virtual_assistant.user_image(name, wa_id)
        self.human_message[wa_id]["message"] = f"Descrição da imagem: {answer}. "
        self.answer_text_message(name, wa_id, timestamp, message_id, answer)

        
    def send_media(self, wa_id:str, msg_type:str, media_id:str) -> None:
        '''https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages/#media-object\n
        Exemplos de msg_type: "audio", "document", "image", "sticker", "video")
        Este método envia mensagems com mídia para o cliente.'''
        
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
                "longitude": os.environ.get("LONGITUDE"), 
                "latitude": os.environ.get("LATITUDE"),
                "name": os.environ.get("NAME"),
                "address": os.environ.get("ADDRESS")
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

########### TESTE:
# teste = Bot()
# data = {
#         "messaging_product": "whatsapp",
#         "recipient_type": "individual",
#         "to": "5531920016652",
#         "type": "text",
#         "text": {
#         "body": "Teste!!"
#         }
#     }
# teste.send_message(data)