import json
import os
import PySimpleGUI as sg
import requests
import time
from dotenv import load_dotenv
load_dotenv()

# https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#get-media-id

# Este módulo serve para gerir as mídias utilizadas para envio de respostas ao cliente.

class MediaUploader:
    def __init__(self) -> None:
        self.ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
        self.PHONE_NUMBER_ID = os.environ["PHONE_NUMBER_ID"]
        self.my_medias = dict()


    def upload_media(self, my_file:str, mime_type:str="audio/ogg") -> tuple:
        '''Upload a media and get its media_id.\n
        mime_type: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#supported-media-types\n
        ex.: "audio/ogg", "application/pdf", "image/jpeg", "image/webp"\n
        Max. size = 500KB'''
       
        file_size = os.path.getsize(my_file)
        file_name = my_file.split("/")[-1]

        if  file_size <= 500000: # Bytes
            with open(my_file, "rb") as file:
                url = f"https://graph.facebook.com/v20.0/{self.PHONE_NUMBER_ID}/media"
                headers = {
                    'Authorization': f'Bearer {self.ACCESS_TOKEN}'
                }
                files = {
                    'file': (file_name, file, mime_type)
                }
                data = {
                    'messaging_product': 'WHATSAPP'
                }
                response = requests.post(url, headers=headers, files=files, data=data)
            

        else:
            return f"Tamanho do arquivo excedido: {file_size} Bytes (máximo: 500KB)."
        
        if response.status_code == 200:
            response = response.json()
            short_file_name = file_name.split(".")[0]
            media_id = response.get("id")
            timestamp = round(time.time())
            self.my_medias[short_file_name] = {"file_name":file_name, "mime_type":mime_type, "media_id":media_id, "timestamp":timestamp}
            
            return f"Aquivo {file_name} enviado com sucesso!\nMedia ID: {media_id}"
        
        else:
            return f"Erro ao enviar a mídia: {response.status_code}"
            


class MediaManager:
    def __init__(self) -> None:
        pass


    def get_date(self, timestamp):
        today = time.localtime(int(timestamp))
        day = today.tm_mday
        month = today.tm_mon
        year = today.tm_year
        return f"{day}/{month}/{year}"


    def create_media_dictionary(self, medias:dict) -> None:
        # Caso já exista o arquivo "my_media_id.json", os dados salvos são carregados 
        # para que os dados novos sejam anexados.
        my_path = os.path.dirname(__file__)
        if "my_media_id.json" in os.listdir(my_path):
            with open(f"{my_path}/my_media_id.json", "r") as file:
                saved_medias = file.read()
                saved_medias = json.loads(saved_medias)
            
            for key, value in saved_medias.items():
                if key in medias.keys():
                    pass # dá preferência ao novo item vindo de "media", atualizando o item do json
                else:
                    medias[key] = value # insere os novos itens de "media" ao json

        data = json.dumps(medias, indent=4)

        with open(f"{my_path}/my_media_id.json", "w") as file:
            file.write(data)


    def read_media_dictionary(self):
        my_path = os.path.dirname(__file__)
        if "my_media_id.json" in os.listdir(my_path):
            with open(f"{my_path}/my_media_id.json", "r") as file:
                my_media_id = file.read()
                my_media_id = json.loads(my_media_id) # dict
                one_day = 86400 # seconds
                media_collection = str()
                
                for key in my_media_id.keys():
                    file_name = my_media_id[key].get("file_name")
                    mime_type = my_media_id[key].get("mime_type")
                    media_id = my_media_id[key].get("media_id")
                    timestamp = my_media_id[key].get("timestamp")
                    upload_date = self.get_date(timestamp)
                    expiration_date = 30 - round((time.time() - timestamp)//one_day)
                    
                    media_collection = media_collection + f'Arquivo: {file_name}\nMIME: {mime_type}\nMedia ID = {media_id}\nData de upload: {upload_date}\nValidade: {expiration_date} dias\n{"-"*60}\n'

                media_collection = media_collection + f"Total de mídias: {len(my_media_id)}"

            return media_collection

        else:
            return f"O Aquivo {my_path}/my_media_id.json não existe!"



class Interface:
    def __init__(self) -> None:
        self.media_manager = MediaManager()
        self.media_uploader = MediaUploader()


    def make_window(self):
        # themes = "SystemDefault SystemDefaultForReal SystemDefault1 LightBrown12 DarkGrey10 LightGreen4 Reddit DarkTeal11 DarkGrey7 DarkBlue LightBrown12".split()
        sg.theme("DarkBlue")
        
        layout = [
            [
                [sg.Multiline(key="console", size=(60,15), font='arial 12', auto_refresh=True)],
                [sg.Button("biblioteca", key="manage", visible=True, size=8), sg.Button("upload", key="upload", visible=True, size=8)
                ]
            ]
        ]

        window = sg.Window("Media Manager", layout, size=(350,350), resizable=False)
    
        return window
    

    def open_window(self):
        window = self.make_window()
        while True:
            event, values = window.read() # onde values é dict

            if event == sg.WIN_CLOSED:
                break
            
            elif event == "manage":
                media_dictionaty = self.media_manager.read_media_dictionary()
                window["console"].update(media_dictionaty)
                
            elif event == "upload":
                # Seleciona o arquivo de mídia:
                window["console"].update("")
                my_file = sg.popup_get_file('Selecione a media:', keep_on_top=True)
                mime_type = None

                # Seleciona o tipo de mídia (MIME) se um arquivo foi escolhido:
                if my_file is not None:
                    popup_layout = [
                        [sg.Radio("áudio .acc", "MIME_Types", key="audio/aac")], 
                        [sg.Radio("áudio .amr", "MIME_Types", key="audio/amr")], 
                        [sg.Radio("áudio .mp3", "MIME_Types", key="audio/mpeg")], 
                        [sg.Radio("áudio .m4a", "MIME_Types", key="audio/mp4")], 
                        [sg.Radio("áudio .ogg", "MIME_Types", key="audio/ogg")], 
                        [sg.Radio("documento .pdf", "MIME_Types", key="application/pdf")], 
                        [sg.Radio("figurinha .webp", "MIME_Types", key="image/webp")], 
                        [sg.Radio("imagem .jpeg", "MIME_Types", key="image/jpeg")], 
                        [sg.Radio("imagem .png", "MIME_Types", key="image/png")], 
                        [sg.Radio("vídeo .mp4", "MIME_Types", key="video/mp4")], 
                        [sg.Button("ok")]
                        ]
                    mime_window = sg.Window("MIME Type", popup_layout, size=(200,300))
                    while True:
                        event, values = mime_window.read() # onde values é do tipo dict
                        if event == sg.WIN_CLOSED:
                            window["console"].update("Você fechou a janela sem escolher o tipo de mídia!")
                            break
                        elif event == "ok":
                            for key, value in values.items():
                                if value is True:
                                    mime_type = key
                                    mime_window.close()
                                    print(mime_type)
                            break

                    # Faz upload da mídia:
                    if my_file is not None and mime_type is not None:
                        window["console"].update(self.media_uploader.upload_media(my_file, mime_type))
                        self.media_manager.create_media_dictionary(self.media_uploader.my_medias)

        window.close()



app = Interface()
app.open_window()