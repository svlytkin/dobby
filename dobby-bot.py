# [] перенести время напоминания
#   [✓] через команду !
#   [] через поиск только даты в сообщении, и предыдущее отправил бот
#   [] сделать обновление в бд, а не дописывание
#   [] возможно могу делать реплай сообщения, которое напоминаю, по message.message_id
# [] ввод даты после отправки сообщения
# [] поменять время в пн, вт итд на 9 утра
# [] сделать относительные даты – завтра, вечером, днем, утром, через неделю, через мес, через Х часов/минут/?секунд?
# [] отменить последнее действие через клавиатуру и текст

# сервер
# [] сделать чтобы работал на сервере
# [] чтобы в телеграм приходили ошибки
 
# украшения
# [] вывести дату и время в норм формате в сообщении, что принял напоминание – не понятно как сделать вывод человеческого дня "четверг", "мая" и тд
# [] убрать слова напомни/напомнить из сообщения напоминания
# [] убрать дату из сообщения напоминания
# [] добавить поддержку таймзоны

# ошибки
# [] напоминание приходит раньше на несколько секунд http://take.ms/c1X5e

import app
import sqlite3, os, sys
import telebot
import threading
from datetime import datetime
from datetime import timedelta
from dateutil import parser
from threading import Event, Thread



# подключаем бота
API_TOKEN = app.your_token
bot = telebot.TeleBot(API_TOKEN)

interval = 5 #интвервал проверки базы данных в секундах
default_time = 9 # время, во сколько ставится напоминание по умолчанию, если не задано время

# --- Функции ---
class RussianParserInfo(parser.parserinfo):
    WEEKDAYS = [("пн", "Понедельник"),
        ("вт", "Вторник"),
        ("ср", "Среда"),
        ("чт", "Четверг"),
        ("пт", "Пятница"),
        ("сб", "Суббота"),
        ("вс", "Воскресенье")]

    MONTHS = [('Jan', 'January', 'ян', 'янв', 'января', 'январь'), 
        ('Feb', 'February', 'фев', 'февраля', 'февраль'), 
        ('Mar', 'March', 'мар', 'марта', 'март'), 
        ('Apr', 'April', 'апр', 'апреля', 'апрель'), 
        ('May', 'мая', 'май'), 
        ('Jun', 'June', 'июня', 'июнь'), 
        ('Jul', 'July', 'июля', 'июль'), 
        ('Aug', 'August', 'авг', 'августа', 'август'),
        ('Sep', 'Sept', 'September', 'сент', 'сен', 'сентября', 'сентябрь'),
        ('Oct', 'October', 'окт', 'октября', 'октябрь'),
        ('Nov', 'November', 'ноя', 'ноября', 'ноябрь'),
        ('Dec', 'December', 'дек', 'декабря', 'декабрь')]
    HMS = [("h", "hour", "hours", "ч", "часов", "час"),
        ("m", "minute", "minutes", "мин", "минут", "минуту", "минута"),
        ("s", "second", "seconds", "с", "сек", "секунд", "секунду", "секунда")]
    JUMP = [" ", ".", ",", ";", "-", "/", "'",
        "at", "on", "and", "ad", "m", "t", "of",
        "st", "nd", "rd", "th", "в"]
    AMPM = [("am", "a", "утра"),
        ("pm", "p", "вечера")]
    UTCZONE = ["UTC", "GMT", "Z"]
    PERTAIN = ["of"]

date_symbols = [" ", ".", ",", ";", "-", "/", "'",
        "at", "on", "and", "ad", "m", "t", "of",
        "st", "nd", "rd", "th", "в", "напомни"]    

def sql_fetchall(sql):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(sql)
    con.commit()
    return cur.fetchall()

def sql_commit(sql):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(sql)
    con.commit()

# / --- Функции ---

# создаём базу данных и проверяем правильность подключения, если есть ошибки, выходим
cur_dir = os.getcwd() #получаем папку, где находится файл
DB = os.path.join(cur_dir,'tg.db') # возвращаем адрес базы данных
try:
  con = sqlite3.connect(DB) # подсоединяемся к базе, стандартный метод
  cur = con.cursor() # ?? как-то подключаем бд, чтобы с ней чтобы делать
except sqlite3.Error as e :
  print(u'Ошибка при подключении к базе %s' % DB)
  sys.exit(1)


# try:
#   cur.execute("SELECT rowid from users limit 0,1") # выполняем запрос к базе данных – проверяем, есть такая база или нет
# except sqlite3.Error as e :  
#   sql = """
#   CREATE TABLE "reminders" ("chat_id" ,"messages", "created_at" DATETIME, "remind_at" DATETIME) 
#   """
#   cur.execute(sql) # если таблицы нет, создаём её

# записываем сообщение боту в базу данных и пишем об этом в боте
def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper

def no_date(message):
    set_default_time = datetime.now().replace(hour=default_time,minute=0,second=0,microsecond=0)
    if datetime.now() > set_default_time:
        set_default_time = set_default_time + timedelta(days=1)
    sql_commit('insert into reminders (user_id, chat_id, messages, remind_at, message_id, created_at) values ("{}", "{}", "{}", "{}", "{}", "{}")'.format(message.from_user.id, message.chat.id, message.text, set_default_time, message.message_id, int(datetime.today().timestamp())))
    bot.send_message(message.chat.id, 'напомню завтра в {}, или введите дату'.format(default_time))

def check_date_in_a_string(message):
    try:
        date, list2 = parser.parse(message.text, parserinfo=RussianParserInfo(),fuzzy_with_tokens=True) #list2 - список слов без даты
        list2 = ' '.join(list2).split()
        list3 = [x for x in list2 if x not in date_symbols]
        return list3 == []
    except ValueError as e:
        pass

@bot.message_handler(func=check_date_in_a_string)
@bot.message_handler(regexp="^!.+")
def upd_reminder (message):
    try:
        upd_remind_at = parser.parse(message.text, parserinfo=RussianParserInfo(),fuzzy=True)
        last_message = sql_fetchall('select rowid, * from reminders where (user_id = "{}") and (chat_id = "{}") order by created_at desc limit 1'.format(message.from_user.id, message.chat.id))
        last_message = list(last_message[-1])
        print(last_message[-1], type(last_message[-1]))
        last_reminder = sql_fetchall('select * from last_reminders where (user_id = "{}") and (chat_id = "{}") order by reminder_sent_at desc limit 1'.format(message.from_user.id, message.chat.id))
        last_reminder = list(last_reminder[-1])
        if last_message[-1] < last_reminder[-1]: #[] -1  – это таймстэмп, когда создан, лучше сюда переменную всатавить, чтобы не потерялся, если случайно перенесу столбец с таймстэмпом
            sql_commit('insert into reminders (user_id, chat_id, messages, remind_at, message_id, created_at) values ("{}", "{}", "{}", "{}", "{}", "{}")'.format(last_reminder[0], last_reminder[1], last_reminder[2], upd_remind_at, message.message_id, int(datetime.today().timestamp())))
            bot.send_message(last_reminder[1], 'я перенёс "{}" на {}'.format(last_reminder[2], datetime.strftime(upd_remind_at, "%H:%M, %d/%m/%Y")))
        else:
            sql_commit('update reminders set remind_at = "{}" where (user_id = "{}") and (chat_id = "{}") and (rowid = "{}")'.format(upd_remind_at,last_message[1], last_message[2], last_message[0]))
            bot.send_message(message.chat.id, 'карашо, перенёс "{}" на {}'.format(last_message[3], datetime.strftime(upd_remind_at, "%H:%M, %d/%m/%Y"), last_message[6]))
    except ValueError as e:
        no_date(message)

    # sql_select_rowid = 'select rowid_in_reminders from last_reminders where (user_id = "{}") and (chat_id = "{}")'.format(message.from_user.id, message.chat.id)
    # print(sql_select_rowid)
    # cur.execute(sql_select_rowid)
    # con.commit()
    # row_id = cur.fetchall()
    # print(sql_upd_last_reminder)
    # cur.execute(sql_upd_last_reminder)
    # con.commit()

@bot.message_handler()
def add_message(message): # Название функции не играет никакой роли, в принципе
    # записываем сообщение, дату создания и дату напоминания в базу
    # sql = "INSERT INTO messages VALUES (?)"
    # cur.execute(sql, message.text)
    try:
        remind_at = parser.parse(message.text, parserinfo=RussianParserInfo(),fuzzy=True) # ищем дату в сообщении
        con = sqlite3.connect(DB)
        cur = con.cursor()
        sql = 'insert into reminders (user_id, chat_id, messages, remind_at, message_id, created_at) values ("{}", "{}", "{}", "{}", "{}", "{}")'.format(message.from_user.id, message.chat.id, message.text, remind_at, message.message_id, int(datetime.today().timestamp()))
        # сделать апдэйт, если такой чат и юзер уже есть ^
        cur.execute(sql)
        con.commit()
        bot.send_message(message.chat.id, 'карашо, напомню {} в {}'.format(message.text, datetime.strftime(remind_at, "%H:%M, %d/%m/%Y"))) 
    except ValueError as e:
        no_date(message)

def send_reminder():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    reminders = sql_fetchall('select user_id, chat_id, messages, message_id, created_at from reminders where (remind_at >= "{}") and (remind_at < "{}")'.format(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"), datetime.strftime(datetime.now()+timedelta(seconds=interval), "%Y-%m-%d %H:%M:%S")))
    print('select user_id, chat_id, messages, message_id, created_at from reminders where (remind_at >= "{}") and (remind_at < "{}")'.format(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"), datetime.strftime(datetime.now()+timedelta(seconds=interval), "%Y-%m-%d %H:%M:%S")))
    for reminder in reminders:
        # [] вырезать слова напомни / напомнить и дату перед отправкой
        try:
            cur.executescript('update last_reminders set (user_id, chat_id, last_reminder_text, reminder_message_id, reminder_sent_at) = ("{uid}", "{ch_id}", "{m_text}", "{mes_id}", "{s_at}") where (user_id = "{uid}") and (chat_id = "{ch_id}");insert into last_reminders (user_id, chat_id, last_reminder_text, reminder_message_id, reminder_sent_at) select "{uid}", "{ch_id}", "{m_text}", "{mes_id}", "{s_at}" where (Select Changes() = 0)'.format(uid=reminder[0], ch_id=reminder[1], m_text=reminder[2], mes_id=reminder[3], s_at=int(datetime.today().timestamp())))
            con.commit()
            bot.send_message(reminder[1], reminder[2])
        except ValueError as e:
            pass

def call_repeatedly(interval, func):
    stopped = Event()
    def loop():
        while not stopped.wait(interval):
            func()
    Thread(target=loop).start()    
    return stopped.set
    
cancel_future_calls = call_repeatedly(interval, send_reminder)  

bot.polling(none_stop=True)