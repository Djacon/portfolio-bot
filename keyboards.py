from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import ReplyKeyboardRemove
from database import DB


def getCourseKeyboard(i: int, isAdmin: bool):
    sub = InlineKeyboardButton('✍ Воспользоваться нейросетью',
                               callback_data=f'open-{i}')
    back = InlineKeyboardButton('⬅ Назад', callback_data='courses')
    homepage = InlineKeyboardButton('🏠 На главную', callback_data='homepage')
    courses_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
    if not isAdmin:
        return courses_keyboard.add(sub).row(back, homepage)
    edit = InlineKeyboardButton('Отредактировать',
                                callback_data=f'editCourse-{i}')
    return courses_keyboard.add(sub).row(edit).row(back, homepage)


def getCoursesKeyboard(isAdmin: bool):
    courses = []
    for i, x in enumerate(DB.getCourses()):
        courses.append(InlineKeyboardButton(f"{i+1}. {x[0]}",
                       callback_data=f'course-{i}'))
    homepage = InlineKeyboardButton('🏠 На главную', callback_data='homepage')
    courses_keyboard = InlineKeyboardMarkup(resize_keyboard=True, row_width=2)
    if not isAdmin:
        return courses_keyboard.add(*courses).row(homepage)
    add = InlineKeyboardButton('✅ Добавить нейросеть', callback_data='add')
    return courses_keyboard.add(*courses).row(add).row(homepage)


def getEditCourseKeyboard(i: int):
    title = InlineKeyboardButton('Изменить заголовок',
                                 callback_data=f'title-{i}')
    desc = InlineKeyboardButton('Изменить описание',
                                callback_data=f'description-{i}')
    delete = InlineKeyboardButton('❌ Удалить нейросеть',
                                  callback_data=f'delete-{i}')
    back = InlineKeyboardButton('⬅ Назад', callback_data=f'course-{i}')
    homepage = InlineKeyboardButton('🏠 На главную', callback_data='homepage')
    courses_keyboard = InlineKeyboardMarkup(resize_keyboard=True, row_width=1)
    return courses_keyboard.add(title, desc, delete).row(back, homepage)


def getDeleteKeyboard(i: int):
    yes = InlineKeyboardButton('Да', callback_data=f'delete_surely-{i}')
    no = InlineKeyboardButton('Нет', callback_data=f'editCourse-{i}')
    return InlineKeyboardMarkup(resize_keyboard=True).add(yes, no)


def getAddKeyboard():
    yes = InlineKeyboardButton('Да', callback_data='add_surely')
    no = InlineKeyboardButton('Нет', callback_data='courses')
    return InlineKeyboardMarkup(resize_keyboard=True).add(yes, no)


addKb = getAddKeyboard()

mainKb = InlineKeyboardButton('Показать нейросети', callback_data='courses')
mainKb = InlineKeyboardMarkup(resize_keyboard=True).add(mainKb)

cancelKb = KeyboardButton('Отмена')
cancelKb = ReplyKeyboardMarkup(resize_keyboard=True).add(cancelKb)

exitKb = KeyboardButton('Выход')
exitKb = ReplyKeyboardMarkup(resize_keyboard=True).add(exitKb)

noneKb = ReplyKeyboardRemove()
