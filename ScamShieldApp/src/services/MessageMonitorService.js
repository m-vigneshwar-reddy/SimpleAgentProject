// src/services/MessageMonitorService.js
// ─────────────────────────────────────────────────────────────────────────────
// Real-Time Message Monitor
// Bridges the Android native receivers to the JS ML engine.
// Listens to native events: SMS, Notifications (WhatsApp/Instagram/etc), Calls
// Runs analyseMessage() on every incoming item immediately.
// ─────────────────────────────────────────────────────────────────────────────

import { NativeEventEmitter, NativeModules, Platform, AppState } from 'react-native';
import PushNotification from 'react-native-push-notification';
import { store } from '../store';
import { addMessage, blockSender } from '../store';
import { incrementScanned, updateTrainProgress } from '../store';
import { analyseMessage, submitFeedback } from '../ml/ScamDetectionEngine';

const { ScamShieldModule } = NativeModules;

class MessageMonitorService {
  constructor() {
    this.emitter = null;
    this.subscriptions = [];
    this.isRunning = false;
    this.callbacks = [];
    this.processedIds = new Set(); // deduplicate
  }

  // ── INIT ──────────────────────────────────────────────────────────────────
  start() {
    if (this.isRunning) return;
    this.isRunning = true;
    console.log('[ScamShield] Monitor service starting…');

    if (Platform.OS === 'android' && ScamShieldModule) {
      this.emitter = new NativeEventEmitter(ScamShieldModule);
      this._listenToSMS();
      this._listenToNotifications();
      this._listenToCalls();
      this._listenToAppData();
    }

    this._configurePushNotifications();
    console.log('[ScamShield] Monitor service active ✓');
  }

  stop() {
    this.subscriptions.forEach(sub => sub.remove());
    this.subscriptions = [];
    this.isRunning = false;
  }

  // ── SMS LISTENER ─────────────────────────────────────────────────────────
  _listenToSMS() {
    const sub = this.emitter.addListener('onIncomingMessage', (data) => {
      if (data.source === 'SMS') {
        this._processIncoming(data);
      }
    });
    this.subscriptions.push(sub);
    console.log('[ScamShield] SMS listener active');
  }

  // ── NOTIFICATION LISTENER (WhatsApp, Instagram, Facebook, LinkedIn, etc) ──
  _listenToNotifications() {
    const sub = this.emitter.addListener('onIncomingMessage', (data) => {
      if (data.source !== 'SMS' && data.source !== 'Call') {
        this._processIncoming(data);
      }
    });
    this.subscriptions.push(sub);
    console.log('[ScamShield] Notification listener active');
  }

  // ── CALL LISTENER ────────────────────────────────────────────────────────
  _listenToCalls() {
    const callSub = this.emitter.addListener('onIncomingCall', (data) => {
      const settings = store.getState().settings;
      if (!settings.monitoring.calls) return;
      this._processIncoming({
        ...data,
        source: 'Call',
        text: data.text || `Incoming call from ${data.sender}`,
      });
    });
    this.subscriptions.push(callSub);
    console.log('[ScamShield] Call listener active');
  }

  // ── APP DATA / GAME FEEDBACK LISTENER ────────────────────────────────────
  _listenToAppData() {
    // Listens for notifications from games and apps (fake reward pop-ups etc.)
    const sub = this.emitter.addListener('onIncomingMessage', (data) => {
      if (data.source && !['SMS','Call','WhatsApp','Instagram','Facebook','LinkedIn',
          'Telegram','Gmail','Outlook'].includes(data.source)) {
        this._processIncoming({ ...data, source: data.source || 'App' });
      }
    });
    this.subscriptions.push(sub);
  }

  // ── CORE PROCESSING PIPELINE ──────────────────────────────────────────────
  async _processIncoming(rawData) {
    // Deduplicate
    if (!rawData.id || this.processedIds.has(rawData.id)) return;
    this.processedIds.add(rawData.id);
    if (this.processedIds.size > 1000) {
      const arr = [...this.processedIds];
      this.processedIds = new Set(arr.slice(arr.length - 500));
    }

    const { settings } = store.getState();

    // Check if monitoring is enabled for this source
    const sourceKey = this._sourceKey(rawData.source);
    if (sourceKey && !settings.monitoring[sourceKey]) return;

    // Check if sender is whitelisted
    const { whitelistedSenders } = store.getState().messages;
    if (whitelistedSenders.includes(rawData.sender)) return;

    // ── RUN ML ANALYSIS ────────────────────────────────────────────────────
    const analysis = analyseMessage(rawData.text, rawData.source, rawData.sender);

    const message = {
      ...rawData,
      ...analysis,
      receivedAt: new Date().toLocaleTimeString(),
    };

    // Check blocked senders
    const { blockedSenders } = store.getState().messages;
    if (blockedSenders.includes(rawData.sender)) {
      message.autoBlocked = true;
    }

    // Auto-block if enabled and SCAM verdict
    if (settings.autoBlock && analysis.verdict === 'SCAM') {
      store.dispatch(blockSender(rawData.sender));
      message.autoBlocked = true;
    }

    // Update Redux store
    store.dispatch(addMessage(message));
    store.dispatch(incrementScanned({
      source: rawData.source,
      verdict: analysis.verdict,
      type: analysis.type,
    }));
    store.dispatch(updateTrainProgress());

    // ── FIRE NOTIFICATION IF SCAM ──────────────────────────────────────────
    if ((analysis.verdict === 'SCAM' || analysis.verdict === 'SUSPICIOUS')
        && settings.notifications.enabled) {
      this._sendScamNotification(message);
    }

    // Notify in-app callbacks (for live feed)
    this.callbacks.forEach(cb => cb(message));
  }

  // ── PUSH NOTIFICATION FOR SCAM ───────────────────────────────────────────
  _sendScamNotification(msg) {
    const isHighRisk = msg.verdict === 'SCAM';
    const preview = msg.text.length > 100 ? msg.text.slice(0, 100) + '…' : msg.text;

    PushNotification.localNotification({
      channelId: 'scamshield_alerts',
      title: isHighRisk
        ? `🚨 Scam Detected — ${msg.source}`
        : `⚠️ Suspicious Message — ${msg.source}`,
      message: `From: ${msg.sender}\n${preview}`,
      bigText: `From: ${msg.sender}\n\n${msg.text}\n\nRisk Score: ${msg.riskScore}/100\nType: ${msg.type}`,
      color: isHighRisk ? '#FF4757' : '#FF9F43',
      vibrate: true,
      vibration: 500,
      priority: 'high',
      importance: 'high',
      actions: ['✅ Not a Scam', '🗑 Remove', '🔍 View Details'],
      userInfo: { messageId: msg.id },
    });
  }

  // ── CONFIGURE PUSH NOTIFICATIONS ─────────────────────────────────────────
  _configurePushNotifications() {
    PushNotification.configure({
      onAction: (notification) => {
        const { messageId } = notification.userInfo || {};
        if (!messageId) return;
        if (notification.action === '✅ Not a Scam') {
          store.dispatch(require('../store').markNotScam(messageId));
          submitFeedback(messageId, false);
        }
      },
      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });

    PushNotification.createChannel({
      channelId: 'scamshield_alerts',
      channelName: 'ScamShield Alerts',
      channelDescription: 'Scam and fraud detection alerts',
      importance: 5,
      vibrate: true,
    });
  }

  _sourceKey(source) {
    const map = {
      'SMS': 'sms', 'WhatsApp': 'whatsapp', 'Instagram': 'instagram',
      'Facebook': 'facebook', 'LinkedIn': 'linkedin', 'Telegram': 'telegram',
      'Gmail': 'email', 'Outlook': 'email', 'Call': 'calls',
    };
    return map[source] || 'apps';
  }

  onMessage(callback) { this.callbacks.push(callback); }
  offMessage(callback) { this.callbacks = this.callbacks.filter(c => c !== callback); }
}

export default new MessageMonitorService();
