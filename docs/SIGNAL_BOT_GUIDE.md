# ⚡ SIGNAL BOT "ГРІМ" - VIKA AI

## 📊 OVERVIEW
The Signal Bot (Codename: **ГРІМ**) provides a secure, end-to-end encrypted interface for Vika. This allows authorized users to interact with Vika via any Signal-enabled device, ensuring that communications remain private and protected.

---

## 🚀 1. PREREQUISITES
1. **Signal Number:** A dedicated phone number (or VoIP number) for the bot.
2. **Java Runtime:** Required for `signal-cli`.
3. **Registration:** Complete the one-time registration process.

---

## 🛠️ 2. INSTALLATION (SIGNAL-CLI)
1. Download the latest release of [signal-cli](https://github.com/AsamK/signal-cli).
2. Install Java 21+ if not available.
3. Link or register your number:
   ```bash
   signal-cli -u +380XXXXXXXXX register
   signal-cli -u +380XXXXXXXXX verify CODE
   ```

---

## 🏗️ 3. PYTHON INTEGRATION
The bot works by listening for incoming messages, processing them through Vika's brain, and replying.

### Basic Bot Structure
```python
import subprocess
import json

def process_signal_message(sender, message):
    # Logic to route message to Vika's LLM
    response = vika_brain.query(message)
    send_signal_reply(sender, response)

def send_signal_reply(recipient, text):
    subprocess.run([
        "signal-cli", "-u", "+380XXXXXXXXX", 
        "send", "-m", text, recipient
    ])
```

---

## 🔒 4. SECURITY & PERMISSIONS
1. **Whitelisting:** ONLY respond to authorized phone numbers.
2. **Auto-Purge:** Messages should be deleted from the system after processing.
3. **Encrypted Storage:** Do not store message history on disk in plain text.

### Authorization Check
```python
AUTHORIZED_NUMBERS = ["+380971234567", "+380509876543"]

def is_authorized(number):
    return number in AUTHORIZED_NUMBERS
```

---

## 🎖️ NEXT STEPS (DAY 2-3)
1. Setup the Signal Bot daemon.
2. Implement the command processing layer.
3. Test end-to-end encryption from a mobile device to Vika.

*Created 15 березня 2026*
*For в/ч А7022 | Позывной БАС*
