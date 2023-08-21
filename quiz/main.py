from aiogram import Bot, types
from aiogram.utils import executor
import asyncio
from aiogram.dispatcher import Dispatcher
from aiogram.utils.exceptions import Throttled
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
import config
import keyboards
import logging
import commands
import sql_commands
import re

storage = MemoryStorage()
bot = Bot(token=config.botkey, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(filename='log.txt', level=logging.INFO, format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s '
                                                                   u'[%(asctime)s] %(message)s')


# настраиваем FSM
class CaptainStates(StatesGroup):
    Choose_date = State()
    Cap_or_Lonely = State()
    Prev_data_or_new = State()
    Old_data = State()
    Old_data_show = State()
    New_data_show = State()
    Complete_new_registr = State()
    Finish_edit_second_registration = State()
    Team_name = State()
    Team_name_support = State()
    Capt_name = State()
    Capt_name_support = State()
    Amount_participants = State()
    Amount_participants_new = State()
    Capt_phone_number = State()
    Capt_phone_number_support = State()
    Choose_soc_net = State()
    Telegram = State()
    Instagram = State()
    Facebook = State()
    Other_soc_net = State()
    Link_support = State()
    Lonely_player = State()
    Lonely_player_support = State()
    Capt_comments = State()
    Capt_comments_support = State()
    Capt_comments_support_enter = State()
    Show_info_to_capt = State()
    Finish_edit = State()
    Edit_game_date = State()
    Edit_team_name = State()
    Edit_capt_name = State()
    Edit_amount_participants = State()
    Edit_capt_phone = State()
    Edit_capt_link = State()
    Edit_capt_link_telegram = State()
    Edit_capt_link_instagram = State()
    Edit_capt_link_facebook = State()
    Edit_capt_link_other_soc_net = State()
    Edit_lonely_player = State()
    Edit_capt_comment = State()
    Edit_capt_comment_enter = State()
    Edit_game_date_second = State()
    Edit_team_name_second = State()
    Edit_capt_name_second = State()
    Edit_amount_participants_second = State()
    Edit_capt_phone_second = State()
    Edit_capt_link_second = State()
    Edit_capt_link_telegram_second = State()
    Edit_capt_link_instagram_second = State()
    Edit_capt_link_facebook_second = State()
    Edit_capt_link_other_soc_net_second = State()
    Edit_lonely_player_second = State()
    Edit_capt_comment_second = State()
    Edit_capt_comment_enter_second = State()


class PlayersStates(StatesGroup):
    Have_a_nice_day = State()
    Show_short_info_to_player = State()
    Choose_from_several_dates = State()
    Player_name = State()
    Player_name_support = State()
    Player_comments = State()
    Players_comments_support = State()
    Players_comments_support_enter = State()
    Show_all_info_to_player = State()
    Finish_player_edit = State()
    Player_edit_game_date = State()
    Player_edit_name = State()
    Player_edit_comments = State()
    Player_edit_comment_enter = State()


class LonelyPlayerStates(StatesGroup):
    Lonely_player_name = State()
    Lonely_player_name_support = State()
    Lonely_player_comment = State()
    Lonely_player_comment_support = State()
    Lonely_player_comment_support_enter = State()
    Show_info_to_lonely_player = State()
    Finish_lonely_player_edit = State()
    Lonely_player_edit_game_date = State()
    Lonely_player_edit_name = State()
    Lonely_player_edit_comments = State()
    Lonely_player_edit_comment_enter = State()
    Lonely_player_Choose_soc_net = State()
    Lonely_player_Telegram = State()
    Lonely_player_Instagram = State()
    Lonely_player_Facebook = State()
    Lonely_player_Other_soc_net = State()
    Lonely_player_link_support = State()
    Edit_lonely_player_link = State()
    Edit_lonely_player_link_telegram = State()
    Edit_lonely_player_link_instagram = State()
    Edit_lonely_player_link_facebook = State()
    Edit_lonely_player_link_other_soc_net = State()


# хэндлер отвечает на команду /start
# сортирует
# /start                  --> капитан
# /start + id капитана    --> игрок команды
# /start                  --> одинокий пользователь
@dp.message_handler(Command('start'), state=None)
async def welcome(message: types.Message, state: FSMContext):
    # здесь сохраняем команду /start в её изначальном виде, как она пришла от пользователя
    start_command = message.text
    # если команда /start пустая, длина referrer_id = 0
    # значит перед нами либо
    #  --> капитан
    #  --> одинокий пользователь
    referrer_id = start_command[7:]
    # сюда попадёт капитан, если вдруг попытается перейти по своей собственной реферальной ссылке
    if referrer_id == str(message.from_user.id):
        await bot.send_message(message.from_user.id, "Нельзя регистрироваться по собственной ссылке",
                               reply_markup=keyboards.ok_keyboard)
        await PlayersStates.Have_a_nice_day.set()
    # сюда попадёт игрок, перешедший по реферальной ссылке своего капитана
    elif referrer_id != str(message.from_user.id) and len(referrer_id) != 0:
        # сохраним в FSM id капитана и id самого игрока
        await state.update_data(referrer_id=int(referrer_id))
        player_id = str(message.from_user.id)
        await state.update_data(player_id=int(player_id))
        # создадим список со всеми датами, на которые зарегистрирован капитан
        dates = sql_commands.all_dates_captain_registered_is_except_past(referrer_id)
        # если капитан зарегистрирован только на одну игру
        if len(dates) == 1:
            # информируем об этом участника, даём клавишу с текстом "Всё верно" для перехода далее
            await bot.send_message(message.chat.id, text=f'Капитан зарегистрирован на игру датой: \n*{dates[0]}*',
                                   reply_markup=keyboards.this_is_right_keyboard, parse_mode='Markdown')
            # сохраняем дату игры в FSM
            await state.update_data(game_date=dates[0])
            # но прежде чем идти дальше, нужно проверить, не зарегистрирован ли уже этот участник на эту дату
            data = await state.get_data()
            player_id = data.get('player_id')
            game_date = data.get('game_date')
            # максимально в 'name' может вернуться только 1 имя, т.к. в функцию передаём только 1 id и 1 дату игры
            name = sql_commands.check_player_name_into_base_by_playerid_date(player_id, game_date)
            # и если игрок на выбранную дату ещё не зарегистрирован, то len(name) будет 0
            if len(name) == 0:
                # пропускаем дальше в регистрацию
                await PlayersStates.Show_short_info_to_player.set()
            # если же 'name' не пустой, то там хранится имя игрока, зарегистрированного на выбранную дату
            else:
                # информируем игрока об этом
                await bot.send_message(message.chat.id, text=f'Игрок: *{name[0][0]}* уже зарегистрирован на эту дату\n',
                                       reply_markup=keyboards.ok_keyboard, parse_mode='Markdown')
                # назначим вспомогательный стейт для плавного выхода из ситуации (принимает "ок")
                await PlayersStates.Have_a_nice_day.set()
        # если капитан зарегистрирован больше, чем на одну игру
        elif len(dates) > 1:
            # клавиатура для участника со всеми датами игр, на которые капитан зарегистрирован
            # кроме прошедших дат
            dates_captain_registered_is = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                                    row_width=1)
            all_dates = sql_commands.all_dates_captain_registered_is_except_past(referrer_id)
            list_of_buttons_with_dates = []
            for one_date in all_dates:
                one_button_date = types.KeyboardButton(f"{one_date}")
                list_of_buttons_with_dates.append(one_button_date)

            for date_button in list_of_buttons_with_dates:
                dates_captain_registered_is.insert(date_button)
            # пишем игроку сообщение, открываем клавиатуру с этими датами для выбора
            await bot.send_message(message.chat.id, text=f'Даты, на которые зарегистрирован ваш капитан ⬇️\n'
                                                         f'Выберите, когда хотите играть',
                                   reply_markup=dates_captain_registered_is)
            # это состояние будет отлавливать нажатие клавиш с датами и сохранять дату в FSM
            await PlayersStates.Choose_from_several_dates.set()
        # эта ошибка возникнет, если капитан не зарегистрирован ни на одну игру
        else:
            await bot.send_message(message.chat.id,
                                   text='Произошла какая-то ошибка. \nКапитан, по чьей ссылке вы перешли, '
                                        'не зарегистрирован ни на одну игру.', reply_markup=keyboards.ok_keyboard)
            await PlayersStates.Have_a_nice_day.set()
    # сюда попадают те, у кого пустая команда /start
    # т.е. либо капитаны, желающие зарегистрироваться, либо одинокие игроки и выбирают дату игры
    else:
        await bot.send_message(message.chat.id,
                               text=f"Привет, {message.from_user.first_name}!\n"
                                    f"Выберите дату игры",
                               reply_markup=keyboards.game_dates_buttons, parse_mode='Markdown')
        await CaptainStates.Choose_date.set()


# здесь сохраняем выбранную дату игры
# спрашиваем польз-ля капитан он или одиночный участник
@dp.message_handler(content_types='text', state=CaptainStates.Choose_date)
async def catch_date_from_cap_or_lonely(message: types.Message, state: FSMContext):
    # дата игры, которую выбрал пользователь в предыдущем состоянии (в формате ДД.ММ.ГГГГ (День недели ЧЧ:ММ))
    all_about_one_date = message.text
    # ИЗ БАЗЫ: список с кортежами со всеми датами игр, кроме тех, что уже прошли
    all_dates = sql_commands.all_dates_from_game_dates()
    # в список 'list_of_dates' циклом накидываем даты из базы
    # db style
    list_of_dates = []
    for one_tuple in all_dates:
        # в каждом кортеже содержится "дата", "день недели", "время"
        # кортеж по индексу 0 вернёт нам дату
        # кортеж по индексу 1 вернёт нам день недели
        # кортеж по индексу 2 вернёт нам время
        list_of_dates.append(f"{one_tuple[0]} {one_tuple[1]} {one_tuple[2]}")
    # из всех данных о нашей дате мы регуляркой забираем только число
    # регулярка возвращает СПИСОК !
    game_date_in_list = re.findall(r'\d\d.\d\d.\d\d\d\d', all_about_one_date)
    # "очищенная" дата, только ДД.ММ.ГГГГ, тип данных - строка
    game_date = game_date_in_list[0]
    # из всех данных о дате регуляркой забираем день недели
    week_day_in_list = re.findall(r'([А-я][а-я]+)', all_about_one_date)
    # "очищенный" день недели, тип данных - строка
    week_day = week_day_in_list[0]
    # из всех данных о дате регуляркой забираем время ЧЧ:ММ
    game_time_in_list = re.findall(r'\d\d:\d\d', all_about_one_date)
    # "очищенное" время игры, только ЧЧ:ММ, тип данных - строка
    game_time = game_time_in_list[0]
    # проверка, чтобы данные с датой, пришедшие в хэндлер совпадали с данными из базы
    # т.е. ТАКАЯ ДАТА + ВРЕМЯ + ДЕНЬ НЕДЕЛИ есть в базе
    if f"{game_date} {week_day} {game_time}" in list_of_dates:
        # записываем дату ДД.ММ.ГГГГ, день недели и время ЧЧ:ММ в fsm
        await state.update_data(game_date=game_date, week_day=week_day, game_time=game_time)
        # шлём сообщение для перехода в след.состояние
        await bot.send_message(message.chat.id,
                               text="Хотите зарегистрироваться как капитан команды или как одиночный участник?",
                               reply_markup=keyboards.who_you_are, parse_mode='Markdown')
        await CaptainStates.Cap_or_Lonely.set()
    else:
        await bot.send_message(message.chat.id, text='Произошла какая-то ошибка. Попробуйте ещё раз.\n'
                                                     'Ожидается ввод даты 📆\nЖмите кнопочки ⬇️')


# хэндлер ловит нажание кнопки "капитан" или "одиночный участник"
@dp.message_handler(content_types='text', state=CaptainStates.Cap_or_Lonely)
async def captain_or_participant(message: types.Message, state: FSMContext):
    if message.text == 'Капитан':
        # сохраняем id КАПИТАНА КОМАНДЫ
        capt_telegram_id = message.from_user.id
        await state.update_data(capt_telegram_id=capt_telegram_id)
        # прежде чем пускать капитана в дальнейшую регистрацию, нужно проверить, что
        # в БД по ключу  >>"id капитана + выбранная дата"<<  не было записей
        # а вдруг он уже зарег-н на эту дату
        # получаем данные из fsm
        data = await state.get_data()
        # поскольку в fsm дата хранится в формате ДД.ММ.ГГГГ, переделываем её для передачи в базу
        new_date = data.get('game_date')
        # срезами получаем отдельно день, месяц, год
        n_day = new_date[0:2]
        n_month = new_date[3:5]
        n_year = new_date[6:10]
        # в нужном порядке и без пробелов передаём их в новую переменную
        date_for_check = f"{n_year}{n_month}{n_day}"
        # из id капитана и даты игры без пробелов формируем первичный ключ для передачи в функцию
        capt_telegram_id_game_date = (str(data.get('capt_telegram_id')) + date_for_check)
        player_name_check = sql_commands.select_player_name_by_playerid_gamedate(capt_telegram_id_game_date)
        lonely_player_name_check = sql_commands.select_lonely_player_name_by_lonely_playerid_gamedate(
            capt_telegram_id_game_date)
        # ф-ция возвращает ИМЯ КОМАНДЫ по первич. ключу "id капитана + дата игры", если такая запись есть в БД
        # максимально в 'team_name' может вернуться только одно имя
        team_name = sql_commands.check_team_name_into_base_by_captid_date(capt_telegram_id_game_date)
        # список с датами игр, на которые капитан когда-либо регистрировался
        # если в списке есть хотя бы одна дата, то капитан уже есть в базе
        all_dates_capt = sql_commands.all_dates_captain_registered_is(capt_telegram_id)
        # проверяем, чтобы капитан не был зарегистрирован нигде как игрок
        if len(player_name_check) == 0:
            # также проверяем что капитан не числится на эту дату и как одиночный игрок
            if len(lonely_player_name_check) == 0:
                # если длина 'team_name' == 0, капитан на выбранную дату не зарегистрирован
                if len(team_name) == 0:
                    # КАПИТАН ПОВТОРНЫЙ
                    # предлагаем зарегистрироваться повторно быстрее, не вводить заново всю инфу
                    if len(all_dates_capt) != 0:
                        await bot.send_message(message.chat.id,
                                               text="Желаете зарегистрироваться быстрее или ввести всё заново?",
                                               reply_markup=keyboards.previous_or_new)
                        await CaptainStates.Prev_data_or_new.set()
                    # если длина этого списка == 0, то этот капитан НИКОГДА не регистрировался в базе
                    # КАПИТАН НОВИЧОК
                    else:
                        await bot.send_message(message.chat.id,
                                               text='Вы капитан! Придумайте название для своей команды. '
                                                    'Придерживаемся приличия. 😉',
                                               parse_mode='Markdown',
                                               reply_markup=types.ReplyKeyboardRemove())
                        await CaptainStates.Team_name.set()
                # если длина 'team_name' != 0, то на эту дату капитан уже зарегистрирован
                else:
                    await bot.send_message(message.chat.id,
                                           text=f"Вы уже зарегистрированы на эту игру как "
                                                f"капитан команды *{team_name[0][0]}*\n"
                                                "Можете выбрать другую игру 😊",
                                           reply_markup=keyboards.game_dates_buttons, parse_mode='Markdown')
                    await CaptainStates.Choose_date.set()
            # капитан на выбранную дату зарегистрирован как одиночный игрок
            else:
                await bot.send_message(message.chat.id,
                                       text=f"На выбранную дату вы зарегистрированы как "
                                            f"одиночный игрок *{lonely_player_name_check[0][0]}*\n"
                                            "Попробуйте выбрать другую дату 😊",
                                       reply_markup=keyboards.game_dates_buttons, parse_mode='Markdown')
                await CaptainStates.Choose_date.set()
        # капитан на выбранную дату зарегистрирован как игрок команды
        else:
            await bot.send_message(message.chat.id,
                                   text=f"На выбранную дату вы зарегистрированы как игрок *{player_name_check[0][0]}*\n"
                                        "Попробуйте выбрать другую дату 😊",
                                   reply_markup=keyboards.game_dates_buttons, parse_mode='Markdown')
            await CaptainStates.Choose_date.set()
    elif message.text == 'Одиночный участник':
        # прежде, чем пойти в регистрацию одиночного участника, нужно проверить,
        # не зарегистрирован ли он на выбранную дату в кач-ве капитана или как игрок команды
        lon_player_id = int(message.from_user.id)
        await state.update_data(lon_player_id=lon_player_id)
        data = await state.get_data()
        game_date_from_fsm_user_style = data.get('game_date')
        day = game_date_from_fsm_user_style[0:2]
        month = game_date_from_fsm_user_style[3:5]
        year = game_date_from_fsm_user_style[6:10]
        date_for_check = f"{year}{month}{day}"
        lonely_player_telegram_id_game_date = (str(data.get('lon_player_id')) + date_for_check)
        cap_name = sql_commands.select_captname_by_capid_gamedate(lonely_player_telegram_id_game_date)
        player_name_from_db = sql_commands.select_player_name_by_playerid_gamedate(lonely_player_telegram_id_game_date)
        lonely_player_name_check = sql_commands.select_lonely_player_name_by_lonely_playerid_gamedate(
            lonely_player_telegram_id_game_date)
        if len(cap_name) == 0:
            if len(player_name_from_db) == 0:
                if len(lonely_player_name_check) == 0:
                    await bot.send_message(message.chat.id,
                                           text='Вы одиночный участник!\nНапишите ваше имя ⬇️',
                                           reply_markup=types.ReplyKeyboardRemove())
                    await LonelyPlayerStates.Lonely_player_name.set()
                else:
                    await bot.send_message(message.chat.id,
                                           text=f"На выбранную дату вы зарегистрированы как "
                                                f"одиночный игрок *{lonely_player_name_check[0][0]}*\n"
                                                "Попробуйте выбрать другую дату 😊",
                                           reply_markup=keyboards.game_dates_buttons, parse_mode='Markdown')
                    await CaptainStates.Choose_date.set()
            else:
                await bot.send_message(message.chat.id,
                                       text=f"Вы уже зарегистрированы на данную игру "
                                            f"как игрок *{player_name_from_db[0][0]}*"
                                            f"Попробуйте выбрать другую дату 😊",
                                       parse_mode='Markdown', reply_markup=keyboards.game_dates_buttons)
                await CaptainStates.Choose_date.set()
        else:
            await bot.send_message(message.chat.id,
                                   text=f'Вы уже зарегистрированы на данную игру как капитан *{cap_name[0][0]}*'
                                        f'Попробуйте выбрать другую дату 😊',
                                   parse_mode='Markdown', reply_markup=keyboards.game_dates_buttons)
            await CaptainStates.Choose_date.set()
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔄\n"
                                                     "Капитан или одиночный участник?\n"
                                                     "Жмите кнопочки ⬇️")


"""

-------------------------------------->>>> БЛОК КОДА ДЛЯ РЕГИСТРАЦИИ КАПИТАНА <<<<--------------------------------------

"""


# ЛОВИТ НАЗВАНИЕ КОМАНДЫ
@dp.message_handler(state=CaptainStates.Team_name)
async def team_name_handler(message: types.Message, state: FSMContext):
    # сюда попадает НАЗВАНИЕ КОМАНДЫ, вписанное капитаном
    # сохраняем НАЗВАНИЕ КОМАНДЫ в переменную "team_name"
    team_name = message.text
    # обновляем СОСТОЯНИЕ (Team_name) данными,
    # ключ - 'team_name', значение - НАЗВАНИЕ КОМАНДЫ
    await state.update_data(team_name=team_name)
    # шлём польз-лю сообщение что данные сохранены, провешиваем клавиатуру 'Редактировать - Далее'
    await bot.send_message(message.chat.id, f"Название команды: *{team_name}*.\nСохраняем 👌",
                           reply_markup=keyboards.edit_data, parse_mode='Markdown')
    await CaptainStates.Team_name_support.set()


# хэндлер ловит кнопки РЕДАКТИРОВАТЬ - ДАЛЕЕ
@dp.message_handler(state=CaptainStates.Team_name_support)
async def team_name_support(message: types.Message):
    if message.text == 'Редактировать':
        # просит поль-ля снова ввести название команды
        await bot.send_message(message.chat.id, text='Введите новое название команды',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Team_name.set()
    # обработка кнопки "Далее", запрос имени (для след.состояния), пропуск в следующее состояние Capt_name
    elif message.text == 'Далее':
        await bot.send_message(message.chat.id, text="Напишите ваше имя",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Capt_name.set()
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


# ЛОВИТ имя КАПИТАНА
@dp.message_handler(state=CaptainStates.Capt_name)
async def captain_nik_handler(message: types.Message, state: FSMContext):
    # сюда попадает имя КАПИТАНА
    # сохраняем ИМЯ КАПИТАНА в переменную 'capt_name'
    capt_name = message.text
    # создаём реферальный код для капитана
    data = await state.get_data()
    capt_telegram_id_from_fsm = data.get('capt_telegram_id')
    capt_referral = f"https://t.me/{config.bot_nickname}?start={capt_telegram_id_from_fsm}"
    # обновляем СОСТОЯНИЕ (Capt_name) данными,
    # ключ - 'capt_name', значение - НИК КАПИТАНА КОМАНДЫ
    # ключ - 'capt_referral', значение - РЕФЕРАЛЬНЫЙ КОД
    await state.update_data(capt_name=capt_name, capt_referral=capt_referral)
    # шлём капитану сообщение, что данные сохранены, провешиваем клавиатуру 'Редактировать', 'Далее'
    await bot.send_message(message.chat.id, f"Ваше имя сохранено, *{capt_name}* 😉",
                           reply_markup=keyboards.edit_data, parse_mode='Markdown')
    await CaptainStates.Capt_name_support.set()


@dp.message_handler(state=CaptainStates.Capt_name_support)
async def capt_name_support(message: types.Message):
    # этот кусок кода срабатывает при нажатии кнопки 'Редактировать'
    if message.text == 'Редактировать':
        # запрашивает повторное введение имени
        await bot.send_message(message.chat.id, text='Напишите ваше имя',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Capt_name.set()
    # обработка кнопки "Далее", запрос кол-ва игроков для след.состония, перевод в след.состояние
    elif message.text == 'Далее':
        await bot.send_message(message.chat.id, text='Укажите количество игроков. (Можно примерно).',
                               reply_markup=keyboards.amount_part_keyboard)
        await CaptainStates.Amount_participants.set()
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


# ЛОВИТ КОЛИЧЕСТВО ИГРОКОВ (ИЗ ИНЛАЙН-КНОПОК)
@dp.callback_query_handler(text_contains='', state=CaptainStates.Amount_participants)
async def amount_of_team(call: types.CallbackQuery, state: FSMContext):
    # сюда попадает КОЛИЧЕСТВО ИГРОКОВ в виде callback_query
    amount_players = int(call['data'])
    await state.update_data(amount_players=amount_players)
    # шлём польз-лю сообщение, что данные сохранены, провешиваем клавиатуру 'Редактировать', 'Далее'
    await bot.send_message(call.message.chat.id, text=f"Количество игроков: *{call['data']}*. \nЗаписано 👍",
                           reply_markup=keyboards.edit_data, parse_mode='Markdown')
    # назначаем состояние для след. хэндлера, будет ловить "Редактировать - Далее"
    await CaptainStates.Amount_participants_new.set()


# здесь обрабатываем нажатие кнопок РЕДАКТИРОВАТЬ или ДАЛЕЕ
@dp.message_handler(state=CaptainStates.Amount_participants_new)
async def edit_amount_or_not(message: types.Message):
    if message.text == "Редактировать":
        await bot.send_message(message.chat.id, text='Укажите количество игроков. (Можно примерно)',
                               reply_markup=keyboards.amount_part_keyboard)
        await CaptainStates.Amount_participants.set()
    elif message.text == 'Далее':
        await bot.send_message(message.chat.id,
                               text="Впишите ваш номер телефона. \nБот принимает только польские номера 🇵🇱\n"
                                    "Начало должно быть +48 или 48", reply_markup=types.ReplyKeyboardRemove())
        await CaptainStates.Capt_phone_number.set()
    else:
        await message.answer('Произошла какая-то ошибка. Попробуйте ещё раз 🔁\n'
                             'Нажимайте кнопочки ⬇️')


# ЛОВИТ НОМЕР ТЕЛЕФОНА КАПИТАНА
@dp.message_handler(state=CaptainStates.Capt_phone_number)
async def capt_phone(message: types.Message, state: FSMContext):
    # сюда попадает НОМЕР ТЕЛЕФОНА КАПИТАНА
    # обрабатываем исключения, которые могут возникнуть, если вписать вместо цифр буквы
    try:
        # сохраняем НОМЕР ТЕЛЕФОНА (тип данных пока 'str')
        capt_phone_number = message.text
        # очищаем строчку с номером от "+", "(", ")" и пробелов, приводим к типу 'int'
        capt_phone_number_int = int(
            capt_phone_number.replace('+', '').replace(' ', '').replace('(', '').replace(')', ''))
    # в случае возникновение исключения (были введены буквы)
    except ValueError:
        # отравляем сообщение, просим повторно ввести телефон
        await message.answer(text="Неверный ввод.\nПопробуйте ещё раз 🔁")
    # когда всё внесено правильно (цифрами)
    else:
        # проверяем, чтобы телефон был польским, начинался с +48 или 48
        # проверяем пер-ю "capt_phone_number", т.к. это строка
        if capt_phone_number.startswith('+48') or capt_phone_number.startswith('48'):
            # также польский номер без кода +48 должен содержать в себе 9 цифр
            # проверяем это длиной строки, в кот-ю мы превратили наш номер без +() и пробелов и из кот-й удалили 48
            if len(str(capt_phone_number_int).replace('48', '')) == 9:
                # записываем телефон в состояние по ключу "capt_phone_number", в виде строки, без пробелов
                await state.update_data(capt_phone_number=capt_phone_number.replace(' ', ''))
                # пишем польз-лю, что данные сохранены, открываем клавиатуру 'Редактировать', 'Далее'
                await bot.send_message(message.chat.id, text=f"Номер телефона {capt_phone_number} сохранён 🥳",
                                       reply_markup=keyboards.edit_data)
                await CaptainStates.Capt_phone_number_support.set()
            # если в номере больше 9 цифр
            elif len(str(capt_phone_number_int).replace('48', '')) > 9:
                # пишем об этом польз-лю
                await message.answer(text="В вашем номере больше 9 цифр, попробуйте внимательнее",
                                     reply_markup=types.ReplyKeyboardRemove())
            # если в номере меньше 9 цифр
            elif len(str(capt_phone_number_int).replace('48', '')) < 9:
                # пишем об этом польз-лю
                await message.answer(text="В вашем номере меньше 9 цифр, попробуйте внимательнее",
                                     reply_markup=types.ReplyKeyboardRemove())
        # если телефон не начинается с +48 или 48, то он явно не польский
        else:
            # запрашиваем повторный ввод
            await message.answer(text="Введите польский номер 🇵🇱\n(начинается с +48 или 48) 😊",
                                 reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=CaptainStates.Capt_phone_number_support)
async def capt_phone_number_support(message: types.Message):
    if message.text == 'Редактировать':
        await bot.send_message(message.chat.id, text='Введите номер телефона ещё раз 🔁\n'
                                                     'Бот принимает только польские номера 🇵🇱\n'
                                                     'Начало должно быть +48 или 48',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Capt_phone_number.set()
    # обработка кнопки "Далее", запрос соц.сети (для след.состояния), пропуск в следующее состояние
    elif message.text == 'Далее':
        await bot.send_message(message.chat.id, text="Выберите соц.сеть/мессенджер, по которой с вами можно связаться.",
                               reply_markup=keyboards.soc_network)
        await CaptainStates.Choose_soc_net.set()
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


# хэндлер-"маршрутизатор", ловит нажатие кнопок "Telegram", "Instagram", "Facebook"
@dp.message_handler(state=CaptainStates.Choose_soc_net)
async def capt_soc_net(message: types.Message):
    # при нажатии кнопки пишем сообщение, переводим в следующий стейт
    if message.text == "Telegram":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш аккаунт Telegram",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Telegram.set()
    elif message.text == "Instagram":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш Instagram аккаунт",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Instagram.set()
    elif message.text == "Facebook":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш Facebook аккаунт",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Facebook.set()
    elif message.text == "Другое":
        await bot.send_message(message.chat.id, text="Внесите ссылку", reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Other_soc_net.set()
    else:
        await message.answer('Произошла какая-то ошибка. Попробуйте ещё раз 🔁\n'
                             'Нажимайте кнопочки ⬇️')


# хэндлер для введения ссылки на телеграм
@dp.message_handler(state=CaptainStates.Telegram)
async def capt_link_telegram(message: types.Message, state: FSMContext):
    # сюда попадает ССЫЛКА НА ТЕЛЕГРАМ КАПИТАНА
    # проверка, чтобы ссылка на телегу начиналась с https://t.me/ или @ не была пустая
    if (message.text.startswith('https://t.me/') and len(message.text[13:]) != 0) or (
            message.text.startswith("@") and len(message.text[1:]) != 0):
        # сохраняем ссылку
        cap_link_telegram = message.text
        # записываем её в пространство имён состояния под ключом "capt_link"
        await state.update_data(capt_link=cap_link_telegram)
        # пишем сообщение о сохранении данных, открываем клавиатуру для редактир-я или перехода дальше
        await bot.send_message(message.chat.id, "Ссылка сохранена ✅", reply_markup=keyboards.edit_data)
        await CaptainStates.Link_support.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁")


# хэндлер для введения ссылки на инстаграм
@dp.message_handler(state=CaptainStates.Instagram)
async def capt_link_instagram(message: types.Message, state: FSMContext):
    # сюда попадает ССЫЛКА НА ИНСТАГРАМ КАПИТАНА
    # проверка, чтобы ссылка на инсту начиналась с чего надо и не была пустая
    if (message.text.startswith('https://www.instagram.com/') and len(message.text[26:]) != 0) or \
            (message.text.startswith('https://instagram.com/') and len(message.text[22:]) != 0):
        # сохраняем ссылку
        capt_link_inst = message.text
        # записываем её в пространство имён состояния под ключом "capt_link"
        await state.update_data(capt_link=capt_link_inst)
        # пишем, что всё сохранено, открываем клавиатуру для редактир-я или перехода дальше
        await bot.send_message(message.chat.id, "Ссылка на Instagram сохранена ✅", reply_markup=keyboards.edit_data)
        await CaptainStates.Link_support.set()
    # если ссылка начинается иначе
    else:
        # просим ещё раз написать
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁")


# хэндлер для введения ссылки на фэйсбук
@dp.message_handler(state=CaptainStates.Facebook)
async def capt_link_facebook(message: types.Message, state: FSMContext):
    # сюда попадает ССЫЛКА НА ФЭЙСБУК КАПИТАНА
    # проверка, чтобы ссылка на фэйсбук начиналась с https://www.facebook.com/ и не была пустая
    if message.text.startswith('https://www.facebook.com/') and len(message.text[25:]) != 0:
        # сохраняем ссылку
        capt_link_fcbk = message.text
        # записываем её в пространство имён состояния под ключом "capt_link"
        await state.update_data(capt_link=capt_link_fcbk)
        # пишем сообщение, открываем клавиатуру для редактир-я или перехода дальше
        await bot.send_message(message.chat.id, "Ссылка на Facebook сохранена ✅", reply_markup=keyboards.edit_data)
        await CaptainStates.Link_support.set()
    # если ссылка начинается иначе
    else:
        # просим ещё раз написать
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁")


# хэндлер для ловли ссылки на другую соц.сеть
@dp.message_handler(state=CaptainStates.Other_soc_net)
async def capt_link_other_soc_net(message: types.Message, state: FSMContext):
    capt_link_other = message.text
    await state.update_data(capt_link=capt_link_other)
    await bot.send_message(message.chat.id, "Ссылка сохранена ✅", reply_markup=keyboards.edit_data)
    await CaptainStates.Link_support.set()


@dp.message_handler(state=CaptainStates.Link_support)
async def capt_link_telegram_support(message: types.Message):
    if message.text == 'Редактировать':
        # возвращаем юзера в предыдущий стейт, где он выбирал соц.сеть
        await bot.send_message(message.chat.id,
                               text="Выберите соц.сеть/мессенджер, по которой с вами можно связаться",
                               reply_markup=keyboards.soc_network)
        await CaptainStates.Choose_soc_net.set()
    # если нажата кнопка 'Далее'
    elif message.text == 'Далее':
        # задаём вопрос для след.стейта
        await bot.send_message(message.chat.id, text="Готовы ли вы принять в вашу команду игрока/ов? 👤",
                               reply_markup=keyboards.yes_or_no)
        # переводим в следующий стейт
        await CaptainStates.Lonely_player.set()
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


# хэндлер ловит нажание кнопок ДА или НЕТ после вопроса об одиноких игроках
@dp.message_handler(state=CaptainStates.Lonely_player)
async def capt_agree_lonely_player(message: types.Message, state: FSMContext):
    # при нажатии кнопки "Да"
    if message.text == 'Да':
        # записываем согласие в переменную в виде булевого значения "True"
        capt_agree = True
        # записываем это в пространство имён состояния
        await state.update_data(capt_agree=capt_agree)
        # шлём сообщение, выставляем клавиатуру РЕДАКТИРОВАТЬ - ДАЛЕЕ
        await bot.send_message(message.chat.id, "Так и запишем!", reply_markup=keyboards.edit_data)
        # присваиваем следующий стейт (будет отлавливать кнопки РЕДАКТИРОВАТЬ - ДАЛЕЕ)
        await CaptainStates.Lonely_player_support.set()
    # при нажатии кнопки "Нет"
    elif message.text == 'Нет':
        # записываем несогласие в переменную в виде булевого значения "False"
        capt_agree = False
        # записываем это в пространство имён состояния
        await state.update_data(capt_agree=capt_agree)
        # шлём сообщение, выставляем клавиатуру РЕДАКТИРОВАТЬ - ДАЛЕЕ
        await bot.send_message(message.chat.id, "Так и запишем!", reply_markup=keyboards.edit_data)
        # присваиваем следующий стейт (будет отлавливать кнопки РЕДАКТИРОВАТЬ - ДАЛЕЕ)
        await CaptainStates.Lonely_player_support.set()
    else:
        await message.answer("Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


# хэндлер ловит кнопки РЕДАКТИРОВАТЬ - ДАЛЕЕ (после сохранения ответа о согласии)
@dp.message_handler(state=CaptainStates.Lonely_player_support)
async def capt_agree_lonely_player_support(message: types.Message):
    # при нажатии кнопки "Редактировать"
    if message.text == 'Редактировать':
        # снова задаём вопрос
        await bot.send_message(message.chat.id, text='Готовы ли вы принять в вашу команду игрока/ов? 👤 ',
                               reply_markup=keyboards.yes_or_no)
        # возвращаем поль-ля в предыдущее состояние
        await CaptainStates.Lonely_player.set()
    # если нажата кнопка "Далее"
    elif message.text == 'Далее':
        # задаём вопрос для следующего состояния, вывешиваем клавиатуру ДА или НЕТ
        await bot.send_message(message.chat.id, text='Есть ли у вас комментарии? 📝', reply_markup=keyboards.yes_or_no)
        # присваиваем следующее состояние
        await CaptainStates.Capt_comments.set()
    else:
        await message.answer('Произошла какая-то ошибка. Попробуйте ещё раз 🔁')


# хэндлер ловит нажатие кнопок ДА или НЕТ после вопроса 'Есть ли у вас комментарии?'
@dp.message_handler(state=CaptainStates.Capt_comments)
async def capt_comment_handler(message: types.Message, state: FSMContext):
    # при нажатии кнопки "Да"
    if message.text == 'Да':
        # запрашиваем у капитана комментарий, закрываем какие бы то ни было клавиатуры
        await bot.send_message(message.chat.id, "Внесите ваш комментарий ✏️",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        # присваиваем стейт, в котором будет ожидаться ввод текста с комментарием и сохранение его
        await CaptainStates.Capt_comments_support_enter.set()
    # при нажатии кнопки "Нет"
    elif message.text == 'Нет':
        # запишем как пустую строку
        capt_comment = ''
        await state.update_data(capt_comment=capt_comment)
        # пишем, выставляем клавиатуру РЕДАКТИРОВАТЬ - ДАЛЕЕ
        await bot.send_message(message.chat.id, f"Сохранили!", reply_markup=keyboards.edit_data)
        # присваиваем следующий стейт (будет отлавливать кнопки РЕДАКТИРОВАТЬ - ДАЛЕЕ)
        await CaptainStates.Capt_comments_support.set()
    else:
        await message.answer("Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


# хэндлер ожидает ввод текста комментария
@dp.message_handler(state=CaptainStates.Capt_comments_support_enter)
async def capt_comment_enter_handler(message: types.Message, state: FSMContext):
    # сохраняем этот комментарий
    capt_comment = message.text
    await state.update_data(capt_comment=capt_comment)
    # кинули в польз-ля сообщение, открыли клавиатуру РЕДАКТИРОВАТЬ - ДАЛЕЕ
    await bot.send_message(message.chat.id, text="Записали 👍", reply_markup=keyboards.edit_data)
    await CaptainStates.Capt_comments_support.set()


# хэндлер ловит кнопки РЕДАКТИРОВАТЬ - ДАЛЕЕ после сохранения комментария
@dp.message_handler(state=CaptainStates.Capt_comments_support)
async def capt_comment_support_handler(message: types.Message):
    # при нажатии кнопки "Редактировать"
    if message.text == 'Редактировать':
        # снова задаём вопрос
        await bot.send_message(message.chat.id, text='Есть ли у вас комментарии? 📝',
                               reply_markup=keyboards.yes_or_no)
        # возвращаем поль-ля в предыдущее состояние
        await CaptainStates.Capt_comments.set()
    # если нажата кнопка "Далее"
    elif message.text == 'Далее':
        # пишем, что дальше будет вывод всей внесённой ранее информации
        await bot.send_message(message.chat.id,
                               text='следующее сообщение будет выводом всей введённой ранее информации',
                               reply_markup=keyboards.ok_keyboard)
        # присваиваем следующее состояние
        await CaptainStates.Show_info_to_capt.set()
    else:
        await message.answer('Произошла какая-то ошибка. Попробуйте ещё раз 🔁')


# здесь шлём сообщение капитану со всей введённой им информацией, чтобы он проверил всё ли ок
@dp.message_handler(state=CaptainStates.Show_info_to_capt)
async def show_info_to_captain(message: types.Message, state: FSMContext):
    # вытягиваем всё что есть в fsm
    data = await state.get_data()
    game_date_user_style_from_fsm = data.get('game_date')
    n_day = game_date_user_style_from_fsm[0:2]
    n_month = game_date_user_style_from_fsm[3:5]
    n_year = game_date_user_style_from_fsm[6:10]
    game_date_db_style = f"{n_year}{n_month}{n_day}"
    week_day_from_fsm = data.get('week_day')
    game_time_from_fsm = data.get('game_time')
    team_name_from_fsm = data.get('team_name')
    capt_telegram_id_from_fsm = data.get('capt_telegram_id')
    capt_name_from_fsm = data.get('capt_name')
    capt_referral_from_fsm = data.get('capt_referral')
    amount_players_from_fsm = data.get('amount_players')
    capt_phone_number_from_fsm = data.get('capt_phone_number')
    capt_link_from_fsm = data.get('capt_link')
    capt_agree_from_fsm = str(data.get('capt_agree'))
    capt_comment_from_fsm = data.get('capt_comment')
    capt_telegram_id_game_date_from_fsm = (str(data.get('capt_telegram_id')) + game_date_db_style)
    # в таком виде передаём в базу для записи
    date_string_for_db = f"{n_year}-{n_month}-{n_day} {game_time_from_fsm}:00"
    if message.text == "Ок":
        # капитан СОГЛАСЕН НА ОДИНОКОГО ИГРОКА
        if capt_agree_from_fsm is True or capt_agree_from_fsm == 'True':
            # у капитана НЕТ КОММЕНТАРИЕВ
            if len(capt_comment_from_fsm) == 0:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_fsm}*\n'
                                            f'Имя капитана: *{capt_name_from_fsm}*\n'
                                            f'Количество участников в команде: *{amount_players_from_fsm}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_fsm}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_fsm}*\n'
                                            f'Согласен/согласна присоединить одиноких игрока/игроков',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
            # у капитана ЕСТЬ КОММЕНТАРИЙ
            else:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_fsm}*\n'
                                            f'Имя капитана: *{capt_name_from_fsm}*\n'
                                            f'Количество участников в команде: *{amount_players_from_fsm}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_fsm}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_fsm}*\n'
                                            f'Согласен/согласна присоединить одиноких игрока/игроков\n'
                                            f'Ваш комментарий: *{capt_comment_from_fsm}*',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
        # капитан НЕ СОГЛАСЕН НА ОДИНОЧЕК
        else:
            # у капитана НЕТ КОММЕНТАРИЕВ
            if capt_comment_from_fsm is None or len(capt_comment_from_fsm) == 0:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_fsm}*\n'
                                            f'Имя капитана: *{capt_name_from_fsm}*\n'
                                            f'Количество участников в команде: *{amount_players_from_fsm}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_fsm}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_fsm}*\n'
                                            f'Не согласен/не согласна присоединить одиноких игрока/игроков',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
            # у капитана ЕСТЬ КОММЕНТАРИЙ
            else:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_fsm}*\n'
                                            f'Имя капитана: *{capt_name_from_fsm}*\n'
                                            f'Количество участников в команде: *{amount_players_from_fsm}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_fsm}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_fsm}*\n'
                                            f'Не согласен/не согласна присоединить одиноких игрока/игроков\n'
                                            f'Ваш комментарий: *{capt_comment_from_fsm}*',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
    elif message.text == "Завершить регистрацию":
        # СОХРАНЯЕМ В БАЗУ ДАННЫХ
        sql_commands.saving_cap_info_to_database(capt_telegram_id_game_date_from_fsm, capt_telegram_id_from_fsm,
                                                 date_string_for_db, week_day_from_fsm, capt_name_from_fsm,
                                                 capt_phone_number_from_fsm, capt_link_from_fsm, capt_referral_from_fsm,
                                                 team_name_from_fsm, amount_players_from_fsm,
                                                 capt_agree_from_fsm, capt_comment_from_fsm)
        await bot.send_message(message.chat.id, text="Поздравляем, вы зарегистрированы на игру! 🥳",
                               reply_markup=types.ReplyKeyboardRemove())
        # ШЛЁМ РЕФЕРАЛЬНУЮ ССЫЛКУ ДЛЯ ПРИГЛАШЕНИЯ УЧАСТНИКОВ
        await bot.send_message(message.chat.id,
                               text='Можете пригласить участников в свою команду, выслав им реферальную ссылку ⬇️',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await bot.send_message(message.chat.id, text=f"{capt_referral_from_fsm}",
                               reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
    elif message.text == "Редактировать данные":
        await bot.send_message(message.chat.id,
                               text='Выберите команду и нажмите на неё для редактирования конкретных данных',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        # шлём список команд для редактирования данных в формате "/команда"
        await bot.send_message(message.chat.id, text=f'{commands.capt_commands}',
                               reply_markup=types.ReplyKeyboardRemove())
        await CaptainStates.Finish_edit.set()
    else:
        await message.answer('Что-то не так. Попробуйте ещё раз 🔁')


"""

------------------------------------->>>> БЛОК КОМАНД ДЛЯ РЕДАКТИРОВАНИЯ ДАННЫХ <<<<------------------------------------
----------------------------------------------->>>> ДЛЯ КАПИТАНА <<<<---------------------------------------------------
"""


@dp.message_handler(Command('game_date'), state=CaptainStates.Finish_edit)
async def captain_edit_game_date(message: types.Message):
    await bot.send_message(message.chat.id, text='Выберите дату игры', reply_markup=keyboards.game_dates_buttons)
    await CaptainStates.Edit_game_date.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_game_date)
async def catch_new_captain_date(message: types.Message, state: FSMContext):
    all_about_one_date = message.text
    all_dates = sql_commands.all_dates_from_game_dates()
    list_of_dates = []
    for one_tuple in all_dates:
        list_of_dates.append(f"{one_tuple[0]} {one_tuple[1]} {one_tuple[2]}")
    game_date_in_list = re.findall(r'\d\d.\d\d.\d\d\d\d', all_about_one_date)
    game_date = game_date_in_list[0]
    week_day_in_list = re.findall(r'([А-я][а-я]+)', all_about_one_date)
    week_day = week_day_in_list[0]
    game_time_in_list = re.findall(r'\d\d:\d\d', all_about_one_date)
    game_time = game_time_in_list[0]
    # проверка - что дата пришедшая в хэндлер полностью совпадает с датой из базы
    if f"{game_date} {week_day} {game_time}" in list_of_dates:
        data = await state.get_data()
        n_day = all_about_one_date[0:2]
        n_month = all_about_one_date[3:5]
        n_year = all_about_one_date[6:10]
        date_for_check = f"{n_year}{n_month}{n_day}"
        capt_telegram_id_game_date = (str(data.get('capt_telegram_id')) + date_for_check)
        lonely_player_name_check = sql_commands.select_lonely_player_name_by_lonely_playerid_gamedate(
            capt_telegram_id_game_date)
        team_name = sql_commands.check_team_name_into_base_by_captid_date(capt_telegram_id_game_date)
        # проверяем, чтобы капитан не был зарегистрирован нигде как игрок
        player_name_check = sql_commands.select_player_name_by_playerid_gamedate(capt_telegram_id_game_date)
        if len(player_name_check) == 0:
            # также проверяем что капитан не числится на эту дату и как одиночный игрок
            if len(lonely_player_name_check) == 0:
                # проверка, чтобы капитан не был зарегистрирован на вновь выбранную дату
                if len(team_name) == 0:
                    await state.update_data(game_date=game_date, week_day=week_day, game_time=game_time)
                    await bot.send_message(message.chat.id, text='Записали!', reply_markup=keyboards.ok_keyboard)
                    await CaptainStates.Show_info_to_capt.set()
                else:
                    await bot.send_message(message.chat.id,
                                           text=f"Вы уже зарегистрированы на эту игру как "
                                                f"капитан команды *{team_name[0][0]}*\n"
                                                "Попробуйте ещё раз 🔁", parse_mode='Markdown')
            # капитан на выбранную дату зарегистрирован как одиночный игрок
            else:
                await bot.send_message(message.chat.id,
                                       text=f"На выбранную дату вы зарегистрированы как "
                                            f"одиночный игрок *{lonely_player_name_check[0][0]}*\n"
                                            "Попробуйте выбрать другую дату 😊", parse_mode='Markdown')
        # капитан на выбранную дату зарегистрирован как игрок команды
        else:
            await bot.send_message(message.chat.id,
                                   text=f"На выбранную дату вы зарегистрированы как игрок *{player_name_check[0][0]}*\n"
                                        "Попробуйте выбрать другую дату 😊", parse_mode='Markdown')
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁\n"
                                                     "Жмите кнопочки ⬇️")


@dp.message_handler(Command('team_name'), state=CaptainStates.Finish_edit)
async def captain_edit_team_name(message: types.Message):
    await bot.send_message(message.chat.id, text='Впишите новое название команды',
                           reply_markup=keyboards.ReplyKeyboardRemove())
    await CaptainStates.Edit_team_name.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_team_name)
async def catch_captain_team_name(message: types.Message, state: FSMContext):
    new_team_name = message.text
    await state.update_data(team_name=new_team_name)
    await bot.send_message(message.chat.id, text='Новое название команды записано!',
                           reply_markup=keyboards.ok_keyboard)
    await CaptainStates.Show_info_to_capt.set()


@dp.message_handler(Command('capt_name'), state=CaptainStates.Finish_edit)
async def captain_edit_capt_name(message: types.Message):
    await bot.send_message(message.chat.id, text='Напишите ваше имя', reply_markup=keyboards.ReplyKeyboardRemove())
    await CaptainStates.Edit_capt_name.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_name)
async def catch_captain_name(message: types.Message, state: FSMContext):
    new_capt_name = message.text
    await state.update_data(capt_name=new_capt_name)
    await bot.send_message(message.chat.id, text=f"Ваше имя сохранено, *{new_capt_name}* 😉",
                           reply_markup=keyboards.ok_keyboard, parse_mode='Markdown')
    await CaptainStates.Show_info_to_capt.set()


@dp.message_handler(Command('amount_players'), state=CaptainStates.Finish_edit)
async def captain_edit_amount_players(message: types.Message):
    await bot.send_message(message.chat.id, text='Укажите количество игроков. (Можно примерно)',
                           reply_markup=keyboards.amount_part_keyboard)
    await CaptainStates.Edit_amount_participants.set()


@dp.callback_query_handler(text_contains='', state=CaptainStates.Edit_amount_participants)
async def catch_captain_amount_players(call: types.CallbackQuery, state: FSMContext):
    amount_players = int(call['data'])
    await state.update_data(amount_players=amount_players)
    await bot.send_message(call.message.chat.id, text=f"Количество игроков: *{amount_players}*. \nЗаписано 👍",
                           reply_markup=keyboards.ok_keyboard, parse_mode='Markdown')
    await CaptainStates.Show_info_to_capt.set()


@dp.message_handler(Command('capt_phone'), state=CaptainStates.Finish_edit)
async def captain_edit_capt_phone(message: types.Message):
    await bot.send_message(message.chat.id,
                           text="Впишите ваш номер телефона. \nБот принимает только польские номера 🇵🇱\n"
                                "Начало должно быть +48 или 48", reply_markup=keyboards.ReplyKeyboardRemove())
    await CaptainStates.Edit_capt_phone.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_phone)
async def catch_captain_capt_phone(message: types.Message, state: FSMContext):
    try:
        new_capt_phone = message.text
        new_capt_phone_int = int(
            new_capt_phone.replace('+', '').replace(' ', '').replace('(', '').replace(')', ''))
    except ValueError:
        await message.answer('Неверный ввод.\nПопробуйте ещё раз 🔁"', reply_markup=types.ReplyKeyboardRemove())
    else:
        if new_capt_phone.startswith('+48') or new_capt_phone.startswith('48'):
            if len(str(new_capt_phone_int).replace('48', '')) == 9:
                await state.update_data(capt_phone_number=new_capt_phone.replace(' ', ''))
                await bot.send_message(message.chat.id, text=f"Номер телефона {new_capt_phone} сохранён 🥳",
                                       reply_markup=keyboards.ok_keyboard)
                await CaptainStates.Show_info_to_capt.set()
            elif len(str(new_capt_phone_int).replace('48', '')) > 9:
                await message.answer(text="В вашем номере больше 9 цифр, попробуйте внимательнее",
                                     reply_markup=types.ReplyKeyboardRemove())
            elif len(str(new_capt_phone_int).replace('48', '')) < 9:
                await message.answer(text="В вашем номере меньше 9 цифр, попробуйте внимательнее",
                                     reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer(text="Введите польский номер 🇵🇱\n(начинается с +48 или 48) 😊",
                                 reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(Command('capt_link'), state=CaptainStates.Finish_edit)
async def captain_edit_link(message: types.Message):
    await bot.send_message(message.chat.id, text='Выберите соц.сеть/мессенджер, по которой с вами можно связаться.',
                           reply_markup=keyboards.soc_network)
    await CaptainStates.Edit_capt_link.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_link)
async def catch_captain_link(message: types.Message):
    if message.text == "Telegram":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш аккаунт Telegram",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Edit_capt_link_telegram.set()
    elif message.text == "Instagram":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш Instagram аккаунт",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Edit_capt_link_instagram.set()
    elif message.text == "Facebook":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш Facebook аккаунт",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Edit_capt_link_facebook.set()
    elif message.text == "Другое":
        await bot.send_message(message.chat.id, text="Внесите ссылку", reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Edit_capt_link_other_soc_net.set()
    else:
        await message.answer('Ошибка. Попробуйте ещё раз 🔁')


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_link_telegram)
async def catch_captain_link_telegram(message: types.Message, state: FSMContext):
    if (message.text.startswith('https://t.me/') and len(message.text[13:]) != 0) or (
            message.text.startswith("@") and len(message.text[1:]) != 0):
        new_link_tel = message.text
        await state.update_data(capt_link=new_link_tel)
        await bot.send_message(message.chat.id, text='Ссылка сохранена ✅', reply_markup=keyboards.ok_keyboard)
        await CaptainStates.Show_info_to_capt.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_link_instagram)
async def catch_captain_link_instagram(message: types.Message, state: FSMContext):
    if (message.text.startswith('https://www.instagram.com/') and len(message.text[26:]) != 0) or \
            (message.text.startswith('https://instagram.com/') and len(message.text[22:]) != 0):
        new_link_inst = message.text
        await state.update_data(capt_link=new_link_inst)
        await bot.send_message(message.chat.id, text='Ссылка на Instagram сохранена ✅',
                               reply_markup=keyboards.ok_keyboard)
        await CaptainStates.Show_info_to_capt.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_link_facebook)
async def catch_captain_link_facebook(message: types.Message, state: FSMContext):
    if message.text.startswith('https://www.facebook.com/') and len(message.text[25:]) != 0:
        new_link_facb = message.text
        await state.update_data(capt_link=new_link_facb)
        await bot.send_message(message.chat.id, text='Ссылка на Facebook сохранена ✅',
                               reply_markup=keyboards.ok_keyboard)
        await CaptainStates.Show_info_to_capt.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_link_other_soc_net)
async def catch_captain_link_other_soc_net(message: types.Message, state: FSMContext):
    new_link_other_soc_net = message.text
    await state.update_data(capt_link=new_link_other_soc_net)
    await bot.send_message(message.chat.id, text='Ссылка сохранена ✅',
                           reply_markup=keyboards.ok_keyboard)
    await CaptainStates.Show_info_to_capt.set()


@dp.message_handler(Command('lonely_player'), state=CaptainStates.Finish_edit)
async def captain_edit_agree_lonely_player(message: types.Message):
    await bot.send_message(message.chat.id, text='Готовы ли вы принять в вашу команду игрока/ов? 👤 ',
                           reply_markup=keyboards.yes_or_no)
    await CaptainStates.Edit_lonely_player.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_lonely_player)
async def catch_captain_agree_lonely_player(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        new_capt_agree = True
        await state.update_data(capt_agree=new_capt_agree)
        await bot.send_message(message.chat.id, "Так и запишем!", reply_markup=keyboards.ok_keyboard)
        await CaptainStates.Show_info_to_capt.set()
    elif message.text == 'Нет':
        new_capt_agree = False
        await state.update_data(capt_agree=new_capt_agree)
        await bot.send_message(message.chat.id, "Так и запишем!", reply_markup=keyboards.ok_keyboard)
        await CaptainStates.Show_info_to_capt.set()
    else:
        await message.answer("Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


@dp.message_handler(Command('capt_comment'), state=CaptainStates.Finish_edit)
async def captain_edit_comment(message: types.Message):
    await bot.send_message(message.chat.id, text='Есть ли у вас комментарии? 📝',
                           reply_markup=keyboards.yes_or_no)
    await CaptainStates.Edit_capt_comment.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_comment)
async def catch_captain_comment(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        await bot.send_message(message.chat.id, "Внесите ваш комментарий ✏️",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Edit_capt_comment_enter.set()
    elif message.text == 'Нет':
        await state.update_data(capt_comment='')
        await bot.send_message(message.chat.id, "Сохранили!", reply_markup=keyboards.ok_keyboard)
        await CaptainStates.Show_info_to_capt.set()
    else:
        await message.answer("Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_comment_enter)
async def catch_captain_comment_enter(message: types.Message, state: FSMContext):
    new_comment = message.text
    await state.update_data(capt_comment=new_comment)
    await bot.send_message(message.chat.id, "Записали 👍", reply_markup=keyboards.ok_keyboard)
    await CaptainStates.Show_info_to_capt.set()


"""

-------------------------------------->>>> ПОВТОРНАЯ РЕГИСТРАЦИЯ КАПИТАНА <<<<------------------------------------------

"""


# ЛОВИТ НАЖАТИКЕ КНОПОК "Данные с предыдущих игр" ИЛИ "Новые данные"
# при повторной регистрации капитана
@dp.message_handler(state=CaptainStates.Prev_data_or_new)
async def cap_second_reg_new_or_old_data(message: types.Message, state: FSMContext):
    if message.text == 'Данные с предыдущих игр':
        # лезем в fsm, забираем id капитана
        data = await state.get_data()
        capt_telegram_id = data.get('capt_telegram_id')
        # обращаемся к базе, получаем список всех дат, на которые когда-либо регистрировался этот капитан
        # там должна быть как минимум одна дата, иначе капитан сюда бы не попал
        # пример списка: ['2023-08-14 19:00:00', '2023-08-16 18:00:00']
        # db style
        all_dates_capt = sql_commands.all_dates_captain_registered_is(capt_telegram_id)
        # если у капитана в базе только одна старая дата
        if len(all_dates_capt) == 1:
            # приводим старую дату к формату ДД.ММ.ГГГГ
            old_game_date_from_db = all_dates_capt[0]
            old_game_date_in_list = re.findall(r'\d\d\d\d-\d\d-\d\d', old_game_date_from_db)
            old_game_date = old_game_date_in_list[0]
            old_year = old_game_date[0:4]
            old_month = old_game_date[5:7]
            old_day = old_game_date[8:10]
            old_date_user_style = f"{old_day}.{old_month}.{old_year}"
            # сохраняем старую дату в fsm, чуть позже она нам понадобится
            await state.update_data(old_game_date=old_date_user_style)
            # информируем капитана, что нашли только одну запись с ним
            await bot.send_message(message.chat.id,
                                   text=f"Ранее вы регистрировались только на 1 игру датой: *{old_date_user_style}*",
                                   parse_mode='Markdown',
                                   reply_markup=keyboards.ok_keyboard)
            await CaptainStates.Old_data_show.set()
        # капитан регистрировался на несколько игр (как прошлых, так и будущих)
        elif len(all_dates_capt) > 1:
            # создаем клавиатуру со всеми этими датами
            # all_dates_capt = ['2023-08-14 19:00:00', '2023-08-16 18:00:00']
            all_dates_capt_user_style = []
            for one_date_time in all_dates_capt:
                one_date = one_date_time[0:10]
                year = one_date[0:4]
                month = one_date[5:7]
                day = one_date[8:10]
                one_date_user_style = f"{day}.{month}.{year}"
                all_dates_capt_user_style.append(one_date_user_style)
            dates_captain_registered_was = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                                                     one_time_keyboard=True, row_width=1)
            list_of_buttons_with_dates = []
            for one_date in all_dates_capt_user_style:
                one_button_date = types.KeyboardButton(f"{one_date}")
                list_of_buttons_with_dates.append(one_button_date)
            for date_button in list_of_buttons_with_dates:
                dates_captain_registered_was.insert(date_button)
            # даём капитану выбрать, с какой даты игры забрать старые данные регистрации
            await bot.send_message(message.chat.id,
                                   text="Выберите дату, откуда забирать прежние данные регистрации",
                                   reply_markup=dates_captain_registered_was)
            await CaptainStates.Old_data.set()
        else:
            await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁")
    elif message.text == 'Новые данные':
        await bot.send_message(message.chat.id,
                               text='Придумайте название для своей команды.'
                                    'Придерживаемся приличия. 😉',
                               parse_mode='Markdown',
                               reply_markup=types.ReplyKeyboardRemove())
        await CaptainStates.Team_name.set()
    else:
        await message.answer('Произошла какая-то ошибка. Попробуйте ещё раз 🔁\n'
                             'Хотите воспользоваться данными с прошлых игр или ввести новые данные?\n'
                             'Нажмите соответствующую кнопку ⬇️')


# принимает дату предыдущей игры, из которой нужно забрать данные
@dp.message_handler(state=CaptainStates.Old_data)
async def cap_second_reg_catch_old_data(message: types.Message, state: FSMContext):
    old_game_date_user_style = message.text
    data = await state.get_data()
    capt_telegram_id = data.get('capt_telegram_id')
    # нужно проверить, дата ли пришла в хэндлер
    if old_game_date_user_style.replace('.', '').isdigit():
        # ещё одна проверка, что на полученную дату капитан действительно когда-то был зарегистрирован
        if old_game_date_user_style in sql_commands.all_dates_captain_registered_is_without_time(capt_telegram_id):
            # записываем старую дату в fsm
            await state.update_data(old_game_date=old_game_date_user_style)
            await bot.send_message(message.chat.id,
                                   text=f"Итак, забираем данные регистрации с даты *{old_game_date_user_style}*",
                                   parse_mode='Markdown', reply_markup=keyboards.ok_keyboard)
            await CaptainStates.Old_data_show.set()
        else:
            await bot.send_message(message.chat.id, text="Ошибка. На выбранную дату вы не были зарегистрированы.")
    # пришли не цифры
    else:
        await bot.send_message(message.chat.id, text="Ошибка. Попробуйте ещё раз 🔁")


# здесь забираем старые данные из БД по старой дате и id капитана, показываем эти данные капитану
@dp.message_handler(state=CaptainStates.Old_data_show)
async def cap_second_reg_show_old_data(message: types.Message, state: FSMContext):
    if message.text == "Ок":
        data = await state.get_data()
        game_date_from_fsm = data.get('game_date')
        old_game_gate_user_style = data.get('old_game_date')
        week_day_from_fsm = data.get('week_day')
        game_time_from_fsm = data.get('game_time')
        day = old_game_gate_user_style[0:2]
        month = old_game_gate_user_style[3:5]
        year = old_game_gate_user_style[6:10]
        old_date_db_style = f"{year}{month}{day}"
        # из id капитана и старой даты игры формируем аргумент для передачи в функцию
        capt_tel_id_old_game_date = (str(data.get('capt_telegram_id')) + old_date_db_style)
        # обращаемся к базе, забираем все данные капитана из старой игры
        all_old_data_from_db = sql_commands.select_all_registr_info_by_capid_gamedate(capt_tel_id_old_game_date)
        capt_name_from_db = all_old_data_from_db[0][0]
        capt_phone_number_from_db = all_old_data_from_db[0][1]
        capt_link_from_db = all_old_data_from_db[0][2]
        capt_referral_from_db = all_old_data_from_db[0][3]
        team_name_from_db = all_old_data_from_db[0][4]
        amount_players_from_db = all_old_data_from_db[0][5]
        capt_agree_from_db = all_old_data_from_db[0][6]
        capt_comment_from_db = all_old_data_from_db[0][7]
        # шлём капитану все его старые данные
        # капитан СОГЛАСЕН НА ОДИНОКОГО ИГРОКА
        if capt_agree_from_db == 'True':
            # у капитана НЕТ КОММЕНТАРИЕВ
            if len(capt_comment_from_db) == 0:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_db}*\n'
                                            f'Имя капитана: *{capt_name_from_db}*\n'
                                            f'Количество участников в команде: *{amount_players_from_db}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_db}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_db}*\n'
                                            f'Согласен/согласна присоединить одиноких игрока/игроков',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
                await CaptainStates.Complete_new_registr.set()
            # у капитана ЕСТЬ КОММЕНТАРИЙ
            else:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_db}*\n'
                                            f'Имя капитана: *{capt_name_from_db}*\n'
                                            f'Количество участников в команде: *{amount_players_from_db}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_db}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_db}*\n'
                                            f'Согласен/согласна присоединить одиноких игрока/игроков\n'
                                            f'Ваш комментарий: *{capt_comment_from_db}*',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
                await CaptainStates.Complete_new_registr.set()
        # капитан НЕ СОГЛАСЕН НА ОДИНОЧЕК
        else:
            # у капитана НЕТ КОММЕНТАРИЕВ
            if len(capt_comment_from_db) == 0:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_db}*\n'
                                            f'Имя капитана: *{capt_name_from_db}*\n'
                                            f'Количество участников в команде: *{amount_players_from_db}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_db}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_db}*\n'
                                            f'Не согласен/не согласна присоединить одиноких игрока/игроков',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
                await CaptainStates.Complete_new_registr.set()
            # у капитана ЕСТЬ КОММЕНТАРИЙ
            else:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_db}*\n'
                                            f'Имя капитана: *{capt_name_from_db}*\n'
                                            f'Количество участников в команде: *{amount_players_from_db}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_db}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_db}*\n'
                                            f'Не согласен/не согласна присоединить одиноких игрока/игроков\n'
                                            f'Ваш комментарий: *{capt_comment_from_db}*',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
                await CaptainStates.Complete_new_registr.set()
        # запишем все старые данные в fsm
        await state.update_data(capt_name=capt_name_from_db, capt_phone_number=capt_phone_number_from_db,
                                capt_link=capt_link_from_db, capt_referral=capt_referral_from_db,
                                team_name=team_name_from_db, amount_players=amount_players_from_db,
                                capt_agree=capt_agree_from_db, capt_comment=capt_comment_from_db)
    else:
        await message.answer('Что-то не так. Попробуйте ещё раз 🔁')


# здесь забираем данные из FSM и показываем их капитану
@dp.message_handler(state=CaptainStates.New_data_show)
async def cap_second_reg_show_new_data(message: types.Message, state: FSMContext):
    if message.text == "Ок":
        data = await state.get_data()
        game_date_user_style_from_fsm = data.get('game_date')
        week_day_from_fsm = data.get('week_day')
        game_time_from_fsm = data.get('game_time')
        team_name_from_fsm = data.get('team_name')
        capt_name_from_fsm = data.get('capt_name')
        amount_players_from_fsm = data.get('amount_players')
        capt_phone_number_from_fsm = data.get('capt_phone_number')
        capt_link_from_fsm = data.get('capt_link')
        capt_agree_from_fsm = str(data.get('capt_agree'))
        capt_comment_from_fsm = data.get('capt_comment')
        # капитан СОГЛАСЕН НА ОДИНОКОГО ИГРОКА
        if capt_agree_from_fsm is True or capt_agree_from_fsm == 'True':
            # у капитана НЕТ КОММЕНТАРИЕВ
            if len(capt_comment_from_fsm) == 0:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_fsm}*\n'
                                            f'Имя капитана: *{capt_name_from_fsm}*\n'
                                            f'Количество участников в команде: *{amount_players_from_fsm}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_fsm}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_fsm}*\n'
                                            f'Согласен/согласна присоединить одиноких игрока/игроков',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
                await CaptainStates.Complete_new_registr.set()
            # у капитана ЕСТЬ КОММЕНТАРИЙ
            else:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_fsm}*\n'
                                            f'Имя капитана: *{capt_name_from_fsm}*\n'
                                            f'Количество участников в команде: *{amount_players_from_fsm}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_fsm}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_fsm}*\n'
                                            f'Согласен/согласна присоединить одиноких игрока/игроков\n'
                                            f'Ваш комментарий: *{capt_comment_from_fsm}*',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
                await CaptainStates.Complete_new_registr.set()
        # капитан НЕ СОГЛАСЕН НА ОДИНОЧЕК
        else:
            # у капитана НЕТ КОММЕНТАРИЕВ
            if capt_comment_from_fsm is None or len(capt_comment_from_fsm) == 0:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_fsm}*\n'
                                            f'Имя капитана: *{capt_name_from_fsm}*\n'
                                            f'Количество участников в команде: *{amount_players_from_fsm}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_fsm}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_fsm}*\n'
                                            f'Не согласен/не согласна присоединить одиноких игрока/игроков',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
                await CaptainStates.Complete_new_registr.set()
            # у капитана ЕСТЬ КОММЕНТАРИЙ
            else:
                await bot.send_message(message.chat.id,
                                       text=f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                            f'День недели: *{week_day_from_fsm}*\n'
                                            f'Время игры: *{game_time_from_fsm}*\n'
                                            f'Название команды: *{team_name_from_fsm}*\n'
                                            f'Имя капитана: *{capt_name_from_fsm}*\n'
                                            f'Количество участников в команде: *{amount_players_from_fsm}*\n'
                                            f'Ваш номер телефона: *{capt_phone_number_from_fsm}*\n'
                                            f'Ссылка на вашу соц.сеть: *{capt_link_from_fsm}*\n'
                                            f'Не согласен/не согласна присоединить одиноких игрока/игроков\n'
                                            f'Ваш комментарий: *{capt_comment_from_fsm}*',
                                       reply_markup=keyboards.complete_registr,
                                       parse_mode='Markdown')
                await CaptainStates.Complete_new_registr.set()
    else:
        await message.answer('Что-то не так. Попробуйте ещё раз 🔁')


# сюда попадает капитан при повторной регистрации, после того, как выбрал с какой старой даты забрать данные
# и уже увидел эти данные
@dp.message_handler(state=CaptainStates.Complete_new_registr)
async def cap_second_reg_complete_new_registr(message: types.Message, state: FSMContext):
    if message.text == "Завершить регистрацию":
        # вытягиваем из fsm всё, что там есть
        data = await state.get_data()
        game_date_user_style_from_fsm = data.get('game_date')
        n_day = game_date_user_style_from_fsm[0:2]
        n_month = game_date_user_style_from_fsm[3:5]
        n_year = game_date_user_style_from_fsm[6:10]
        game_date_db_style = f"{n_year}{n_month}{n_day}"
        week_day_from_fsm = data.get('week_day')
        game_time_from_fsm = data.get('game_time')
        team_name_from_fsm = data.get('team_name')
        capt_telegram_id_from_fsm = data.get('capt_telegram_id')
        capt_name_from_fsm = data.get('capt_name')
        capt_referral_from_fsm = data.get('capt_referral')
        amount_players_from_fsm = data.get('amount_players')
        capt_phone_number_from_fsm = data.get('capt_phone_number')
        capt_link_from_fsm = data.get('capt_link')
        capt_agree_from_fsm = str(data.get('capt_agree'))
        capt_comment_from_fsm = data.get('capt_comment')
        capt_tel_id_game_date_from_fsm = (str(data.get('capt_telegram_id')) + game_date_db_style)
        # в таком виде передаём в базу для записи
        date_string_for_db = f"{n_year}-{n_month}-{n_day} {game_time_from_fsm}:00"
        # записываем в базу
        sql_commands.saving_cap_info_to_database(capt_tel_id_game_date_from_fsm, capt_telegram_id_from_fsm,
                                                 date_string_for_db, week_day_from_fsm, capt_name_from_fsm,
                                                 capt_phone_number_from_fsm, capt_link_from_fsm, capt_referral_from_fsm,
                                                 team_name_from_fsm, amount_players_from_fsm, capt_agree_from_fsm,
                                                 capt_comment_from_fsm)
        await bot.send_message(message.chat.id, text="Поздравляем, вы зарегистрированы на игру! 🥳",
                               reply_markup=types.ReplyKeyboardRemove())
        # ШЛЁМ РЕФЕРАЛЬНУЮ ССЫЛКУ ДЛЯ ПРИГЛАШЕНИЯ УЧАСТНИКОВ
        await bot.send_message(message.chat.id,
                               text='Можете пригласить участников в свою команду, выслав им реферальную ссылку ⬇️',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await bot.send_message(message.chat.id, text=f"{capt_referral_from_fsm}",
                               reply_markup=types.ReplyKeyboardRemove())
        # регистрация завершена
        await state.finish()
    elif message.text == "Редактировать данные":
        await bot.send_message(message.chat.id,
                               text='Выберите команду и нажмите на неё для редактирования конкретных данных',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        # шлём список команд для редактирования данных в формате "/команда"
        await bot.send_message(message.chat.id, text=f'{commands.capt_commands}',
                               reply_markup=types.ReplyKeyboardRemove())
        await CaptainStates.Finish_edit_second_registration.set()
    else:
        await message.answer('Что-то не так. Попробуйте ещё раз 🔁')


"""

------------------------------------->>>> КОНЕЦ ПОВТОРНОЙ РЕГИСТРАЦИИ КАПИТАНА <<<<-------------------------------------

"""

"""

------------------------------------->>>> БЛОК КОМАНД ДЛЯ РЕДАКТИРОВАНИЯ ДАННЫХ <<<<------------------------------------
----------------------------------------------->>>> ДЛЯ КАПИТАНА <<<<---------------------------------------------------
---------------------------------------->>>> ПРИ ПОВТОРНОЙ РЕГИСТРАЦИИ <<<<---------------------------------------------
"""


@dp.message_handler(Command('game_date'), state=CaptainStates.Finish_edit_second_registration)
async def cap_edit_game_date_second_reg(message: types.Message):
    await bot.send_message(message.chat.id, text='Выберите дату игры', reply_markup=keyboards.game_dates_buttons)
    await CaptainStates.Edit_game_date_second.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_game_date_second)
async def catch_cap_new_date_second_reg(message: types.Message, state: FSMContext):
    all_about_one_date = message.text
    all_dates = sql_commands.all_dates_from_game_dates()
    list_of_dates = []
    for one_tuple in all_dates:
        list_of_dates.append(f"{one_tuple[0]} {one_tuple[1]} {one_tuple[2]}")
    game_date_in_list = re.findall(r'\d\d.\d\d.\d\d\d\d', all_about_one_date)
    game_date = game_date_in_list[0]
    week_day_in_list = re.findall(r'([А-я][а-я]+)', all_about_one_date)
    week_day = week_day_in_list[0]
    game_time_in_list = re.findall(r'\d\d:\d\d', all_about_one_date)
    game_time = game_time_in_list[0]
    # проверка - что дата пришедшая в хэндлер полностью совпадает с датой из базы
    if f"{game_date} {week_day} {game_time}" in list_of_dates:
        data = await state.get_data()
        n_day = all_about_one_date[0:2]
        n_month = all_about_one_date[3:5]
        n_year = all_about_one_date[6:10]
        capt_telegram_id = data.get('capt_telegram_id')
        dates = sql_commands.all_dates_captain_registered_is(capt_telegram_id)
        date_for_check = f"{n_year}{n_month}{n_day}"
        capt_telegram_id_game_date = (str(capt_telegram_id) + date_for_check)
        lonely_player_name_check = sql_commands.select_lonely_player_name_by_lonely_playerid_gamedate(
            capt_telegram_id_game_date)
        # проверяем, чтобы капитан не был зарегистрирован нигде как игрок команды
        player_name_check = sql_commands.select_player_name_by_playerid_gamedate(capt_telegram_id_game_date)
        if len(player_name_check) == 0:
            # проверяем, чтобы капитан не был зарегистрирован нигде как одиночный игрок
            if len(lonely_player_name_check) == 0:
                # проверка, если капитан зарегистрирован уже на эту дату
                if f"{n_year}-{n_month}-{n_day} {game_time}:00" in dates:
                    await bot.send_message(message.chat.id,
                                           text='На эту дату вы уже зарегистрированы. Попробуйте другую 😊',
                                           reply_markup=keyboards.game_dates_buttons)
                else:
                    await state.update_data(game_date=game_date, week_day=week_day, game_time=game_time)
                    await bot.send_message(message.chat.id, text='Записали!', reply_markup=keyboards.ok_keyboard)
                    await CaptainStates.New_data_show.set()
            else:
                await bot.send_message(message.chat.id,
                                       text=f"На выбранную дату вы зарегистрированы как "
                                            f"одиночный игрок *{lonely_player_name_check[0][0]}*\n"
                                            "Попробуйте выбрать другую дату 😊", parse_mode='Markdown')
        else:
            await bot.send_message(message.chat.id,
                                   text=f"На выбранную дату вы зарегистрированы как игрок *{player_name_check[0][0]}*\n"
                                        "Попробуйте выбрать другую дату 😊", parse_mode='Markdown')
    else:
        await bot.send_message(message.chat.id,
                               text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁\nЖмите кнопочки ⬇️")


@dp.message_handler(Command('team_name'), state=CaptainStates.Finish_edit_second_registration)
async def cap_edit_team_name_second_reg(message: types.Message):
    await bot.send_message(message.chat.id, text='Впишите новое название команды',
                           reply_markup=keyboards.ReplyKeyboardRemove())
    await CaptainStates.Edit_team_name_second.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_team_name_second)
async def catch_cap_team_name_second_reg(message: types.Message, state: FSMContext):
    new_team_name = message.text
    await state.update_data(team_name=new_team_name)
    await bot.send_message(message.chat.id, text='Новое название команды записано!',
                           reply_markup=keyboards.ok_keyboard)
    await CaptainStates.New_data_show.set()


@dp.message_handler(Command('capt_name'), state=CaptainStates.Finish_edit_second_registration)
async def cap_edit_name_second_reg(message: types.Message):
    await bot.send_message(message.chat.id, text='Напишите ваше имя', reply_markup=keyboards.ReplyKeyboardRemove())
    await CaptainStates.Edit_capt_name_second.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_name_second)
async def catch_cap_name_second_reg(message: types.Message, state: FSMContext):
    new_capt_name = message.text
    await state.update_data(capt_name=new_capt_name)
    await bot.send_message(message.chat.id, text=f"Ваше имя сохранено, *{new_capt_name}* 😉",
                           reply_markup=keyboards.ok_keyboard, parse_mode='Markdown')
    await CaptainStates.New_data_show.set()


@dp.message_handler(Command('amount_players'), state=CaptainStates.Finish_edit_second_registration)
async def cap_edit_amount_players_second_reg(message: types.Message):
    await bot.send_message(message.chat.id, text='Укажите количество игроков. (Можно примерно)',
                           reply_markup=keyboards.amount_part_keyboard)
    await CaptainStates.Edit_amount_participants_second.set()


@dp.callback_query_handler(text_contains='', state=CaptainStates.Edit_amount_participants_second)
async def catch_cap_amount_players_second_reg(call: types.CallbackQuery, state: FSMContext):
    amount_players = int(call['data'])
    await state.update_data(amount_players=amount_players)
    await bot.send_message(call.message.chat.id, text=f"Количество игроков: *{amount_players}*. \nЗаписано 👍",
                           reply_markup=keyboards.ok_keyboard, parse_mode='Markdown')
    await CaptainStates.New_data_show.set()


@dp.message_handler(Command('capt_phone'), state=CaptainStates.Finish_edit_second_registration)
async def cap_edit_phone_number_second_reg(message: types.Message):
    await bot.send_message(message.chat.id,
                           text="Впишите ваш номер телефона. \nБот принимает только польские номера 🇵🇱\n"
                                "Начало должно быть +48 или 48", reply_markup=keyboards.ReplyKeyboardRemove())
    await CaptainStates.Edit_capt_phone_second.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_phone_second)
async def catch_capt_phone_number_second_reg(message: types.Message, state: FSMContext):
    try:
        new_capt_phone = message.text
        new_capt_phone_int = int(
            new_capt_phone.replace('+', '').replace(' ', '').replace('(', '').replace(')', ''))
    except ValueError:
        await message.answer('Неверный ввод.\nПопробуйте ещё раз 🔁"', reply_markup=types.ReplyKeyboardRemove())
    else:
        if new_capt_phone.startswith('+48') or new_capt_phone.startswith('48'):
            if len(str(new_capt_phone_int).replace('48', '')) == 9:
                await state.update_data(capt_phone_number=new_capt_phone.replace(' ', ''))
                await bot.send_message(message.chat.id, text=f"Номер телефона {new_capt_phone} сохранён 🥳",
                                       reply_markup=keyboards.ok_keyboard)
                await CaptainStates.New_data_show.set()
            elif len(str(new_capt_phone_int).replace('48', '')) > 9:
                await message.answer(text="В вашем номере больше 9 цифр, попробуйте внимательнее",
                                     reply_markup=types.ReplyKeyboardRemove())
            elif len(str(new_capt_phone_int).replace('48', '')) < 9:
                await message.answer(text="В вашем номере меньше 9 цифр, попробуйте внимательнее",
                                     reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer(text="Введите польский номер 🇵🇱\n(начинается с +48 или 48) 😊",
                                 reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(Command('capt_link'), state=CaptainStates.Finish_edit_second_registration)
async def cap_edit_link_second_reg(message: types.Message):
    await bot.send_message(message.chat.id, text='Выберите соц.сеть/мессенджер, по которой с вами можно связаться.',
                           reply_markup=keyboards.soc_network)
    await CaptainStates.Edit_capt_link_second.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_link_second)
async def catch_cap_link_second_reg(message: types.Message):
    if message.text == "Telegram":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш аккаунт Telegram",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Edit_capt_link_telegram_second.set()
    elif message.text == "Instagram":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш Instagram аккаунт",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Edit_capt_link_instagram_second.set()
    elif message.text == "Facebook":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш Facebook аккаунт",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Edit_capt_link_facebook_second.set()
    elif message.text == "Другое":
        await bot.send_message(message.chat.id, text="Внесите ссылку", reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Edit_capt_link_other_soc_net_second.set()
    else:
        await message.answer('Ошибка. Попробуйте ещё раз 🔁')


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_link_telegram_second)
async def catch_cap_link_telegram_second_reg(message: types.Message, state: FSMContext):
    if (message.text.startswith('https://t.me/') and len(message.text[13:]) != 0) or (
            message.text.startswith("@") and len(message.text[1:]) != 0):
        new_link_tel = message.text
        await state.update_data(capt_link=new_link_tel)
        await bot.send_message(message.chat.id, text='Ссылка сохранена ✅', reply_markup=keyboards.ok_keyboard)
        await CaptainStates.New_data_show.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_link_instagram_second)
async def catch_cap_link_instagram_second_reg(message: types.Message, state: FSMContext):
    if (message.text.startswith('https://www.instagram.com/') and len(message.text[26:]) != 0) or \
            (message.text.startswith('https://instagram.com/') and len(message.text[22:]) != 0):
        new_link_inst = message.text
        await state.update_data(capt_link=new_link_inst)
        await bot.send_message(message.chat.id, text='Ссылка на Instagram сохранена ✅',
                               reply_markup=keyboards.ok_keyboard)
        await CaptainStates.New_data_show.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_link_facebook_second)
async def catch_cap_link_facebook_second_reg(message: types.Message, state: FSMContext):
    if message.text.startswith('https://www.facebook.com/') and len(message.text[25:]) != 0:
        new_link_facb = message.text
        await state.update_data(capt_link=new_link_facb)
        await bot.send_message(message.chat.id, text='Ссылка на Facebook сохранена ✅',
                               reply_markup=keyboards.ok_keyboard)
        await CaptainStates.New_data_show.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_link_other_soc_net_second)
async def catch_cap_link_other_soc_net_second_reg(message: types.Message, state: FSMContext):
    new_link_other_soc_net = message.text
    await state.update_data(capt_link=new_link_other_soc_net)
    await bot.send_message(message.chat.id, "Ссылка сохранена ✅", reply_markup=keyboards.ok_keyboard)
    await CaptainStates.New_data_show.set()


@dp.message_handler(Command('lonely_player'), state=CaptainStates.Finish_edit_second_registration)
async def cap_edit_lonely_player_agree_second_reg(message: types.Message):
    await bot.send_message(message.chat.id, text='Готовы ли вы принять в вашу команду игрока/ов? 👤 ',
                           reply_markup=keyboards.yes_or_no)
    await CaptainStates.Edit_lonely_player_second.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_lonely_player_second)
async def catch_cap_lonely_player_agree_second_reg(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        new_capt_agree = True
        await state.update_data(capt_agree=new_capt_agree)
        await bot.send_message(message.chat.id, "Так и запишем!", reply_markup=keyboards.ok_keyboard)
        await CaptainStates.New_data_show.set()
    elif message.text == 'Нет':
        new_capt_agree = False
        await state.update_data(capt_agree=new_capt_agree)
        await bot.send_message(message.chat.id, "Так и запишем!", reply_markup=keyboards.ok_keyboard)
        await CaptainStates.New_data_show.set()
    else:
        await message.answer("Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


@dp.message_handler(Command('capt_comment'), state=CaptainStates.Finish_edit_second_registration)
async def cap_edit_comment_second_reg(message: types.Message):
    await bot.send_message(message.chat.id, text='Есть ли у вас комментарии? 📝',
                           reply_markup=keyboards.yes_or_no)
    await CaptainStates.Edit_capt_comment_second.set()


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_comment_second)
async def catch_cap_comment_second_reg(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        await bot.send_message(message.chat.id, "Внесите ваш комментарий ✏️",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await CaptainStates.Edit_capt_comment_enter_second.set()
    elif message.text == 'Нет':
        await state.update_data(capt_comment='')
        await bot.send_message(message.chat.id, "Сохранили!", reply_markup=keyboards.ok_keyboard)
        await CaptainStates.New_data_show.set()
    else:
        await message.answer("Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


@dp.message_handler(content_types='text', state=CaptainStates.Edit_capt_comment_enter_second)
async def catch_cap_comment_enter_second_reg(message: types.Message, state: FSMContext):
    new_comment = message.text
    await state.update_data(capt_comment=new_comment)
    await bot.send_message(message.chat.id, "Записали 👍", reply_markup=keyboards.ok_keyboard)
    await CaptainStates.New_data_show.set()


"""

-------------------------------------->>>> ОКОНЧАНИЕ РЕГИСТРАЦИИ КАПИТАНА <<<<------------------------------------------

"""

"""

---------------------------------->>>> НАЧАЛО РЕГИСТРАЦИИ УЧАСТНИКА КОМАНДЫ <<<<----------------------------------------

"""


# вспомогательный стейт 'Have_a_nice_day' для плавного выхода из любой ситуации :)))
# (принимает "ок")
# финалит стейт
@dp.message_handler(state=PlayersStates.Have_a_nice_day)
async def have_a_nice_day(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, text='Приятного дня', reply_markup=types.ReplyKeyboardRemove())
    await state.finish()


# хэндлер ловит нажатие клавиш с датами игр и сохраняет дату игры, которую выбрал игрок
# (в случае если капитан зарегистрирован больше, чем на одну игру)
@dp.message_handler(content_types='text', state=PlayersStates.Choose_from_several_dates)
async def player_choose_one_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    referrer_id = data.get('referrer_id')
    game_date_user_style = message.text
    # проверяем чтобы сообщение, которое прилетело в этот хэндлер, если его очистить от "-", содержало цифры
    if game_date_user_style.replace('.', '').isdigit():
        all_dates = sql_commands.all_dates_captain_registered_is_except_past(referrer_id)
        # проверяем, чтобы на выбранную дату капитан действительно был зарегистрирован
        if game_date_user_style in all_dates:
            # перед тем, как идти дальше нужно проверить, не зарегистрирован ли уже этот участник на эту дату
            # берём из fsm всё, что нам надо для обращения к базе
            await state.update_data(game_date=game_date_user_style)
            data = await state.get_data()
            referrer_id = data.get('referrer_id')
            player_id = data.get('player_id')
            game_date_from_fsm_user_style = data.get('game_date')
            day = game_date_from_fsm_user_style[0:2]
            month = game_date_from_fsm_user_style[3:5]
            year = game_date_from_fsm_user_style[6:10]
            game_date_db_style = f"{year}{month}{day}"
            info = sql_commands.select_teamname_captname_by_capid_gamedate(referrer_id, game_date_db_style)
            game_time = info[0][3]
            game_date_string_for_db = f"{year}-{month}-{day} {game_time}:00"
            # обращаемся в базу, передаём id игрока и выбранную дату игры
            # максимально в 'name' может вернуться одно имя - это значит на выбранную дату игрок уже зарегистрирован
            name = sql_commands.check_player_name_into_base_by_playerid_date(player_id, game_date_string_for_db)
            player_id_game_date_for_db = (str(player_id) + game_date_db_style)
            cap_name_check = sql_commands.select_captname_by_capid_gamedate(player_id_game_date_for_db)
            lonely_player_name_check = sql_commands.select_lonely_player_name_by_lonely_playerid_gamedate(
                player_id_game_date_for_db)
            # если в 'name' ничего не вернулось, соответственно - игрока под выбранной датой ещё не существует в базе
            if len(name) == 0:
                if len(cap_name_check) == 0:
                    if len(lonely_player_name_check) == 0:
                        await bot.send_message(message.chat.id, "Продолжим 👍", reply_markup=keyboards.ok_keyboard)
                        await PlayersStates.Show_short_info_to_player.set()
                    else:
                        await bot.send_message(message.chat.id,
                                               text=f"На выбранную дату вы зарегистрированы как "
                                                    f"одиночный игрок *{lonely_player_name_check[0][0]}*\n"
                                                    "Попробуйте выбрать другую дату 😊", parse_mode='Markdown')
                else:
                    await bot.send_message(message.chat.id,
                                           text=f"На выбранную дату вы зарегистрированы как "
                                                f"капитан *{cap_name_check[0][0]}*\n"
                                                "Попробуйте выбрать другую дату 😊", parse_mode='Markdown')
            # игрок уже зарегистрирован на выбранную дату
            else:
                # тут же предлагаем ему выбрать другую дату из всех, на которые зарег-н его капитан, точно как в начале
                await bot.send_message(message.chat.id, text=f'Игрок *{name[0][0]}* уже зарегистрирован на эту дату\n'
                                                             f'Попробуйте выбрать другую дату', parse_mode='Markdown')
                dates_captain_registered_is = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                                        row_width=1)
                all_dates = sql_commands.all_dates_captain_registered_is_except_past(referrer_id)
                list_of_buttons_with_dates = []
                for one_date in all_dates:
                    one_button_date = types.KeyboardButton(f"{one_date}")
                    list_of_buttons_with_dates.append(one_button_date)

                for date_button in list_of_buttons_with_dates:
                    dates_captain_registered_is.insert(date_button)
                # пишем игроку сообщение, открываем клавиатуру с этими датами для выбора
                await bot.send_message(message.chat.id, text=f'Даты, на которые зарегистрирован ваш капитан ⬇️\n'
                                                             f'Выберите, когда хотите играть',
                                       reply_markup=dates_captain_registered_is)
        else:
            await bot.send_message(message.chat.id, text="На такую дату капитан не зарегистрирован\n"
                                                         "Попробуйте ещё раз 🔁")
    # это сработает если прилетела какая-то ерунда вместо даты, например буквы
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁\n"
                                                     "Жмите кнопочки ⬇️")


# хэндлер отлавливает:
# 1) текст нажатой кнопки "Всё верно" после того как игроку показали дату игры,
# (в случае если капитан зарегистрирован только на одну игру)
# 2) текст кнопки "Ок" после того, как игрок выбрал одну дату из нескольких
# (в случае если капитан зарегистрирован на несколько игр)
@dp.message_handler(content_types='text', state=PlayersStates.Show_short_info_to_player)
async def player_date_is_right(message: types.Message, state: FSMContext):
    if message.text == "Ок" or message.text == "Всё верно":
        # теперь мы можем обратиться в базу по id капитана и дате игры
        # и вытянуть из БД название команды и имя капитана
        data = await state.get_data()
        capt_id = data.get('referrer_id')
        game_date_user_style_from_fsm = data.get('game_date')
        n_day = game_date_user_style_from_fsm[0:2]
        n_month = game_date_user_style_from_fsm[3:5]
        n_year = game_date_user_style_from_fsm[6:10]
        game_date_db_style = f"{n_year}{n_month}{n_day}"
        info = sql_commands.select_teamname_captname_by_capid_gamedate(capt_id, game_date_db_style)
        team_name = info[0][0]
        capt_name = info[0][1]
        week_day = info[0][2]
        game_time = info[0][3]
        # название команды и имя капитана тут же сохраняем в fsm
        await state.update_data(team_name=team_name, capt_name=capt_name, week_day=week_day, game_time=game_time)
        # шлём сообщение с полученной из базы информацией
        await bot.send_message(message.chat.id,
                               text=f'Итак, давайте зарегистрируем Вас в команду: *{team_name}*\n'
                                    f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                    f'День недели: *{week_day}*\n'
                                    f'Время игры: *{game_time}*\n'
                                    f'Капитан: *{capt_name}*',
                               reply_markup=types.ReplyKeyboardRemove(), parse_mode='Markdown')
        await bot.send_message(message.chat.id, text='Напишите ваше имя', reply_markup=types.ReplyKeyboardRemove())
        await PlayersStates.Player_name.set()
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


# ЛОВИТ имя игрока
@dp.message_handler(state=PlayersStates.Player_name)
async def player_name(message: types.Message, state: FSMContext):
    # сюда попадает имя игрока
    # сохраняем ИМЯ игрока в переменную 'player_name' и в FSM
    player_name_for_save = message.text
    await state.update_data(player_name=player_name_for_save)
    # шлём игроку сообщение, что его ник сохранён, провешиваем клавиатуру 'Редактировать', 'Далее'
    await bot.send_message(message.chat.id, f"Ваше имя сохранено, *{player_name_for_save}* 😉",
                           reply_markup=keyboards.edit_data, parse_mode='Markdown')
    await PlayersStates.Player_name_support.set()


@dp.message_handler(state=PlayersStates.Player_name_support)
async def player_name_support(message: types.Message):
    # этот кусок кода срабатывает при нажатии кнопки 'Редактировать'
    if message.text == 'Редактировать':
        # запрашивает повторное введение имени
        await bot.send_message(message.chat.id, text='Напишите ваше имя',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await PlayersStates.Player_name.set()
    # обработка кнопки "Далее"
    elif message.text == 'Далее':
        # задаём вопрос для следующего состояния, вывешиваем клавиатуру ДА или НЕТ
        await bot.send_message(message.chat.id, text='Есть ли у вас комментарии? 📝', reply_markup=keyboards.yes_or_no)
        # присваиваем следующее состояние
        await PlayersStates.Player_comments.set()
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


# хэндлер ловит нажатие кнопок ДА или НЕТ после вопроса 'Есть ли у вас комментарии?'
@dp.message_handler(state=PlayersStates.Player_comments)
async def player_comm(message: types.Message, state: FSMContext):
    # при нажатии кнопки "Да"
    if message.text == 'Да':
        # запрашиваем у игрока комментарий, закрываем какие бы то ни было клавиатуры
        await bot.send_message(message.chat.id, "Внесите ваш комментарий ✏️",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        # присваиваем стейт, в котором будет ожидаться ввод текста с комментарием и сохранение его
        await PlayersStates.Players_comments_support_enter.set()
    # при нажатии кнопки "Нет"
    elif message.text == 'Нет':
        # запишем как пустую строку
        player_comment = ''
        await state.update_data(player_comment=player_comment)
        # пишем, выставляем клавиатуру РЕДАКТИРОВАТЬ - ДАЛЕЕ
        await bot.send_message(message.chat.id, f"Сохранили!", reply_markup=keyboards.edit_data)
        # присваиваем следующий стейт (будет отлавливать кнопки РЕДАКТИРОВАТЬ - ДАЛЕЕ)
        await PlayersStates.Players_comments_support.set()
    else:
        await message.answer("Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


# хэндлер ожидает ввод текста комментария и сохраняет его
@dp.message_handler(state=PlayersStates.Players_comments_support_enter)
async def player_comm_enter(message: types.Message, state: FSMContext):
    # сохраняем этот комментарий
    player_comment = message.text
    await state.update_data(player_comment=player_comment)
    # кинули в польз-ля сообщение, открыли клавиатуру РЕДАКТИРОВАТЬ - ДАЛЕЕ
    await bot.send_message(message.chat.id, text="Записали 👍", reply_markup=keyboards.edit_data)
    await PlayersStates.Players_comments_support.set()


# хэндлер ловит кнопки РЕДАКТИРОВАТЬ - ДАЛЕЕ
@dp.message_handler(state=PlayersStates.Players_comments_support)
async def player_comm_support(message: types.Message):
    # при нажатии кнопки "Редактировать"
    if message.text == 'Редактировать':
        # снова задаём вопрос
        await bot.send_message(message.chat.id, text='Есть ли у вас комментарии? 📝',
                               reply_markup=keyboards.yes_or_no)
        # возвращаем поль-ля в предыдущее состояние
        await PlayersStates.Player_comments.set()
    # если нажата кнопка "Далее"
    elif message.text == 'Далее':
        # пишем, что дальше будет вывод всей внесённой ранее информации
        await bot.send_message(message.chat.id,
                               text='следующее сообщение будет выводом всей введённой ранее информации',
                               reply_markup=keyboards.ok_keyboard)
        # присваиваем следующее состояние
        await PlayersStates.Show_all_info_to_player.set()
    else:
        await message.answer('Произошла какая-то ошибка. Попробуйте ещё раз 🔁')


# показываем игроку всю информацию прежде чем сохранить в базу
@dp.message_handler(state=PlayersStates.Show_all_info_to_player)
async def show_all_info_to_player(message: types.Message, state: FSMContext):
    # достаём все что есть в fsm
    data = await state.get_data()
    referrer_id_from_fsm = data.get('referrer_id')
    player_id_from_fsm = data.get('player_id')
    game_date_user_style_from_fsm = data.get('game_date')
    n_day = game_date_user_style_from_fsm[0:2]
    n_month = game_date_user_style_from_fsm[3:5]
    n_year = game_date_user_style_from_fsm[6:10]
    game_date_db_style = f"{n_year}{n_month}{n_day}"
    week_day_from_fsm = data.get('week_day')
    game_time_from_fsm = data.get('game_time')
    team_name_from_fsm = data.get('team_name')
    capt_name_from_fsm = data.get('capt_name')
    player_name_from_fsm = data.get('player_name')
    player_comment_from_fsm = data.get('player_comment')
    capt_telegram_id_game_date_from_fsm = str(data.get('referrer_id')) + game_date_db_style
    player_telegr_id_game_date_from_fsm = str(data.get('player_id')) + game_date_db_style
    reff_url = f"https://t.me/{config.bot_nickname}?start={referrer_id_from_fsm}"
    date_string_for_db = f"{n_year}-{n_month}-{n_day} {game_time_from_fsm}:00"
    if message.text == "Ок":
        # у игрока НЕТ КОММЕНТАРИЕВ
        if len(player_comment_from_fsm) == 0:
            await bot.send_message(message.chat.id,
                                   text=f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                        f'День недели: *{week_day_from_fsm}*\n'
                                        f'Время игры: *{game_time_from_fsm}*\n'
                                        f'Название команды: *{team_name_from_fsm}*\n'
                                        f'Имя капитана: *{capt_name_from_fsm}*\n'
                                        f'Ваше имя: *{player_name_from_fsm}*',
                                   reply_markup=keyboards.complete_registr,
                                   parse_mode='Markdown')
        # у игрока ЕСТЬ КОММЕНТАРИЙ
        else:
            await bot.send_message(message.chat.id,
                                   text=f'Дата игры: *{game_date_user_style_from_fsm}*\n'
                                        f'День недели: *{week_day_from_fsm}*\n'
                                        f'Время игры: *{game_time_from_fsm}*\n'
                                        f'Название команды: *{team_name_from_fsm}*\n'
                                        f'Имя капитана: *{capt_name_from_fsm}*\n'
                                        f'Ваше имя: *{player_name_from_fsm}*\n'
                                        f'Ваш комментарий: *{player_comment_from_fsm}*',
                                   reply_markup=keyboards.complete_registr,
                                   parse_mode='Markdown')
    elif message.text == "Завершить регистрацию":
        # сохраняем в базу
        sql_commands.saving_player_to_database(capt_telegram_id_game_date_from_fsm, referrer_id_from_fsm,
                                               player_telegr_id_game_date_from_fsm, player_id_from_fsm,
                                               date_string_for_db, week_day_from_fsm, team_name_from_fsm,
                                               capt_name_from_fsm, player_name_from_fsm, player_comment_from_fsm)
        await bot.send_message(message.chat.id, text="Поздравляем, вы зарегистрированы на игру! 🥳",
                               reply_markup=types.ReplyKeyboardRemove())
        # ШЛЁМ РЕФЕРАЛЬНУЮ ССЫЛКУ ДЛЯ ПРИГЛАШЕНИЯ УЧАСТНИКОВ
        await bot.send_message(message.chat.id,
                               text='Можете пригласить участников в свою команду, выслав им реферальную ссылку ⬇️',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await bot.send_message(message.chat.id, text=f"{reff_url}",
                               reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
    elif message.text == "Редактировать данные":
        await bot.send_message(message.chat.id,
                               text='Выберите команду и нажмите на неё для редактирования конкретных данных',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        # шлём список команд для редактирования данных в формате '/команда'
        await bot.send_message(message.chat.id, text=f'{commands.player_commands}',
                               reply_markup=types.ReplyKeyboardRemove())
        await PlayersStates.Finish_player_edit.set()
    else:
        await message.answer('Что-то не так. Попробуйте ещё раз 🔁')


"""

------------------------------------->>>> БЛОК КОМАНД ДЛЯ РЕДАКТИРОВАНИЯ ДАННЫХ <<<<------------------------------------
------------------------------------------->>>> ДЛЯ УЧАСТНИКА КОМАНДЫ <<<<----------------------------------------------
"""


@dp.message_handler(Command('game_date'), state=PlayersStates.Finish_player_edit)
async def player_edit_game_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    referrer_id = data.get('referrer_id')
    dates = sql_commands.all_dates_captain_registered_is_except_past(referrer_id)
    if len(dates) == 1:
        await bot.send_message(message.chat.id,
                               text='Капитан зарегистрирован только на 1 игру. Вы не можете поменять дату игры.',
                               reply_markup=keyboards.ok_keyboard)
        await PlayersStates.Show_all_info_to_player.set()
    elif len(dates) > 1:
        dates_captain_registered_is = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                                row_width=1)
        all_dates = sql_commands.all_dates_captain_registered_is_except_past(referrer_id)
        list_of_buttons_with_dates = []
        for one_date in all_dates:
            one_button_date = types.KeyboardButton(f"{one_date}")
            list_of_buttons_with_dates.append(one_button_date)

        for date_button in list_of_buttons_with_dates:
            dates_captain_registered_is.insert(date_button)
        # пишем игроку сообщение, открываем клавиатуру с этими датами для выбора
        await bot.send_message(message.chat.id, text=f'Даты, на которые зарегистрирован ваш капитан ⬇️\n'
                                                     f'Выберите, когда хотите играть',
                               reply_markup=dates_captain_registered_is)
        # это состояние будет отлавливать нажатие клавиш с датами и сохранять дату в FSM
        await PlayersStates.Player_edit_game_date.set()
    else:
        await bot.send_message(message.chat.id,
                               text='Произошла какая-то ошибка. \nКапитан, по чьей ссылке вы перешли, '
                                    'не зарегистрирован ни на одну игру.', reply_markup=keyboards.ok_keyboard)
        await PlayersStates.Have_a_nice_day.set()


@dp.message_handler(content_types='text', state=PlayersStates.Player_edit_game_date)
async def catch_new_player_date(message: types.Message, state: FSMContext):
    new_game_date_user_style = message.text
    day = new_game_date_user_style[0:2]
    month = new_game_date_user_style[3:5]
    year = new_game_date_user_style[6:10]
    game_date_db_style = f"{year}{month}{day}"
    data = await state.get_data()
    capt_id = data.get('referrer_id')
    player_id = data.get('player_id')
    # проверяем чтобы сообщение, которое прилетело в этот хэндлер, если его очистить от ".", содержало цифры
    if new_game_date_user_style.replace('.', '').isdigit():
        dates = sql_commands.all_dates_captain_registered_is_except_past(capt_id)
        # проверяем, чтобы на выбранную дату капитан действительно был зарегистрирован
        if new_game_date_user_style in dates:
            info = sql_commands.select_teamname_captname_by_capid_gamedate(capt_id, game_date_db_style)
            team_name = info[0][0]
            capt_name = info[0][1]
            week_day = info[0][2]
            game_time = info[0][3]
            game_date_string_for_db = f"{year}-{month}-{day} {game_time}:00"
            name = sql_commands.check_player_name_into_base_by_playerid_date(player_id, game_date_string_for_db)
            player_id_game_date_for_check = (str(player_id) + game_date_db_style)
            cap_name_check = sql_commands.select_captname_by_capid_gamedate(player_id_game_date_for_check)
            lonely_player_name_check = sql_commands.select_lonely_player_name_by_lonely_playerid_gamedate(
                player_id_game_date_for_check)
            if len(name) == 0:
                if len(cap_name_check) == 0:
                    if len(lonely_player_name_check) == 0:
                        await state.update_data(team_name=team_name, capt_name=capt_name,
                                                game_date=new_game_date_user_style,
                                                week_day=week_day, game_time=game_time)
                        await bot.send_message(message.chat.id, text='Записали!', reply_markup=keyboards.ok_keyboard)
                        await PlayersStates.Show_all_info_to_player.set()
                    else:
                        await bot.send_message(message.chat.id,
                                               text=f"На выбранную дату вы зарегистрированы как "
                                                    f"одиночный игрок *{lonely_player_name_check[0][0]}*\n"
                                                    "Попробуйте выбрать другую дату 😊", parse_mode='Markdown')
                else:
                    await bot.send_message(message.chat.id,
                                           text=f"На выбранную дату вы зарегистрированы как "
                                                f"капитан *{cap_name_check[0][0]}*\n"
                                                "Попробуйте выбрать другую дату 😊", parse_mode='Markdown')
            else:
                await bot.send_message(message.chat.id, text=f'Игрок: *{name[0][0]}* уже зарегистрирован на эту дату\n'
                                                             f'Попробуйте выбрать другую дату', parse_mode='Markdown')
        else:
            await bot.send_message(message.chat.id, text="На такую дату капитан не зарегистрирован\n"
                                                         "Попробуйте ещё раз 🔁")
    # это сработает если прилетела какая-то ерунда вместо даты, например буквы
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁\n"
                                                     "Жмите кнопочки ⬇️")


@dp.message_handler(Command('player_name'), state=PlayersStates.Finish_player_edit)
async def player_edit_name(message: types.Message):
    await bot.send_message(message.chat.id, text='Напишите ваше имя', reply_markup=keyboards.ReplyKeyboardRemove())
    await PlayersStates.Player_edit_name.set()


@dp.message_handler(content_types='text', state=PlayersStates.Player_edit_name)
async def catch_player_name(message: types.Message, state: FSMContext):
    new_player_name = message.text
    await state.update_data(player_name=new_player_name)
    await bot.send_message(message.chat.id, text=f"Ваше имя сохранено, *{new_player_name}* 😉",
                           reply_markup=keyboards.ok_keyboard, parse_mode='Markdown')
    await PlayersStates.Show_all_info_to_player.set()


@dp.message_handler(Command('player_comment'), state=PlayersStates.Finish_player_edit)
async def player_edit_comment(message: types.Message):
    await bot.send_message(message.chat.id, text='Есть ли у вас комментарии? 📝',
                           reply_markup=keyboards.yes_or_no)
    await PlayersStates.Player_edit_comments.set()


@dp.message_handler(content_types='text', state=PlayersStates.Player_edit_comments)
async def catch_player_comment(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        await bot.send_message(message.chat.id, "Внесите ваш комментарий ✏️",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await PlayersStates.Player_edit_comment_enter.set()
    elif message.text == 'Нет':
        await state.update_data(player_comment='')
        await bot.send_message(message.chat.id, "Сохранили!", reply_markup=keyboards.ok_keyboard)
        await PlayersStates.Show_all_info_to_player.set()
    else:
        await message.answer("Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


@dp.message_handler(content_types='text', state=PlayersStates.Player_edit_comment_enter)
async def catch_player_comment_enter(message: types.Message, state: FSMContext):
    new_comment = message.text
    await state.update_data(player_comment=new_comment)
    await bot.send_message(message.chat.id, "Записали 👍", reply_markup=keyboards.ok_keyboard)
    await PlayersStates.Show_all_info_to_player.set()


"""

---------------------------------->>>> ОКОНЧАНИЕ РЕГИСТРАЦИИ УЧАСТНИКА КОМАНДЫ <<<<-------------------------------------

"""

"""

--------------------------------->>>> БЛОК КОДА ДЛЯ РЕГИСТРАЦИИ ОДИНОЧНОГО ИГРОКА <<<<----------------------------------

"""


# хэндлер ловит имя одинокого игрока
@dp.message_handler(state=LonelyPlayerStates.Lonely_player_name)
async def lonely_player_name(message: types.Message, state: FSMContext):
    lon_player_name = message.text
    await state.update_data(lon_player_name=lon_player_name)
    await bot.send_message(message.chat.id, text=f"Ваше имя сохранено, *{lon_player_name}* 😉",
                           reply_markup=keyboards.edit_data, parse_mode='Markdown')
    await LonelyPlayerStates.Lonely_player_name_support.set()


# после внесения ссылки будем спрашивать про комментарии
# await bot.send_message(message.chat.id, text="Есть ли у вас комментарии? 📝",
#                                reply_markup=keyboards.yes_or_no)
#         await LonelyPlayerStates.Lonely_player_comment.set()
@dp.message_handler(state=LonelyPlayerStates.Lonely_player_name_support)
async def lonely_player_name_support(message: types.Message):
    if message.text == 'Редактировать':
        await bot.send_message(message.chat.id, text="Напишите ваше имя",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Lonely_player_name.set()
    elif message.text == 'Далее':
        await bot.send_message(message.chat.id, text="Выберите соц.сеть/мессенджер, по которой с вами можно связаться.",
                               reply_markup=keyboards.soc_network)
        await LonelyPlayerStates.Lonely_player_Choose_soc_net.set()
    else:
        await message.answer('Произошла какая-то ошибка. Попробуйте ещё раз 🔁')


@dp.message_handler(state=LonelyPlayerStates.Lonely_player_Choose_soc_net)
async def lonely_player_soc_net(message: types.Message):
    # при нажатии кнопки пишем сообщение, переводим в следующий стейт
    if message.text == "Telegram":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш аккаунт Telegram",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Lonely_player_Telegram.set()
    elif message.text == "Instagram":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш Instagram аккаунт",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Lonely_player_Instagram.set()
    elif message.text == "Facebook":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш Facebook аккаунт",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Lonely_player_Facebook.set()
    elif message.text == "Другое":
        await bot.send_message(message.chat.id, text="Внесите ссылку", reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Lonely_player_Other_soc_net.set()
    else:
        await message.answer('Произошла какая-то ошибка. Попробуйте ещё раз 🔁\n'
                             'Нажимайте кнопочки ⬇️')


# хэндлер для введения ссылки на телеграм
@dp.message_handler(state=LonelyPlayerStates.Lonely_player_Telegram)
async def lonely_player_link_telegram(message: types.Message, state: FSMContext):
    # сюда попадает ССЫЛКА НА ТЕЛЕГРАМ
    # проверка, чтобы ссылка на телегу начиналась с https://t.me/ или @ не была пустая
    if (message.text.startswith('https://t.me/') and len(message.text[13:]) != 0) or (
            message.text.startswith("@") and len(message.text[1:]) != 0):
        # сохраняем ссылку
        lon_player_link_telegram = message.text
        # записываем её в пространство имён состояния
        await state.update_data(lon_player_link=lon_player_link_telegram)
        # пишем сообщение о сохранении данных, открываем клавиатуру для редактир-я или перехода дальше
        await bot.send_message(message.chat.id, "Ссылка сохранена ✅", reply_markup=keyboards.edit_data)
        await LonelyPlayerStates.Lonely_player_link_support.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁")


# хэндлер для введения ссылки на инстаграм
@dp.message_handler(state=LonelyPlayerStates.Lonely_player_Instagram)
async def lonely_player_link_instagram(message: types.Message, state: FSMContext):
    # сюда попадает ССЫЛКА НА ИНСТАГРАМ
    # проверка, чтобы ссылка на инсту начиналась с чего надо и не была пустая
    if (message.text.startswith('https://www.instagram.com/') and len(message.text[26:]) != 0) or \
            (message.text.startswith('https://instagram.com/') and len(message.text[22:]) != 0):
        # сохраняем ссылку
        lon_player_link_inst = message.text
        # записываем её в пространство имён состояния под ключом "capt_link"
        await state.update_data(lon_player_link=lon_player_link_inst)
        # пишем, что всё сохранено, открываем клавиатуру для редактир-я или перехода дальше
        await bot.send_message(message.chat.id, "Ссылка на Instagram сохранена ✅", reply_markup=keyboards.edit_data)
        await LonelyPlayerStates.Lonely_player_link_support.set()
    # если ссылка начинается иначе
    else:
        # просим ещё раз написать
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁")


# хэндлер для введения ссылки на фэйсбук
@dp.message_handler(state=LonelyPlayerStates.Lonely_player_Facebook)
async def lonely_player_link_facebook(message: types.Message, state: FSMContext):
    # сюда попадает ССЫЛКА НА ФЭЙСБУК
    # проверка, чтобы ссылка на фэйсбук начиналась с https://www.facebook.com/ и не была пустая
    if message.text.startswith('https://www.facebook.com/') and len(message.text[25:]) != 0:
        # сохраняем ссылку
        lon_player_link_fcbk = message.text
        # записываем её в пространство имён состояния под ключом "capt_link"
        await state.update_data(lon_player_link=lon_player_link_fcbk)
        # пишем сообщение, открываем клавиатуру для редактир-я или перехода дальше
        await bot.send_message(message.chat.id, "Ссылка на Facebook сохранена ✅", reply_markup=keyboards.edit_data)
        await LonelyPlayerStates.Lonely_player_link_support.set()
    # если ссылка начинается иначе
    else:
        # просим ещё раз написать
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁")


# хэндлер для ловли ссылки на другую соц.сеть
@dp.message_handler(state=LonelyPlayerStates.Lonely_player_Other_soc_net)
async def lonely_player_link_other_soc_net(message: types.Message, state: FSMContext):
    lon_player_link_other = message.text
    await state.update_data(lon_player_link=lon_player_link_other)
    await bot.send_message(message.chat.id, "Ссылка сохранена ✅", reply_markup=keyboards.edit_data)
    await LonelyPlayerStates.Lonely_player_link_support.set()


@dp.message_handler(state=LonelyPlayerStates.Lonely_player_link_support)
async def lonely_player_link_telegram_support(message: types.Message):
    if message.text == 'Редактировать':
        # возвращаем юзера в предыдущий стейт, где он выбирал соц.сеть
        await bot.send_message(message.chat.id,
                               text="Выберите соц.сеть/мессенджер, по которой с вами можно связаться",
                               reply_markup=keyboards.soc_network)
        await LonelyPlayerStates.Lonely_player_Choose_soc_net.set()
    # если нажата кнопка 'Далее'
    elif message.text == 'Далее':
        # задаём вопрос для след.стейта
        await bot.send_message(message.chat.id, text="Есть ли у вас комментарии? 📝", reply_markup=keyboards.yes_or_no)
        await LonelyPlayerStates.Lonely_player_comment.set()
    else:
        await bot.send_message(message.chat.id, text="Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


@dp.message_handler(state=LonelyPlayerStates.Lonely_player_comment)
async def lonely_player_comment(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        await bot.send_message(message.chat.id, text="Внесите ваш комментарий ✏️",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Lonely_player_comment_support_enter.set()
    elif message.text == 'Нет':
        lon_player_comment = ''
        await state.update_data(lon_player_comment=lon_player_comment)
        await bot.send_message(message.chat.id, text="Сохранили!", reply_markup=keyboards.edit_data)
        await LonelyPlayerStates.Lonely_player_comment_support.set()
    else:
        await message.answer("Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


@dp.message_handler(state=LonelyPlayerStates.Lonely_player_comment_support_enter)
async def lonely_player_comment_support_enter(message: types.Message, state: FSMContext):
    lon_player_comment = message.text
    await state.update_data(lon_player_comment=lon_player_comment)
    await bot.send_message(message.chat.id, text="Записали 👍", reply_markup=keyboards.edit_data)
    await LonelyPlayerStates.Lonely_player_comment_support.set()


@dp.message_handler(state=LonelyPlayerStates.Lonely_player_comment_support)
async def lonely_player_comment_support(message: types.Message):
    if message.text == 'Редактировать':
        await bot.send_message(message.chat.id, text='Есть ли у вас комментарии? 📝',
                               reply_markup=keyboards.yes_or_no)
        await LonelyPlayerStates.Lonely_player_comment.set()
    elif message.text == 'Далее':
        await bot.send_message(message.chat.id,
                               text='следующее сообщение будет выводом всей введённой ранее информации',
                               reply_markup=keyboards.ok_keyboard)
        await LonelyPlayerStates.Show_info_to_lonely_player.set()
    else:
        await message.answer('Произошла какая-то ошибка. Попробуйте ещё раз 🔁')


@dp.message_handler(state=LonelyPlayerStates.Show_info_to_lonely_player)
async def show_info_to_lonely_player(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lon_player_tel_id_from_fsm = data.get('lon_player_id')
    game_date_user_style_from_fsm = data.get('game_date')
    day = game_date_user_style_from_fsm[0:2]
    month = game_date_user_style_from_fsm[3:5]
    year = game_date_user_style_from_fsm[6:10]
    date_db_style = f"{year}{month}{day}"
    week_day_from_fsm = data.get('week_day')
    game_time_from_fsm = data.get('game_time')
    lon_player_name_from_fsm = data.get('lon_player_name')
    lon_player_link_from_fsm = data.get('lon_player_link')
    lon_player_comment_from_fsm = data.get('lon_player_comment')
    date_string_for_db = f"{year}-{month}-{day} {game_time_from_fsm}:00"
    lon_player_tel_id_game_date_from_fsm = (str(data.get('lon_player_id')) + date_db_style)
    if message.text == "Ок":
        # у игрока НЕТ КОММЕНТАРИЕВ
        if len(lon_player_comment_from_fsm) == 0:
            await bot.send_message(message.chat.id,
                                   text=f"Дата игры: *{game_date_user_style_from_fsm}*\n"
                                        f"День недели: *{week_day_from_fsm}*\n"
                                        f"Время игры: *{game_time_from_fsm}*\n"
                                        f"Ваше имя: *{lon_player_name_from_fsm}*\n"
                                        f"Ссылка на вашу соц.сеть: *{lon_player_link_from_fsm}*",
                                   reply_markup=keyboards.complete_registr,
                                   parse_mode='Markdown')
        # у игрока ЕСТЬ КОММЕНТАРИЙ
        else:
            await bot.send_message(message.chat.id,
                                   text=f"Дата игры: *{game_date_user_style_from_fsm}*\n"
                                        f"День недели: *{week_day_from_fsm}*\n"
                                        f"Время игры: *{game_time_from_fsm}*\n"
                                        f"Ваше имя: *{lon_player_name_from_fsm}*\n"
                                        f"Ссылка на вашу соц.сеть: *{lon_player_link_from_fsm}*\n"
                                        f"Ваш комментарий: *{lon_player_comment_from_fsm}*",
                                   reply_markup=keyboards.complete_registr,
                                   parse_mode='Markdown')
    elif message.text == "Завершить регистрацию":
        sql_commands.saving_lonely_player_to_database(lon_player_tel_id_game_date_from_fsm, lon_player_tel_id_from_fsm,
                                                      date_string_for_db, week_day_from_fsm, lon_player_name_from_fsm,
                                                      lon_player_link_from_fsm, lon_player_comment_from_fsm)
        await bot.send_message(message.chat.id, text="Поздравляем, вы зарегистрированы на игру! 🥳",
                               reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
    elif message.text == "Редактировать данные":
        await bot.send_message(message.chat.id,
                               text='Выберите команду и нажмите на неё для редактирования конкретных данных',
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await bot.send_message(message.chat.id, text=f'{commands.lonely_player_commands}',
                               reply_markup=types.ReplyKeyboardRemove())
        await LonelyPlayerStates.Finish_lonely_player_edit.set()
    else:
        await message.answer('Что-то не так. Попробуйте ещё раз 🔁')


"""

------------------------------------->>>> БЛОК КОМАНД ДЛЯ РЕДАКТИРОВАНИЯ ДАННЫХ <<<<------------------------------------
------------------------------------------->>>> ДЛЯ ОДИНОЧНОГО ИГРОКА <<<<----------------------------------------------
"""


@dp.message_handler(Command('game_date'), state=LonelyPlayerStates.Finish_lonely_player_edit)
async def lonely_player_edit_game_gate(message: types.Message):
    await bot.send_message(message.chat.id, text="Выберите дату игры",
                           reply_markup=keyboards.game_dates_buttons)
    await LonelyPlayerStates.Lonely_player_edit_game_date.set()


@dp.message_handler(content_types='text', state=LonelyPlayerStates.Lonely_player_edit_game_date)
async def catch_new_date_lonely_player(message: types.Message, state: FSMContext):
    all_about_one_date = message.text
    all_dates = sql_commands.all_dates_from_game_dates()
    list_of_dates = []
    for one_tuple in all_dates:
        list_of_dates.append(f"{one_tuple[0]} {one_tuple[1]} {one_tuple[2]}")
    game_date_in_list = re.findall(r'\d\d.\d\d.\d\d\d\d', all_about_one_date)
    game_date = game_date_in_list[0]
    week_day_in_list = re.findall(r'([А-я][а-я]+)', all_about_one_date)
    week_day = week_day_in_list[0]
    game_time_in_list = re.findall(r'\d\d:\d\d', all_about_one_date)
    game_time = game_time_in_list[0]
    # проверка, чтобы данные с датой, пришедшие в хэндлер совпадали с данными из базы
    # т.е. ТАКАЯ ДАТА + ВРЕМЯ + ДЕНЬ НЕДЕЛИ есть в базе
    if f"{game_date} {week_day} {game_time}" in list_of_dates:
        # записываем дату в fsm
        await state.update_data(ame_date=game_date, week_day=week_day, game_time=game_time)
        await bot.send_message(message.chat.id, text='Записали!', reply_markup=keyboards.ok_keyboard)
        await LonelyPlayerStates.Show_info_to_lonely_player.set()
    else:
        await bot.send_message(message.chat.id, text='Произошла какая-то ошибка. Попробуйте ещё раз.\n'
                                                     'Ожидается ввод даты 📆\nЖмите кнопочки ⬇️')


@dp.message_handler(Command('lonely_player_name'), state=LonelyPlayerStates.Finish_lonely_player_edit)
async def lonely_player_edit_player_name(message: types.Message):
    await bot.send_message(message.chat.id, text='Напишите ваше имя', reply_markup=keyboards.ReplyKeyboardRemove())
    await LonelyPlayerStates.Lonely_player_edit_name.set()


@dp.message_handler(content_types='text', state=LonelyPlayerStates.Lonely_player_edit_name)
async def catch_new_name_lonely_player(message: types.Message, state: FSMContext):
    new_lonely_player_name = message.text
    await state.update_data(lon_player_name=new_lonely_player_name)
    await bot.send_message(message.chat.id, text=f"Ваше имя сохранено, *{new_lonely_player_name}* 😉",
                           reply_markup=keyboards.ok_keyboard, parse_mode='Markdown')
    await LonelyPlayerStates.Show_info_to_lonely_player.set()


@dp.message_handler(Command('lonely_player_link'), state=LonelyPlayerStates.Finish_lonely_player_edit)
async def captain_edit_link(message: types.Message):
    await bot.send_message(message.chat.id, text='Выберите соц.сеть/мессенджер, по которой с вами можно связаться.',
                           reply_markup=keyboards.soc_network)
    await LonelyPlayerStates.Edit_lonely_player_link.set()


@dp.message_handler(content_types='text', state=LonelyPlayerStates.Edit_lonely_player_link)
async def catch_captain_link(message: types.Message):
    if message.text == "Telegram":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш аккаунт Telegram",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Edit_lonely_player_link_telegram.set()
    elif message.text == "Instagram":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш Instagram аккаунт",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Edit_lonely_player_link_instagram.set()
    elif message.text == "Facebook":
        await bot.send_message(message.chat.id, text="Внесите ссылку на ваш Facebook аккаунт",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Edit_lonely_player_link_facebook.set()
    elif message.text == "Другое":
        await bot.send_message(message.chat.id, text="Внесите ссылку", reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Edit_lonely_player_link_other_soc_net.set()
    else:
        await message.answer('Ошибка. Попробуйте ещё раз 🔁')


@dp.message_handler(content_types='text', state=LonelyPlayerStates.Edit_lonely_player_link_telegram)
async def catch_lonely_player_link_telegram(message: types.Message, state: FSMContext):
    if (message.text.startswith('https://t.me/') and len(message.text[13:]) != 0) or (
            message.text.startswith("@") and len(message.text[1:]) != 0):
        new_link_tel = message.text
        await state.update_data(lon_player_link=new_link_tel)
        await bot.send_message(message.chat.id, text='Ссылка сохранена ✅', reply_markup=keyboards.ok_keyboard)
        await LonelyPlayerStates.Show_info_to_lonely_player.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types='text', state=LonelyPlayerStates.Edit_lonely_player_link_instagram)
async def catch_lonely_player_link_instagram(message: types.Message, state: FSMContext):
    if (message.text.startswith('https://www.instagram.com/') and len(message.text[26:]) != 0) or \
            (message.text.startswith('https://instagram.com/') and len(message.text[22:]) != 0):
        new_link_inst = message.text
        await state.update_data(lon_player_link=new_link_inst)
        await bot.send_message(message.chat.id, text='Ссылка на Instagram сохранена ✅',
                               reply_markup=keyboards.ok_keyboard)
        await LonelyPlayerStates.Show_info_to_lonely_player.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types='text', state=LonelyPlayerStates.Edit_lonely_player_link_facebook)
async def catch_lonely_player_link_facebook(message: types.Message, state: FSMContext):
    if message.text.startswith('https://www.facebook.com/') and len(message.text[25:]) != 0:
        new_link_facb = message.text
        await state.update_data(lon_player_link=new_link_facb)
        await bot.send_message(message.chat.id, text='Ссылка на Facebook сохранена ✅',
                               reply_markup=keyboards.ok_keyboard)
        await LonelyPlayerStates.Show_info_to_lonely_player.set()
    else:
        await message.answer("Неверная ссылка. Попробуйте ещё раз 🔁", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types='text', state=LonelyPlayerStates.Edit_lonely_player_link_other_soc_net)
async def catch_lonely_player_link_other_soc_net(message: types.Message, state: FSMContext):
    new_link_other_soc_net = message.text
    await state.update_data(lon_player_link=new_link_other_soc_net)
    await bot.send_message(message.chat.id, text='Ссылка сохранена ✅',
                           reply_markup=keyboards.ok_keyboard)
    await LonelyPlayerStates.Show_info_to_lonely_player.set()


@dp.message_handler(Command('lonely_player_comment'), state=LonelyPlayerStates.Finish_lonely_player_edit)
async def lonely_player_edit_comment(message: types.Message):
    await bot.send_message(message.chat.id, text="Есть ли у вас комментарии? 📝",
                           reply_markup=keyboards.yes_or_no)
    await LonelyPlayerStates.Lonely_player_edit_comments.set()


@dp.message_handler(content_types='text', state=LonelyPlayerStates.Lonely_player_edit_comments)
async def catch_comment_lonely_player(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        await bot.send_message(message.chat.id, "Внесите ваш комментарий ✏️",
                               reply_markup=keyboards.ReplyKeyboardRemove())
        await LonelyPlayerStates.Lonely_player_edit_comment_enter.set()
    elif message.text == 'Нет':
        await state.update_data(lon_player_comment='')
        await bot.send_message(message.chat.id, "Сохранили!", reply_markup=keyboards.ok_keyboard)
        await LonelyPlayerStates.Show_info_to_lonely_player.set()
    else:
        await message.answer("Произошла какая-то ошибка. Попробуйте ещё раз 🔁")


@dp.message_handler(content_types='text', state=LonelyPlayerStates.Lonely_player_edit_comment_enter)
async def catch_comment_enter_lonely_player(message: types.Message, state: FSMContext):
    new_comment = message.text
    await state.update_data(lon_player_comment=new_comment)
    await bot.send_message(message.chat.id, "Записали 👍", reply_markup=keyboards.ok_keyboard)
    await LonelyPlayerStates.Show_info_to_lonely_player.set()


"""

---------------------------->>>> ОКОНЧАНИЕ РЕГИСТРАЦИИ РЕГИСТРАЦИИ ОДИНОЧНОГО ИГРОКА <<<<-------------------------------

"""

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
