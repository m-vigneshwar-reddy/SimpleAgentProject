// server/emailConnector.js
// ─────────────────────────────────────────────────────────────────────────────
//  Real Email Connector — connects to your actual Gmail / Outlook / Yahoo
//  inbox via IMAP and streams new emails in real time to the ML engine.
//
//  Uses IMAP (Internet Message Access Protocol) — the same protocol your
//  email app uses to fetch messages from the server.
// ─────────────────────────────────────────────────────────────────────────────

const Imap       = require('imap');
const { simpleParser } = require('mailparser');
require('dotenv').config();

// ── IMAP SERVER CONFIG PER PROVIDER ──────────────────────────────────────────
const IMAP_CONFIGS = {
  gmail: {
    host: 'imap.gmail.com',
    port: 993,
    tls: true,
    label: 'Gmail',
  },
  outlook: {
    host: 'outlook.office365.com',
    port: 993,
    tls: true,
    label: 'Outlook / Hotmail',
  },
  yahoo: {
    host: 'imap.mail.yahoo.com',
    port: 993,
    tls: true,
    label: 'Yahoo Mail',
  },
  zoho: {
    host: 'imap.zoho.com',
    port: 993,
    tls: true,
    label: 'Zoho Mail',
  },
  custom: {
    host: process.env.CUSTOM_IMAP_HOST || 'imap.yourprovider.com',
    port: parseInt(process.env.CUSTOM_IMAP_PORT) || 993,
    tls: true,
    label: 'Custom Mail',
  },
};

class EmailConnector {
  constructor(onEmailReceived, onStatusChange) {
    this.onEmailReceived = onEmailReceived;   // callback: called with parsed email
    this.onStatusChange  = onStatusChange;    // callback: called with status updates
    this.imap            = null;
    this.isConnected     = false;
    this.reconnectTimer  = null;
    this.pollTimer       = null;
    this.seenUIDs        = new Set();         // track emails we already processed
    this.provider        = (process.env.EMAIL_PROVIDER || 'gmail').toLowerCase();
    this.email           = process.env.EMAIL_ADDRESS;
    this.password        = process.env.EMAIL_APP_PASSWORD;
    this.folder          = process.env.EMAIL_FOLDER || 'INBOX';
    this.pollInterval    = parseInt(process.env.POLL_INTERVAL || '30') * 1000;
  }

  // ── PUBLIC: START MONITORING ────────────────────────────────────────────────
  start() {
    if (!this.email || !this.password ||
        this.email === 'yourname@gmail.com' ||
        this.password === 'your-app-password-here') {
      this.onStatusChange({
        connected: false,
        error: true,
        message: 'Please fill in your email credentials in the .env file first.',
        setupRequired: true,
      });
      return;
    }
    console.log(`[ScamShield] Connecting to ${this.email} via ${this.provider}…`);
    this.onStatusChange({ connected: false, connecting: true, message: `Connecting to ${this.email}…` });
    this._connect();
  }

  stop() {
    clearTimeout(this.reconnectTimer);
    clearInterval(this.pollTimer);
    if (this.imap) {
      try { this.imap.end(); } catch(e) {}
    }
    this.isConnected = false;
  }

  // ── INTERNAL: CONNECT VIA IMAP ──────────────────────────────────────────────
  _connect() {
    const config = IMAP_CONFIGS[this.provider] || IMAP_CONFIGS.gmail;

    this.imap = new Imap({
      user:     this.email,
      password: this.password,
      host:     config.host,
      port:     config.port,
      tls:      config.tls,
      tlsOptions: { rejectUnauthorized: false, servername: config.host },
      keepalive: {
        interval:  10000,   // send keepalive every 10s
        idleInterval: 300000,
        forceNoop: true,
      },
      connTimeout: 30000,
      authTimeout: 15000,
    });

    // ── EVENT: CONNECTED ─────────────────────────────────────────────────────
    this.imap.once('ready', () => {
      console.log(`[ScamShield] ✓ Connected to ${this.email}`);
      this.isConnected = true;

      this.onStatusChange({
        connected: true,
        email: this.email,
        provider: config.label,
        message: `Connected to ${this.email} — monitoring ${this.folder}`,
      });

      this._openInbox();
    });

    // ── EVENT: ERROR ─────────────────────────────────────────────────────────
    this.imap.once('error', (err) => {
      console.error('[ScamShield] IMAP error:', err.message);
      this.isConnected = false;

      let friendlyError = err.message;
      if (err.message.includes('Invalid credentials') || err.message.includes('AUTHENTICATIONFAILED')) {
        friendlyError = 'Wrong email or app password. Check your .env file.';
      } else if (err.message.includes('ENOTFOUND') || err.message.includes('getaddrinfo')) {
        friendlyError = 'Cannot reach mail server. Check your internet connection.';
      } else if (err.message.includes('ECONNREFUSED')) {
        friendlyError = 'Connection refused by mail server.';
      }

      this.onStatusChange({ connected: false, error: true, message: friendlyError });
      this._scheduleReconnect();
    });

    // ── EVENT: DISCONNECTED ──────────────────────────────────────────────────
    this.imap.once('end', () => {
      console.log('[ScamShield] IMAP connection ended');
      this.isConnected = false;
      clearInterval(this.pollTimer);
      if (!this._stopping) {
        this.onStatusChange({ connected: false, message: 'Disconnected — reconnecting…' });
        this._scheduleReconnect();
      }
    });

    this.imap.connect();
  }

  // ── OPEN INBOX AND START MONITORING ─────────────────────────────────────────
  _openInbox() {
    this.imap.openBox(this.folder, false, (err, box) => {
      if (err) {
        console.error('[ScamShield] Cannot open inbox:', err.message);
        this.onStatusChange({ connected: false, error: true, message: `Cannot open ${this.folder}: ${err.message}` });
        return;
      }

      console.log(`[ScamShield] Inbox opened — ${box.messages.total} total messages`);

      // Fetch the 10 most recent emails on startup
      this._fetchRecentEmails(10);

      // Listen for NEW emails arriving in real time (IMAP IDLE / push)
      this.imap.on('mail', (numNewMsgs) => {
        console.log(`[ScamShield] ${numNewMsgs} new email(s) arrived!`);
        this._fetchNewEmails();
      });

      // Also poll every N seconds as a fallback (some servers don't push)
      clearInterval(this.pollTimer);
      this.pollTimer = setInterval(() => {
        if (this.isConnected) this._fetchNewEmails();
      }, this.pollInterval);

      this.onStatusChange({
        connected: true,
        email:    this.email,
        provider: IMAP_CONFIGS[this.provider]?.label || this.provider,
        folder:   this.folder,
        total:    box.messages.total,
        message:  `Monitoring ${this.email} — ${box.messages.total} emails in inbox`,
      });
    });
  }

  // ── FETCH RECENT EMAILS (initial load) ──────────────────────────────────────
  _fetchRecentEmails(count) {
    this.imap.search(['ALL'], (err, uids) => {
      if (err || !uids || uids.length === 0) return;

      // Take last N UIDs
      const recentUIDs = uids.slice(-count);
      recentUIDs.forEach(uid => this.seenUIDs.add(uid)); // mark as seen so we don't re-alert on startup

      const fetch = this.imap.fetch(recentUIDs, { bodies: '', struct: true });
      fetch.on('message', (msg) => this._parseMessage(msg, false)); // false = no alert for old emails
      fetch.once('error', (e) => console.error('[ScamShield] Fetch error:', e.message));
    });
  }

  // ── FETCH NEW UNSEEN EMAILS ──────────────────────────────────────────────────
  _fetchNewEmails() {
    this.imap.search(['UNSEEN'], (err, uids) => {
      if (err || !uids || uids.length === 0) return;

      // Only process UIDs we haven't seen yet
      const newUIDs = uids.filter(uid => !this.seenUIDs.has(uid));
      if (newUIDs.length === 0) return;

      console.log(`[ScamShield] ${newUIDs.length} new unseen email(s) to analyse`);
      newUIDs.forEach(uid => this.seenUIDs.add(uid));

      const fetch = this.imap.fetch(newUIDs, { bodies: '', struct: true, markSeen: false });
      fetch.on('message', (msg) => this._parseMessage(msg, true)); // true = fire alert
      fetch.once('error', (e) => console.error('[ScamShield] Fetch error:', e.message));
    });
  }

  // ── PARSE A RAW EMAIL MESSAGE ────────────────────────────────────────────────
  _parseMessage(msg, triggerAlert) {
    let buffer = '';
    let uid    = null;

    msg.on('attributes', (attrs) => { uid = attrs.uid; });

    msg.on('body', (stream) => {
      stream.on('data',  (chunk) => { buffer += chunk.toString('utf8'); });
      stream.once('end', async () => {
        try {
          const parsed = await simpleParser(buffer);

          // Extract clean email fields
          const from    = parsed.from?.text || 'Unknown';
          const subject = parsed.subject    || '(No Subject)';
          const body    = parsed.text       || parsed.html?.replace(/<[^>]+>/g, ' ') || '';
          const date    = parsed.date       || new Date();
          const to      = parsed.to?.text   || '';

          // Build the full text the ML engine will analyse
          // Subject carries a lot of scam signals so we weight it heavily
          const fullText = `Subject: ${subject}\n\nFrom: ${from}\n\n${body}`.trim();

          // Build clean email object
          const email = {
            uid,
            source:   'Email',
            sender:   from,
            to,
            subject,
            body:     body.slice(0, 2000), // cap at 2000 chars
            text:     fullText.slice(0, 3000),
            date:     date.toLocaleString(),
            receivedAt: new Date().toLocaleTimeString(),
            triggerAlert,
          };

          console.log(`[ScamShield] Email from: ${from} | Subject: ${subject.slice(0,50)}`);
          this.onEmailReceived(email);

        } catch (parseErr) {
          console.error('[ScamShield] Parse error:', parseErr.message);
        }
      });
    });
  }

  // ── RECONNECT AFTER FAILURE ──────────────────────────────────────────────────
  _scheduleReconnect() {
    clearTimeout(this.reconnectTimer);
    console.log('[ScamShield] Reconnecting in 15 seconds…');
    this.reconnectTimer = setTimeout(() => {
      if (!this.isConnected) this._connect();
    }, 15000);
  }

  getStatus() {
    return {
      connected: this.isConnected,
      email:     this.email,
      provider:  this.provider,
      folder:    this.folder,
    };
  }
}

module.exports = EmailConnector;
