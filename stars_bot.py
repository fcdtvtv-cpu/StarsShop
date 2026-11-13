import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiocryptopay import AioCryptoPay, Networks

# === ТВОИ ДАННЫЕ ===

# ==================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
crypto = None

class CustomStars(StatesGroup):
    waiting_for_amount = State()

def get_main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 100 Stars - 100₽", callback_data="buy_100")],
        [InlineKeyboardButton(text="🔥 500 Stars - 450₽", callback_data="buy_500")],
        [InlineKeyboardButton(text="🔥 1000 Stars - 850₽", callback_data="buy_1000")],
        [InlineKeyboardButton(text="✍️ Ввести свое количество", callback_data="custom_amount")],
        [InlineKeyboardButton(text="🛡 Отзывы", callback_data="reviews"), 
         InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ])
    return kb

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    text = (
        "🌟 <b>Добро пожаловать в наш магазин Telegram Stars!</b>\n\n"
        "⚡️ Моментальная выдача.\n"
        "🛡 Безопасная сделка через Telegram Wallet.\n\n"
        "Выберите товар или введите свое количество:"
    )
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Выберите товар или введите свое количество:", reply_markup=get_main_menu(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "custom_amount")
async def ask_custom_amount(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]])
    await callback.message.edit_text(
        "✍️ <b>Введите количество звезд, которое хотите купить:</b>\n"
        "(Например: 250, 3500 и т.д.)",
        reply_markup=kb,
        parse_mode="HTML"
    )
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
    price_usdt = round(stars * 0.015, 2) # Примерный курс
    
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
            [InlineKeyboardButton(text="💳 Оплатить через Wallet", url=invoice.bot_invoice_url)],
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_{invoice.invoice_id}_{stars}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
        ])
        
        text = (
            f"🛒 Вы выбрали: <b>{stars} Stars</b>\n"
            f"💰 К оплате: <b>{price_rub}₽</b>\n\n"
            f"👇 Нажмите кнопку ниже. Откроется Telegram Wallet.\n"
            f"💳 <i>Там вы сможете оплатить картой РФ или через СБП.</i>\n\n"
            f"⚠️ После оплаты обязательно нажмите «Я оплатил»!"
        )
        
        try:
            await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
            
    except Exception as e:
        print(f"Ошибка при создании счета: {e}")

@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: types.CallbackQuery):
    # Мгновенный ответ, чтобы бот не завис
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
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_menu")]]),
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

@dp.callback_query(F.data == "reviews")
async def show_reviews(callback: types.CallbackQuery):
    names = ["Артем", "Даниил", "Игорь", "Максим", "Егор", "Кирилл", "Влад"]
    products = ["100 Stars", "500 Stars", "1000 Stars", "250 Stars"]
    texts = [
        "Брал вчера, все пришло моментально, спасибо!",
        "Сначала думал развод, но нет, звезды упали через 5 минут.",
        "Дешевле чем в официальном магазине, буду брать еще.",
        "Все четко, оплата через СБП прошла.",
        "Спасибо, выручили. Скинул друзьям ваш бот."
    ]
    fake_reviews = ""
    for _ in range(4):
        fake_reviews += f"⭐️⭐️⭐️⭐️⭐️ <b>{random.choice(names)}</b> купил {random.choice(products)}\n<i>“{random.choice(texts)}”</i>\n\n"
        
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]])
    await callback.message.edit_text(
        f"🛡 <b>Последние отзывы:</b>\n\n{fake_reviews}"
        f"📊 Рейтинг: <b>4.9 / 5</b> (На основе 124 отзывов)",
        reply_markup=kb, 
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "support")
async def show_support(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]])
    await callback.message.edit_text(
        "🆘 <b>Служба поддержки</b>\n\n"
        "Если у вас возникли вопросы, напишите менеджеру: @CodeitHelp\n\n"
        "Время ответа: от 1 до 5 минут.",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

async def main():
    global crypto 
    crypto = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.MAIN_NET)
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
