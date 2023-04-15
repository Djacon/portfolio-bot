from aiogram.types import Message
from aiogram import Bot, Dispatcher
from aiogram.utils.exceptions import MessageNotModified
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

from os import environ

from keyboards import mainKb

# Токен для получения доступа к боту
TOKEN = environ['TOKEN']

# Класс для работы с Ботом
bot = Bot(TOKEN)

# Создание хранилища для состояний сцен
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Сцена Модели (для редактирования заголовка и описания)
class ModelEdit(StatesGroup):
    index = State()        # Индекс выбранной модели
    title = State()        # Заголовок
    description = State()  # Описание


# Игнорирование ошибки при неизмененном сообщении
@dp.errors_handler(exception=MessageNotModified)
async def message_not_modified_handler(*_):
    return True


# Показать главное меню
async def show_homepage(call, is_edit=False):
    user = call.from_user.first_name
    greet = (f'Приветствую вас, {user}!\n\nВыберите любую нейросеть из моего '
             'портфолио, и я помогу вам протестировать ее работу:')
    if is_edit:
        await bot.answer_callback_query(call.id)
        return await call.message.edit_text(greet, reply_markup=mainKb)
    await call.answer(greet, reply_markup=mainKb)
