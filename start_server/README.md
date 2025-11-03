# MovieVerse Server Startup Scripts

This directory contains automated startup scripts for running the MovieVerse web application.

## 🚀 Quick Start

### macOS/Linux

```bash
cd start_server
./start_server.sh
```

### Windows

```cmd
cd start_server
start_server.bat
```

## 📋 What the Scripts Do

The startup scripts handle the complete setup and launch process:

1. **Check Python Installation** - Verifies Python 3 is available
2. **Create Virtual Environment** - Sets up `.venv/` if it doesn't exist
3. **Install Python Dependencies** - Installs packages from `requirements.txt` (only on first run)
4. **Download spaCy Model** - Gets the English language model `en_core_web_sm`
5. **Check Node.js Installation** - Verifies Node.js is available
6. **Install Frontend Dependencies** - Runs `npm install` in `frontend/` (only on first run)
7. **Build Frontend** - Builds the React app to `frontend/dist/` (only on first run)
8. **Start Flask Server** - Launches the backend at `http://127.0.0.1:8000`

## ⚙️ Options

### Force Rebuild Frontend

If you made changes to the frontend code and want to rebuild:

**macOS/Linux:**
```bash
./start_server.sh --rebuild
```

**Windows:**
```cmd
start_server.bat --rebuild
```

## 🔍 Smart Dependency Checking

The scripts are optimized to skip redundant installations:

- **Python dependencies** - Only installed if `.venv/deps_installed` marker file is missing
- **Node.js dependencies** - Only installed if `frontend/node_modules/` doesn't exist
- **Frontend build** - Only runs if `frontend/dist/` doesn't exist (unless `--rebuild` is used)
- **spaCy model** - Only downloaded if not already installed

This means subsequent runs are much faster - just the server startup!

## 🛠️ Prerequisites

### Required Software

- **Python 3.8+** - [Download](https://python.org/)
- **Node.js 18+** - [Download](https://nodejs.org/)

### First Run

The first time you run the script, it will:
- Download and install all Python packages (~100MB)
- Download and install all Node.js packages (~200MB)
- Download spaCy language model (~15MB)
- Build the frontend application

This may take 5-10 minutes depending on your internet speed.

## ✅ Subsequent Runs

After the first setup, running the script again will:
- Skip all installations (already done!)
- Just start the Flask server
- Takes only a few seconds

## 🚪 Stopping the Server

Press `CTRL+C` in the terminal to stop the server.

## 📝 Notes

- The virtual environment is created at `../.venv/` (project root)
- Frontend build output is in `../frontend/dist/`
- Server runs on port 8000 by default
- All paths are relative to the project root, so the scripts work from anywhere

## 🐛 Troubleshooting

**Port 8000 already in use?**
```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Dependencies out of date?**
```bash
# Delete the marker file to force reinstall
rm ../.venv/deps_installed
```

**Frontend changes not showing?**
```bash
# Force rebuild
./start_server.sh --rebuild
```
