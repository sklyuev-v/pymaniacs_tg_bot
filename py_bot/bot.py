from py_bot.utils import load_message, load_prompt, send_text_buttons, \
    send_text, send_image, show_main_menu
from py_bot.gpt import ChatGptService
from typing import NoReturn
# import logging
import pickle
from environs import Env
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, ConversationHandler
from telegram.ext import CommandHandler, MessageHandler, \
    CallbackQueryHandler, filters
from py_bot.open_weather import fetch_weather


# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO)

# Bot work modes for ConversationHandlers
MENU, RANDOM, TALK_WITH_CHAT_GPT, QUIZ, VOCABULARY, WEATHER_FORECAST = range(6)


# Main menu - entry point for bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Главное меню',
        'random': 'Узнать случайный интересный факт 🧠',
        'gpt': 'Задать вопрос чату GPT 🤖',
        'talk': 'Поговорить с известной личностью 👤',
        'quiz': 'Поучаствовать в квизе ❓',
        'translate': 'Перевести текст 📝',
        'advise': 'Порекомендовать фильм/книгу/музыку 📽️',
        'vocabularytrain': 'Тренировать словарный запас 📖',
        'weatherforecast': 'Текущая погода ⛅'
    })
    return MENU


# Taks 1 - Echo-bot
async def echo_handler(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> NoReturn:
    """
    Simple echo bot - resend user messages

    """
    await update.message.reply_text(update.message.text)


# Task 2 - Random facts bot
async def random(update: Update,
                 context: ContextTypes.DEFAULT_TYPE) -> NoReturn:
    """Random fact
    Send in chat some random fact by ChatGPT
    """
    prompt = load_prompt('random')
    await send_image(update, context, 'random')
    await send_text(update, context, 'Думаю над случайным фактом...')
    answer = await chat_gpt.send_question(prompt, '')
    await send_text_buttons(update, context,
                            answer, {'random_more': 'Больше интересностей!',
                                     'stop': 'Хватит на сегодня'})
    return RANDOM


async def random_button(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> NoReturn:
    """ Button handler
        Another random fact by ChatGPT
    """
    await update.callback_query.answer()
    await random(update, context)


# Taks 3 - ChatGPT dialog bot
async def gpt_question(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> int:
    """gpt question

    Sets ChatGPT to the required role.
    Prints gpt-dialog-mode welcome image and text into Telegram chat to user.

    Returns:
        int: a constant that switches ConversationHandler to another state
    """
    prompt = load_prompt('gpt')
    chat_gpt.set_prompt(prompt)
    message = load_message('gpt')
    await send_image(update, context, 'gpt')
    await send_text(update, context, message)

    return TALK_WITH_CHAT_GPT


async def talk_with_chat_gpt(update: Update,
                             context: ContextTypes.DEFAULT_TYPE) -> NoReturn:
    """Talk to chat GPT
    Gets a message from Telegram chat.
    Sends it to chatGPT and receives a response.
    Sends the response into telegram chat to user.
    """
    question = update.message.text
    answer = await chat_gpt.send_message(question)
    await send_text_buttons(update, context,
                            answer, {'stop': 'Закончить общение'})


# Task 4 - ChatGPT as a Person dialog
async def talk_with_person(update: Update,
                           context: ContextTypes.DEFAULT_TYPE) -> NoReturn:
    """Talk to ChatGPT that pretends to be a famous person
    """
    message = load_message('talk')
    await send_image(update, context, 'talk')
    await send_text_buttons(update, context, message,
                            {'talk_cobain': 'Курт Кобейн',
                             'talk_hawking': 'Стивен Хокинг',
                             'talk_feynman': 'Ричард Фейнман',
                             'talk_nietzsche': 'Фридрих Нитцше',
                             'talk_queen': 'Королева Виктория',
                             'talk_tolkien': 'Джон Рональд Руэл Толкин',
                             'talk_martin': 'Джордж Мартин'})


async def talk_button(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> NoReturn:
    await update.callback_query.answer()
    cb = update.callback_query.data
    prompt = load_prompt(cb)
    chat_gpt.set_prompt(prompt)
    msg = 'Кратко расскажи о себе. И напиши приветствие.'
    hello_msg = await chat_gpt.send_message(msg)
    await send_image(update, context, cb)
    await send_text(update, context, hello_msg)

    return TALK_WITH_CHAT_GPT


# Task 5 - Quiz
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = load_prompt('quiz')
    chat_gpt.set_prompt(prompt)
    await send_image(update, context, 'quiz')
    infotext = load_message('quiz')
    context.user_data['quiz_good'] = 0
    context.user_data['quiz_count'] = 0
    await send_text_buttons(update, context, infotext,
                            {'quiz_prog': 'Программирования на Python',
                             'quiz_math': 'Математические теории',
                             'quiz_biology': 'Биология',
                             })

    return QUIZ


async def quiz_button(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> NoReturn:
    await update.callback_query.answer()
    cb = update.callback_query.data
    question = await chat_gpt.send_message(cb)
    await send_text(update, context, question)


async def quiz_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    result = await chat_gpt.send_message(answer)
    if result.startswith('Правил'):
        context.user_data['quiz_good'] += 1
    context.user_data['quiz_count'] += 1

    count = context.user_data['quiz_count']
    good = context.user_data['quiz_good']

    result = f'{result}\n Правильных ответов: {good} из {
        count} *{int((good/count)*100)}%*'
    await send_text_buttons(update, context, result, {
        'q_next_question': 'Следующий вопрос',
        'q_change_theme': 'Сменить тему',
        'stop': 'Закончить Квиз'
    })


async def quiz_message_buttons(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    cb = update.callback_query.data
    if cb == 'q_next_question':
        message = await chat_gpt.send_message('quiz_more')
        await send_text(update, context, message)
    else:
        await send_text_buttons(update, context,
                                'На какую тему будем проверять знания:',
                                {'quiz_prog': 'Программирования на Python',
                                 'quiz_math': 'Математические теории',
                                 'quiz_biology': 'Биология',
                                 })


# Task 6 - Translate text
async def translate_text(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> NoReturn:
    prompt = load_prompt('translate')
    chat_gpt.set_prompt(prompt)
    await send_image(update, context, 'translate')
    tr_info = 'Все последующие сообщения будут переведены на русский язык'
    await send_text(update, context, tr_info)
    return TALK_WITH_CHAT_GPT


# Task 7 - Advisor
async def advise_something(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = load_prompt('advisor')
    chat_gpt.set_prompt(prompt)
    await send_image(update, context, 'advisor')
    await send_text_buttons(update, context, 'Выбери что ты хочешь:', {
        'adv_movie': 'Порекомендуй фильм',
        'adv_music': 'Порекомендуй музыкального исполнителя',
        'adv_book': 'Порекомендуй книгу'
    })


async def advise_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    cb = update.callback_query.data
    await chat_gpt.send_message(cb)
    await send_text(update, context, 'Дайте мне описание того, что вы хотите')

    return TALK_WITH_CHAT_GPT


# Task 8 - Vocabulary Trainer
async def vocabulary_train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = load_prompt('vocabulary')
    chat_gpt.set_prompt(prompt)

    await send_image(update, context, 'vocabulary')

    context.user_data['voc_count'] = 0
    context.user_data['voc_good'] = 0

    question = await chat_gpt.send_message('vocab_more')
    await send_text(update, context, question)

    return VOCABULARY


async def vocabulary_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    result = await chat_gpt.send_message(answer)
    if result.startswith('Правил'):
        context.user_data['voc_good'] += 1
    context.user_data['voc_count'] += 1

    voc_count = context.user_data['voc_count']
    voc_good = context.user_data['voc_good']

    result = f'{result}\n Правильно {voc_good} из {
        voc_count} WR: {int((voc_good/voc_count)*100)}%'
    await send_text_buttons(update, context, result, {
        'vocab_more': 'Следующий вопрос',
        'stop': 'Закончить тренировку'
    })


async def vocabulary_button(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    message = await chat_gpt.send_message('vocab_more')
    await send_text(update, context, message)


async def stop_button(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> NoReturn:
    await start(update, context)
    return MENU


# Task 10 - Weather forecast from OpenWeather
users = {}


async def weather_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city_flag'] = False
    users = load_city_data()
    await send_image(update, context, 'weather')
    await send_text(update, context, 'Текущая погода:')
    if update.message.chat_id not in users:
        await send_text(update, context, 'Введите город:')
        return WEATHER_FORECAST
    else:
        weather = await fetch_weather(OPEN_WEATHER_TOKEN,
                                      users[update.message.chat_id])
        await send_text(update, context, weather)


async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data['city_flag']:
        city = update.message.text
        users[update.message.chat_id] = city
        context.user_data['city_flag'] = True
        save_city_data(users)
        await weather_forecast(update, context)
    else:
        await send_text_buttons(update, context, 'Город уже установлен', {
            'change_city': 'Изменить город',
            'stop': 'Вернуться на главную страницу'
        })


async def change_city_button(update: Update,
                             context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city_flag'] = False
    await send_text(update, context, 'Введите город')


def save_city_data(data):
    with open('py_bot/users.pkl', 'wb') as file:
        pickle.dump(data, file)


def load_city_data():
    with open('py_bot/users.pkl', 'rb') as file:
        return pickle.load(file)


def main():

    env: Env = Env()
    env.read_env()

    BOT_TOKEN = env('BOT_TOKEN')
    GPT_TOKEN = env('CHAT_GPT_TOKEN')
    global OPEN_WEATHER_TOKEN
    OPEN_WEATHER_TOKEN = env('OPEN_WEATHER_TOKEN')

    global chat_gpt
    chat_gpt = ChatGptService(GPT_TOKEN)
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU: [
                CommandHandler('random', random),
                CommandHandler('gpt', gpt_question),
                CommandHandler('talk', talk_with_person),
                CommandHandler('quiz', quiz),
                CommandHandler('translate', translate_text),
                CommandHandler('advise', advise_something),
                CommandHandler('vocabtrain', vocabulary_train),
                CommandHandler('weatherforecast', weather_forecast),
                CallbackQueryHandler(talk_button, pattern='^talk_.*'),
                CallbackQueryHandler(quiz_button, '^quiz_.*'),
                CallbackQueryHandler(advise_button, '^adv_.*'),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, echo_handler)
            ],
            RANDOM: [
                CallbackQueryHandler(random_button, pattern='^random_.*'),
                CallbackQueryHandler(stop_button, pattern='stop')
            ],
            TALK_WITH_CHAT_GPT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, talk_with_chat_gpt),
                CallbackQueryHandler(stop_button, pattern='stop')
            ],
            QUIZ: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, quiz_talk),
                CallbackQueryHandler(quiz_button, '^quiz_.*'),
                CallbackQueryHandler(quiz_message_buttons, '^q_.*'),
                CallbackQueryHandler(stop_button, pattern='stop'),
            ],
            VOCABULARY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, vocabulary_talk),
                CallbackQueryHandler(vocabulary_button, '^vocab_.*'),
                CallbackQueryHandler(stop_button, pattern='stop'),
            ],
            WEATHER_FORECAST: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, set_city),
                CallbackQueryHandler(change_city_button, 'change_city'),
                CallbackQueryHandler(stop_button, pattern='stop'),
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    bot.add_handler(conv_handler)

    bot.run_polling()


if __name__ == '__main__':
    main()
