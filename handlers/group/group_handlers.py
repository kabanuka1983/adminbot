import re
from asyncio import sleep

from datetime import datetime

from aiogram import types
from aiogram.dispatcher.filters import IDFilter

from config import ADMIN_ID, CHAT_ID, NEED_USERS
from utils import database

from loader import dp, bot


db = database.DBCommands()


@dp.message_handler(IDFilter(chat_id=CHAT_ID), content_types=['new_chat_members'])
async def new_member(message: types.Message):
    referrer_id = types.User.get_current().id
    chat_id = message.chat.id
    timestamp = datetime.now().timestamp()
    need_users = int(NEED_USERS)

    for member in message.new_chat_members:
        if member.is_bot:
            if referrer_id != int(ADMIN_ID):
                member_id = member.id
                await bot.kick_chat_member(chat_id=chat_id, user_id=member_id)  # todo delete until_date
        elif referrer_id != member.id:
            referral = referrer_id
            referral_in_db = await db.get_user(user_id=referral)
            if not referral_in_db:
                await db.add_new_user(member=message.from_user, timestamp=timestamp)
                await db.referrer_update(need_users=need_users, referral=referral, timestamp=timestamp)
            user = await db.add_new_user(member=member, referral=referral, timestamp=timestamp)
            if user:
                await db.referrer_update(need_users=need_users, referral=referral, timestamp=timestamp)
        else:
            await db.add_new_user(member=member, timestamp=timestamp)
    await message.delete()


@dp.message_handler(IDFilter(chat_id=CHAT_ID), content_types=['left_chat_member'])
async def left_member(message: types.Message):
    await message.delete()


@dp.message_handler(IDFilter(chat_id=CHAT_ID), lambda message: len(message.entities) > 0)
@dp.edited_message_handler(IDFilter(chat_id=CHAT_ID), lambda message: len(message.entities) > 0)
async def delete_links(message: types.Message):
    user_id = message.from_user.id
    print(3)
    for entity in message.entities:
        if entity.type in ["text_link"] and user_id != int(ADMIN_ID):
            await message.delete()
        elif entity.type in ["url"] and user_id != int(ADMIN_ID):
            re_string = r"chat.whatsapp|t.me/joinchat"
            text = message.text.lower()
            re_link = re.search(re_string, text)
            if re_link:
                await message.delete()
            else:
                await referral_control(message)
        else:
            await referral_control(message)


async def restrict_message(message, name, number):
    ending = ["я", "ей"]
    if number == 1:
        end = ending[0]
    else:
        end = ending[1]
    await message.reply(
        text=f"{name}, \n\nдобавьте в группу \nещё {number} пользовател{end}, \nчтобы иметь возможность размещать объявления"
    )


@dp.message_handler(IDFilter(chat_id=CHAT_ID))
async def referral_control(message: types.Message):
    user_id = types.User.get_current().id
    print(4)
    print(message)
    name = types.User.get_current().full_name
    timestamp = datetime.now().timestamp()
    need_users = int(NEED_USERS)

    if user_id != int(ADMIN_ID):
        db_user = await db.get_user(user_id)
        if db_user:
            if db_user.timestamp <= timestamp:
                number = need_users - db_user.referral_amount
                await sleep(1)
                await restrict_message(message=message, name=name, number=number)
                await message.delete()
            else:
                return
        else:
            db_user = await db.add_new_user(member=message.from_user, timestamp=timestamp)
            number = need_users - db_user.referral_amount
            await sleep(1)
            await restrict_message(message=message, name=name, number=number)
            await message.delete()
