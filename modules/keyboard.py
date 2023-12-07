# -*- coding: utf8 -*-
import asyncio
from datetime import datetime

from . import database
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def start_markup():
    start_buttons = ["На сегодня", "На неделю", "Следующая пара"]
    start_buttons1 = ["Баг репорт", "Консультации", "Настройки"]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_buttons).add(*start_buttons1)

    start_buttons2 = ["На завтра", "На неделю", "Следующая пара"]
    start_buttons3 = ["Баг репорт", "Консультации", "Настройки"]
    keyboard3 = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard3.add(*start_buttons2).add(*start_buttons3)

    now = datetime.now()
    time = now.strftime("%H:%M")
    if time < "17:30":
        return keyboard
    return keyboard3


async def list_group_markup(number, method=1):
    group_list = await database.Get_group_list()
    list_len = len(group_list)
    group_list.sort()
    page = int((list_len - 26) / 12) + 3
    if number == 1:
        group_list = group_list[:13]
    elif number == page:
        group_list = group_list[(int(page - 1) * 12) + 1::]
    else:
        group_list = group_list[(int(number - 1) * 12) + 1::][:12]
    loop = 1
    loop_main = 1
    item_len = 0
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []

    if method == 1:
        callback_data_main = ['register_3', 'register_list']
    else:
        callback_data_main = ['settings_group', 'settings_group']

    len_group = len(group_list)
    for group in group_list:
        item_len += 1
        name = group
        name = name[0].title() + name[1:]
        if loop == 3 or len_group == item_len:
            if len(buttons) == 2:
                buttons.append(InlineKeyboardButton(name, callback_data=f'{callback_data_main[0]}_{group}_1_{number}'))
            markup.add(*buttons)
            buttons = []
            loop = 0
            if loop_main == 4 or len_group == item_len:
                markup.add(*buttons)
                if number == 1:
                    markup.add(
                        InlineKeyboardButton(name, callback_data=f'{callback_data_main[0]}_{group}_1_{number}'),
                        InlineKeyboardButton(f"(..{number}/{page}..)", callback_data="-"),
                        InlineKeyboardButton("===>", callback_data=f"{callback_data_main[1]}_{number + 1}")
                    )
                elif number == page:
                    markup.add(
                        InlineKeyboardButton("<===", callback_data=f"{callback_data_main[1]}_{number - 1}"),
                        InlineKeyboardButton(f"(..{number}/{page}..)", callback_data="-"),
                        InlineKeyboardButton(name, callback_data=f'{callback_data_main[0]}_{group}_1_{number}')
                    )
                else:
                    markup.add(
                        InlineKeyboardButton("<===", callback_data=f"{callback_data_main[1]}_{number - 1}"),
                        InlineKeyboardButton(f"(..{number}/{page}..)", callback_data="-"),
                        InlineKeyboardButton("===>", callback_data=f"{callback_data_main[1]}_{number + 1}")
                    )
                break
            loop_main += 1
            loop += 1
            continue
        buttons.append(InlineKeyboardButton(name, callback_data=f'{callback_data_main[0]}_{group}_1_{number}'))
        loop += 1
    if method != 1:
        markup.add(
            InlineKeyboardButton(text="Назад", callback_data=f"settings")
        )
    return markup


if __name__ == '__main__':
    asyncio.run(list_group_markup(4))
