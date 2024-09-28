from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, User, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.enums import ParseMode
from loguru import logger

from secret import secret_api_token

API_TOKEN = secret_api_token

# Включаем логирование
logger.add("logfile.log", level="DEBUG")

dp = Dispatcher()
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


days_available = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
times_available = ["14:00", "15:00", "16:00", "17:00", "18:00"]


class UserStatus(StatesGroup):
	picking_day = State()
	picking_time = State()
	approving = State()
	appointment_approved = State()


def create_keyboard(options: list):
	buttons = []
	for button in options:
		buttons.append(KeyboardButton(text=button))
	keyboard = ReplyKeyboardMarkup(keyboard=[buttons])
	return keyboard


@dp.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext):
	await message.answer(
		text="Выберите день",
		reply_markup=create_keyboard(days_available)
	)
	await state.set_state(UserStatus.picking_day)
	logger.info(f"User {message.from_user.id} status was changed to {await state.get_state()}")


@dp.message(F.text, UserStatus.picking_day)
async def process_answer_date(message: Message, state: FSMContext):
	user_day = message.text.strip().capitalize()

	if user_day not in days_available:
		await message.answer("Выберите из предложенных дней")
		logger.warning(f"User {message.from_user.id} sent an invalid day: {user_day}")

	else:
		logger.info(f"User {message.from_user.id} chose day: {user_day}")
		await state.set_data({"day": user_day})
		await message.answer(
			text='Ответ получен. Выберите время',
			reply_markup=create_keyboard(times_available)
		)
		await state.set_state(UserStatus.picking_time)
		logger.info(f"User {message.from_user.id} status was changed to {await state.get_state()}")


@dp.message(F.text, UserStatus.picking_time)
async def process_answer_time(message: Message, state: FSMContext):
	user_time = message.text.strip()

	if user_time not in times_available:
		await message.answer("Выберите из предложенного времени")
		logger.warning(f"User {message.from_user.id} sent an invalid time: {user_time}")

	else:
		logger.info(f"User {message.from_user.id} chose time {user_time}")
		await state.update_data({"time": user_time})
		data = await state.get_data()
		day = data.get("day")
		time = data.get("time")
		await message.answer(
			text=f"Ответ получен. Выбранное время: {day}, выбранное время: {time}",
			reply_markup=create_keyboard(["Подтвердить", "Изменить"])
		)
		await state.set_state(UserStatus.approving)
		logger.info(f"User {message.from_user.id} status was changed to {await state.get_state()}")


@dp.message(F.text == "Подтвердить", UserStatus.approving)
async def approve_appointment(message: Message, state: FSMContext):
	logger.info(f"User {message.from_user.id} approved appointment")
	await message.answer(
		text=f'Запись подтверждена',
		reply_markup=ReplyKeyboardRemove()
	)
	await state.set_state(UserStatus.appointment_approved)
	logger.info(f"User {message.from_user.id} status was changed to {await state.get_state()}")


@dp.message(F.text == "Изменить", UserStatus.approving)
async def change_appointment(message: Message, state: FSMContext):
	logger.info(f"User {message.from_user.id} didn't approve appointment. Choosing another day and time")
	await state.clear()
	await message.answer(
		text='Выберите день',
		reply_markup=create_keyboard(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
	)
	await state.set_state(UserStatus.picking_day)
	logger.info(f"User {message.from_user.id} status was changed to {await state.get_state()}")


async def main() -> None:
	await dp.start_polling(bot)


asyncio.run(main())