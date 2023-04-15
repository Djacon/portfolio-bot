from requests import get as rget

from imports import Message, State, StatesGroup, TOKEN
from imports import dp, bot, show_homepage
from database import USER_DB

from keyboards import exitKb, noneKb

# from emotion_detection import predict_emotions
from image_segmentation import segment_photo, segment_video


NO_ROOT_MSG = ('Упс, похоже у вас недостаточно прав чтобы воспользоваться'
               ' ботом, пожалуйста напишите @Djacon, чтобы получить'
               ' доступ ко всевозможным функциям')


def userInDatabase(message) -> bool:
    return True  # Временный доступ для всех пользователей
    return message.from_user.id in USER_DB.getUsers()


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

    if message.content_type == 'photo':
        file = await message.photo[-1].get_file()
        await file.download()

        img_path = file['file_path']

        segment_photo(img_path)

        with open(img_path, 'rb') as image:
            await message.answer_photo(image)

    elif message.content_type == 'video':
        file = await message.video.get_file()
        await file.download()

        vid_path = file['file_path']
        new_path = segment_video(vid_path)

        with open(new_path, 'rb') as video:
            await message.answer_video(video)
