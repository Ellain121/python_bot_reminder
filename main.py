import asyncio
from aiogram import F, Dispatcher, Bot, Router, BaseMiddleware
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, TelegramObject, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from DatabaseManager import DatabaseManager, Entry
import logging
import my_token_unsecure
from typing import Dict, Any, Callable, Awaitable, List
from datetime import datetime


def isdigit(char: int):
    return char >= 48 and char <= 57


class AddTask(StatesGroup):
    waiting_for_task_text = State()


class DelTask(StatesGroup):
    waiting_for_tasks_id = State()


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        data["db_manager"] = self.db_manager
        return await handler(event, data)


filename = str("./logs/") + datetime.now().strftime("%d_%b_%Y_%A_logs.txt")
# logging.basicConfig(filename=filename, filemode='a',
#                     format='(%(asctime)s, %(name)s, %(levelname)s): %(message)s', level=logging.INFO)
logging.basicConfig(format='---> (%(asctime)s, %(name)s, %(levelname)s): %(message)s', level=logging.INFO, handlers=[
    logging.FileHandler(filename=filename, mode="a"),
    logging.StreamHandler()
])
router = Router()
db_manager = DatabaseManager()
router.message.middleware(DatabaseMiddleware(db_manager))


def get_cmd_keyboard():
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(KeyboardButton(text="/add"),
                   KeyboardButton(text="/done"),
                   KeyboardButton(text="/show"))
    return kb_builder.as_markup(resize_keyboard=True, input_field_placeholder="Choose action")


@router.message(Command("help"))
@router.message(Command("start"))
async def help_message(message: Message):
    help_msg = \
        """/help - to print this message\
        \n/done - to delete specific entry\
        \n/add - to add new entry\
        \n/show - to show current entries"""
    cmd_keyboard = get_cmd_keyboard()
    await message.answer(help_msg, reply_markup=cmd_keyboard)


@router.message(StateFilter(None), Command("add"))
async def add_task(message: Message, state: FSMContext):
    await message.answer("Write your text", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddTask.waiting_for_task_text)


@router.message(AddTask.waiting_for_task_text, F.text)
async def get_task_info(message: Message, db_manager: DatabaseManager, state: FSMContext):
    db_manager.addEntry(Entry(message.text))
    await show_tasks(message, db_manager, send_kb=True)
    await state.clear()


@router.message(Command("done"))
async def done_tasks(message: Message, state: FSMContext):
    await message.answer("Write your id(s).\nOne or multiple divide them by (,| )", reply_markup=ReplyKeyboardRemove())
    await state.set_state(DelTask.waiting_for_tasks_id)


@router.message(DelTask.waiting_for_tasks_id, F.text)
async def get_task_ids(message: Message, db_manager: DatabaseManager, state: FSMContext):
    ids = []
    id = 0
    msg = message.text + "|"
    for i in range(len(msg)):
        char = ord(msg[i])
        if isdigit(char):
            id = id * 10 + char - 48
        else:
            ids.append(id - 1)
            id = 0
            continue
    print(f"ids: {ids}")
    db_ids = []
    tasks: List[Any] = db_manager.getEntries()
    print(tasks)
    for id in ids:
        entry = tasks[id]
        db_id = entry[0]
        print(f"{entry[0]}|{entry[1]}|{entry[2]}")
        db_ids.append(str(db_id))

    db_manager.delEntries(db_ids)
    await state.clear()
    await show_tasks(message, db_manager, send_kb=True)


@router.message(Command("show"))
async def show_tasks(message: Message, db_manager: DatabaseManager, send_kb: bool = False):
    tasks: List[Any] = db_manager.getEntries()
    tasks_txt = ""
    indx = 1
    for entry in tasks:
        id: int = entry[0]
        task_txt: str = entry[1]
        timestamp: int = entry[2]
        tasks_txt = tasks_txt + str(indx) + ") " + task_txt + "\n"
        indx += 1

    if not tasks_txt:
        tasks_txt = "No tasks!"
    if send_kb:
        await message.answer(tasks_txt, reply_markup=get_cmd_keyboard())
    else:
        await message.answer(tasks_txt)


async def main():
    bot = Bot(my_token_unsecure.Token)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)

asyncio.run(main())
