from aiogram import Bot, types
import sql_commands
import json
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup

# клавиатура для выбора КАПИТАН или УЧАСТНИК
who_you_are = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
capt = types.KeyboardButton("Капитан")
participant = types.KeyboardButton("Одиночный участник")
who_you_are.add(capt, participant)

# клавиатура для выбора ДА или НЕТ
yes_or_no = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
yes = types.KeyboardButton("Да")
no = types.KeyboardButton("Нет")
yes_or_no.add(yes, no)

# клавиатура с кнопками РЕДАКТИРОВАТЬ и ДАЛЕЕ
edit_data = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
edit = types.KeyboardButton("Редактировать")
next_btn = types.KeyboardButton("Далее")
edit_data.add(edit, next_btn)

# клавиатура с кнопками ДАННЫЕ С ПРЕДЫДУЩИХ ИГР и НОВЫЕ ДАННЫЕ
previous_or_new = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
previous = types.KeyboardButton("Данные с предыдущих игр")
new = types.KeyboardButton("Новые данные")
previous_or_new.add(previous, new)

# клавиатура для выбора соц.сети
soc_network = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
tlgrm = types.KeyboardButton("Telegram ")
instgrm = types.KeyboardButton("Instagram")
fcbk = types.KeyboardButton("Facebook")
other = types.KeyboardButton("Другое")
soc_network.add(tlgrm, instgrm, fcbk, other)

# клавиатура для завершения регистрации
complete_registr = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
cmplt = types.KeyboardButton("Завершить регистрацию")
edt = types.KeyboardButton("Редактировать данные")
complete_registr.add(cmplt, edt)

# клавиатура с кнопкой ОК
ok_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
ok_key = types.KeyboardButton("Ок")
ok_keyboard.add(ok_key)

# клавиатура с кнопкой "Всё верно"
this_is_right_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
this_is_right_key = types.KeyboardButton("Всё верно")
this_is_right_keyboard.add(this_is_right_key)

# клавиатура с цифрами от 1 до 10 для выбора кол-ва участников в команде
amount_part_keyboard = types.InlineKeyboardMarkup()
btn1 = types.InlineKeyboardButton('1', callback_data='1')
btn2 = types.InlineKeyboardButton('2', callback_data='2')
btn3 = types.InlineKeyboardButton('3', callback_data='3')
btn4 = types.InlineKeyboardButton('4', callback_data='4')
btn5 = types.InlineKeyboardButton('5', callback_data='5')
btn6 = types.InlineKeyboardButton('6', callback_data='6')
btn7 = types.InlineKeyboardButton('7', callback_data='7')
btn8 = types.InlineKeyboardButton('8', callback_data='8')
btn9 = types.InlineKeyboardButton('9', callback_data='9')
btn10 = types.InlineKeyboardButton('10', callback_data='10')
amount_part_keyboard.row(btn1, btn2, btn3, btn4, btn5)
amount_part_keyboard.row(btn6, btn7, btn8, btn9, btn10)


# клавиатура для капитана со всеми датами игр
game_dates_buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)
all_dates = sql_commands.all_dates_from_game_dates()
list_of_dates = []
for index in range(0, len(all_dates)):
    one_button_date = types.KeyboardButton(f"{all_dates[index][0]} ({all_dates[index][1]} {all_dates[index][2]})")
    list_of_dates.append(one_button_date)

for date in list_of_dates:
    game_dates_buttons.insert(date)

