# https://openai.com/index/whisper/
# https://github.com/openai/whisper
# https://www.youtube.com/watch?v=OEPkmsJmY2I&ab_channel=HashtagPrograma%C3%A7%C3%A3o

from dotenv import load_dotenv
import os
import requests
import whisper


class AudioDownload:
    def __init__(self) -> None:
        load_dotenv()
        self.ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]


    def audio_download(self, audio_id: str) -> str:
        """Baixa o audio identificado por 'audio_id' e retorna o path do arquivo."""
        
        url = f"https://graph.facebook.com/v20.0/{str(audio_id)}"
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}"
        }

        response = requests.get(url, headers=headers) # Retorna um json, com uma chave "url" do áudio.
        audio_data = response.json()

        if response.status_code == 200:
            audio_url = audio_data.get("url")
            response = requests.get(audio_url, headers=headers)
            
            if response.status_code == 200:
                audio = response.content

            my_path = f"{os.path.dirname(__file__)}/media"
            
            with open(f"{my_path}/audio_{audio_id}.ogg", "wb") as file:
                file.write(audio)

            audio_path = f"{my_path}/audio_{audio_id}.ogg"
            
            if f"audio_{audio_id}.ogg" in os.listdir(my_path):
                return audio_path

        else:
            print(f"Erro ao buscar o áudio: {response.status_code}")

    
    
class SpeechRecognition:
    def speech_recognition(self, audio_path: str) -> str:
        audio = audio_path
        model = whisper.load_model("tiny")
        result = model.transcribe(audio)
        transcription = result["text"]
        return transcription
    

# file = "WhatsApp Audio 2024-11-19 at 08.15.20.ogg"
# path = f"{os.path.dirname(__file__)}/media/{file}"
# teste = SpeechRecognition()
# transcricao = teste.speech_recognition(path)
# print(transcricao)

