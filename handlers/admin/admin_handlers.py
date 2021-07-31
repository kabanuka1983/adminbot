from asyncio import sleep
from datetime import datetime
from time import time

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ForwardedMessageFilter

from config import ADMIN_ID, permissions_restrict
from keyboard.default.menu import menu
from loader import dp, bot
from utils import database
from utils.states import UpOneMonth, DownOneMonth, UserStatus

db = database.DBCommands()


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    commands=["start", "омощь"], commands_prefix=["/", "П"])
async def show_menu(message):
    markup = menu
    text = "Команды: \n\n<b>!+30</b> - продлить подписку на 30 дней \n<b>!-30</b> - уменьшить подписку на 30 дней" \
           "\n<b>?status</b> - посмотреть срок подписки" \
           "\n\n<b>Как пользоваться:</b> сообщение нужного пользователя <b>ПЕРЕСЛАТЬ</b> в группу " \
           "сопроводив соответствующей командой" \
           "\n\n\n\nЕщё команды: \n\n<b>!ban</b> - бан на сутки без продления подписки" \
           "\n\n<b>Как пользоваться: ОТВЕТИТЬ</b> на сообщение нужного пользователя в группе " \
           "сопроводив соответствующей командой"
    await message.answer(text=text, reply_markup=markup, parse_mode="HTML")


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    commands=["ban"], commands_prefix="!")
async def set_restrict(message: types.Message):
    if not message.reply_to_message:
        await message.delete()
        return

    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id
    await message.delete()
    await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, until_date=time()+60,
                                   permissions=permissions_restrict)

    name = message.reply_to_message.from_user.full_name
    await message.reply_to_message.reply(f"{name} ты забанен на сутки")


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    commands=["+30"], commands_prefix="!", state=None)
async def get_command_mess_id(message: types.Message, state: FSMContext):
    print('get_command_mess_id')
    await UpOneMonth.mess_id.set()
    command_mess_id = message.message_id
    await state.update_data(id=command_mess_id)
    await message.delete()
    await sleep(1)
    await state.reset_state()


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    commands=["-30"], commands_prefix="!", state=None)
async def get_command_mess_id_down(message: types.Message, state: FSMContext):
    print('get_command_mess_id_down')
    await DownOneMonth.mess_id.set()
    command_mess_id = message.message_id
    await state.update_data(id=command_mess_id)
    await message.delete()
    await sleep(1)
    await state.reset_state()


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    commands=["status"], commands_prefix="?", state=None)
async def get_command_mess_id_status(message: types.Message, state: FSMContext):
    print('get_command_mess_id_status')
    await UserStatus.mess_id.set()
    command_mess_id = message.message_id
    await state.update_data(id=command_mess_id)
    await message.delete()
    await sleep(1)
    await state.reset_state()


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    commands=["+30"], commands_prefix="!", state="*")
async def reset_up(message: types.Message, state: FSMContext):
    print('reset_up')
    await state.reset_state()
    await get_command_mess_id(message=message, state=state)


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    commands=["-30"], commands_prefix="!", state="*")
async def reset_down(message: types.Message, state: FSMContext):
    print('reset_down')
    await state.reset_state()
    await get_command_mess_id_down(message=message, state=state)


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    commands=["status"], commands_prefix="?", state="*")
async def reset_status(message: types.Message, state: FSMContext):
    print('reset_status')
    await state.reset_state()
    await get_command_mess_id_status(message=message, state=state)


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    ForwardedMessageFilter(True), state=UpOneMonth.mess_id)
async def set_user_update_month(message: types.Message, state: FSMContext):
    print('set_user_update_month')
    data = await state.get_data()
    command_mess_id = data.get("id")
    current_mess_id = message.message_id
    timestamp = datetime.now().timestamp()
    referral = message.forward_from.id

    await db.add_new_user(member=message.forward_from, timestamp=timestamp)

    if current_mess_id == command_mess_id+1:
        upd = await db.user_timestamp_update(referral=referral, timestamp=timestamp)
        upd_date = datetime.fromtimestamp(upd)
        name = message.forward_from.full_name
        text = f"Пользователь: <b>{name}</b> \n<b>ПРОДЛЕНА</b> подписка на 30 дней. \n" \
               f"Подписка до: <b>{upd_date.strftime('%d-%m-%Y %H:%M')}</b>"
        await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")

    await state.reset_state()
    await message.delete()


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    ForwardedMessageFilter(True), state=DownOneMonth.mess_id)
async def set_user_downgrade_month(message: types.Message, state: FSMContext):
    print('set_user_downgrade_month')
    data = await state.get_data()
    command_mess_id = data.get("id")
    current_mess_id = message.message_id
    timestamp = datetime.now().timestamp()
    referral = message.forward_from.id

    await db.add_new_user(member=message.forward_from, timestamp=timestamp)

    if current_mess_id == command_mess_id + 1:
        upd = await db.user_timestamp_downgrade(referral=referral, timestamp=timestamp)
        upd_date = datetime.fromtimestamp(upd)
        name = message.forward_from.full_name
        text = f"Пользователь: <b>{name}</b> \n<b>УМЕНЬШЕНА</b> подписка на 30 дней. \n" \
               f"Подписка до: <b>{upd_date.strftime('%d-%m-%Y %H:%M')}</b>"
        await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")

    await state.reset_state()
    await message.delete()


@dp.message_handler(lambda message: message.from_user.id == int(ADMIN_ID),
                    ForwardedMessageFilter(True), state=UserStatus.mess_id)
async def get_user_status(message: types.Message, state: FSMContext):
    print('get_user_status')
    data = await state.get_data()
    command_mess_id = data.get("id")
    current_mess_id = message.message_id
    timestamp = datetime.now().timestamp()
    referral = message.forward_from.id

    if current_mess_id == command_mess_id + 1:
        user = await db.get_user(referral)
        if not user:
            user = await db.add_new_user(member=message.forward_from, timestamp=timestamp)
        name = message.forward_from.full_name
        timestamp_from_db = user.timestamp
        date = datetime.fromtimestamp(timestamp_from_db)
        text = f"Пользователь: <b>{name}</b> \nПодписка до: <b>{date.strftime('%d-%m-%Y %H:%M')}</b>"
        await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")

    await state.reset_state()
    await message.delete()
