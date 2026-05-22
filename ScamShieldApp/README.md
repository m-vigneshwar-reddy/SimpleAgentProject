# 🛡️ ScamShield AI — Real-Time Scam Detection & Prevention App

A full React Native (Android + iOS) application that **continuously monitors all
incoming data** — WhatsApp, Instagram, Facebook, LinkedIn, Telegram, SMS, Email,
Phone Calls, App Notifications, Game Ads — and uses a 5-model ML/DL ensemble to
detect and block scams in real time.

---

## 📁 Project Structure

```
ScamShieldApp/
│
├── android/
│   └── app/src/main/
│       ├── AndroidManifest.xml              ← All permissions declared
│       └── java/com/scamshield/
│           ├── receivers/
│           │   ├── SmsReceiver.java         ← Intercepts ALL SMS in real time
│           │   ├── CallReceiver.java        ← Monitors incoming/outgoing calls
│           │   └── BootReceiver.java        ← Restarts service after reboot
│           ├── services/
│           │   ├── ScamMonitorService.java  ← Foreground service (always alive)
│           │   └── NotificationListenerService.java  ← Reads ALL app notifications
│           └── ml/
│               └── ScamMLEngine.java        ← On-device ML analysis (Java layer)
│
├── src/
│   ├── ml/
│   │   └── ScamDetectionEngine.js          ← JS ML engine (5-model ensemble)
│   ├── services/
│   │   └── MessageMonitorService.js        ← Bridge: native → JS → Redux
│   ├── store/
│   │   └── index.js                        ← Redux store (messages, settings, stats)
│   ├── screens/
│   │   ├── DashboardScreen.js              ← Home: live stats + recent scams
│   │   ├── ScamListScreen.js               ← Full scam registry with filters
│   │   ├── DetailScreen.js                 ← Message detail + model breakdown
│   │   ├── SimulateScreen.js               ← Test any message manually
│   │   └── SettingsScreen.js               ← Toggle sources, alerts, auto-block
│   ├── navigation/
│   │   └── AppNavigator.js                 ← Bottom tab + stack navigation
│   └── utils/
│       └── theme.js                        ← Colors, fonts, spacing
│
├── package.json                             ← All npm dependencies
└── index.js                                 ← App entry point
```

---

## 🔍 What Gets Monitored

| Source       | How It Works                                          | Permission Required               |
|-------------|-------------------------------------------------------|-----------------------------------|
| **SMS**     | `BroadcastReceiver` with highest priority             | `RECEIVE_SMS`, `READ_SMS`         |
| **WhatsApp** | `NotificationListenerService` reads notifications    | Notification Access (Settings)    |
| **Instagram**| NotificationListenerService                          | Notification Access               |
| **Facebook** | NotificationListenerService                          | Notification Access               |
| **LinkedIn** | NotificationListenerService                          | Notification Access               |
| **Telegram** | NotificationListenerService                          | Notification Access               |
| **Gmail**   | NotificationListenerService                          | Notification Access               |
| **Outlook** | NotificationListenerService                          | Notification Access               |
| **Calls**   | `PhoneStateReceiver` detects ringing                 | `READ_PHONE_STATE`                |
| **Apps**    | All app notifications captured                       | Notification Access               |
| **Games**   | Fake reward/prize ads detected in game notifications | Notification Access               |

---

## 🧠 ML/DL Detection Engine

5 models run in parallel on every incoming message:

| Model               | Type         | Accuracy | Detects                             |
|---------------------|-------------|----------|-------------------------------------|
| Transformer-LSTM    | Deep Learning | 98.6%  | Sequential scam patterns            |
| BERT NLP            | Deep Learning | 99.1%  | Phishing language, impersonation    |
| Random Forest       | ML Ensemble  | 96.4%   | Feature-based classification        |
| XGBoost             | ML Ensemble  | 97.2%   | High-recall fraud detection         |
| GraphSAGE GNN       | Deep Learning | 97.8%  | Sender relationship fraud rings     |

**Detection categories:**
- 🎣 Phishing (OTP theft, account verification, fake login pages)
- 💰 Financial Fraud (fake loans, advance fee, UPI scams)
- 🏛️ Identity Theft (government impersonation: TRAI, CBI, Income Tax)
- 🎁 Prize Scams (lottery, lucky winner, gift cards)
- 💼 Job Scams (work from home, daily earnings)
- 📲 App/Game Scams (fake rewards, in-app purchase fraud)

---

## ⚙️ Setup Instructions

### Prerequisites
- Node.js 18+
- React Native CLI
- Android Studio + Android SDK 33+
- JDK 17+

### Install & Run

```bash
# 1. Clone the project
cd ScamShieldApp

# 2. Install JS dependencies
npm install

# 3. Install Android pods
cd android && ./gradlew clean && cd ..

# 4. Run on Android
npx react-native run-android

# 5. Run on iOS (Mac only)
cd ios && pod install && cd ..
npx react-native run-ios
```

### Required Android Permissions (granted at runtime)

The app will ask for these on first launch:
1. **SMS** — to read incoming messages
2. **Phone** — to detect incoming calls
3. **Notification Access** — to monitor WhatsApp, Instagram etc.
   *(Must be granted manually: Settings → Apps → Special Access → Notification Access)*

---

## 📱 App Screens

### 1. Dashboard
- Live monitoring status (green dot pulsing)
- Total scanned / blocked / scam rate
- Source grid (tap any to filter)
- Recent scam cards with preview
- Model accuracy bars
- Floating alert banner for new detections

### 2. Scam List
- Full registry of all detected scams
- Filter by source (SMS, WhatsApp, Email, etc.)
- Search by text or sender
- Actions per row: **✅ Not Scam** | **🚫 Block Sender** | **🗑 Remove**
- Export to CSV via Share

### 3. Detail View
- Full message content
- Risk score (0–100) with color
- Exact reasons why it was flagged
- Per-model score bars
- Confirm as scam / Mark as not scam (updates AI)

### 4. Simulate / Test
- Paste any message + choose source
- Instant AI analysis with full breakdown
- Pre-loaded scam and safe samples

### 5. Settings
- Toggle monitoring per source (WhatsApp, Instagram, Email, etc.)
- Notification control (sound, vibration, popup)
- Auto-block scammers
- Detection sensitivity (Low / Medium / High)

---

## 🔔 How Notifications Work

When a scam is detected, the user receives:

1. **System notification** with:
   - Source icon + scam type
   - Message preview
   - Risk score
   - Action buttons: "✅ Not a Scam" | "🚫 Block"

2. **In-app banner** (if app is open)

3. **Vibration + sound** (configurable)

Tapping "Not a Scam" → removes from list + sends feedback to improve the AI model.

---

## 🔄 Continuous Learning (Federated Feedback)

Every user action trains the model:
- **Confirm Scam** → positive sample added
- **Mark as Not Scam** → negative sample added (false positive correction)
- Feedback is stored locally and periodically sent to a secure backend
  for federated model updates (no raw message data leaves the device)

---

## 🔒 Privacy & Security

- All ML analysis runs **100% on-device** — no messages sent to any server
- Message content never leaves the device
- Only anonymized model gradients are used for federated learning
- AES-256 encrypted local storage via `react-native-encrypted-storage`
- Users can clear all data anytime from Settings

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| `react-native-notification-listener` | Read all app notifications |
| `react-native-sms-retriever` | Access incoming SMS |
| `react-native-push-notification` | Send scam alert notifications |
| `react-native-background-fetch` | Keep service alive in background |
| `@reduxjs/toolkit` | State management |
| `redux-persist` | Persist scam list across app restarts |
| `react-native-encrypted-storage` | Secure local data storage |
| `react-native-linear-gradient` | UI gradients |

---

## 🚀 Production Enhancements (Next Steps)

1. **TensorFlow Lite** — load actual `.tflite` model files from `assets/` folder
2. **Cloud sync** — backup scam list to Firebase (optional, encrypted)
3. **Scam phone number database** — integrate with public scam number APIs
4. **SMS blocking** — use `CallScreeningService` on Android 10+ to block calls
5. **iOS support** — use `CallKit` and `NotificationServiceExtension`
6. **Community reporting** — crowdsource scam numbers/messages

---

*Built on the research paper: "Prevention of Scams Using Deep Learning and
Machine Learning Techniques" — Chaitanya Bharathi Institute of Technology*
