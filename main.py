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
        print(challenge, 200)
        return challenge, 200
    else:
        # Se o token não corresponde ou o modo está errado, retornar 403 Forbidden
        print("Verificação falhou", 403)
        return "Verificação falhou", 403


# Rota para receber os dados do webhook
@app.route('/', methods=['POST'])
def webhook():
    response = request.get_json()
    if not response:
        return jsonify({"error": "Nenhum dado recebido"}), 400
    
    try:
        name, wa_id, timestamp, text = bot.read_message(response)
        bot.answer_message(name, wa_id, timestamp, text)
    except:
        pass

    return jsonify({"status": "sucesso", "response": response}), 200





if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)