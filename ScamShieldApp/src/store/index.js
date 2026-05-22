// src/store/index.js
import { configureStore, createSlice } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { combineReducers } from 'redux';

// ── MESSAGES SLICE ───────────────────────────────────────────────────────────
const messagesSlice = createSlice({
  name: 'messages',
  initialState: {
    all: [],
    scamList: [],
    blockedSenders: [],
    whitelistedSenders: [],
    filter: 'all',
  },
  reducers: {
    addMessage(state, { payload }) {
      state.all.unshift(payload);
      if (state.all.length > 500) state.all.pop();
      if (payload.verdict === 'SCAM' || payload.verdict === 'SUSPICIOUS') {
        if (!state.scamList.find(m => m.id === payload.id)) {
          state.scamList.unshift(payload);
        }
      }
    },
    confirmScam(state, { payload: id }) {
      const msg = state.scamList.find(m => m.id === id);
      if (msg) msg.confirmed = true;
    },
    dismissScam(state, { payload: id }) {
      state.scamList = state.scamList.filter(m => m.id !== id);
      const msg = state.all.find(m => m.id === id);
      if (msg) msg.dismissed = true;
    },
    markNotScam(state, { payload: id }) {
      state.scamList = state.scamList.filter(m => m.id !== id);
      const msg = state.all.find(m => m.id === id);
      if (msg) { msg.verdict = 'SAFE'; msg.userCorrected = true; }
    },
    blockSender(state, { payload: sender }) {
      if (!state.blockedSenders.includes(sender)) {
        state.blockedSenders.push(sender);
      }
    },
    unblockSender(state, { payload: sender }) {
      state.blockedSenders = state.blockedSenders.filter(s => s !== sender);
    },
    whitelistSender(state, { payload: sender }) {
      if (!state.whitelistedSenders.includes(sender)) {
        state.whitelistedSenders.push(sender);
      }
    },
    setFilter(state, { payload }) { state.filter = payload; },
    clearAll(state) { state.all = []; state.scamList = []; },
  },
});

// ── SETTINGS SLICE ───────────────────────────────────────────────────────────
const settingsSlice = createSlice({
  name: 'settings',
  initialState: {
    monitoring: {
      sms: true, whatsapp: true, instagram: true,
      facebook: true, linkedin: true, telegram: true,
      email: true, calls: true, apps: true, games: true,
    },
    notifications: {
      enabled: true, sound: true, vibrate: true, popup: true,
    },
    autoBlock: false,
    sensitivity: 'medium',  // low | medium | high
    darkMode: true,
    onboardingDone: false,
  },
  reducers: {
    toggleMonitoring(state, { payload: source }) {
      state.monitoring[source] = !state.monitoring[source];
    },
    toggleNotification(state, { payload: key }) {
      state.notifications[key] = !state.notifications[key];
    },
    toggleAutoBlock(state) { state.autoBlock = !state.autoBlock; },
    setSensitivity(state, { payload }) { state.sensitivity = payload; },
    toggleDarkMode(state) { state.darkMode = !state.darkMode; },
    completeOnboarding(state) { state.onboardingDone = true; },
  },
});

// ── STATS SLICE ──────────────────────────────────────────────────────────────
const statsSlice = createSlice({
  name: 'stats',
  initialState: {
    totalScanned: 0, totalBlocked: 0, totalSafe: 0,
    bySource: {}, byType: {}, byDay: [],
    trainProgress: 0,
  },
  reducers: {
    incrementScanned(state, { payload: { source, verdict, type } }) {
      state.totalScanned++;
      if (verdict !== 'SAFE') { state.totalBlocked++; }
      else state.totalSafe++;
      state.bySource[source] = (state.bySource[source] || 0) + 1;
      if (type) state.byType[type] = (state.byType[type] || 0) + 1;
      // Rolling daily stats
      const today = new Date().toLocaleDateString();
      const day = state.byDay.find(d => d.date === today);
      if (day) { day.scanned++; if (verdict !== 'SAFE') day.blocked++; }
      else state.byDay.push({ date: today, scanned: 1, blocked: verdict !== 'SAFE' ? 1 : 0 });
      if (state.byDay.length > 30) state.byDay.shift();
    },
    updateTrainProgress(state) {
      state.trainProgress = Math.min(100, state.trainProgress + 0.2);
    },
  },
});

// ── COMBINE & PERSIST ────────────────────────────────────────────────────────
const rootReducer = combineReducers({
  messages: messagesSlice.reducer,
  settings: settingsSlice.reducer,
  stats: statsSlice.reducer,
});

const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['messages', 'settings', 'stats'],
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({ serializableCheck: false }),
});

export const persistor = persistStore(store);
export const { addMessage, confirmScam, dismissScam, markNotScam, blockSender, unblockSender, whitelistSender, setFilter, clearAll } = messagesSlice.actions;
export const { toggleMonitoring, toggleNotification, toggleAutoBlock, setSensitivity, completeOnboarding } = settingsSlice.actions;
export const { incrementScanned, updateTrainProgress } = statsSlice.actions;
