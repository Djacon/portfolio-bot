from aiogram.types import Message
from aiogram import Bot, Dispatcher
from aiogram.utils.exceptions import MessageNotModified
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

from os import environ

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


# Сцена Модели (для запуска определенной модели)
class ModelPlay(StatesGroup):
    emotion = State()      # Russian Emotion Detection
    test = State()         # Тестовый (в случае если модель не задана)


# Игнорирование ошибки при неизмененном сообщении
@dp.errors_handler(exception=MessageNotModified)
async def message_not_modified_handler(*_):
    return True
