from keyboards import getCancelKeyboard

MAX_COUNT_QUERIES = 10


# Класс для обработки запросов пользователей с помощью очередей
class QueryHandler:
    def __init__(self):
        self._tasks = []
        self._calls = []
        self._bars = []

        self.is_active = False

    async def add(self, task, call):
        if len(self._tasks) >= MAX_COUNT_QUERIES:
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
        i = 0
        while i < len(self._bars):
            if self._calls[i].message_id == call_id:
                self._tasks.pop(i)
                self._calls.pop(i)
                bar = self._bars.pop(i)
                return await bar.edit_text('Отменено')
            i += 1

    async def update_bars(self):
        i = 0
        while i < len(self._bars):
            await self._bars[i].edit_text(
                f'Запрос поставлен в очередь: {i+1}',
                reply_markup=getCancelKeyboard(self._calls[i].message_id))
            i += 1

    async def _iterative_call(self):
        self.is_active = True

        while len(self._bars):
            task = self._tasks.pop(0)
            call = self._calls.pop(0)
            bar = self._bars.pop(0)
            await task(call, bar)

            await self.update_bars()

        self.is_active = False


QUEUE = QueryHandler()
