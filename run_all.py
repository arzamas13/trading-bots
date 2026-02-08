import subprocess
import time

print("Запускаем все боты...")

# Запускаем первый бот
subprocess.Popen(["python3", "levels_bot.py"])

# Запускаем второй бот
subprocess.Popen(["python3", "pump_dump.py"])

# Запускаем третий бот
subprocess.Popen(["python3", "pump_dump_zapusti_esli_malo_signalov_na_test_29_01_25.py"])

# Держим процесс живым
print("Все боты запущены")
while True:
    time.sleep(60)
