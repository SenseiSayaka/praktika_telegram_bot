import telebot
from telebot import types
import google.generativeai as genai
import re
import logging
import psycopg2

# Инициализация логирования
logging.basicConfig(filename='bot.log', level=logging.INFO, format='[%(asctime)s] - %(levelname)s - %(message)s')

# Инициализация бота
bot = telebot.TeleBot('7063155279:AAGziL92beb3kqPJQ3dE85ypqutqXAKXbgY')

# Настройка генеративной модели AI
genai.configure(api_key="AIzaSyAzbNtz8KX_xC_kwnvFwFxtX8paenVXa2I")
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest", generation_config=generation_config,
                              safety_settings=safety_settings)
convo = model.start_chat(history=[])

# Подключение к базе данных PostgreSQL
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='21099314422',
    host='127.0.0.1',
    port='5432'
)
cursor = conn.cursor()

# Создание таблицы users, если её не существует
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL
)
""")
conn.commit()

# Словарь для отслеживания состояния пользователя
user_state = {}


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Пожалуйста, введите ваш логин:')
    user_state[message.chat.id] = {'state': 'awaiting_login'}


# Обработчик всех текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.chat.id not in user_state:
        bot.send_message(message.chat.id, 'Введите команду /start для начала.')
        return

    state = user_state[message.chat.id]['state']

    if state == 'awaiting_login':
        user_state[message.chat.id] = {'state': 'awaiting_password', 'login': message.text}
        bot.send_message(message.chat.id, 'Пожалуйста, введите ваш пароль:')

    elif state == 'awaiting_password':
        login = user_state[message.chat.id]['login']
        password = message.text

        # Проверка логина и пароля в базе данных
        cursor.execute("SELECT * FROM users WHERE login=%s AND password=%s", (login, password))
        user = cursor.fetchone()

        if user:
            bot.send_message(message.chat.id, 'Успешный вход! Можете использовать команды /info и /prt.')
            user_state[message.chat.id] = {'state': 'authenticated'}
        else:
            bot.send_message(message.chat.id, 'Неверный логин или пароль. Попробуйте снова.')
            user_state[message.chat.id] = {'state': 'awaiting_login'}

    elif state == 'authenticated':
        if message.text.startswith('/info'):
            info(message)
        elif message.text.startswith('/prt'):
            code_prompt(message)
        else:
            bot.send_message(message.chat.id, 'Неизвестная команда. Используйте /info или /prt.')


# Обработчик команды /info
@bot.message_handler(commands=['info'])
def info(message):
    if user_state.get(message.chat.id) == {'state': 'authenticated'}:
        bot.send_message(message.chat.id,
                         'Gemini 1.5 Pro - это мощная языковая модель, разработанная исследовательским подразделением Google Brain. Она может обрабатывать до 1 миллиона токенов, генерировать тексты, обрабатывать большой объем данных, распознавать изображения и видео')

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text='Узнать больше', url='https://deepmind.google/technologies/gemini/')
        markup.add(btn1)
        bot.send_message(message.from_user.id, "По кнопке ниже можно перейти на сайт Google DeepMind",
                         reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Введите команду /start для начала.')


# Функция для форматирования ответов
def format_response(response):
    # Проверка на URL
    if re.match(r"https?://", response):
        return f'[{response}]({response})'
    # Проверка на код
    if response.startswith("```") and response.endswith("```"):
        return response
    return response


# Обработчик команды /prt
@bot.message_handler(commands=['prt'], content_types=['text'])
def code_prompt(message):
    if user_state.get(message.chat.id) == {'state': 'authenticated'}:
        logging.info(
            f"Пользователь ({message.from_user.username or message.from_user.first_name or message.from_user.id}): {message.text}")

        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id, 'Подождите, Gemini думает...')
        
        convo.send_message(message.text)
        response = convo.last.text

        # Логирование сырого ответа для отладки
        logging.info(f"Сырой ответ модели: {response}")

        formatted_response = format_response(response)

        # Логирование форматированного ответа для отладки
        logging.info(f"Форматированный ответ модели: {formatted_response}")

        # Попробуйте сначала отправить сообщение в виде простого текста
        try:
            bot.reply_to(message, formatted_response, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение: {e}")
            bot.reply_to(message, "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова.")
    else:
        bot.send_message(message.chat.id, 'Введите команду /start для начала.')


# Запуск polling
bot.polling(none_stop=True)