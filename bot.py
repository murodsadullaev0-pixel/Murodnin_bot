import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
EXCHANGE_API_URL = "https://open.er-api.com/v6/latest/USD"

CURRENCIES = {
    "🇺🇿 UZS": "UZS",
    "🇷🇺 RUB": "RUB",
    "🇪🇺 EUR": "EUR",
    "🇬🇧 GBP": "GBP",
    "🇨🇳 CNY": "CNY",
    "🇰🇿 KZT": "KZT",
    "🇹🇷 TRY": "TRY",
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def main_keyboard():
    buttons = [
        [KeyboardButton(text="💱 Valyuta kurslari")],
        [KeyboardButton(text="🔄 Konvertatsiya"), KeyboardButton(text="📊 Barcha kurslar")],
        [KeyboardButton(text="ℹ️ Ma'lumot")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def currency_inline_keyboard():
    buttons = []
    row = []
    for name, code in CURRENCIES.items():
        row.append(InlineKeyboardButton(text=name + " " + code, callback_data=f"rate_{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def fetch_rates():
    async with aiohttp.ClientSession() as session:
        async with session.get(EXCHANGE_API_URL) as resp:
            data = await resp.json()
            return data.get("rates", {})

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Salom, <b>{message.from_user.first_name}</b>!\n\n"
        "💰 <b>Valyuta Kurslari Boti</b>ga xush kelibsiz!\n\n"
        "Quyidagi tugmalardan foydalaning 👇",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "💱 Valyuta kurslari")
async def show_currency_list(message: types.Message):
    await message.answer(
        "📌 Qaysi valyuta kursini ko'rmoqchisiz?",
        parse_mode="HTML",
        reply_markup=currency_inline_keyboard()
    )

@dp.message(F.text == "📊 Barcha kurslar")
@dp.message(Command("rates"))
async def show_all_rates(message: types.Message):
    await message.answer("⏳ Kurslar yuklanmoqda...")
    try:
        rates = await fetch_rates()
        text = "📊 <b>Bugungi valyuta kurslari</b>\n<i>(1 USD ga nisbatan)</i>\n\n"
        for name, code in CURRENCIES.items():
            rate = rates.get(code)
            if rate:
                text += f"{name}: <code>{rate:,.2f}</code>\n"
        await message.answer(text, parse_mode="HTML", reply_markup=main_keyboard())
    except:
        await message.answer("❌ Xatolik yuz berdi.", reply_markup=main_keyboard())

@dp.callback_query(F.data.startswith("rate_"))
async def show_single_rate(callback: types.CallbackQuery):
    code = callback.data.split("_")[1]
    try:
        rates = await fetch_rates()
        rate = rates.get(code)
        if rate:
            reverse = 1 / rate
            text = (
                f"💱 <b>1 USD = {rate:,.2f} {code}</b>\n"
                f"💱 <b>1 {code} = {reverse:.6f} USD</b>"
            )
            await callback.message.answer(text, parse_mode="HTML", reply_markup=main_keyboard())
    except:
        await callback.message.answer("❌ Xatolik yuz berdi.")
    await callback.answer()

@dp.message(F.text == "🔄 Konvertatsiya")
async def convert_prompt(message: types.Message):
    await message.answer(
        "🔄 Format: <code>100 USD UZS</code>",
        parse_mode="HTML"
    )

@dp.message(F.text.regexp(r"^\d+(\.\d+)?\s+[A-Za-z]{3}\s+[A-Za-z]{3}$"))
async def do_convert(message: types.Message):
    parts = message.text.strip().upper().split()
    amount = float(parts[0])
    from_cur = parts[1]
    to_cur = parts[2]
    try:
        rates = await fetch_rates()
        if from_cur == "USD":
            result = amount * rates.get(to_cur, 0)
        elif to_cur == "USD":
            result = amount / rates.get(from_cur, 1)
        else:
            result = (amount / rates.get(from_cur, 1)) * rates.get(to_cur, 0)
        await message.answer(
            f"✅ <code>{amount:,.2f} {from_cur}</code> = <b><code>{result:,.2f} {to_cur}</code></b>",
            parse_mode="HTML", reply_markup=main_keyboard()
        )
    except:
        await message.answer("❌ Format: <code>100 USD UZS</code>", parse_mode="HTML")

@dp.message(F.text == "ℹ️ Ma'lumot")
async def show_info(message: types.Message):
    await message.answer(
        "ℹ️ <b>Valyuta Kurslari Boti v1.0</b>\n\n"
        "📡 API: Open Exchange Rates\n"
        "🔄 Real vaqtda yangilanadi",
        parse_mode="HTML", reply_markup=main_keyboard()
    )

@dp.message()
async def unknown(message: types.Message):
    await message.answer("❓ Tugmalardan foydalaning 👇", reply_markup=main_keyboard())

async def main():
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
