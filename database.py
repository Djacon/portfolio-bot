import json


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

    def addModel(self):
        index = len(self._models) + 1
        self._models.append([f'Нейросеть {index}', 'Здесь будет расположено'
                             f' описание {index}-й Модели'])
        self._save()

    def getModels(self):
        return self._models

    def getModel(self, id: int):
        return self._models[id]

    def modelCount(self):
        return len(self._models)

    def editModel(self, id: int, index: int, value: str):
        self._models[id][index] = value
        self._save()

    def deleteModel(self, index: int):
        self._models.pop(index)
        self._save()

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self._models, f, ensure_ascii=False)


class USERS:
    def __init__(self, filename: str):
        self.filename = filename
        self._users = []
        self.IS_LIMIT_MODE = False
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self._users = json.load(f)
        except FileNotFoundError:
            with open(filename, 'w') as f:
                f.write('[]')

    def addUser(self, userid):
        self._users.append(userid)
        self._save()

    def getUsers(self):
        return self._users

    def userCount(self):
        return len(self._users)

    def deleteUser(self, userid: int):
        index = self._users.index(userid)
        self._users.pop(index)
        self._save()

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self._users, f, ensure_ascii=False)


DB = MODELS('models.json')
USER_DB = USERS('users.json')
