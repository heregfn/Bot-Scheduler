# -*- coding: utf8 -*-
import asyncio
import calendar
import datetime
import logging
import random
from datetime import datetime
import time

import aiogram.utils.exceptions
import aioschedule
import aiosqlite
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext, DEFAULT_RATE_LIMIT
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import ClientSession
from pyqiwip2p import AioQiwiP2P
from modules.database import *
from modules.keyboard import *

log_name = datetime.now().strftime("logs/%H_%M_%S_%Y-%m-%d.txt")
logging.basicConfig(format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
                    # filename=log_name,
                    # filemode='a',
                    datefmt="%d/%b/%Y %H:%M:%S",
                    level=logging.INFO)

bot = Bot(token="")
QIWI_PRIV_KEY = ""

p2p = AioQiwiP2P(auth_key=QIWI_PRIV_KEY)
dp = Dispatcher(bot, storage=MemoryStorage())


async def send_analytics(user_id, user_lang_code, action_name, time):
    """
    Send record to Google Analytics
    """
    params = {
        'client_id': str(user_id),
        'events': [{
            'name': action_name,
            'params': {
                'user_id': str(user_id),
                'language': user_lang_code,
                'engagement_time_msec': "1",
                'funs_time': time
            }
        }],
    }
    async with ClientSession() as session:
        await session.post(
            f'https://www.google-analytics.com/'
            f'mp/collect?measurement_id=G-7KP4D9V1CD&api_secret=u44AWVlcR9OK78_34uuzlA',
            json=params)
    logging.info("pass")


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_', logger=__name__):
        self.rate_limit = 0.5
        self.prefix = key_prefix
        if not isinstance(logger, logging.Logger):
            logger = logging.getLogger(logger)
        self.logger = logger
        super(ThrottlingMiddleware, self).__init__()

    def check_timeout(self, obj):
        start = obj.conf.get('_start', None)
        if start:
            del obj.conf['_start']
            return round((time.time() - start) * 1000)
        return -1

    async def on_pre_process_update(self, update: types.Update, data: dict):
        update.conf['_start'] = time.time()
        self.logger.debug(f"Received update [ID:{update.update_id}] [{update}]")

    async def on_post_process_update(self, update: types.Update, result, data: dict):
        timeout = self.check_timeout(update)
        if timeout > 0:
            if update.callback_query is not None:
                msg = await update.callback_query.answer('')
                await send_analytics(update.callback_query.from_user.id, update.callback_query.from_user.language_code,
                                     update.callback_query.data, timeout)
                self.logger.info(
                    f"Process update [ID:{update.update_id}] \"{update.callback_query.data}\": [success] (in {timeout} ms)")
            elif update.message is not None:
                try:
                    text = update.message.text[::40]
                except:
                    text = None
                await send_analytics(update.message.from_user.id, update.message.from_user.language_code,
                                     text, timeout)
            else:
                self.logger.info(f"IDK message update: {update}")


@dp.message_handler(commands="start")
async def start(message: types.Message):
    try:
        user_id = message.from_user.id
        answer = await DB_reg(user_id, message.from_user.username)
        reply_markup = await start_markup()
        if answer == 'Ok':
            if user_id == 438670811:
                await bot.send_message(1020238041, f'{message.text}')
            else:
                args = message.get_args()
                if args == '':
                    await message.answer('🖐 Привет! Вот твое меню',
                                         disable_web_page_preview=True, reply_markup=reply_markup)
                else:
                    yes = InlineKeyboardButton("✅ Подтвердить", callback_data=f"connect_yes_{args}")
                    no = InlineKeyboardButton("❌ Отменить", callback_data="connect_no")
                    connect = InlineKeyboardMarkup(row_width=2).add(yes, no)
                    await message.answer("Нажимая на кнопку ниже вы подтвердите связывание ВК и ТГ",
                                         reply_markup=connect)
        elif answer == 'No found':
            yes = InlineKeyboardButton("Не нужно", callback_data=f"register_no")
            no = InlineKeyboardButton("Давай :)", callback_data="register_yes")
            start_register = InlineKeyboardMarkup(row_width=2).add(no, yes)
            await message.answer('🖐 Привет! Я вижу ты тут новенький, давай помогу тебе :)',
                                 disable_web_page_preview=True, reply_markup=start_register)
        else:
            user_id = message.from_user.id
            await bot.send_message(1020238041, f'[ERROR] /start ({user_id}): {answer}')
    except Exception as stat_ex:
        user_id = message.from_user.id
        await bot.send_message(1020238041, f'[ERROR] /start ({user_id}): {stat_ex}')


@dp.callback_query_handler(Text(startswith="register_"))
async def register_query_handler(msg: types.CallbackQuery):
    data = msg.data
    split_data = data.split('_')
    data_1 = None
    data_2 = None
    user_id = msg.from_user.id
    message = msg.message
    if len(split_data) >= 3:
        data_1 = split_data[2]
    if len(split_data) >= 5:
        data_2 = split_data[4]
    # ______________________ 1 этап ____________________________
    if data == 'register_yes':
        markup = await list_group_markup(1)
        await message.edit_text(
            "Хорошо, выбери тогда свою группу из списка ниже. Список можно переключать нажимая на стрелочки",
            reply_markup=markup)
    elif data == 'register_no':
        await message.edit_text("Хорошо, удачи:)", reply_markup=(await start_markup()))
        await DB_reg_pass(user_id)

    # ______________________ 2 этап ____________________________
    elif data == f'register_list_{data_1}':
        markup = await list_group_markup(int(data_1))
        await message.edit_text(
            "Хорошо, выбери тогда свою группу из списка ниже. Список можно переключать нажимая на стрелочки",
            reply_markup=markup)

    # ______________________ 3 этап ____________________________
    elif data == f'register_3_{data_1}_1_{data_2}':
        await message.edit_text(f"Ты уверен что твоя группа \"{data_1}\"?",
                                reply_markup=InlineKeyboardMarkup(row_width=2).add(
                                    InlineKeyboardButton('Да!', callback_data=f"register_3_{data_1}_1"),
                                    InlineKeyboardButton('Я ошибся', callback_data=f"register_list_{data_2}")
                                ))
    elif data == f'register_3_{data_1}_1':
        await Set_group(user_id=msg.from_user.id, username=msg.from_user.username, group=data_1)
        await message.edit_text(
            f"Хорошо, так-с группу ты выбрал... это хорошо, а точно у бота же есть еще выбор под группы, нажми там на кнопку :)",
            reply_markup=InlineKeyboardMarkup(row_width=2).add(
                InlineKeyboardButton('Я 1 подгруппа', callback_data=f'register_4_1'),
                InlineKeyboardButton('Я 2 подгруппа', callback_data=f'register_4_2')
            ))

    # ______________________ 4 этап ____________________________
    elif data == f'register_4_{data_1}':
        await Set_pod_group(user_id=user_id, group_pod=data_1)
        await message.edit_text(
            f"Хм... а ты быстрый, ну ладно продолжим, бот может присылать тебе уведомления о следующих парах\n\n"
            f"Как пример. Ты сидишь на паре, ну или дома:), а бот тебе за 5-7 минут до окончания пар скинет след. пару, ну что включаем?",
            reply_markup=InlineKeyboardMarkup(row_width=2).add(
                InlineKeyboardButton('Ну давай :)', callback_data=f'register_5_1'),
                InlineKeyboardButton('Нехотю', callback_data=f'register_5_2')
            ))

    # ______________________ 5 этап ____________________________
    elif data == f'register_5_{data_1}':
        await message.edit_text(
            "И так, ну вот и все можешь уже полноценно пользоваться ботом он полностью настроен под тебя :), удачки",
            reply_markup=None)
        await asyncio.sleep(1)
        await message.answer('Вот твое меню',
                             disable_web_page_preview=True, reply_markup=await start_markup())
        await DB_reg_pass(user_id)
    else:
        pass


@dp.callback_query_handler(Text(startswith="Update_"))
async def register_query_handler(msg: types.CallbackQuery):
    data = msg.data
    split_data = data.split('_')
    data_1 = None
    data_2 = None
    message = msg.message
    user_id = msg.from_user.id
    if len(split_data) >= 2:
        data_1 = split_data[1]
    if len(split_data) >= 3:
        data_2 = split_data[2]
    if data == f'Update_{data_1}_{data_2}':
        a = await Pars(4, user_id, data_1, data_2)
        try:
            await message.edit_text(text=a[1][0][0], reply_markup=message.reply_markup)
        except aiogram.utils.exceptions.MessageNotModified:
            await msg.answer(text='Расписание актуально изменений нет.', show_alert=True)


# ---------------------------------------------- Расписания ------------------------------------------------------------
@dp.message_handler(Text(equals="На сегодня"))
@dp.message_handler(commands="nowday")
async def now_day(message: types.Message):
    user_id = message.from_user.id
    text = await Pars(1, user_id)
    if text[0] is True:
        for item in text[1]:
            await message.answer(text=item[0], reply_markup=InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton(text="Обновить", callback_data=f'Update_{item[1]}_{item[2]}')
            ))
    elif text[0] is False:
        if text[1] == 'No pars':
            await message.answer('На данный момент еще нет расписания на этот день')
        elif text[1] == 'No found group':
            yes = InlineKeyboardButton("Не нужно", callback_data=f"register_no")
            no = InlineKeyboardButton("Давай :)", callback_data="register_yes")
            start_register = InlineKeyboardMarkup(row_width=2).add(no, yes)
            await message.answer('У вас не выбрана ваша группа, пройдем регистрацию?', reply_markup=start_register)


@dp.message_handler(Text(equals="На завтра"))
@dp.message_handler(commands="nextday")
async def next_day(message: types.Message):
    user_id = message.from_user.id
    text = await Pars(2, user_id)
    if text[0] is True:
        for item in text[1]:
            await message.answer(text=item[0], reply_markup=InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton(text="Обновить", callback_data=f'Update_{item[1]}_{item[2]}')
            ))
    elif text[0] is False:
        if text[1] == 'No pars':
            await message.answer('На данный момент еще нет расписания на этот день')
        elif text[1] == 'No found group':
            yes = InlineKeyboardButton("Не нужно", callback_data=f"register_no")
            no = InlineKeyboardButton("Давай :)", callback_data="register_yes")
            start_register = InlineKeyboardMarkup(row_width=2).add(no, yes)
            await message.answer('У вас не выбрана ваша группа, пройдем регистрацию?', reply_markup=start_register)
        elif text[1] == 'No pars to day':
            await message.answer('Пар в воскресенье нет :)')


@dp.message_handler(Text(equals="На неделю"))
@dp.message_handler(commands="week")
async def week(message: types.Message):
    user_id = message.from_user.id
    text = await Pars(3, user_id)
    if text[0] is True:
        for item in text[1]:
            await message.answer(text=item[0], reply_markup=InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton(text="Обновить", callback_data=f'Update_{item[1]}_{item[2]}')
            ))
    elif text[0] is False:
        if text[1] == 'No pars':
            await message.answer('На данный момент еще нет расписания след неделю')
        elif text[1] == 'No found group':
            yes = InlineKeyboardButton("Не нужно", callback_data=f"register_no")
            no = InlineKeyboardButton("Давай :)", callback_data="register_yes")
            start_register = InlineKeyboardMarkup(row_width=2).add(no, yes)
            await message.answer('У вас не выбрана ваша группа, пройдем регистрацию?', reply_markup=start_register)
        elif text[1] == 'No pars to day':
            await message.answer('Пар в воскресенье нет :)')
# ______________________________________________________________________________________________________________________


@dp.message_handler(Text(equals="Настройки"))
@dp.message_handler(commands="settings")
async def settings(message: types.Message):
    await message.answer("Ты попал в настройки, выбери нужный пункт ниже.",
                         reply_markup=InlineKeyboardMarkup(row_width=2).add(
                             InlineKeyboardButton(text="Сменить группу", callback_data="settings_group"),
                             InlineKeyboardButton(text="Сменить под-группу", callback_data="settings_pod_group"),
                             InlineKeyboardButton(text="Премиум", callback_data="settings_subs")
                         ))


@dp.callback_query_handler(Text(startswith="settings"))
async def settings_query_handler(msg: types.CallbackQuery):
    user_id = msg.from_user.id
    data = msg.data
    message = msg.message
    # -----------------------------------
    items_data = data.split('_')
    # -----------------------------------
    if data == "settings":
        await message.edit_text("Ты попал в настройки, выбери нужный пункт ниже.",
                                reply_markup=InlineKeyboardMarkup(row_width=2).add(
                                    InlineKeyboardButton(text="Сменить группу", callback_data="settings_group"),
                                    InlineKeyboardButton(text="Смена под-группы", callback_data="settings_pod_group"),
                                    InlineKeyboardButton(text="Премиум", callback_data="settings_subs")
                                ))
    # -----------------------------------
    if "settings_group" in data:
        items_data_1 = None
        items_data_2 = None
        if len(items_data) >= 3:
            items_data_1 = items_data[2]
        if len(items_data) >= 5:
            items_data_2 = items_data[4]
        if data == f"settings_group":
            await message.edit_text('Выбери свою группу из списка ниже', reply_markup=await list_group_markup(1, method=2))
        elif data == f"settings_group_{items_data_1}":
            await message.edit_text('Выбери свою группу из списка ниже',
                                    reply_markup=await list_group_markup(int(items_data_1), method=2))
        elif data == f"settings_group_{items_data_1}_1_{items_data_2}":
            await message.edit_text(f'Вы уверены что хотите выбрать группу {items_data_1}?',
                                    reply_markup=InlineKeyboardMarkup(row_width=2).add(
                                        InlineKeyboardButton(text="Да",
                                                             callback_data=f"settings_group_{items_data_1}_2_{items_data_2}"),
                                        InlineKeyboardButton(text="Нет", callback_data=f"settings_group_{items_data_2}")
                                    ))
        elif data == f"settings_group_{items_data_1}_2_{items_data_2}":
            await Set_group(
                user_id=msg.from_user.id,
                username=msg.from_user.username,
                group=items_data_1.lower().strip()
            )
            await msg.answer(f'Вы успешно выбрали группу {items_data_1}', show_alert=True)
            await message.edit_text("Ты попал в настройки, выбери нужный пункт ниже.",
                                    reply_markup=InlineKeyboardMarkup(row_width=2).add(
                                        InlineKeyboardButton(text="Сменить группу", callback_data="settings_group"),
                                        InlineKeyboardButton(text="Смена под-группы",
                                                             callback_data="settings_pod_group"),
                                        InlineKeyboardButton(text="Премиум", callback_data="settings_subs")
                                    ))
        else:
            print(data, ", settings_pod_group")
    # -----------------------------------
    elif "settings_pod_group" in data:
        items_data_1 = None
        if len(items_data) >= 4:
            items_data_1 = items_data[3]
        if data == f"settings_pod_group":
            await message.edit_text("Ты попал в настройки под-группы, выбери нужный пункт ниже.",
                                    reply_markup=InlineKeyboardMarkup(row_width=2).add(
                                        InlineKeyboardButton(text="Я 1 подгруппа",
                                                             callback_data="settings_pod_group_1"),
                                        InlineKeyboardButton(text="Я 2 подгруппа",
                                                             callback_data="settings_pod_group_2"),
                                        InlineKeyboardButton(text="Назад", callback_data="settings")
                                    ))
        elif data == f"settings_pod_group_{items_data_1}":
            await Set_pod_group(user_id=user_id, group_pod=items_data_1)
            await msg.answer(f"Вы успешно сменили под-группу на {items_data_1}", show_alert=True)
            await message.edit_text("Ты попал в настройки, выбери нужный пункт ниже.",
                                    reply_markup=InlineKeyboardMarkup(row_width=2).add(
                                        InlineKeyboardButton(text="Сменить группу", callback_data="settings_group"),
                                        InlineKeyboardButton(text="Смена под-группы",
                                                             callback_data="settings_pod_group"),
                                        InlineKeyboardButton(text="Премиум", callback_data="settings_subs")
                                    ))
        else:
            print(data, ", settings_pod_group")
    # -----------------------------------
    elif "settings_subs" in data:
        await msg.answer('В разработке')
        return

        if data == f"settings_subs":
            await message.edit_text("Ты в настройках для премиум пользователей, выбери нужный пункт ниже.",
                                    reply_markup=InlineKeyboardMarkup(row_width=2).add(
                                        InlineKeyboardButton(text="Рассылки", callback_data="settings_subs_send"),
                                        InlineKeyboardButton(text="Статистика", callback_data="settings_subs_statick"),
                                        InlineKeyboardButton(text="Мастерская дизайнов", callback_data="-")).add(
                                        InlineKeyboardButton(text="Назад", callback_data="settings")
                                    ))
        elif "settings_subs_send" in data:
            if data == f"settings_subs_send":
                await message.edit_text("Ты выбрал настройки рассылок, выбери нужный пункт ниже.",
                                        reply_markup=InlineKeyboardMarkup(row_width=2).add(
                                            InlineKeyboardButton(text="Авто пары", callback_data="settings_subs_send_1"),
                                            InlineKeyboardButton(text="Авто изменения", callback_data="settings_subs_send_2"),
                                            InlineKeyboardButton(text="Назад", callback_data="settings_subs")
                                        ))
            # -----------------Авто пары--------------------
            elif "settings_subs_send_1" in data:
                if data == f"settings_subs_send_1":
                    await message.edit_text(
                        "Авто пары - Функция которая автоматически за выбранный период (5 Мин, 10 Мин, 15 Мин) "
                        "присылает вам следующие пары, а также вечером в 20:00 пришлет вам расписание на след. день. "
                        "При появлении нового расписания на неделю бот пришлет новое расписание.", reply_markup=InlineKeyboardMarkup(row_width=2).add(
                            InlineKeyboardButton(text="Вкл / Выкл", callback_data="settings_subs_send_1_1"),
                            InlineKeyboardButton(text="Настройка", callback_data="settings_subs_send_1_2"),
                            InlineKeyboardButton(text="Назад", callback_data="settings_subs_send")
                        )
                    )
                elif data == f"settings_subs_send_1_1":
                    pass
                elif "settings_subs_send_1_2" in data:
                    items_data_1 = None
                    if len(items_data) >= 7:
                        items_data_1 = items_data[6]
                    if data == f"settings_subs_send_1_2":
                        await message.edit_text("Ты выбрал внутренние настройки Авто-пары, выбери нужный пункт ниже.",
                                                reply_markup=InlineKeyboardMarkup(row_width=1).add(
                                                    InlineKeyboardButton(text="Настройка периодичности", callback_data="settings_subs_send_1_2_1"),
                                                    InlineKeyboardButton(text="Настройка уведомлений", callback_data="settings_subs_send_1_2_2"),
                                                    InlineKeyboardButton(text="Назад", callback_data="settings_subs_send_1")
                                                ))
                    elif data == f"settings_subs_send_1_2_1":
                        await message.edit_text("Выбери за сколько минут присылать след. пару", reply_markup=InlineKeyboardMarkup(row_width=1).add(
                            InlineKeyboardButton(text="5 минут", callback_data="settings_subs_send_1_2_1_1"),
                            InlineKeyboardButton(text="10 минут", callback_data="settings_subs_send_1_2_1_2"),
                            InlineKeyboardButton(text="15 минут", callback_data="settings_subs_send_1_2_1_3"),
                            InlineKeyboardButton(text="Назад", callback_data="settings_subs_send_1_2"),
                        ))
                    elif data == f"settings_subs_send_1_2_1_{items_data_1}":
                        pass
                    elif data == f"settings_subs_send_1_2_2":
                        await message.edit_text("Выбери какие уведомления ты хочешь включить / выключить. \n❌ - Выключено\n✅ - Включено", reply_markup=None)
            # --------------Авто изменения-------------------
            elif "settings_subs_send_2" in data:
                if data == f"settings_subs_send_2":
                    await message.edit_text("Авто изменения - Функция которая при изменении расписания присылает измененную пару моментально в чат",
                                            reply_markup=InlineKeyboardMarkup(row_width=1).add(
                                                InlineKeyboardButton(text="Включить / Выключить", callback_data="settings_subs_send_2_1"),
                                                InlineKeyboardButton(text="Назад", callback_data="settings_subs_send"),
                                            ))
                elif data == f"settings_subs_send_2_1":
                    pass
            # --------------------------------------
        elif "settings_subs_statick" in data:
            await msg.answer('В разработке')
            if data == f"settings_subs_statick":
                await message.edit_text("Ты выбрал меню статистики, выбери нужный пункт ниже.",
                                        reply_markup=InlineKeyboardMarkup(row_width=1).add(
                                            InlineKeyboardButton(text="Статистика предметов", callback_data="settings_subs_statick_1"),
                                            InlineKeyboardButton(text="Статистика преподавателей", callback_data="settings_subs_statick_2"),
                                            InlineKeyboardButton(text="Поиск преподавателей", callback_data="settings_subs_statick_3"),
                                            InlineKeyboardButton(text="Статистика бота", callback_data="settings_subs_statick_4"),
                                            InlineKeyboardButton(text="Назад", callback_data="settings_subs"),
                                        ))
            elif data == f"settings_subs_statick_1":
                pass
            elif data == f"settings_subs_statick_2":
                pass
            elif data == f"settings_subs_statick_3":
                pass
            elif data == f"settings_subs_statick_4":
                pass
        else:
            print(data, ", settings_subs")
    # -----------------------------------
    else:
        print(data)


@dp.message_handler(commands="test")
async def test(msg: types.Message):
    await msg.answer('1', reply_markup=InlineKeyboardMarkup().add(
        InlineKeyboardButton('1', callback_data='Update_1687750200_1687761600')
    ))


@dp.message_handler(content_types=types.ContentType.all())
async def inecorect(message: types.Message):
    pass


if __name__ == '__main__':
    dp.middleware.setup(ThrottlingMiddleware())
    executor.start_polling(dp, skip_updates=False)
