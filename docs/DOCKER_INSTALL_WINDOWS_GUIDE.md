# 🐳 DOCKER INSTALLATION GUIDE (WINDOWS) - VIKA AI

## 📊 OVERVIEW
Docker is essential for running **Qdrant** (Vector Database). This guide provides step-by-step instructions for installing Docker Desktop on Windows.

---

## 🚀 1. SYSTEM REQUIREMENTS
- **Windows 10/11** (Home, Pro, or Enterprise).
- **WSL 2 (Windows Subsystem for Linux)** is highly recommended for performance.
- **Hardware Virtualization** must be enabled in BIOS.

---

## 🛠️ 2. INSTALLATION STEPS

### Step A: Enable WSL 2
1. Open PowerShell as Administrator.
2. Run:
   ```powershell
   wsl --install
   ```
3. Restart your computer.

### Step B: Download & Install Docker Desktop
1. Go to the [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) website.
2. Download the installer.
3. Run the installer and ensure **"Use WSL 2 instead of Hyper-V"** is checked.
4. Restart your computer if prompted.

### Step C: Verify Installation
1. Open a new PowerShell or Command Prompt.
2. Run:
   ```bash
   docker --version
   docker run hello-world
   ```
3. If you see "Hello from Docker!", the installation was successful.

---

## 🏗️ 3. TROUBLESHOOTING
- **BIOS Error:** If you get a virtualization error, restart and enable "Intel VT-x" or "AMD-V" in your BIOS settings.
- **WSL Update:** If prompted, update the WSL kernel by running `wsl --update`.

---

## 🎖️ NEXT STEPS
Once Docker is verified, proceed to `docs/QDRANT_SETUP_GUIDE.md` to start the vector database.

*Created 15 березня 2026*
*For в/ч А7022 | Позывной БАС*
