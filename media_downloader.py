import os
import requests

class ImageDownloader:
    def __init__(self) -> None:
        self.ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
        self.PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]


    def get_media_url(self, media_id:str) -> str:
        url = f"https://graph.facebook.com/v22.0/{media_id}/"
        headers = {
            'Authorization': f'Bearer {self.ACCESS_TOKEN}'
        }
        data = {
            'messaging_product': 'WHATSAPP'
        }
        response = requests.get(url, headers=headers, data=data)
        response = response.json()
        media_url = response["url"]
        return media_url
    

    def download_image(self, media_id:str) -> None:
        media_url = self.get_media_url(media_id)
        headers = {
        'Authorization': f'Bearer {self.ACCESS_TOKEN}'
        }
        response = requests.get(media_url, headers=headers)

        my_path = os.path.dirname(__file__)
        with open(f"{my_path}/media/image.jpeg", "wb") as file:
            file.write(response.content)