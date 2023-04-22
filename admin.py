from imports import Message, dp
from database import DB, USER_DB


def isAdmin(message) -> bool:
    return message.from_user.id == 915782472


@dp.message_handler(commands=['info'])
async def users(message: Message):
    if not isAdmin(message):
        await message.answer('Извините, команда доступна только админу!')
        return
    info = ('Bot Info:\n'
            f"-Users in DB: {USER_DB.userCount()}"
            f"\n-Models in DB: {DB.modelCount()}"
            f"\n-Is Limit Mode: {USER_DB.IS_LIMIT_MODE}"
            "\n\nAdmin Commands:"
            "\n/useradd, /userdel, /getusers, /limitmode")
    await message.answer(info)


@dp.message_handler(commands=['useradd'])
async def useradd(message: Message):
    if not isAdmin(message):
        await message.answer('Извините, команда доступна только админу!')
        return

    userid = message.text[9:]

    if not userid.isdigit():
        return await message.answer(f'Некорректный ввод - `{userid}`')

    userid = int(userid)
    if userid in USER_DB.getUsers():
        await message.answer(f'Пользователя с таким ID уже есть - `{userid}`')
        return

    USER_DB.addUser(userid)
    await message.answer(f'Пользователь с id={userid} успешно добавлен!')


@dp.message_handler(commands=['userdel'])
async def userdel(message: Message):
    if not isAdmin(message):
        await message.answer('Извините, команда доступна только админу!')
        return

    userid = message.text[9:]

    if not userid.isdigit():
        return await message.answer(f'Некорректный ввод - `{userid}`')

    userid = int(userid)
    if userid not in USER_DB.getUsers():
        await message.answer(f'Пользователя с таким ID нет в БД - `{userid}`')
        return

    USER_DB.deleteUser(int(userid))
    await message.answer(f'Пользователь с id={userid} успешно удален!')


@dp.message_handler(commands=['getusers'])
async def getusers(message: Message):
    if not isAdmin(message):
        await message.answer('Извините, команда доступна только админу!')
        return

    await message.answer(f"USERS:\n{USER_DB.getUsers()}")


@dp.message_handler(commands=['limitmode'])
async def users(message: Message):
    if not isAdmin(message):
        await message.answer('Извините, команда доступна только админу!')
        return

    USER_DB.IS_LIMIT_MODE = not USER_DB.IS_LIMIT_MODE
    await message.answer(f"Режим изменен: {USER_DB.IS_LIMIT_MODE}")
