from aiogram import executor

from imports import *

from keyboards import *
from admin import *
from models import *


# Стандартная команда /start для начала работы с ботом
@dp.message_handler(commands=['start'])
async def start(message: Message):
    await show_homepage(message)


# Вывод страницы редактирования нейросети
@dp.callback_query_handler(lambda c: c.data.startswith('editModel'))
async def show_editModel(call):
    message = call.message
    index = int(call.data.split('-')[1])
    await bot.answer_callback_query(call.id)
    await message.edit_text(
        f"Нейросеть: {DB.getModel(index)[0]}\n\n"
        f'{DB.getModel(index)[1]}',
        reply_markup=getEditModelKeyboard(index),
        disable_web_page_preview=True)


# Вывод окна для редактирования заголовка или описания нейросети
async def show_edit(call, text):
    message = call.message
    ind = int(call.data.split('-')[1])

    state = dp.current_state(user=call.from_user.id)
    await state.update_data(index=ind)
    await message.delete()
    await bot.answer_callback_query(call.id)
    await call.message.answer(text, reply_markup=cancelKb)


# Вывод окна для редактировании заголовка
@dp.callback_query_handler(lambda c: c.data.startswith('title'))
async def show_editTitle(call):
    await show_edit(call, 'Введите новый заголовок:')
    await ModelEdit.title.set()


# Вывод окна для редактирования описания
@dp.callback_query_handler(lambda c: c.data.startswith('description'))
async def show_editDesc(call):
    await show_edit(call, 'Введите новое описание:')
    await ModelEdit.description.set()


# Изменение заголовка и описания нейросети
async def editModel(message, state, id):
    async with state.proxy() as data:
        index = data['index']
    await state.finish()

    if message.text.lower() != 'отмена':
        DB.editModel(index, id, message.text)
        await message.answer('Изменено', reply_markup=noneKb)
    else:
        await message.answer('Отменено', reply_markup=noneKb)

    await message.answer(
        f"Нейросеть: {DB.getModel(index)[0]}\n\n"
        f'{DB.getModel(index)[1]}',
        reply_markup=getEditModelKeyboard(index),
        disable_web_page_preview=True)


# Сцена для редактирования заголовка
@dp.message_handler(state=ModelEdit.title)
async def editTitle(message: Message, state):
    await editModel(message, state, 0)


# Сцена для редактирования описания
@dp.message_handler(state=ModelEdit.description)
async def editDesc(message: Message, state):
    await editModel(message, state, 1)


# Вывод страницы выбранной модели
@dp.callback_query_handler(lambda c: c.data.startswith('model-'))
async def show_model(call):
    message = call.message
    index = int(call.data.split('-')[1])
    await bot.answer_callback_query(call.id)
    await message.edit_text(
        f"Нейросеть: {DB.getModel(index)[0]}\n\n"
        f'{DB.getModel(index)[1]}',
        reply_markup=getModelKeyboard(index, isAdmin(call)),
        disable_web_page_preview=True)


# Вывод списка имеющихся нейросетей
async def models_page(call):
    message = call.message
    await bot.answer_callback_query(call.id)
    await message.edit_text(
        'Список нейросетей:\n\n' +
        '\n\n'.join([f"{i+1}. {x[0]}" for i, x in enumerate(DB.getModels())]),
        reply_markup=getModelsKeyboard(isAdmin(call)))


# Окно для создания новой страницы для модели
@dp.callback_query_handler(lambda c: c.data == 'add')
async def show_add(call):
    message = call.message
    await bot.answer_callback_query(call.id)
    await message.edit_text('Вы хотите добавить новую модель?',
                            reply_markup=addKb)


# Добавление новой страницы модели
@dp.callback_query_handler(lambda c: c.data == 'add_surely')
async def show_add(call):
    DB.addModel()
    await models_page(call)


# Удаление страницы с моделью
@dp.callback_query_handler(lambda c: c.data.startswith('delete_surely'))
async def show_delete(call):
    index = int(call.data.split('-')[1])
    DB.deleteModel(index)
    await models_page(call)


# Окно для удаления страницы модели
@dp.callback_query_handler(lambda c: c.data.startswith('delete'))
async def show_delete(call):
    message = call.message
    index = int(call.data.split('-')[1])
    await bot.answer_callback_query(call.id)
    await message.edit_text('Вы точно уверены, что хотите удалить модель?',
                            reply_markup=getDeleteKeyboard(index))


# Вывод списка имеющихся нейросетей
@dp.callback_query_handler(lambda c: c.data == 'models')
async def show_models(call):
    await models_page(call)


# Вернуться на главную страницу /start
@dp.callback_query_handler(lambda c: c.data == 'homepage')
async def back_to_homepage(call):
    await show_homepage(call, is_edit=True)


# from aiogram.dispatcher.filters import Text
# from random import random


# # Print iterations progress
# def progressBar(iteration, total, length=15):
#     percent = '{0:.1f}'.format(100 * (iteration / float(total)))
#     filledLength = int(length * iteration // total)
#     bar = '█' * filledLength + '-' * (length - filledLength)
#     return f'`Загрузка: |{bar}| {percent}% ({iteration}/{total})`'


# @dp.message_handler(Text(equals='Загрузка', ignore_case=True))
# async def animation_handler(message):
#     size = 228
#     progress = progressBar(0, size)
#     bar = await message.answer(progress)
#     for i in range(size):
#         s = 0
#         for _ in range(1_000_000):
#             s += random()
#         progress = progressBar(i+1, size)
#         await bar.edit_text(progress, parse_mode="MarkdownV2")


# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
