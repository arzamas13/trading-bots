# ==================== НАСТРОЙКИ (меняй только здесь) ====================
CONFIG = {
    # Binance
    "symbol_suffix": "USDT", # что добавлять, если пользователь написал просто BTC
    # Таймфреймы для мониторинга
    "timeframes": ["1h", "4h", "1d"],
    # Сколько свечей качать для анализа уровней
    "lookback_bars": 600,
    # Сила pivot (сколько баров слева и справа должно быть меньше/больше)
    "pivot_strength": 5,
    # Горизонтальные уровни
    "min_touches_horizontal": 2, # минимум касаний для горизонтального уровня
    "horizontal_zone_percent": 0.4, # ширина зоны в % от цены
    # Наклонные трендлайны
    "min_touches_sloped": 3, # минимум касаний для наклонной линии
    "min_angle_degrees": 8, # минимальный угол наклона (градусы)
    "max_lines_per_tf": 10, # максимум уровней на один таймфрейм
    # Приближение цены к уровню = сигнал
    "proximity_percent": 2, # ±X% от уровня (было 0.5)
    # График в сообщении
    "plot_last_bars": 250, # сколько последних свечей показывать на скриншоте
    # Telegram
    "telegram_token": "8571611252:AAFEfoXAx-ngSzVHJYUjCor623C6Vu25EQI", # токен от @BotFather
    "allowed_chat_id": 395756791, # твой chat_id (узнай через @userinfobot)
    # Период проверки всех монет
    "check_interval_seconds": 180, # каждые 3 минуты - 180 (было каждые 5 минут - 300 сек)
}
# =====================================================================

import asyncio
import os
import numpy as np
import pandas as pd
import mplfinance as mpf
import ccxt
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, ReplyKeyboardRemove

# ======================= БИРЖА =======================
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# ======================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =======================
def fetch_ohlcv(symbol: str, tf: str):
    bars = exchange.fetch_ohlcv(symbol, tf, limit=CONFIG["lookback_bars"])
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def find_pivots(df, strength):
    highs, lows = [], []
    for i in range(strength, len(df) - strength):
        if df['high'].iloc[i] == df['high'].iloc[i-strength:i+strength+1].max():
            highs.append(i)
        if df['low'].iloc[i] == df['low'].iloc[i-strength:i+strength+1].min():
            lows.append(i)
    return highs, lows

def calculate_angle(x1, y1, x2, y2):
    return np.degrees(np.arctan((y2 - y1) / (x2 - x1))) if x2 != x1 else 0

def is_near_level(price, level, percent):
    return abs(price - level) / level * 100 <= percent

def create_line_series(df, touch_points):
    if len(touch_points) < 2:
        return None
    (x1, y1), (x2, y2) = touch_points[0], touch_points[-1]
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    x_vals = np.arange(len(df))
    y_vals = slope * x_vals + intercept
    return pd.Series(y_vals, index=df.index)

def detect_levels(symbol: str, tf: str):
    df = fetch_ohlcv(symbol, tf)
    highs_idx, lows_idx = find_pivots(df, CONFIG["pivot_strength"])
    levels = []
    # Горизонтальные уровни
    pivot_prices = list(df['high'].iloc[highs_idx]) + list(df['low'].iloc[lows_idx])
    unique_levels = []
    for p in pivot_prices:
        if not any(abs(p - u) / u * 100 < CONFIG["horizontal_zone_percent"] * 2 for u in unique_levels):
            unique_levels.append(p)
    for price in unique_levels:
        touches = sum(1 for i in highs_idx + lows_idx
                      if is_near_level(df.iloc[i]['high'] if i in highs_idx else df.iloc[i]['low'], price, CONFIG["horizontal_zone_percent"]))
        if touches >= CONFIG["min_touches_horizontal"]:
            levels.append({"type": "horizontal", "price": price, "touches": touches, "tf": tf})
    # Наклонные up (по лоям)
    for i in range(len(lows_idx)):
        for j in range(i + CONFIG["min_touches_sloped"] - 1, len(lows_idx)):
            x1, y1 = lows_idx[i], df['low'].iloc[lows_idx[i]]
            x2, y2 = lows_idx[j], df['low'].iloc[lows_idx[j]]
            angle = abs(calculate_angle(x1, y1, x2, y2))
            if angle < CONFIG["min_angle_degrees"]:
                continue
            touch_points = [(lows_idx[k], df['low'].iloc[lows_idx[k]]) for k in range(i, j+1)]
            levels.append({
                "type": "sloped_up", "price": y2, "angle": angle,
                "touches": j-i+1, "touch_points": touch_points, "tf": tf
            })
            if len([l for l in levels if l["type"].startswith("sloped")]) >= CONFIG["max_lines_per_tf"]:
                break
    # Наклонные down (по хаям)
    for i in range(len(highs_idx)):
        for j in range(i + CONFIG["min_touches_sloped"] - 1, len(highs_idx)):
            x1, y1 = highs_idx[i], df['high'].iloc[highs_idx[i]]
            x2, y2 = highs_idx[j], df['high'].iloc[highs_idx[j]]
            angle = abs(calculate_angle(x1, y1, x2, y2))
            if angle < CONFIG["min_angle_degrees"]:
                continue
            touch_points = [(highs_idx[k], df['high'].iloc[highs_idx[k]]) for k in range(i, j+1)]
            levels.append({
                "type": "sloped_down", "price": y2, "angle": -angle,
                "touches": j-i+1, "touch_points": touch_points, "tf": tf
            })
            if len([l for l in levels if l["type"].startswith("sloped")]) >= CONFIG["max_lines_per_tf"]:
                break
    levels.sort(key=lambda x: x.get("touch_points", [(0,0)])[-1][0], reverse=True)
    return levels[:CONFIG["max_lines_per_tf"] * 2]

def plot_with_levels(df, levels, symbol, tf, active_level=None):
    df_plot = df.tail(CONFIG["plot_last_bars"]).copy()
    addplots = []
    for lvl in levels:
        color = 'red' if active_level and lvl == active_level else ('blue' if lvl["type"] == "horizontal" else 'orange')
        width = 3.0 if active_level and lvl == active_level else 1.5
        linestyle = '-' if 'sloped' in lvl["type"] else '--'
        if lvl["type"] == "horizontal":
            line = pd.Series([lvl["price"]] * len(df_plot), index=df_plot.index)
        else:
            line = create_line_series(df_plot, lvl.get("touch_points", []))
        if line is not None:
            addplots.append(mpf.make_addplot(line, color=color, width=width, linestyle=linestyle))
    filename = f"signal_{symbol}_{tf}.png"
    mpf.plot(df_plot, type='candle', style='charles', addplot=addplots,
             title=f"{symbol} {tf.upper()} — приближение", figsize=(12, 7),
             savefig=filename)
    return filename

# ======================= TELEGRAM БОТ =======================
bot = Bot(token=CONFIG["telegram_token"])
dp = Dispatcher()
monitored = {} # symbol -> list of current levels
# словарь для запоминания, какие уровни уже уведомлялись
# ключ: symbol, значение: set из строк вида "horizontal_12345.67" или "sloped_up_56789.12"
sent_levels = {}

def code(text: str) -> str:
    return f"<code>{text}</code>"

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить монету"), KeyboardButton(text="➖ Удалить монету")],
            [KeyboardButton(text="📋 Посмотреть список монет")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выбери действие…"
    )
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "👋 Привет! Я бот для отслеживания горизонтальных и наклонных уровней на Binance Futures.\n\n"
        "Кнопки ниже всегда под рукой. Присылай монеты в любом формате (BTC или BTCUSDT)."
    )
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")

@dp.message(lambda m: m.text in ["➕ Добавить монету", "Добавить монету"])
async def btn_add(message: types.Message):
    await message.answer(
        "Отправь название монеты:\n\nПримеры:\n• BTC\n• ETHUSDT\n• SOL\n• 1000PEPE",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

@dp.message(lambda m: m.text in ["➖ Удалить монету", "Удалить монету"])
async def btn_remove(message: types.Message):
    await message.answer(
        "Отправь название монеты для удаления:\n\nПримеры:\n• BTC\n• ETHUSDT",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

@dp.message(lambda m: m.text in ["📋 Посмотреть список монет", "Посмотреть список монет"])
async def btn_list(message: types.Message):
    if not monitored:
        await message.answer("Список пуст.", reply_markup=get_main_menu(), parse_mode="HTML")
        return
    coins = "\n".join(code(coin) for coin in sorted(monitored.keys()))
    await message.answer(f"📋 Мониторим сейчас:\n\n{coins}", reply_markup=get_main_menu(), parse_mode="HTML")

# Обработка любого текстового сообщения (добавление / удаление)
@dp.message()
async def handle_text(message: types.Message):
    text = message.text.strip().upper()
    if len(text) < 3:
        await message.answer("Не похоже на монету. Попробуй ещё раз.", reply_markup=get_main_menu(), parse_mode="HTML")
        return
    if not text.endswith("USDT"):
        text += CONFIG["symbol_suffix"]
    if text in monitored:
        del monitored[text]
        await message.answer(f"🗑 {code(text)} удалена из списка.", reply_markup=get_main_menu(), parse_mode="HTML")
    else:
        monitored[text] = []
        await message.answer(f"✅ {code(text)} добавлена в мониторинг.", reply_markup=get_main_menu(), parse_mode="HTML")

# ======================= ФОНОВАЯ ПРОВЕРКА =======================
async def background_checker():
    while True:
        for symbol in list(monitored.keys()):
            for tf in CONFIG["timeframes"]:
                levels = detect_levels(symbol, tf)
                monitored[symbol] = levels
                current_price = exchange.fetch_ticker(symbol)['last']
                for lvl in levels:
                            level_price = lvl.get("price", 0)
                            level_type = lvl["type"]
                           
                            # уникальный идентификатор уровня: тип + цена (округлённая до 4 знаков для надёжности)
                            level_id = f"{level_type}_{level_price:.4f}"
                           
                            # инициализируем для символа, если ещё нет
                            if symbol not in sent_levels:
                                sent_levels[symbol] = set()
                           
                            if is_near_level(current_price, level_price, CONFIG["proximity_percent"]):
                                # проверяем, отправляли ли уже по этому уровню
                                if level_id in sent_levels[symbol]:
                                    continue # уже уведомляли → пропускаем
                               
                                df = fetch_ohlcv(symbol, tf)
                                chart_file = plot_with_levels(df, levels, symbol, tf, active_level=lvl)
                                caption = (
                                    f"📍 <b>{symbol}</b> {tf.upper()}\n"
                                    f"🔴 Приближение к уровню ≈ {level_price:.4f}\n"
                                    f"Текущая цена: {current_price:.4f} (±{CONFIG['proximity_percent']}%)\n"
                                    f"Касаний: {lvl.get('touches', '?')} | Тип: {level_type}\n"
                                    f"Пара: {code(symbol)}"
                                )
                                await bot.send_photo(
                                    CONFIG["allowed_chat_id"],
                                    FSInputFile(chart_file),
                                    caption=caption,
                                    reply_markup=get_main_menu(),
                                    parse_mode="HTML"
                                )
                                os.remove(chart_file)
                               
                                # запоминаем, что по этому уровню уже отправили
                                sent_levels[symbol].add(level_id)
        await asyncio.sleep(CONFIG["check_interval_seconds"])

# ======================= ЗАПУСК =======================
async def main():
    asyncio.create_task(background_checker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
