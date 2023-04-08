from aiogram.types import Message
from aiogram import Bot, Dispatcher, executor
from aiogram.utils.exceptions import MessageNotModified
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

from emotion_detection import predict_emotions

from re import match
from os import environ
from keyboards import *

TOKEN = environ['TOKEN']

bot = Bot(TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Course(StatesGroup):
    index = State()
    title = State()
    source = State()
    description = State()


@dp.errors_handler(exception=MessageNotModified)
async def message_not_modified_handler(*_):
    return True


def greet(user: int) -> str:
    return (f'Приветствую вас, {user}!\n\nВыберите любую нейросеть из моего '
            'портфолио, и я помогу вам протестировать ее работу:')


def isAdmin(message) -> bool:
    return message.from_user.id in [915782472]


@dp.message_handler(commands=['start'])
async def start(message: Message):
    user = message.from_user.first_name
    await message.answer(greet(user), reply_markup=mainKb)


@dp.message_handler(commands='test')
async def echo(message: Message):
    text = message.text[6:]
    if not len(text):
        await message.answer('Некорректный ввод!')
        return

    emotion = predict_emotions(text).items()

    answer = '```\nПрогноз:'
    for k, v in sorted(emotion, key=lambda x: x[1], reverse=True):
        answer += f"\n{k}:{' '*(11-len(k))}{100*v:.3f}%"
    await message.answer(answer + '```', parse_mode='Markdown')


@dp.callback_query_handler(lambda c: c.data.startswith('editCourse'))
async def show_editCourse(call):
    message = call.message
    index = int(call.data.split('-')[1])
    await bot.answer_callback_query(call.id)
    await message.edit_text(
        f"Нейросеть: {DB.getCourse(index)[0]}\n\n"
        f'{DB.getCourse(index)[1]}',
        reply_markup=getEditCourseKeyboard(index))


async def show_edit(call, text):
    message = call.message
    ind = int(call.data.split('-')[1])

    state = dp.current_state(user=call.from_user.id)
    await state.update_data(index=ind)
    await message.delete()
    await bot.answer_callback_query(call.id)
    await call.message.answer(text, reply_markup=cancelKb)


@dp.callback_query_handler(lambda c: c.data.startswith('title'))
async def show_editTitle(call):
    await show_edit(call, 'Введите новый заголовок:')
    await Course.title.set()


@dp.callback_query_handler(lambda c: c.data.startswith('description'))
async def show_editDesc(call):
    await show_edit(call, 'Введите новое описание:')
    await Course.description.set()


@dp.callback_query_handler(lambda c: c.data.startswith('source'))
async def show_editSource(call):
    await show_edit(call, 'Введите новую ссылку\n'
                    '(ссылка должна быть в формате https://site.ru):')
    await Course.source.set()


async def editCourse(message, state, id):
    async with state.proxy() as data:
        index = data['index']
    await state.finish()

    if message.text.lower() != 'отмена':
        DB.editCourse(index, id, message.text)
        await message.answer('Изменено', reply_markup=noneKb)
    else:
        await message.answer('Отменено', reply_markup=noneKb)

    await message.answer(
        f"Нейросеть: {DB.getCourse(index)[0]}\n\n"
        f'{DB.getCourse(index)[1]}',
        reply_markup=getEditCourseKeyboard(index))


@dp.message_handler(state=Course.title)
async def editTitle(message: Message, state):
    await editCourse(message, state, 0)


@dp.message_handler(state=Course.description)
async def editDesc(message: Message, state):
    await editCourse(message, state, 1)


@dp.message_handler(state=Course.source)
async def editSource(message: Message, state):
    if message.text.lower() == 'отмена' or \
     match(r'^https?:\/\/(www\.)?\w+\.\w+', message.text):
        await editCourse(message, state, 2)
    else:
        await message.answer('Некорректная ссылка!')


@dp.callback_query_handler(lambda c: c.data.startswith('course-'))
async def show_course(call):
    message = call.message
    index = int(call.data.split('-')[1])
    await bot.answer_callback_query(call.id)
    await message.edit_text(
        f"Нейросеть: {DB.getCourse(index)[0]}\n\n"
        f'{DB.getCourse(index)[1]}',
        reply_markup=getCourseKeyboard(index, isAdmin(call)))


async def courses_page(call):
    message = call.message
    await bot.answer_callback_query(call.id)
    await message.edit_text(
        'Список нейросетей:\n\n' +
        '\n\n'.join([f"{i+1}. {x[0]}" for i, x in enumerate(DB.getCourses())]),
        reply_markup=getCoursesKeyboard(isAdmin(call)))


@dp.callback_query_handler(lambda c: c.data == 'add')
async def show_add(call):
    message = call.message
    await bot.answer_callback_query(call.id)
    await message.edit_text('Вы хотите добавить новую модель?',
                            reply_markup=addKb)


@dp.callback_query_handler(lambda c: c.data == 'add_surely')
async def show_add(call):
    DB.addCourse()
    await courses_page(call)


@dp.callback_query_handler(lambda c: c.data.startswith('delete_surely'))
async def show_delete(call):
    index = int(call.data.split('-')[1])
    DB.deleteCourse(index)
    await courses_page(call)


@dp.callback_query_handler(lambda c: c.data.startswith('delete'))
async def show_delete(call):
    message = call.message
    index = int(call.data.split('-')[1])
    await bot.answer_callback_query(call.id)
    await message.edit_text('Вы точно уверены, что хотите удалить модель?',
                            reply_markup=getDeleteKeyboard(index))


@dp.callback_query_handler(lambda c: c.data == 'courses')
async def show_courses(call):
    await courses_page(call)


@dp.callback_query_handler(lambda c: c.data == 'homepage')
async def show_homepage(call):
    user = call.from_user.first_name
    await bot.answer_callback_query(call.id)
    await call.message.edit_text(greet(user), reply_markup=mainKb)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
