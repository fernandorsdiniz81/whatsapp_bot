import os
import requests
from dotenv import load_dotenv


class AudioGen:
    def __init__(self) -> None:
        load_dotenv()
        self.ELEVEN_KEY = os.environ["ELEVEN_KEY"]
    
    
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