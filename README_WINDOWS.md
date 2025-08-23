# WhatsApp AI Chatbot - Windows Quick Start Guide

## 🚀 Quick Start (3 Steps)

### 1. Install
Double-click on `install.bat` to install everything automatically.

### 2. Configure
Add your OpenAI API key to the `.env` file:
- Open `.env` file in Notepad
- Find the line: `OPENAI_API_KEY=your-openai-api-key-here`
- Replace with your actual key: `OPENAI_API_KEY=sk-...`
- Save and close

### 3. Run
Double-click on `quick_start.bat` to start the application.

---

## 📁 Batch Files Overview

### `install.bat` - One-Click Installer
- Checks Python installation
- Creates virtual environment
- Installs all dependencies
- Sets up project structure
- Creates configuration files

### `quick_start.bat` - Quick Launch
- Fastest way to start the application
- Launches both backend and UI
- Shows URLs for access

### `chatbot.bat` - Control Center (Advanced)
Full control panel with menu options:
- **[1] Setup Environment** - First time installation
- **[2] Start Full Application** - Backend + UI
- **[3] Start Backend Only** - API server only
- **[4] Start UI Only** - User interface only
- **[5] Start Demo Mode** - Test without full setup
- **[6] Run Tests** - Execute test suite
- **[7] Check Dependencies** - Verify installation
- **[8] Update Dependencies** - Update packages
- **[9] Database Management** - Backup/restore database
- **[0] Advanced Options** - Developer tools

---

## 🌐 Access Points

Once running, access the application at:
- **UI Interface**: http://localhost:8550
- **API Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 🔧 Troubleshooting

### Python Not Found
- Install Python 3.11+ from https://www.python.org
- During installation, check ✅ "Add Python to PATH"
- Restart your computer after installation

### Dependencies Installation Failed
- Check your internet connection
- Try running `install.bat` again
- Or use `chatbot.bat` → Option [8] Update Dependencies

### OpenAI API Key Issues
- Get your API key from: https://platform.openai.com/api-keys
- Make sure the key starts with `sk-`
- Check that you have credits in your OpenAI account

### Application Won't Start
1. Run `chatbot.bat` → Option [7] Check Dependencies
2. Make sure all critical dependencies show ✓
3. Check the `.env` file has your API key
4. Try Demo Mode first: `chatbot.bat` → Option [5]

---

## 💡 Tips

### Running Demo Mode
You can test the UI without OpenAI API:
1. Run `chatbot.bat`
2. Select Option [5] Start Demo Mode
3. Choose Demo API or Demo UI

### Creating Desktop Shortcut
1. Run `chatbot.bat`
2. Select Option [0] Advanced Options
3. Select Option [8] Create Desktop Shortcut

### Backing Up Your Data
1. Run `chatbot.bat`
2. Select Option [9] Database Management
3. Select Option [3] Backup Database

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run tests: `chatbot.bat` → Option [6]
3. View logs: `chatbot.bat` → Option [0] → Option [2]
4. Check project documentation in `/docs` folder

---

## 🎯 Features

- ✅ WhatsApp-like chat interface
- ✅ AI-powered responses (GPT-4)
- ✅ Document indexing and RAG
- ✅ Multi-project support
- ✅ Real-time file watching
- ✅ WebSocket for instant messaging
- ✅ Voice support (Phase 5 - coming soon)

---

## 🔒 Security Notes

- Never share your `.env` file
- Keep your API keys secret
- Regularly backup your database
- Update dependencies periodically

---

*Enjoy using WhatsApp AI Chatbot! 🤖💬*