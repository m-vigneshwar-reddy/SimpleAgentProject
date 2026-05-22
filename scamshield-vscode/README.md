# 🛡️ ScamShield AI — VS Code Web App

## Run in 3 steps

### Step 1 — Install Node.js
Download from https://nodejs.org (choose LTS version 18 or 20)

### Step 2 — Open in VS Code
1. Unzip this folder
2. Open VS Code → File → Open Folder → select `scamshield-vscode`

### Step 3 — Run
Open the VS Code terminal (Ctrl + ` ) and type:

```
npm install
npm start
```

Then open your browser and go to:
**http://localhost:3001**

That's it — the app is running! ✅

---

## What happens
- `npm install` downloads the 3 required packages (express, ws, cors)
- `npm start` launches the Node.js server on port 3001
- The server streams a new message every 3 seconds (WhatsApp, SMS, Email, Instagram, etc.)
- Open the browser and watch real-time scam detection live

## Alternatively — use VS Code Run button
Press **F5** in VS Code (or go to Run → Start Debugging) to launch the server with the debugger attached.

## Project files
```
scamshield-vscode/
├── server/
│   └── index.js        ← Node.js backend + ML engine + WebSocket
├── public/
│   └── index.html      ← Full web app (auto-served by the server)
├── .vscode/
│   └── launch.json     ← VS Code run config (F5 to launch)
└── package.json        ← Dependencies (express, ws, cors)
```
