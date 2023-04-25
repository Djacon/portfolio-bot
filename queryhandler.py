from keyboards import getCancelKeyboard

MAX_VALID_QUERIES = 10


# Класс для обработки запросов пользователей с помощью очередей
class QueryHandler:
    def __init__(self):
        self._tasks = []
        self._calls = []
        self._bars = []

        self.is_active = False

    async def add(self, task, call):
        if len(self._tasks) >= MAX_VALID_QUERIES:
            return

        self._tasks.append(task)
        self._calls.append(call)

        size = len(self._calls)
        bar = await call.reply(f'Запрос поставлен в очередь: {size}',
                               reply_markup=getCancelKeyboard(call.message_id))
        self._bars.append(bar)

        if not self.is_active:
            await self._iterative_call()

    async def cancel(self, call_id):
        for i in range(len(self._calls)):
            if self._calls[i].message_id == call_id:
                self._tasks.pop(i)
                self._calls.pop(i)
                bar = self._bars.pop(i)
                return await bar.edit_text('Отменено')

    async def _iterative_call(self):
        self.is_active = True

        while len(self._tasks):
            task = self._tasks.pop(0)
            call = self._calls.pop(0)
            bar = self._bars.pop(0)
            await task(call, bar)

        self.is_active = False


QUEUE = QueryHandler()
