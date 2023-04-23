from os import remove

from imports import Message, State, StatesGroup
from imports import dp, bot, show_homepage
from database import USER_DB

from aiogram.utils.exceptions import FileIsTooBig

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


# Сцена для тестирования emotion_detection модели
@dp.message_handler(state=ModelPlay.emotion)
async def playEmotion(message: Message, state):
    text = message.text

    if text.lower() in ('выход', '/start'):
        await state.finish()
        await message.answer('Выход в Главное меню', reply_markup=noneKb)
        return await show_homepage(message)

    emotion = predict_emotions(text).items()
    answer = '```\nПрогноз:'
    for k, v in sorted(emotion, key=lambda x: x[1], reverse=True):
        answer += f"\n-{k}:{' '*(11-len(k))}{100*v:.3f}%"
    await message.answer(answer + '```', parse_mode='Markdown')


async def download_and_get_file_path(file):
    file = await file.get_file()
    await file.download()
    return file['file_path']


async def handle_image(message: Message):
    img_path = await download_and_get_file_path(message.photo[-1])

    bar = await message.answer('Загрузка...')

    segment_photo(img_path)

    await bar.edit_text('Загрузка завершена!')

    with open(img_path, 'rb') as image:
        await message.answer_photo(image)

    remove(img_path)


async def handle_video(message: Message):
    old_path = await download_and_get_file_path(message.video)

    bar = await message.answer('Загрузка...')
    for progress, is_end in segment_video(old_path):
        if is_end:
            await bar.edit_text('Загрузка завершена!')
            break
        await bar.edit_text(progress, parse_mode='MarkdownV2')

    new_path = progress
    with open(new_path, 'rb') as video:
        await message.answer_video(video)

    remove(old_path)
    remove(new_path)


async def handle_gif(message: Message):
    old_path = await download_and_get_file_path(message.animation)

    bar = await message.answer('Загрузка...')
    for progress, is_end in segment_gif(old_path):
        if is_end:
            await bar.edit_text('Загрузка завершена!')
            break
        await bar.edit_text(progress, parse_mode='MarkdownV2')

    new_path = progress
    with open(new_path, 'rb') as gif:
        await message.answer_animation(gif)

    remove(old_path)
    remove(new_path)


# Сцена для тестовой модели
@dp.message_handler(state=ModelPlay.image, content_types='any')
async def playEmotion(message: Message, state):
    if message.content_type == 'text':
        if message.text.lower() in ('выход', '/start'):
            await state.finish()
            await message.answer('Выход в Главное меню', reply_markup=noneKb)
            return await show_homepage(message)
        else:
            return

    try:
        if message.content_type == 'photo':
            await handle_image(message)

        elif message.content_type == 'video':
            await handle_video(message)

        elif message.content_type == 'animation':
            await handle_gif(message)

        # elif message.content_type in ('video', 'animation'):
        #     # Временное избежание обработки больших роликов
        #     await message.reply('Сегментация видео/gif временно недоступно')

    except FileIsTooBig as err:
        if str(err) == 'File is too big':
            err = 'Файл слишком большой! (>20МБ)'
        await message.reply(err)
