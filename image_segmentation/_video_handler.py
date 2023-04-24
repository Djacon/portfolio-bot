

# Класс для обработки файлов пользователей с помощью очереди
class FileHandler:
    def __init__(self):
        self._tasks = []

    def append(self, task):
        self._tasks.append(task)
