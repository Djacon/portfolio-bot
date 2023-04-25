from os import remove

from imports import Message, State, StatesGroup
from imports import dp, bot, show_homepage
from database import USER_DB
from queryhandler import QUEUE

from aiogram.utils.exceptions import FileIsTooBig, BadRequest

from keyboards import exitKb, noneKb

from emotion_detection import predict_emotions
from image_segmentation import segment_photo, segment_video, segment_gif


NO_ROOT_MSG = ('Упс, похоже у вас недостаточно прав чтобы воспользоваться'
               ' ботом, пожалуйста напишите @Djacon, чтобы получить'
               ' доступ ко всевозможным функциям')


def userInDatabase(message) -> bool:
    if USER_DB.IS_LIMIT_MODE:
        return message.from_user.id in USER_DB.getUsers()
    return True


# Сцена Модели (для запуска определенной модели)
class ModelPlay(StatesGroup):
    emotion = State()      # Russian Emotion Detection
    image = State()        # Image Smart Editor (segmentation, detector, etc)
    test = State()         # Тестовый (в случае если модель не задана)


# Запуск выбранной нейросети
@dp.callback_query_handler(lambda c: c.data.startswith('open'))
async def open_model_playground(call):
    message = call.message

    index = int(call.data.split('-')[1])

    await message.delete()
    await bot.answer_callback_query(call.id)

    if not userInDatabase(call):
        await ModelPlay.test.set()
        return await message.answer(NO_ROOT_MSG, reply_markup=exitKb)

    if index == 0:  # Emotion detection
        await message.answer('Введите текст:', reply_markup=exitKb)
        await ModelPlay.emotion.set()
    elif index == 1:  # Image Segmentation
        await message.answer('Загрузите изображение/видео:',
                             reply_markup=exitKb)
        await ModelPlay.image.set()
    else:
        await message.answer('Временно недоступно :(', reply_markup=exitKb)
        await ModelPlay.test.set()


# Сцена для тестовой модели
@dp.message_handler(state=ModelPlay.test)
async def playEmotion(message: Message, state):
    if message.text.lower() in ('выход', '/start'):
        await state.finish()
        await message.answer('Выход в Главное меню', reply_markup=noneKb)
        return await show_homepage(message)


async def handle_emotions(message: Message, bar):
    text = message.text
    emotion = predict_emotions(text).items()
    answer = '```\nПрогноз:'
    for k, v in sorted(emotion, key=lambda x: x[1], reverse=True):
        answer += f"\n-{k}:{' '*(11-len(k))}{100*v:.3f}%"
    await bar.edit_text(answer + '```', parse_mode='Markdown')


# Сцена для тестирования emotion_detection модели
@dp.message_handler(state=ModelPlay.emotion)
async def playEmotion(message: Message, state):
    text = message.text

    if text.lower() in ('выход', '/start'):
        await state.finish()
        await message.answer('Выход в Главное меню', reply_markup=noneKb)
        return await show_homepage(message)

    await QUEUE.add(handle_emotions, message)


##############################################################################

async def download_and_get_file_path(file):
    file = await file.get_file()
    await file.download()
    return file['file_path']


async def handle(file, segment, bar, reply, answer):
    try:
        old_path = await download_and_get_file_path(file)
        for progress, is_end in segment(old_path):
            if is_end:
                await bar.edit_text('Загрузка завершена!')
                break
            await bar.edit_text(progress, parse_mode='Markdown')

        try:
            with open(progress, 'rb') as file:
                await reply(file)
        except BadRequest:
            with open(progress, 'rb') as file:
                await answer(file)
        await bar.delete()

        remove(old_path)
        remove(progress)

    except FileIsTooBig as err:
        if str(err) == 'File is too big':
            err = 'Файл слишком большой! (>20МБ)'
        await bar.edit_text(err)


async def handle_image(message: Message, bar):
    await handle(message.photo[-1], segment_photo, bar,
                 message.reply_photo, bar.answer_photo)


async def handle_video(message: Message, bar):
    await handle(message.video, segment_video, bar,
                 message.reply_video, bar.answer_video)


async def handle_gif(message: Message, bar):
    await handle(message.animation, segment_gif, bar,
                 message.reply_animation, bar.answer_animation)


@dp.callback_query_handler(lambda c: c.data.startswith('cancel-'),
                           state=ModelPlay.image)
async def cancel_task(call):
    ind = int(call.data.split('-')[1])
    await QUEUE.cancel(ind)


# Сцена для тестовой модели
@dp.message_handler(state=ModelPlay.image, content_types='any')
async def playImage(message: Message, state):
    if message.content_type == 'text':
        if message.text.lower() in ('выход', '/start'):
            await state.finish()
            await message.answer('Выход в Главное меню', reply_markup=noneKb)
            return await show_homepage(message)
        else:
            return

    if message.content_type == 'photo':
        await QUEUE.add(handle_image, message)

    elif message.content_type == 'video':
        await QUEUE.add(handle_video, message)

    elif message.content_type == 'animation':
        await QUEUE.add(handle_gif, message)
