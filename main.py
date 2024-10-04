import telebot
import datetime
import time
from threading import Timer

# Токен вашего бота
bot = telebot.TeleBot("7721669403:AAHTMgKeZlDenqUZZfcyqdGs7JUNXkOoXKU")

# Словарь для хранения заметок и расписания
data = {}

def get_user_data(user_id):
  if user_id not in data:
    data[user_id] = {'notes': [], 'schedule': []}
  return data[user_id]

@bot.message_handler(commands=['start'])
def start(message):
  user_data = get_user_data(message.chat.id)
  bot.send_message(message.chat.id, "Привет! Я бот для заметок и расписания. \n\
 Чтобы добавить заметку, напишите /add. \n\
 Чтобы добавить событие в расписание, напишите /schedule. \n\
 Чтобы получить уведомление о ближайшем событии, напишите /remind. \n\
 Чтобы посмотреть, редактировать или удалить заметки, напишите /notes.")

@bot.message_handler(commands=['add'])
def add_note(message):
  user_data = get_user_data(message.chat.id)
  bot.send_message(message.chat.id, "Введите вашу заметку:")
  bot.register_next_step_handler(message, process_note, user_data)

def process_note(message, user_data):
  note = message.text
  user_data['notes'].append(note)
  bot.send_message(message.chat.id, "Заметка добавлена!")

@bot.message_handler(commands=['schedule'])
def schedule_event(message):
  user_data = get_user_data(message.chat.id)
  bot.send_message(message.chat.id, "Введите описание события:")
  bot.register_next_step_handler(message, process_schedule, user_data)

def process_schedule(message, user_data):
  description = message.text
  bot.send_message(message.chat.id,           "Введите дату и время события в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2023-10-27 18:00):")
  bot.register_next_step_handler(message, add_event, description, user_data)

def add_event(message, description, user_data):
  try:
    datetime_str = message.text
    event_datetime = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
    user_data['schedule'].append({'description': description, 'datetime': event_datetime})
    bot.send_message(message.chat.id, "Событие добавлено в расписание!")
    # Планируем уведомление за 10 минут до события
    time_until_event = (event_datetime - datetime.datetime.now()).total_seconds()
    reminder_time = time_until_event - 600 # 600 секунд = 10 минут
    if reminder_time > 0:
      Timer(reminder_time, send_reminder, [message.chat.id, description, event_datetime]).start()
  except ValueError:        bot.send_message(message.chat.id, "Неверный формат даты и времени. Попробуйте снова.")

def send_reminder(chat_id, description, event_datetime):
    bot.send_message(chat_id, f"Напоминание: {description} в {event_datetime.strftime('%Y-%m-%d %H:%M')}.")

@bot.message_handler(commands=['remind'])
def remind(message):
    user_data = get_user_data(message.chat.id)
    if user_data['schedule']:
        # Сортировка событий по дате и времени
        user_data['schedule'].sort(key=lambda item: item['datetime'])
        # Проверка, есть ли события в будущем
        has_future_events = any(event['datetime'] > datetime.datetime.now() for event in user_data['schedule'])
        if has_future_events:
            closest_event = user_data['schedule'][0]
            time_until_event = closest_event['datetime'] - datetime.datetime.now()
            if time_until_event.total_seconds() > 0:
                bot.send_message(message.chat.id, f"Ваше ближайшее событие: {closest_event['description']} в {closest_event['datetime'].strftime('%Y-%m-%d %H:%M')}.")
            else:
                # Событие уже прошло, удаляем его из расписания
                user_data['schedule'].pop(0)
                bot.send_message(message.chat.id, "Похоже, ближайшее событие уже прошло!")
                remind(message)  #  Повторяем remind, чтобы проверить, остались ли события
        else:
            bot.send_message(message.chat.id, "У вас нет событий в расписании.")
    else:
        bot.send_message(message.chat.id, "У вас нет событий в расписании.")

@bot.message_handler(commands=['notes'])
def manage_notes(message):
    user_data = get_user_data(message.chat.id)
    if user_data['notes']:
        bot.send_message(message.chat.id, "Ваши заметки:\n" + "\n".join(user_data['notes']))
        bot.send_message(message.chat.id, "Что вы хотите сделать с заметками? \n\
        /edit - Изменить заметку\n\
        /delete - Удалить заметку\n\
        /cancel - Вернуться назад")
        bot.register_next_step_handler(message, process_notes_action, user_data)
    else:
        bot.send_message(message.chat.id, "У вас нет заметок.")

def process_notes_action(message, user_data):
    if message.text == '/edit':
        edit_note(message, user_data)
    elif message.text == '/delete':
        delete_note(message, user_data)
    elif message.text == '/cancel':
        bot.send_message(message.chat.id, "Отменено.")
    else:
        bot.send_message(message.chat.id, "Неверная команда. Попробуйте снова.")

def edit_note(message, user_data):
    if user_data['notes']:
        bot.send_message(message.chat.id, "Введите номер заметки, которую хотите отредактировать (от 1 до " + str(len(user_data['notes'])) + "):")
        bot.register_next_step_handler(message, choose_note_to_edit, user_data)
    else:
        bot.send_message(message.chat.id, "У вас нет заметок.")

def choose_note_to_edit(message, user_data):
    try:
        note_index = int(message.text) - 1
        if 0 <= note_index < len(user_data['notes']):
            bot.send_message(message.chat.id, "Введите новую заметку:")
            bot.register_next_step_handler(message, update_note, note_index, user_data)
        else:
            bot.send_message(message.chat.id, "Неверный номер заметки. Попробуйте снова.")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный номер заметки. Попробуйте снова.")

def update_note(message, note_index, user_data):
    user_data['notes'][note_index] = message.text
    bot.send_message(message.chat.id, "Заметка отредактирована!")

def delete_note(message, user_data):
    if user_data['notes']:
        bot.send_message(message.chat.id, "Введите номер заметки, которую хотите удалить (от 1 до " + str(len(user_data['notes'])) + "):")
        bot.register_next_step_handler(message, choose_note_to_delete, user_data)
    else:
        bot.send_message(message.chat.id, "У вас нет заметок.")

def choose_note_to_delete(message, user_data):
    try:
        note_index = int(message.text) - 1
        if 0 <= note_index < len(user_data['notes']):
            del user_data['notes'][note_index]
            bot.send_message(message.chat.id, "Заметка удалена!")
        else:
            bot.send_message(message.chat.id, "Неверный номер заметки. Попробуйте снова.")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный номер заметки. Попробуйте снова.")

# Запуск бота
bot.infinity_polling()