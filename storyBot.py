import telebot
import requests
import time
import schedule
import threading
import json
from datetime import datetime, timedelta

chat_id = -1001908568841
token = '12345'
bot = telebot.TeleBot(token)

users_data = {}
email_to_user_id = {}
user_email = None
# user_id = 967700724

# https://get.storytellers.online/teach/control/stream/view/id/289894537

account_name = "storytellersonline"
secret_key = "HWVx4LHIRMXTAEPcWV0FzOQrWA8Ya5T7xJrv6F5WrjDFqVsNVRmfxU7sa5dvIeLBQ3Ll6WwiHKjobP7EhP3rMUJpxXfmK5ICwvHLkk0VWtGdvndpDR35lY2rnkaPJWH4"
url = f'https://{account_name}.getcourse.ru/pl/api/account/users?key={secret_key}&created_at[from]=2023-04-10'

message_start = """Здравствуйте! Введите, пожалуйста, ваш <b>электронный адрес</b>,
по которому вы оплатили <b>Storytellers club</b>. Это нужно, чтобы проверить ваш доступ."""
message_start = message_start.replace('\n', ' ')

message_validate = 'Пожалуйста, введите корректный адрес <b>электронной почты.</b>'

message_check = """Спасибо! Сейчас бот проверит данные. Если все хорошо, то через некоторое
время вам придет сообщение со ссылкой на закрытый канал <b>Storytellers club.</b>"""
message_check = message_check.replace('\n', ' ')

channel_link = 'https://t.me/+G9AipGy58Mk2ZjRi'
message_welcome = f"""Спасибо за ожидание! Мы рады приветствовать вас в канале <b>Storytellers Club.</b>
Чтобы присоединиться к каналу, пожалуйста, перейдите по ссылке: {channel_link}"""
message_welcome = message_welcome.replace('\n', ' ')

message_not_found = 'К сожалению, <b>ваша почта</b> не найдена в списке актуальных плательщиков <b>Storytellers Club.</b>'
# Возможные причины:
# 1. На текущий момент у вас нет действующей подписки Storytellers Club
# 2. Проверьте написание вашей почты и отправьте исправленный вариант
# 3. Если вы уверены, что у вас есть действующая оплаченная подписка, пожалуйста, напишите в нашу службу поддержки @teamstorytellers
message_warning = """Добрый день! Через день у вас истекает доступ к закрытому клубу <b>Storytellers Club.</b> 
                    Чтобы продлить участие, пожалуйста, оплатите подписку на Геткурс, 
                    иначе бот автоматически исключит вас из канала"""

message_kick = """Добрый день! Вы были были автоматически исключены из канала <b>Storytellers Club</b>
                  в связи с истечением срока действия подписки. 
                  Чтобы повторно присоединиться к каналу, пожалуйста, продлите подписку
                  и отправьте свою почту в данный бот."""


# Функция для запуска бота
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in users_data or not users_data[user_id]['isStarted']:
        users_data[user_id] = {'isStarted': True}
        bot.send_message(message.chat.id, message_start, parse_mode='html')
    else:
        check_email_and_save(message)


# Функция для проверки email и сохранения словаря email_to_user_id, который сохраняет данные пользователя { почта: telegram_id }
@bot.message_handler(content_types=['text'])
def check_email_and_save(message):
    if "@" in message.text:
        bot.send_message(message.chat.id, message_check, parse_mode='html')
        
        if data_saved:
            user_email = check_email_match_saved(data_saved, message.text)
            if user_email:
                email_to_user_id[user_email] = message.from_user.id
                save_email_to_user_id(email_to_user_id)
                bot.send_message(message.chat.id, message_welcome, parse_mode='html')
        else:
            export_id = get_export_id()
            if export_id:
                url_2 = f'https://{account_name}.getcourse.ru/pl/api/account/exports/{export_id}?key={secret_key}'
                data = get_data_from_api(url_2)
                if data:
                    user_email = check_email_match(data, message.text)
                    if user_email:
                        email_to_user_id[user_email] = message.from_user.id
                        save_email_to_user_id(email_to_user_id)
                        bot.send_message(message.chat.id, message_welcome, parse_mode='html')
                    else:
                        bot.send_message(message.chat.id, message_not_found, parse_mode='html')
    else:
        bot.send_message(message.chat.id, message_validate, parse_mode='html')


# Функция для получения export_id из API
def get_export_id():
    try:
        response = requests.get(url, verify=True)
        if response.ok:
            response_json = response.json()
            if "export_id" in response_json["info"]:
                return response_json["info"]["export_id"]
            else:
                print('Ошибка при получении экспорта')
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print('Ошибка запроса на формирование export_id: ' + str(e))
    return None


# Функция для получения потока данных в формате JSON
def get_data_from_api(url_2):
    while True:
        time.sleep(3)
        try:
            response = requests.get(url_2, verify=True)
            if response.ok:
                data = response.json()
                if data['success']:
                    return data
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print('Ошибка запроса на получение данных из API: ' + str(e))


# Функция для проверки email на совпадение с myEmail
def check_email_match(data, email):
    try:
        for item in data['info']['items']:
            if item[1].lower() == email.lower():
                return item[1].lower()
        return None
    except KeyError as e:
        print('Ошибка при проверке email на совпадение: ' + str(e))
    return None

# Функция для проверки email на совпадение с myEmail
def check_email_match_saved(data_saved, email):
    try:
        for item in data_saved['info']['items']:
            if item[1].lower() == email.lower():
                return item[1].lower()
        return None
    except KeyError as e:
        print('Ошибка при проверке email на совпадение: ' + str(e))
    return None


# Функция для сохранения email_to_user_id в файле
def save_email_to_user_id(email_to_user_id):
    try:
        with open('email_to_user_id.json', 'w') as export_file:
            json.dump(email_to_user_id, export_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print('Ошибка при сохранении email_to_user_id: ' + str(e))


# Функция для ежедневной проверки даты подписок участников 
def daily_date_check():
    try:
        export_id = get_export_id()
        if export_id:
                url_2 = f'https://{account_name}.getcourse.ru/pl/api/account/exports/{export_id}?key={secret_key}'
                data = get_data_from_api(url_2)
                if data["success"]:
                    # Сохраняем JSON в файл
                    with open('export.json', 'w') as outfile:
                        json.dump(data, outfile, indent=4)
                        print("Экспорт пользователей успешно сохранен в файле export.json")
                    
                    # Читаем сохраненный JSON
                    with open('export.json', 'r') as infile:
                        data = json.load(infile)
                        print("читаем пока норм")
                        
                        # Читаем столбец с датой истечения подписки
                        for item in data['info']['items']:
                            # Извлекаем дату из поля 'date' и преобразуем в объект datetime
                            date_str = item[2]  # предполагаем, что дата хранится в третьем элементе
                            date = datetime.strptime(date_str, '%Y-%m-%d')

                            # Сравниваем дату с текущей датой
                            today = datetime.now().date()
                            email_kick = ''
                            # Если дата окончания подписки на 1 день больше текущей даты, то...
                            if date == today + timedelta(days=1):
                                email_kick = item[1]
                                # ищем user_id человека у которого истекает подписка 
                                if email_kick in email_to_user_id:
                                    user_id = email_to_user_id[email_kick]
                                    print('внимание')
                                    # тут ЧЕКНУТЬ id найденного человека
                                    bot.send_message(user_id, message_warning, parse_mode='html')
                                    
                                    timer_finished = False
                                    def set_timer_finished(value):
                                        global timer_finished
                                        timer_finished = value
                                        
                                    timer = threading.Timer(24 * 60 * 60, lambda: set_timer_finished(True))
                                    timer.start()
                                    # Запускаем бесконечный цикл
                                    while True:
                                        # Выполняем какую-то работу
                                        time.sleep(1)
                                        if timer_finished:
                                            # Проводим финальную проверку и вызываем функцию kick_unban() при необходимости
                                            if some_condition:
                                                kick_unban(user_id)
                                            break
                                        
                                else:
                                    print(f'Не найден user_id пользователя {email_kick}')

                            

        else:
            print("Ошибка при получении экспорта")
    except requests.exceptions.RequestException as e:
        print(e)


# Функция для исключения пользователей с канала и последущим их разбаном
def kick_unban(user_id):
    kick_url = f'https://api.telegram.org/bot{token}/kickChatMember'
    kick_params = {"chat_id": chat_id, "user_id": user_id}
    kick_response = requests.post(kick_url, data=kick_params)
    if not kick_response.ok:
        print("Failed to kick user from the channel")
    else:
        unban_url = f"https://api.telegram.org/bot{token}/unbanChatMember"
        unban_params = {"chat_id": chat_id, "user_id": user_id}
        unban_response = requests.post(unban_url, data=kick_params)
        bot.send_message(user_id, message_kick, parse_mode='html')
    if not unban_response.ok:
        print("Failed to unban user from the channel")

# Запускаем функцию сразу после запуска скрипта
daily_date_check()

# Запускаем задание, которое будет вызывать функцию каждые 12 часов
schedule.every(12).hours.do(daily_date_check)

# Бесконечный цикл, который позволяет заданию выполняться
while True:
    schedule.run_pending()
    time.sleep(1)



bot.polling(none_stop = True)






# @bot.message_handler(commands=['reset'])
# def reset(message):
#     user_id = message.from_user.id
#     if user_id in users_data:
#         del users_data[user_id]
#         bot.send_message(message.chat.id, "Ваши данные были удалены из базы данных бота. Теперь вы можете ввести свой адрес электронной почты заново.")
#     else:
#         bot.send_message(message.chat.id, "У вас нет сохраненных данных.")































