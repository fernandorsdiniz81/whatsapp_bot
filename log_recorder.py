import os
import time

class LogRecorder:
    @staticmethod
    def timestamp_conversor(timestamp:str) -> str:
        my_time = time.localtime(int(timestamp))
        day = my_time.tm_mday
        month = my_time.tm_mon
        year = my_time.tm_year
        hour = my_time.tm_hour
        minute = my_time.tm_min
        second = my_time.tm_sec
        my_time = f"{day}/{month}/{year} {hour}h{minute}min{second}\"" # conversão do timestamp em tempo real
        return my_time
    

    def log_recorder(self, wa_id:str, human_message:dict, bot_message:dict) -> None:
            my_path = f"{os.path.dirname(__file__)}/log"
            name = human_message.get("name")
            human_time = LogRecorder.timestamp_conversor(human_message.get("timestamp"))
            human_message_text = human_message.get("message")
            bot_time = LogRecorder.timestamp_conversor(bot_message.get("timestamp"))
            bot_message_text = bot_message.get("message")

            with open(f"{my_path}/log_{name.split()[0]}_{wa_id[2:]}.txt", "a+") as file:
                dialog = f"{human_time}\n{name}:\n{human_message_text}\n\n{bot_time}\neu(bot):\n{bot_message_text}\n\n\n"
                file.write(dialog)

