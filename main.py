import telebot
import requests
from config import token, api_key
import sqlite3 as sq
from telebot import types

categs_list = []
bot = telebot.TeleBot(token)


def make_connection():
    con = sq.connect('botdb.db')
    cur = con.cursor()
    return [con, cur]


def get_news(call):
    news = requests.get(
        f'https://newsapi.org/v2/top-headlines?apiKey={api_key}&country=ru&category={call.data}&pageSize=3')
    news_list = []
    for i in news.json()['articles']:
        news_list.append([i['title'], i['description'], i['url']])
    for i in news_list:
        bot.send_message(call.message.chat.id, f'{i[0]}. {i[1]}. {i[2]}')
    bot.send_message(call.message.chat.id,
                     'Доброго времени суток!', reply_markup=markup_inline)


try:
    db = make_connection()
    db[1].execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER, PRIMARY KEY("id" AUTOINCREMENT)
        )""")
    db[0].commit()
    db[1].execute("""CREATE TABLE IF NOT EXISTS categories (
            id INTEGER, categ_name TEXT NOT NULL, PRIMARY KEY("id" AUTOINCREMENT)
        )""")
    db[0].commit()
    db[1].execute("""CREATE TABLE IF NOT EXISTS subscribes (
            user_id INTEGER, categ_id INTEGER
        )""")
    db[0].commit()
    categs_list = db[1].execute(
        """SELECT id, categ_name FROM categories""").fetchall()
    categs_list.pop(0)
finally:
    db[0].close()

markup_inline = types.InlineKeyboardMarkup(row_width=2)
markup_inline.add(types.InlineKeyboardButton(text='Подписаться', callback_data='sub'), types.InlineKeyboardButton(
    text='Отписаться', callback_data='unsub'), types.InlineKeyboardButton(text='Просмотреть новости', callback_data='news'))

markup_inline1 = types.InlineKeyboardMarkup(row_width=1)
for cat in categs_list:
    markup_inline1.add(types.InlineKeyboardButton(
        text=f'{cat[1]}', callback_data=f'sub-{cat[1]}'))
markup_inline1.add(types.InlineKeyboardButton(
    text='Отмена', callback_data='back'))


@bot.message_handler(content_types=['text'])
def get_text(message):
    user_id = int(message.from_user.id)
    try:
        db = make_connection()
        if db[1].execute("""SELECT id FROM users WHERE id=?""", (user_id,)).fetchone() == None:
            db[1].execute("""INSERT INTO users(id) VALUES(?)""", (user_id, ))
            db[0].commit()
        bot.send_message(message.chat.id, 'Доброго времени суток!',
                         reply_markup=markup_inline)
    finally:
        db[0].close()


@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    try:
        user_id = int(call.message.from_user.id)
        db = make_connection()
        if call.data == 'sub':
            bot.send_message(call.message.chat.id,
                             'Список категорий:', reply_markup=markup_inline1)
        elif call.data == 'unsub':
            if db[1].execute("""SELECT cats.categ_name FROM categories AS cats INNER JOIN subscribes as subs on cats.id = subs.categ_id WHERE subs.user_id=?""", (user_id,)).fetchall() != None:
                sub_cats = db[1].execute(
                    """SELECT cats.id, cats.categ_name FROM categories AS cats INNER JOIN subscribes as subs on cats.id = subs.categ_id WHERE subs.user_id=?""", (user_id,)).fetchall()
                markup_inline2 = types.InlineKeyboardMarkup(row_width=1)
                for cat in sub_cats:
                    markup_inline2.add(types.InlineKeyboardButton(
                        text=f'{cat[1]}', callback_data=f'unsub-{cat[0]}-{cat[1]}'))
                markup_inline2.add(types.InlineKeyboardButton(
                    text='Отмена', callback_data='back'))
                bot.send_message(
                    call.message.chat.id, 'Категории на которые вы подписаны:', reply_markup=markup_inline2)
            else:
                bot.send_message(
                    call.message.chat.id, 'Вы ещё не подписаны ни на одну из категорий.', reply_markup=markup_inline)
        elif call.data == 'news':
            if db[1].execute("""SELECT cats.categ_name FROM categories AS cats INNER JOIN subscribes as subs on cats.id = subs.categ_id WHERE subs.user_id=?""", (user_id,)).fetchall() != None:
                sub_cats = db[1].execute(
                    """SELECT cats.id, cats.categ_name FROM categories AS cats INNER JOIN subscribes as subs on cats.id = subs.categ_id WHERE subs.user_id=?""", (user_id,)).fetchall()
                markup_inline3 = types.InlineKeyboardMarkup(row_width=1)
                for cat in sub_cats:
                    markup_inline3.add(types.InlineKeyboardButton(
                        text=f'{cat[1]}', callback_data=f'{cat[1]}'))
                markup_inline3.add(types.InlineKeyboardButton(
                    text='По всем категориям', callback_data='all'))
                markup_inline3.add(types.InlineKeyboardButton(
                    text='Отмена', callback_data='back'))
                bot.send_message(
                    call.message.chat.id, 'Выберите категорию:', reply_markup=markup_inline3)
            else:
                bot.send_message(
                    call.message.chat.id, 'Вы ещё не подписаны ни на одну из категорий.', reply_markup=markup_inline)
        elif call.data == 'back':
            bot.send_message(
                call.message.chat.id, 'Доброго времени суток!', reply_markup=markup_inline)
        else:
            string = call.data.split('-')
            if string[0] == 'sub':
                for cat in categs_list:
                    if cat[1] == string[1]:
                        categ_id = cat[0]
                        if db[1].execute("""SELECT categ_id, user_id FROM subscribes WHERE user_id=? AND categ_id=?""", (user_id, categ_id)).fetchone() == None:
                            db[1].execute(
                                """INSERT INTO subscribes (user_id, categ_id) VALUES (?, ?)""", (user_id, categ_id))
                            db[0].commit()
                            bot.send_message(
                                call.message.chat.id, f'Вы успешно подписались на категорию {cat[1]}.', reply_markup=markup_inline1)
                        else:
                            bot.send_message(
                                call.message.chat.id, 'Вы уже подписаны на эту категорию.', reply_markup=markup_inline1)
            elif call.data == 'business':
                get_news(call)
            elif call.data == 'entertainment':
                get_news(call)
            elif call.data == 'general':
                get_news(call)
            elif call.data == 'science':
                get_news(call)
            elif call.data == 'sports':
                get_news(call)
            elif call.data == 'technology':
                get_news(call)
            elif call.data == 'all':
                sub_cats = db[1].execute(
                    """SELECT cats.id, cats.categ_name FROM categories AS cats INNER JOIN subscribes as subs on cats.id = subs.categ_id WHERE subs.user_id=?""", (user_id,)).fetchall()
                news = []
                for cat in sub_cats:
                    news.append(requests.get(
                        f'https://newsapi.org/v2/top-headlines?apiKey={api_key}&country=ru&category={cat[1]}&pageSize=1'))
                news_list = []
                for i in news:
                    for k in i.json()['articles']:
                        news_list.append([k['title'], k['description'], k['url']])
                for i in news_list:
                    bot.send_message(call.message.chat.id,
                                     f'{i[0]}. {i[1]}. {i[2]}')
                bot.send_message(
                    call.message.chat.id, 'Доброго времени суток!', reply_markup=markup_inline)
            else:
                db[1].execute(
                    """DELETE FROM subscribes WHERE user_id=? AND categ_id=?""", (user_id, string[1]))
                db[0].commit()
                bot.send_message(
                    call.message.chat.id, f'Вы успешно отписались от категории {string[2]}', reply_markup=markup_inline)
    finally:
        db[0].close()


bot.infinity_polling()
