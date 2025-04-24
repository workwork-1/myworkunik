import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from booking_system import BookingSystem
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(storage=MemoryStorage())
booking = BookingSystem()

# Состояния
class BookingStates(StatesGroup):
    GET_NAME = State()
    GET_PHONE = State()
    CHOOSE_SERVICE = State()
    CHOOSE_MASTER = State()
    CHOOSE_DATE = State()
    CHOOSE_TIME = State()
    CONFIRM = State()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в салон красоты!\n"
        "Для записи нажмите /book\n"
        "Ваши записи: /my_bookings\n"
        "Отменить запись: /cancel"
    )

# Начало бронирования
@dp.message(Command("book"))
async def cmd_book(message: types.Message, state: FSMContext):
    await state.set_state(BookingStates.GET_NAME)
    await message.answer("Введите ваше имя:")

# Обработка имени
@dp.message(BookingStates.GET_NAME)
async def process_name(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == BookingStates.GET_NAME:
        await state.update_data(name=message.text)
        await state.set_state(BookingStates.GET_PHONE)
        await message.answer("Введите ваш номер телефона (+7XXXXXXXXXX или 8XXXXXXXXXX):")
    else:
        await message.answer("Пожалуйста, следуйте инструкциям и введите имя.")

# Обработка телефона
@dp.message(BookingStates.GET_PHONE)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    
    # Удаляем все нецифровые символы кроме +
    cleaned_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Проверяем номер
    if (cleaned_phone.startswith('+7') and len(cleaned_phone) == 12 or 
        cleaned_phone.startswith('8') and len(cleaned_phone) == 11 or 
        cleaned_phone.startswith('7') and len(cleaned_phone) == 11):
        
        await state.update_data(phone=cleaned_phone)
        await state.set_state(BookingStates.CHOOSE_SERVICE)
        
        services = booking.get_all_services()
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"{s['name']} ({s['duration']} мин)")] 
                for s in services
            ],
            resize_keyboard=True
        )
        await message.answer("Выберите услугу:", reply_markup=keyboard)
    else:
        await message.answer("Пожалуйста, введите корректный номер телефона в формате:\n"
                           "+7XXXXXXXXXX или 8XXXXXXXXXX (11 цифр)")

# Выбор услуги
@dp.message(BookingStates.CHOOSE_SERVICE)
async def process_service(message: types.Message, state: FSMContext):
    services = booking.get_all_services()
    selected_service = next((s for s in services if s['name'] in message.text), None)
    
    if not selected_service:
        await message.answer("Пожалуйста, выберите услугу из списка:")
        return
    
    await state.update_data(
        service_id=selected_service['id'],
        service_name=selected_service['name'],
        duration=selected_service['duration']
    )
    await state.set_state(BookingStates.CHOOSE_MASTER)
    
    masters = booking.get_masters_for_service(selected_service['id'])
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=m['name'])] for m in masters],
        resize_keyboard=True
    )
    await message.answer("Выберите мастера:", reply_markup=keyboard)

# Выбор мастера
@dp.message(BookingStates.CHOOSE_MASTER)
async def process_master(message: types.Message, state: FSMContext):
    masters = booking.get_all_masters()
    selected_master = next((m for m in masters if m['name'] == message.text), None)
    
    if not selected_master:
        await message.answer("Пожалуйста, выберите мастера из списка:")
        return
    
    await state.update_data(
        master_id=selected_master['id'],
        master_name=selected_master['name']
    )
    await state.set_state(BookingStates.CHOOSE_DATE)
    
    today = datetime.now().date()
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=(today + timedelta(days=i)).strftime("%Y-%m-%d"))] 
            for i in range(14) if (today + timedelta(days=i)).weekday() < 5
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите дату:", reply_markup=keyboard)

# Выбор даты
@dp.message(BookingStates.CHOOSE_DATE)
async def process_date(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%Y-%m-%d")
    except ValueError:
        await message.answer("Пожалуйста, выберите дату в формате ГГГГ-ММ-ДД:")
        return
    
    data = await state.get_data()
    slots = booking.get_available_slots(data['master_id'], message.text, data['duration'])
    
    if not slots:
        await message.answer("На эту дату нет свободных слотов. Выберите другую дату:")
        return
    
    await state.update_data(date=message.text)
    await state.set_state(BookingStates.CHOOSE_TIME)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=s['start_time'])] for s in slots],
        resize_keyboard=True
    )
    await message.answer("Выберите время:", reply_markup=keyboard)

# Выбор времени
@dp.message(BookingStates.CHOOSE_TIME)
async def process_time(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    data = await state.get_data()
    
    confirm_text = (
        "Подтвердите запись:\n\n"
        f"Услуга: {data['service_name']}\n"
        f"Мастер: {data['master_name']}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n\n"
        "Все верно?"
    )
    
    await state.set_state(BookingStates.CONFIRM)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")]
        ],
        resize_keyboard=True
    )
    await message.answer(confirm_text, reply_markup=keyboard)

# Подтверждение
@dp.message(BookingStates.CONFIRM)
async def process_confirmation(message: types.Message, state: FSMContext):
    if message.text.lower() != 'да':
        await message.answer("Запись отменена.", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    
    data = await state.get_data()
    
    # Добавляем клиента и получаем его ID
    client_id = booking.add_client(
        name=data['name'],
        phone=data['phone'],
        telegram_id=message.from_user.id
    )
    
    if not client_id:
        await message.answer("❌ Ошибка: не удалось создать или найти клиента", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    
    # Создаем запись
    success = booking.create_booking(
        client_id=client_id,
        service_id=data['service_id'],
        master_id=data['master_id'],
        date=data['date'],
        start_time=data['time']
    )
    
    if success:
        await message.answer("✅ Запись успешно создана!", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("❌ Ошибка при создании записи", reply_markup=types.ReplyKeyboardRemove())
    
    await state.clear()
# Мои записи
@dp.message(Command("my_bookings"))
async def cmd_my_bookings(message: types.Message):
    client_id = booking.get_client_id(telegram_id=message.from_user.id)
    if not client_id:
        await message.answer("У вас нет активных записей.")
        return
    
    bookings = booking.get_client_bookings(client_id)
    if not bookings:
        await message.answer("У вас нет активных записей.")
        return
    
    response = "Ваши записи:\n\n" + "\n\n".join(
        f"📅 {b['date']} в {b['start_time']}\n"
        f"🧴 Услуга: {b['service']}\n"
        f"💇 Мастер: {b['master']}"
        for b in bookings
    )
    await message.answer(response)

# Отмена записи
@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message):
    client_id = booking.get_client_id(telegram_id=message.from_user.id)
    if not client_id:
        await message.answer("У вас нет записей для отмены.")
        return
    
    bookings = booking.get_client_bookings(client_id)
    if not bookings:
        await message.answer("У вас нет записей для отмены.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{b['date']} {b['start_time']} - {b['service']}",
            callback_data=f"cancel_{b['id']}"
        )] for b in bookings
    ])
    await message.answer("Выберите запись для отмены:", reply_markup=keyboard)

# Обработка отмены
@dp.callback_query(lambda c: c.data.startswith('cancel_'))
async def process_cancel(callback: types.CallbackQuery):
    booking_id = int(callback.data.split('_')[1])
    if booking.cancel_booking(booking_id):
        await callback.answer("Запись отменена", show_alert=True)
    else:
        await callback.answer("Ошибка при отмене", show_alert=True)
    
    await callback.message.edit_reply_markup(reply_markup=None)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())