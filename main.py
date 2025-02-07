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

    if not response:
        return jsonify({"error": "Nenhum dado recebido"}), 400

    if "contacts" in response["entry"][0]["changes"][0]["value"].keys(): # Será "True", caso response seja a mensagem do usuário e não da máquina
            bot.read_message(response)
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