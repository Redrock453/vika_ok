import os
import sys
import json
import re
import logging
import subprocess
import asyncio
from agent import VikaOk
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, 
    filename="signal_bridge.log", 
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding='utf-8'
)

class SignalGROM:
    def __init__(self, bot_number, master_number):
        self.bot_num = bot_number
        self.master = master_number
        self.vika = VikaOk()
        
        # Локальные пути к бинарникам
        self.base_dir = Path(__file__).parent.absolute()
        self.java_bin = self.base_dir / "bin" / "java" / "jdk-21.0.2+13" / "bin" / "java.exe"
        self.signal_cli_bin = self.base_dir / "bin" / "signal" / "signal-cli-0.14.1" / "bin" / "signal-cli.bat"
        
        # Регулярки для фильтрации PII
        self.pii_patterns = [
            r"\d{2}\.\d{4,},\s?\d{2}\.\d{4,}", # Координаты
            r"\+?380\d{9}",                    # Укр. номера
        ]

    def filter_pii(self, text):
        clean_text = text
        for pattern in self.pii_patterns:
            clean_text = re.sub(pattern, "[ДАННЫЕ УДАЛЕНЫ]", clean_text)
        return clean_text

    async def run_daemon(self):
        """Запуск signal-cli в режиме демона через JSON-RPC"""
        print(f"[!] ЗАПУСК ДЕМОНА СИГНАЛА ДЛЯ НОМЕРА {self.bot_num}...")
        # Устанавливаем JAVA_HOME для батника signal-cli
        env = os.environ.copy()
        env["JAVA_HOME"] = str(self.base_dir / "bin" / "java" / "jdk-21.0.2+13")
        
        cmd = f'"{self.signal_cli_bin}" -u {self.bot_num} daemon --jsonrpc'
        
        self.proc = await asyncio.create_subprocess_shell(
            cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        print("[!] ГРОМ АКТИВИРОВАН. Ожидаю сообщений...")
        
        async for line in self.proc.stdout:
            data = line.decode('utf-8', errors='ignore').strip()
            if not data: continue
            try:
                msg_json = json.loads(data)
                if "envelope" in msg_json and "dataMessage" in msg_json["envelope"]:
                    envelope = msg_json["envelope"]
                    sender = envelope["sourceNumber"]
                    message = envelope["dataMessage"]["message"]
                    await self.handle_incoming(sender, message)
            except Exception as e:
                logging.error(f"Ошибка парсинга JSON: {e}")

    async def handle_incoming(self, sender, message):
        if sender != self.master:
            logging.warning(f"Игнорирую сообщение от {sender}")
            return

        logging.info(f"Входящее от БАС: {message}")
        response = self.vika.ask(message)
        clean_response = self.filter_pii(response)
        
        # Отправка ответа
        send_cmd = {
            "jsonrpc": "2.0",
            "method": "send",
            "params": {
                "recipient": [self.master],
                "message": clean_response
            },
            "id": int(datetime.now().timestamp())
        }
        self.proc.stdin.write((json.dumps(send_cmd) + "\n").encode())
        await self.proc.stdin.drain()

async def main():
    # ВЯЧЕСЛАВ: ВВЕДИ СВОИ НОМЕРА ТУТ
    BOT_NUM = "+380XXXXXXXXX" # Номер бота
    MASTER_NUM = "+380XXXXXXXXX" # Твой номер
    
    grom = SignalGROM(BOT_NUM, MASTER_NUM)
    await grom.run_daemon()

if __name__ == "__main__":
    asyncio.run(main())
