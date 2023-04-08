import json

DEFAULT = 'https://getcourse.ru/'


class MODELS:
    def __init__(self, filename: str):
        self.filename = filename
        self._models = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self._models = json.load(f)
        except FileNotFoundError:
            with open(filename, 'w') as f:
                f.write('[]')

    def addCourse(self):
        index = len(self._models) + 1
        self._models.append([f'Нейросеть {index}', 'Здесь будет расположено'
                             f' описание {index}-й Модели', DEFAULT])
        self._save()

    def getCourses(self):
        return self._models

    def getCourse(self, id: int):
        return self._models[id]

    def editCourse(self, id: int, index: int, value: str):
        self._models[id][index] = value
        self._save()

    def deleteCourse(self, index: int):
        self._models.pop(index)
        self._save()

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self._models, f, ensure_ascii=False)


DB = MODELS('models.json')
