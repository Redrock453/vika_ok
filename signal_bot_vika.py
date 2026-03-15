import asyncio
import json
import logging
import subprocess
import os
from datetime import datetime
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Загрузка .env
load_dotenv()

# Логирование
BASE_DIR = Path(__file__).parent.absolute()
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'signal_bot_vika.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === КОНФИГ ===
# Используем твой номер бота из .env или дефолт
SIGNAL_NUMBER = os.getenv('SIGNAL_NUMBER', '+380734311153')
MASTER_NUMBER = os.getenv('TELEGRAM_ADMIN_ID') # Можем переиспользовать или создать MASTER_SIGNAL_NUMBER

# Пути к бинарникам (Windows адаптировано)
JAVA_HOME = str(BASE_DIR / "bin" / "java" / "jdk-21.0.2+13")
SIGNAL_CLI_BAT = str(BASE_DIR / "bin" / "signal" / "signal-cli-0.14.1" / "bin" / "signal-cli.bat")
PYTHON_EXE = str(BASE_DIR / "venv" / "Scripts" / "python.exe")
VIKA_SCRIPT = str(BASE_DIR / "agent.py")

# Шифрование audit логов
CIPHER_KEY = os.getenv('CIPHER_KEY')
if not CIPHER_KEY:
    CIPHER_KEY = Fernet.generate_key().decode()
    logger.warning(f"!!! НОВЫЙ КЛЮЧ ШИФРОВАНИЯ: {CIPHER_KEY}")
    logger.warning("СОХРАНИ ЕГО В .env: CIPHER_KEY=...")

cipher = Fernet(CIPHER_KEY.encode())

# === AUDIT LOG (шифрованный) ===
AUDIT_LOG = LOG_DIR / 'signal_audit_vika.enc'

def log_audit(msg_type: str, user: str, text: str, response: str = None):
    try:
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': msg_type,
            'user': user,
            'text': text[:500],
            'response': response[:500] if response else None
        }
        encrypted = cipher.encrypt(json.dumps(entry).encode())
        with open(AUDIT_LOG, 'ab') as f:
            f.write(encrypted + b'\n')
    except Exception as e:
        logger.error(f"Audit log error: {e}")

# === VIKA ИНТЕГРАЦИЯ ===
async def ask_vika(question: str) -> str:
    try:
        # Запускаем через подпроцесс с флагом --query
        proc = await asyncio.create_subprocess_exec(
            PYTHON_EXE,
            VIKA_SCRIPT,
            '--query',
            question,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90)
        except asyncio.TimeoutError:
            proc.kill()
            return "⏱️ Вика зависла на 90 сек. Проверь систему."
        
        response = stdout.decode('utf-8', errors='ignore').strip()
        if not response:
            err = stderr.decode('utf-8', errors='ignore').strip()
            logger.error(f"Vika Error: {err}")
            return "❌ Ошибка при генерации ответа."
            
        return response
    except Exception as e:
        logger.error(f"Vika exec error: {e}")
        return f"❌ Сбой моста: {str(e)}"

# === SIGNAL BOT ===
async def run_signal_bot():
    logger.info("🚀 Запуск Vika Signal Bot...")
    
    # Запуск signal-cli в режиме получения сообщений
    env = os.environ.copy()
    env["JAVA_HOME"] = JAVA_HOME
    
    cmd = f'"{SIGNAL_CLI_BAT}" -u {SIGNAL_NUMBER} daemon --jsonrpc'
    
    logger.info(f"Команда: {cmd}")
    
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    
    logger.info("✅ Бот в сети. Слушаю сообщения...")

    async for line in proc.stdout:
        try:
            data = line.decode('utf-8', errors='ignore').strip()
            if not data: continue
            
            msg_json = json.loads(data)
            if "envelope" in msg_json and "dataMessage" in msg_json["envelope"]:
                env_msg = msg_json["envelope"]
                sender = env_msg.get("sourceNumber") or env_msg.get("source")
                text = env_msg["dataMessage"].get("message", "").strip()
                
                if not text: continue
                
                logger.info(f"📬 Сообщение от {sender}: {text[:50]}...")
                
                # Запрос к Вике
                response = await ask_vika(text)
                
                # Шифрованный лог
                log_audit('msg', sender, text, response)
                
                # Отправка ответа
                send_payload = {
                    "jsonrpc": "2.0",
                    "method": "send",
                    "params": {
                        "recipient": [sender],
                        "message": response
                    },
                    "id": int(datetime.now().timestamp())
                }
                proc.stdin.write((json.dumps(send_payload) + "\n").encode())
                await proc.stdin.drain()
                
        except Exception as e:
            logger.error(f"Processing error: {e}")

async def main():
    await run_signal_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Бот остановлен.")
    except Exception as e:
        logger.error(f"FATAL: {e}")
