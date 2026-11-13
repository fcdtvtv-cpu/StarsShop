import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiocryptopay import AioCryptoPay, Networks

# === БЕРЕМ ДАННЫЕ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_TOKEN")
ADMIN_ID_STR = os.getenv("ADMIN_ID")

if not BOT_TOKEN or not CRYPTO_TOKEN or not ADMIN_ID_STR:
    raise ValueError("ОШИБКА: Не заданы переменные окружения BOT_TOKEN, CRYPTO_TOKEN или ADMIN_ID!")

ADMIN_ID = int(ADMIN_ID_STR)
# ==============================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
crypto = None

class CustomStars(StatesGroup):
    waiting_for_amount = State()

def get_reply_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔥 Купить звезды")],
            [KeyboardButton(text="📖 Как оплатить?"), KeyboardButton(text="🆘 Поддержка")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return kb

def get_inline_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 100 Stars - 100₽", callback_data="buy_100")],
        [InlineKeyboardButton(text="🔥 500 Stars - 450₽", callback_data="buy_500")],
        [InlineKeyboardButton(text="🔥 1000 Stars - 850₽", callback_data="buy_1000")],
        [InlineKeyboardButton(text="✍️ Ввести свое количество", callback_data="custom_amount")],
        [InlineKeyboardButton(text="💳 Инструкция по оплате", callback_data="how_to_pay")]
    ])
    return kb

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    
    await bot.set_my_commands([BotCommand(command="start", description="🏠 Главное меню")])
    
    text = (
        "🌟 <b>Добро пожаловать в наш магазин Telegram Stars!</b>\n\n"
        "⚡️ Моментальная выдача 24/7.\n"
        "💳 Оплата картой РФ, СБП или криптой.\n"
        "🛡 Безопасная сделка.\n\n"
        "👇 Выберите товар или нажмите «Купить звезды» внизу:"
    )
    await message.answer(text, reply_markup=get_reply_menu(), parse_mode="HTML")
    await message.answer("Выберите пакет:", reply_markup=get_inline_menu())

@dp.message(F.text == "🔥 Купить звезды")
async def buy_stars_msg(message: types.Message):
    await message.answer("Выберите пакет или введите свое количество:", reply_markup=get_inline_menu())

# --- ГАЙД ПО ОПЛАТЕ ---
@dp.message(F.text == "📖 Как оплатить?")
async def how_to_pay_msg(message: types.Message):
    text = (
        "💳 <b>Как оплатить заказ?</b>\n\n"
        "1️⃣ Нажмите кнопку <b>«Оплатить»</b> под вашим заказом.\n"
        "2️⃣ У вас откроется официальное окно <b>Telegram Wallet</b> (это встроенный кошелек Телеграма).\n"
        "3️⃣ Нажмите <b>«Пополнить»</b> и выберите удобный способ:\n"
        "   • Карта РФ (МИР, Visa, MasterCard)\n"
        "   • СБП (по QR-коду)\n"
        "   • Криптовалюта (USDT/TON)\n"
        "4️⃣ После оплаты вернитесь в бота и нажмите <b>«✅ Я оплатил»</b>.\n\n"
        "⚠️ <i>Если у вас не открывается Wallet, проверьте, не заблокирован ли он у вас в настройках Телеграма.</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_reply_menu())

@dp.callback_query(F.data == "how_to_pay")
async def how_to_pay_callback(callback: types.CallbackQuery):
    text = (
        "💳 <b>Как оплатить заказ?</b>\n\n"
        "1️⃣ Нажмите кнопку <b>«Оплатить»</b> под вашим заказом.\n"
        "2️⃣ У вас откроется официальное окно <b>Telegram Wallet</b>.\n"
        "3️⃣ Нажмите <b>«Пополнить»</b> и выберите карту РФ или СБП.\n"
        "4️⃣ После оплаты вернитесь в бота и нажмите <b>«✅ Я оплатил»</b>.\n\n"
        "⚠️ <i>Оплата проходит автоматически.</i>"
    )
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shop")]]), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "back_to_shop")
async def back_to_shop(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите пакет:", reply_markup=get_inline_menu())
    await callback.answer()

@dp.message(F.text == "🆘 Поддержка")
async def support_msg(message: types.Message):
    await message.answer(
        "🆘 <b>Служба поддержки</b>\n\n"
        "Если у вас возникли вопросы по оплате, напишите менеджеру: @Твой_Левый_Аккаунт\n\n"
        "Время ответа: от 1 до 5 минут.",
        parse_mode="HTML",
        reply_markup=get_reply_menu()
    )

@dp.callback_query(F.data == "custom_amount")
async def ask_custom_amount(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✍️ <b>Введите количество звезд числом:</b>\n(Например: 250, 3500 и т.д.)", parse_mode="HTML")
    await state.set_state(CustomStars.waiting_for_amount)
    await callback.answer()

@dp.message(CustomStars.waiting_for_amount)
async def process_custom_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Пожалуйста, введите только цифры.")
        return
    
    stars = int(message.text)
    if stars < 50:
        await message.answer("❌ Минимальное количество — 50 звезд.")
        return
        
    price_rub = stars 
    price_usdt = round(stars * 0.015, 2) 
    
    await state.clear()
    await create_crypto_invoice(message, stars, price_rub, price_usdt)

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    stars = int(callback.data.split("_")[1])
    prices = {100: (100, 1.5), 500: (450, 7.0), 1000: (850, 13.0)}
    price_rub, price_usdt = prices.get(stars, (stars, round(stars * 0.015, 2)))
    
    await create_crypto_invoice(callback.message, stars, price_rub, price_usdt)
    await callback.answer()

async def create_crypto_invoice(message: types.Message, stars: int, price_rub: int, price_usdt: float):
    try:
        invoice = await crypto.create_invoice(
            asset='USDT', 
            amount=price_usdt, 
            description=f"Покупка {stars} Stars"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к оплате", url=invoice.bot_invoice_url)],
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_{invoice.invoice_id}_{stars}")],
            [InlineKeyboardButton(text="❓ Как оплатить?", callback_data="how_to_pay")]
        ])
        
        text = (
            f"🛒 Вы выбрали: <b>{stars} Stars</b>\n"
            f"💰 К оплате: <b>{price_rub}₽</b>\n\n"
            f"👇 Нажмите <b>«Перейти к оплате»</b>. Откроется официальное окно Telegram Wallet.\n"
            f"💳 <i>Там вы сможете оплатить картой РФ или через СБП.</i>\n\n"
            f"⚠️ После оплаты обязательно нажмите «✅ Я оплатил»!"
        )
        
        try:
            await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
            
    except Exception as e:
        print(f"Ошибка при создании счета: {e}")

@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: types.CallbackQuery):
    await callback.answer("Проверяем статус...", show_alert=False)
    
    parts = callback.data.split("_")
    invoice_id = int(parts[1])
    stars = int(parts[2])
    
    try:
        invoices = await crypto.get_invoices(invoice_ids=invoice_id)
        
        if invoices and invoices[0].status == 'paid':
            await callback.message.edit_text(
                f"✅ <b>Платеж успешно получен!</b>\n\n"
                f"Ваш заказ на <b>{stars} Stars</b> принят в обработку.\n"
                f"Ожидайте зачисления в течение 15-20 минут.",
                parse_mode="HTML"
            )
            
            admin_text = (
                f"🔥 <b>УСПЕШНАЯ ОПЛАТА!</b>\n\n"
                f"👤 Юзер: @{callback.from_user.username} (ID: {callback.from_user.id})\n"
                f"💰 Сумма: {invoices[0].amount} USDT\n"
                f"⭐️ Товар: {stars} Stars\n"
                f"👉 <i>Деньги на CryptoBot! Меняй ник бота.</i>"
            )
            await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
            
        else:
            await callback.answer("❌ Платеж не найден. Если вы оплатили, подождите 2 минуты и нажмите снова.", show_alert=True)
            
    except Exception as e:
        print(f"Ошибка проверки: {e}")
        await callback.answer("Ошибка проверки статуса.", show_alert=True)

async def main():
    global crypto 
    crypto = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.MAIN_NET)
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
