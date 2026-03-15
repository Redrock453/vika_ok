import os
import sys
import json
import logging
import subprocess
import threading
import requests
import time
from pathlib import Path

# Silence pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

logging.basicConfig(level=logging.ERROR) # Only errors
logger = logging.getLogger("VikaAgent")

# Directories
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# PIPER SETTINGS (Russian Irina)
PIPER_MODEL = MODELS_DIR / "ru_RU-irina-medium.onnx"
PIPER_CONFIG = MODELS_DIR / "ru_RU-irina-medium.onnx.json"

def speak(text):
    if not PIPER_MODEL.exists(): return
    
    clean_text = text.replace("*", "").replace("#", "").replace("", "")
    temp_wav = BASE_DIR / "temp_speech.wav"
    
    try:
        # Generate WAV via Piper
        piper_path = str(BASE_DIR / "venv" / "Scripts" / "piper.exe")
        cmd = [piper_path, "--model", str(PIPER_MODEL), "--config", str(PIPER_CONFIG), "--output_file", str(temp_wav)]
        
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.communicate(input=clean_text.encode('utf-8'))
        
        # Play via Pygame
        pygame.mixer.init()
        pygame.mixer.music.load(str(temp_wav))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.quit()
        
        if temp_wav.exists(): os.remove(temp_wav)
    except Exception as e:
        pass

class VikaAgent:
    def __init__(self, model="llama3.2"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

    def ask(self, prompt):
        data = {"model": self.model, "prompt": prompt, "stream": False}
        try:
            response = requests.post(self.url, json=data, timeout=30)
            return response.json().get("response", "...")
        except:
            return "Ollama error"

def main():
    agent = VikaAgent()
    print("ЁЯОА Vika Agent: Ready.")
    
    while True:
        try:
            user_input = input("-> ")
            if user_input.lower() in ["exit", "quit"]: break
            
            response = agent.ask(user_input)
            print(f"Vika: {response}")
            threading.Thread(target=speak, args=(response,), daemon=True).start()
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
