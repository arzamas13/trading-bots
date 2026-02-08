import requests
import time
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== НАСТРОЙКИ ====================

symbols = [
    "1000CATUSDT", "FHEUSDT", "ACXUSDT", "AIOUSDT", "BULLAUSDT", "CGPTUSDT", "CLOUSDT", "DEEPUSDT", "DEGENUSDT", "EPICUSDT", "0GUSDT", "SSVUSDT", "NIGHTUSDT", "1000000BOBUSDT", "1000BONKUSDT", "1000CHEEMSUSDT", "1000PEPEUSDT", "4USDT", "A2ZUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AIAUSDT", "AKEUSDT", "ALGOUSDT", "ANIMEUSDT", "APEUSDT", "API3USDT", "APRUSDT", "ARBUSDT", "ASRUSDT", "ASTERUSDT", "ATHUSDT", "AVAXUSDT", "AVNTUSDT", "BASUSDT", "BCHUSDT", "BLURUSDT", "BNBUSDT", "BOMEUSDT", "BTRUSDT", "CAKEUSDT", "CELRUSDT", "CKBUSDT", "CROSSUSDT", "CRVUSDT", "CTKUSDT", "CUDISUSDT", "1000LUNCUSDT", "ALCHUSDT", "ALICEUSDT", "ALPINEUSDT", "ARPAUSDT", "ARUSDT", "ATAUSDT", "ATUSDT", "AUCTIONUSDT", "AVAAIUSDT", "AWEUSDT", "B2USDT", "BANANAS31USDT", "BANANAUSDT", "BANKUSDT", "BARDUSDT", "BBUSDT", "BEAMXUSDT", "BEATUSDT", "BELUSDT", "BERAUSDT", "BIDUSDT", "BIOUSDT", "BLESSUSDT", "BLUAIUSDT", "BMTUSDT", "BROCCOLIF3BUSDT", "BRUSDT", "C98USDT", "CATIUSDT", "CETUSUSDT", "CFXUSDT", "CHESSUSDT", "CLANKERUSDT", "COAIUSDT", "CTSIUSDT", "ACTUSDT", "AERGOUSDT", "AIOTUSDT",
    "CVCUSDT", "EULUSDT", "GMTUSDT", "GPSUSDT", "GRIFFAINUSDT", "GRTUSDT", "GUSDT", "IOTXUSDT", "JASMYUSDT", "BUSDT", "CUSDT", "ZBTUSDT", "GUNUSDT", "DEGOUSDT", "DIAUSDT", "DODOXUSDT", "DOGEUSDT", "DOTUSDT", "DRIFTUSDT", "DYDXUSDT", "EDENUSDT", "EIGENUSDT", "ERAUSDT", "ETHFIUSDT", "ETHUSDT", "FARTCOINUSDT", "FETUSDT", "FFUSDT", "FIDAUSDT", "FLUIDUSDT", "FUNUSDT", "GALAUSDT", "GLMUSDT", "HANAUSDT", "HBARUSDT", "HEMIUSDT", "HIGHUSDT", "HOLOUSDT", "HOMEUSDT", "HUMAUSDT", "HYPERUSDT", "HYPEUSDT", "IDOLUSDT", "INUSDT", "IRYSUSDT", "JUPUSDT", "KASUSDT", "CYBERUSDT", "DEXEUSDT", "DFUSDT", "DMCUSDT", "DOODUSDT", "DYMUSDT", "EDUUSDT", "ENAUSDT", "ENSUSDT", "EPTUSDT", "ESPORTSUSDT", "EVAAUSDT", "FILUSDT", "FIOUSDT", "FLOCKUSDT", "FLUXUSDT", "FOLKSUSDT", "FORMUSDT", "FUSDT", "GIGGLEUSDT", "GRASSUSDT", "HAEDALUSDT", "HEIUSDT", "HFTUSDT", "HIPPOUSDT", "HMSTRUSDT", "HOOKUSDT", "HUSDT", "ICNTUSDT", "ICPUSDT", "ILVUSDT", "IOSTUSDT", "IPUSDT", "JELLYJELLYUSDT", "JTOUSDT", "KAITOUSDT", "KAVAUSDT", "KOMAUSDT", "LABUSDT", "CYSUSDT", "DAMUSDT",
    "LDOUSDT", "MAGMAUSDT", "MOCAUSDT", "MOVEUSDT", "NKNUSDT", "POLUSDT", "RIVERUSDT", "STORJUSDT", "SYRUPUSDT", "TAKEUSDT", "KGENUSDT", "TUSDT", "CVXUSDT","KMNOUSDT", "DOLOUSDT","KNCUSDT", "LAUSDT", "LINEAUSDT", "LINKUSDT", "LISTAUSDT", "LTCUSDT", "LYNUSDT", "MANTAUSDT", "MEMEUSDT", "MEUSDT", "MINAUSDT", "MIRAUSDT", "MUBARAKUSDT", "MUSDT", "NEARUSDT", "NEIROUSDT", "ONDOUSDT", "OPENUSDT", "OPUSDT", "PAXGUSDT", "PENDLEUSDT", "PENGUUSDT", "PLUMEUSDT", "PNUTUSDT", "POPCATUSDT", "PROMUSDT", "PROVEUSDT", "PUMPBTCUSDT", "PYTHUSDT", "QUSDT", "RENDERUSDT", "REZUSDT", "SANDUSDT", "SEIUSDT", "SIGNUSDT", "LPTUSDT", "MAGICUSDT", "MASKUSDT", "MAVIAUSDT", "MAVUSDT", "MBOXUSDT", "MELANIAUSDT", "MERLUSDT", "METISUSDT", "MLNUSDT", "MONUSDT", "MOODENGUSDT", "MYXUSDT", "NAORISUSDT", "NMRUSDT", "NTRNUSDT", "OGNUSDT", "OLUSDT", "OMUSDT", "ORCAUSDT", "ORDERUSDT", "PARTIUSDT", "PHAUSDT", "PIEVERSEUSDT", "PIPPINUSDT", "PIXELUSDT", "PLAYUSDT", "PROMPTUSDT", "PTBUSDT", "PUFFERUSDT", "PUMPUSDT", "RAREUSDT", "RAVEUSDT", "RDNTUSDT", "REDUSDT", "RESOLVUSDT", "RLCUSDT", "RLSUSDT", "LUMIAUSDT", "LUNA2USDT",
    "RVNUSDT", "USUSDT", "VVVUSDT", "WALUSDT", "1000WHYUSDT", "WETUSDT", "XAGUSDT", "XVSUSDT", "ZKPUSDT", "ZROUSDT", "币安人生USDT", "SNXUSDT", "ONTUSDT", "SOLUSDT", "OXTUSDT", "SOMIUSDT", "SONICUSDT", "SOONUSDT", "SOPHUSDT", "SPKUSDT", "STBLUSDT", "STOUSDT", "TAOUSDT", "TAUSDT", "THETAUSDT", "THEUSDT", "TIAUSDT", "TLMUSDT", "TONUSDT", "TOSHIUSDT", "TREEUSDT", "TRUTHUSDT", "TRXUSDT", "TURBOUSDT", "TUTUSDT", "UBUSDT", "UNIUSDT", "USELESSUSDT", "VFYUSDT", "VIRTUALUSDT", "WLDUSDT", "WUSDT", "XLMUSDT", "XNYUSDT", "XPINUSDT", "XPLUSDT", "YBUSDT", "ZENUSDT", "ZKCUSDT", "RVVUSDT", "SAHARAUSDT", "SFPUSDT", "SIRENUSDT", "SKLUSDT", "SOLVUSDT", "SQDUSDT", "STGUSDT", "STRKUSDT", "STXUSDT", "SUIUSDT", "SUNUSDT", "SUPERUSDT", "SWARMSUSDT", "SYSUSDT", "TACUSDT", "TAGUSDT", "TANSSIUSDT", "TNSRUSDT", "TRADOORUSDT", "TRUMPUSDT", "TRUSTUSDT", "TSTUSDT", "TWTUSDT", "UMAUSDT", "USTCUSDT", "VELVETUSDT", "VICUSDT", "VINEUSDT", "WCTUSDT", "WIFUSDT", "WLFIUSDT", "XANUSDT", "XRPUSDT", "XTZUSDT", "YALAUSDT", "YGGUSDT", "ZECUSDT", "ZEREBROUSDT", "ZKJUSDT", "ZORAUSDT", "ZRCUSDT", "SAPIENUSDT", "SCRTUSDT",
]

TELEGRAM_BOT_TOKEN = "8260698936:AAEj713IS8VtRB9wzp8_u3lYOhaiGZ2aG34"
TELEGRAM_CHAT_ID = "-1003627898346"  # группа Бермуды

# ==================== ПАРАМЕТРЫ ====================

CHECK_INTERVAL = 60               # секунд — частота запуска проверки (можно 30–120)
SEND_INTERVAL = 120               # секунд — минимальный интервал между отправками (если есть сигналы)
GROWTH_THRESHOLD = 6.0            # минимальный % роста для сигнала. Как и в самом начале
MAX_WORKERS = 40                  # количество параллельных запросов (20–50 — оптимально)
GROWTH_PERIOD_MINUTES = 60        # период измерения роста в минутах (можно менять на 30, 15, 120 и т.д.). Как и в самом начале

# ================================================

logging.basicConfig(
    filename='pump_dump.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

logging.info(f"Скрипт pump_dump.py запущен — параллельные запросы, уведомления ТОЛЬКО при сигналах, период роста {GROWTH_PERIOD_MINUTES} мин")

BASE_URL = "https://fapi.binance.com"
KLINES_ENDPOINT = "/fapi/v1/klines"

# Автоматический расчёт количества свечей по периоду (5-минутные свечи)
candle_interval_min = 5
klines_limit = (GROWTH_PERIOD_MINUTES // candle_interval_min) + 2  # +2 для надёжности

found_coins = []
last_send_time = 0

def get_price_change(symbol, retries=2):
    """Получает изменение цены за указанный период с retry"""
    for attempt in range(retries + 1):
        try:
            params = {"symbol": symbol, "interval": "5m", "limit": klines_limit}
            response = requests.get(BASE_URL + KLINES_ENDPOINT, params=params, timeout=8)
            response.raise_for_status()
            data = response.json()

            if len(data) < klines_limit:
                return None

            # Цена открытия самой старой свечи
            price_old = float(data[0][1])
            # Текущая цена — закрытие последней свечи
            current_price = float(data[-1][4])

            if price_old == 0:
                return None

            growth = (current_price - price_old) / price_old * 100
            return round(growth, 2)

        except Exception as e:
            if attempt == retries:
                logging.warning(f"{symbol} — ошибка после {retries} попыток: {e}")
                return None
            time.sleep(0.5 * (attempt + 1))  # backoff

def check_all_symbols():
    """Параллельная проверка всех символов"""
    temp_found = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        logging.info(f"Начата проверка {len(symbols)} монет (период: {GROWTH_PERIOD_MINUTES} мин)")
        future_to_symbol = {executor.submit(get_price_change, sym): sym for sym in symbols}

        for future in as_completed(future_to_symbol):
            sym = future_to_symbol[future]
            try:
                growth = future.result()
                if growth is not None and growth >= GROWTH_THRESHOLD:
                    temp_found.append((sym, growth))
            except Exception as e:
                logging.error(f"Исключение в потоке для {sym}: {e}")

    logging.info(f"Проверка завершена. Найдено сигналов: {len(temp_found)}")
    return temp_found

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=10)
        logging.info("Сообщение отправлено в группу")
    except Exception as e:
        logging.error(f"Ошибка отправки в Telegram: {e}")

def main_loop():
    global found_coins, last_send_time

    while True:
        current_time = time.time()

        # Проверяем, пора ли отправлять (и есть ли что отправлять)
        if (current_time - last_send_time >= SEND_INTERVAL or last_send_time == 0) and found_coins:
            message = f"<b>🔴Binance🔴 — Обнаружены монеты для 🔴ШОРТА🔴 с ростом ≥{GROWTH_THRESHOLD}% за последние {GROWTH_PERIOD_MINUTES} минут:</b>\n\n"
            for sym, growth in sorted(found_coins, key=lambda x: x[1], reverse=True):
                sign = "+" if growth > 0 else ""
                message += f"<code>{sym}</code> <b>{sign}{growth}%</b>\n"
            logging.info(f"Отправка сигнала: {len(found_coins)} монет")

            send_telegram_message(message)
            found_coins = []  # сбрасываем после отправки
            last_send_time = current_time

        # Параллельная проверка
        temp_found = check_all_symbols()
        if temp_found:
            found_coins = temp_found

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
