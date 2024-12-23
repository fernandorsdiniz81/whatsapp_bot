from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from bot import Bot


bot = Bot()

app = Flask(__name__)

# Rota para configurar o webhook
@app.route('/', methods=['GET'])
def verify():
    # Obter os parâmetros da query string
    load_dotenv()
    VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    # Verificar se o token e o modo estão corretos
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        # Retornar o desafio para a Meta
        print("Sucesso", challenge, 200)
        return challenge, 200
    else:
        # Se o token não corresponde ou o modo está errado, retornar 403 Forbidden
        print("Verificação falhou", 403)
        return 403


# Rota para receber os dados do webhook
@app.route('/', methods=['POST'])

def webhook():
    response = request.get_json()

    print(f"\nResponse:\n{response}\n\n")
    
    if not response:
        return jsonify({"error": "Nenhum dado recebido"}), 400

    if "contacts" in response["entry"][0]["changes"][0]["value"].keys(): # Será "True", caso response seja a mensagem do usuário e não da máquina
        name, wa_id, timestamp, message_id, message_type, text, audio_id = bot.read_message(response)
        
        print(f"\n\nmessage_type: {message_type}\n\n")
        
        if message_type == "text":
            bot.answer_text_message(name, wa_id, timestamp, message_id, text)
        elif message_type == "audio":
            bot.answer_audio_message(name, wa_id, timestamp, message_id, audio_id)
        else: # somente áudio e texto são processados
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": wa_id,
                "type": "text",
                "text": {
                "body": "_Desculpe, mas só entendo texto e áudio... não entendo imagens!_" # itálico
                }
            }
            bot.send_message(data)

        return jsonify({"status": "sucesso", "response": response}), 200

    else:
        return jsonify({"status": "ignorado", "message": "Requisição sem 'contacts' no payload"}), 200


if __name__ == "__main__":
    my_path = os.path.dirname(__file__) 
    folders = os.listdir(my_path)
    if "media" not in folders:
        os.mkdir(f"{my_path}/media")
    if "log" not in folders:
        os.mkdir(f"{my_path}/log")

    app.run(host='0.0.0.0', port=5000, debug=True)