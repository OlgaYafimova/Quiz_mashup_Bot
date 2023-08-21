import sqlite3


# ПРИГОДИТСЯ ДЛЯ АДМИНОВ, ЧТОБЫ ДОБАВЛЯТЬ НОВЫЕ ДАТЫ ИГР
# добавляет в таблицу game_dates новую запись с датой
# принимает два аргумента:
# 1 - дата в формате ГГГГ-ММ-ДД ЧЧ:ММ:СС
# 2 - день недели на русском языке
def insert_into_table_game_dates(date, wday):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()

    query_insert = "INSERT INTO game_dates(GameDate, WeekDay) VALUES (?, ?)"
    cursor.execute(query_insert, (date, wday))
    conn.commit()

    cursor.close()
    conn.close()


# забирает все даты из таблицы game_dates в формате (ДД.ММ.ГГГГ), (ДЕНЬ НЕДЕЛИ), (ЧЧ:ММ), кроме тех, что уже в прошлом
def all_dates_from_game_dates():
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()

    query_select_from_gd = "SELECT STRFTIME('%d.%m.%Y', GameDate), WeekDay, STRFTIME('%H:%M', GameDate) " \
                           "FROM game_dates " \
                           "WHERE GameDate > STRFTIME('%Y-%m-%d', 'now') " \
                           "ORDER BY GameDate"
    cursor.execute(query_select_from_gd)
    all_dates = cursor.fetchall()
    conn.commit()

    cursor.close()
    conn.close()
    return all_dates


# запись в БД всей информации о капитане
def saving_cap_info_to_database(catTelGameD, capTelegrId, date, wday, capName, capPhone, capSocNet, capRef, team,
                                amntPls, capAgr, capCom):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()

    query_save_cap = "INSERT INTO captains(CaptTelegramIdGameDate, CaptTelegramId, GameDate, WeekDay, CaptName, " \
                     "Phone, SocNetLink, ReffURLCapt, TeamName, AmountPlayers, CaptAgree, CaptComment) " \
                     "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"
    cursor.execute(query_save_cap,
                   (catTelGameD, capTelegrId, date, wday, capName, capPhone,
                    capSocNet, capRef, team, amntPls, capAgr, capCom))
    conn.commit()

    cursor.close()
    conn.close()


# забирает из БД даты игр, на которые зарегистрирован этот капитан, кроме тех дат, что уже в прошлом
# дата "сегодня" будет также попадать в выборку
# принимает в кач-ве аргумента telegram id капитана
# возвращает список дат
def all_dates_captain_registered_is_except_past(tel_id):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()

    query = "SELECT STRFTIME('%d.%m.%Y', GameDate) " \
            "FROM captains " \
            "WHERE CaptTelegramId = (?) AND GameDate > STRFTIME('%Y-%m-%d', 'now', '-1 days') " \
            "ORDER BY GameDate"
    cursor.execute(query, (tel_id,))
    all_dates = list(cursor.fetchall())
    list_of_dates = []
    for index in range(0, len(all_dates)):
        for one_date in all_dates[index]:
            list_of_dates.append(one_date)

    conn.commit()

    cursor.close()
    conn.close()
    return list_of_dates


# забирает НАЗВАНИЕ КОМАНДЫ, ИМЯ КАПИТАНА, ДЕНЬ НЕДЕЛИ, ВРЕМЯ ИГРЫ из таблицы капитанов
# принимает в кач-ве аргументов id капитана и дату игры
def select_teamname_captname_by_capid_gamedate(cap_id, date):
    clear_date = str(date).replace('-', '')
    capid_gd = str(cap_id) + clear_date
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()
    query = "SELECT TeamName, CaptName, WeekDay, STRFTIME('%H:%M',GameDate) " \
            "FROM captains " \
            "WHERE CaptTelegramIdGameDate = (?)"
    cursor.execute(query, (capid_gd,))
    data_from_table = cursor.fetchall()

    conn.commit()

    cursor.close()
    conn.close()
    return data_from_table


# запись в БД игрока команды
def saving_player_to_database(catTelGameD, capTelegrId, plrTelIdGdate, plrTelId, date, weekday,
                              team, capName, plrName, plrComm):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()

    query_save_player = "INSERT INTO players(CaptTelegramIdGameDate, CaptTelegramId, PlayerTelegramIdGameDate, " \
                        "PlayerTelegramId, GameDate, WeekDay, TeamName, CaptName, PlayerName, PlayerComment) " \
                        "VALUES(?,?,?,?,?,?,?,?,?, ?)"
    cursor.execute(query_save_player,
                   (catTelGameD, capTelegrId, plrTelIdGdate, plrTelId, date, weekday, team, capName, plrName, plrComm))
    conn.commit()

    cursor.close()
    conn.close()


# забирает ИМЯ игрока команды из таблицы игроков
# принимает id игрока и дату игры
def check_player_name_into_base_by_playerid_date(plrId, gameDate):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()
    query = "SELECT PlayerName FROM players WHERE PlayerTelegramId = (?) AND GameDate = (?)"
    cursor.execute(query, (plrId, gameDate))
    player_name_from_table = cursor.fetchall()

    conn.commit()

    cursor.close()
    conn.close()
    return player_name_from_table


# забирает НАЗВАНИЕ КОМАНДЫ, зарегистрированной на конкретную дату
# принимает в кач-ве аргумента строку "id+дата игры"
# возвращает НАЗВАНИЕ КОМАНДЫ
def check_team_name_into_base_by_captid_date(captIdgameDate):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()
    query = "SELECT TeamName FROM captains WHERE CaptTelegramIdGameDate = (?)"
    cursor.execute(query, (captIdgameDate, ))
    capt_name_from_table = cursor.fetchall()

    conn.commit()

    cursor.close()
    conn.close()
    return capt_name_from_table


# забирает из БД все даты игр, на которые когда-либо регистрировался этот капитан
# принимает в кач-ве аргумента telegram id капитана
# возвращает даты в виде списка
def all_dates_captain_registered_is(tel_id):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()

    query = "SELECT GameDate FROM captains WHERE CaptTelegramId = (?)" \
            "ORDER BY GameDate;"
    cursor.execute(query, (tel_id,))
    all_dates = list(cursor.fetchall())
    list_of_dates = []
    for index in range(0, len(all_dates)):
        for one_date in all_dates[index]:
            list_of_dates.append(one_date)

    conn.commit()

    cursor.close()
    conn.close()
    return list_of_dates


# забирает из БД все даты игр, на которые когда-либо регистрировался этот капитан
# принимает в кач-ве аргумента telegram id капитана
# возвращает даты в виде списка
def all_dates_captain_registered_is_without_time(tel_id):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()

    query = "SELECT STRFTIME('%d.%m.%Y', GameDate) " \
            "FROM captains " \
            "WHERE CaptTelegramId = (?) " \
            "ORDER BY GameDate"
    cursor.execute(query, (tel_id,))
    all_dates = list(cursor.fetchall())
    list_of_dates = []
    for index in range(0, len(all_dates)):
        for one_date in all_dates[index]:
            list_of_dates.append(one_date)

    conn.commit()

    cursor.close()
    conn.close()
    return list_of_dates


# забирает из базы всю информацию о капитане
# принимает в кач-ве аргумента строку "id+дата игры"
def select_all_registr_info_by_capid_gamedate(captIdgameDate):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()
    query = "SELECT CaptName, Phone, SocNetLink, ReffURLCapt, " \
            "TeamName, AmountPlayers, CaptAgree, CaptComment " \
            "FROM captains " \
            "WHERE CaptTelegramIdGameDate = (?)"
    cursor.execute(query, (captIdgameDate,))
    data_from_table = cursor.fetchall()

    conn.commit()

    cursor.close()
    conn.close()
    return data_from_table


# запись в БД одиночного игрока
def saving_lonely_player_to_database(lonPlTelIdGameDate, lonPlTelId, date, weekday, name, socnetlink, comment):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()

    query_save_lonely_player = "INSERT INTO lonely_players(LonelyPlayerTelegramIdGameDate, LonelyPlayerTelegramId, " \
                               "GameDate, WeekDay, LonelyPlayerName, SocNetLink, LonelyPlayerComment) " \
                               "VALUES(?,?,?,?,?,?,?)"
    cursor.execute(query_save_lonely_player,
                   (lonPlTelIdGameDate, lonPlTelId, date, weekday, name, socnetlink, comment))
    conn.commit()

    cursor.close()
    conn.close()


# функция отправляет запрос в БД по CaptTelegramIdGameDate
# забирает имя капитана, если такое есть
def select_captname_by_capid_gamedate(captIdgameDate):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()
    query = "SELECT CaptName FROM captains WHERE CaptTelegramIdGameDate = (?)"
    cursor.execute(query, (captIdgameDate,))
    data_from_table = cursor.fetchall()

    conn.commit()

    cursor.close()
    conn.close()
    return data_from_table


# функция отправляет запрос в БД по PlayerTelegramIdGameDate
# забирает имя игрока, если такое есть
def select_player_name_by_playerid_gamedate(playerIdgameDate):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()
    query = "SELECT PlayerName FROM players WHERE PlayerTelegramIdGameDate = (?)"
    cursor.execute(query, (playerIdgameDate,))
    data_from_table = cursor.fetchall()

    conn.commit()

    cursor.close()
    conn.close()
    return data_from_table


# функция отправляет запрос в БД по LonelyPlayerTelegramIdGameDate
# забирает имя игрока, если такое есть
def select_lonely_player_name_by_lonely_playerid_gamedate(lonplayerIdgameDate):
    conn = sqlite3.connect("qiuz3.db")
    cursor = conn.cursor()
    query = "SELECT LonelyPlayerName FROM lonely_players WHERE LonelyPlayerTelegramIdGameDate = (?)"
    cursor.execute(query, (lonplayerIdgameDate,))
    data_from_table = cursor.fetchall()

    conn.commit()

    cursor.close()
    conn.close()
    return data_from_table
