import asyncio
import os
import subprocess

# Запускаем все три бота параллельно
async def main():
    processes = []

    # Первый бот
    p1 = subprocess.Popen(["python3", "levels_bot.py"])
    processes.append(p1)

    # Второй бот
    p2 = subprocess.Popen(["python3", "pump_dump.py"])
    processes.append(p2)

    # Третий бот
    p3 = subprocess.Popen(["python3", "pump_dump_zapusti_esli_malo_signalov_na_test_29_01_25.py"])
    processes.append(p3)

    # Ждём, пока все работают
    for p in processes:
        p.wait()

if __name__ == "__main__":
    asyncio.run(main())
