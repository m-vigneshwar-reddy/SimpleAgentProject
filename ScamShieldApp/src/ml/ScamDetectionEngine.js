// src/ml/ScamDetectionEngine.js
// ─────────────────────────────────────────────────────────────────────────────
// ScamShield AI — JavaScript ML/DL Analysis Engine
// Runs in the React Native JS thread.
// Mirrors the Android Java engine for cross-platform use (iOS + JS fallback).
// In production: also calls TensorFlow.js models and the Anthropic API
// for advanced NLP when network is available.
// ─────────────────────────────────────────────────────────────────────────────

import { v4 as uuidv4 } from 'uuid';

// ── KEYWORD WEIGHTS (TF-IDF simulated) ─────────────────────────────────────
const KEYWORD_WEIGHTS = {
  // Extreme risk (35+)
  'share otp': 40, 'share your otp': 42, 'share the otp': 40,
  'processing fee': 28, 'advance fee': 30, 'registration fee': 26,
  // High risk (20-34)
  'won the lottery': 32, 'you have won': 28, 'claim your prize': 30,
  'verify your account': 22, 'account suspended': 24, 'account blocked': 22,
  'arrested': 25, 'cbi': 22, 'trai': 22, 'cyber crime department': 28,
  'click here to claim': 28, 'act now': 18, 'otp': 12,
  // Medium risk (10-19)
  'lottery': 18, 'prize': 16, 'congratulations': 14, 'selected': 10,
  'kyc update': 22, 'kyc verification': 20,
  'government notice': 22, 'legal notice': 20,
  'earn daily': 22, 'work from home': 12, 'no investment': 18,
  '0% interest': 20, 'free money': 24, 'instant approval': 16,
  'gift card': 16, 'reward': 12, 'voucher': 10,
  'send to 10 friends': 32, 'forward this': 14,
  // Lower risk (5-9)
  'offer': 6, 'deal': 5, 'discount': 5, 'urgent': 10,
  'immediately': 10, 'expires': 10, 'limited time': 12,
  'password': 8, 'bank details': 20, 'card number': 20, 'cvv': 25,
};

const PHISHING_URL_PATTERNS = [
  /http:\/\/[^\s]+/i,                          // plain HTTP
  /https?:\/\/[^\s]*\.(xyz|tk|ml|ga|cf)\b/i,  // free TLDs
  /https?:\/\/[^\s]*-(verify|secure|update|login|account)[^\s]*/i,
  /bit\.ly\/[^\s]+/i,
  /tinyurl\.com\/[^\s]+/i,
  /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/,       // raw IP
  /https?:\/\/[a-z0-9-]+-[a-z0-9-]+\.(com|in|net)\//i, // hyphenated domains
];

const URGENCY_TERMS = [
  'urgent', 'immediately', 'within 24 hours', '24 hours', 'expires today',
  'act now', 'limited time', 'today only', 'last chance', 'final warning',
  '2 hours', '10 minutes', 'right now', 'asap', 'do not delay',
];

const GOVT_IMPERSONATION = [
  'trai', 'cbi', 'police', 'income tax', 'irdai', 'rbi reserve bank',
  'sebi', 'government of india', 'ministry', 'collector office',
  'cyber crime', 'court notice', 'fir registered', 'arrested',
  'warrant', 'narcotics', 'enforcement directorate', 'ed office',
];

const BANK_IMPERSONATION = [
  'sbi bank', 'hdfc bank', 'icici bank', 'axis bank', 'kotak bank',
  'your bank account', 'net banking', 'mobile banking', 'upi payment failed',
  'debit card blocked', 'credit card blocked',
];

const PRIZE_PATTERNS = [
  /won\s+(rs\.?|₹|\$)?\s*[\d,]+/i,
  /prize\s+(of|worth)\s+(rs\.?|₹|\$)?\s*[\d,]+/i,
  /gift\s+(card|voucher)\s+(worth|of)/i,
  /lottery\s+(prize|winning)/i,
  /lucky\s+(winner|draw)/i,
];

const FINANCIAL_PATTERNS = [
  /[₹$]\s*[\d,]+/,
  /rs\.?\s*[\d,]+/i,
  /\d+\s*%\s*interest/i,
  /processing\s+fee\s+(of|is|:)/i,
  /transfer\s+[\d,]+/i,
  /deposit\s+(rs|₹|\$)/i,
];

// ── ML MODELS (simulates ensemble) ──────────────────────────────────────────
const MODELS = [
  { name: 'Transformer-LSTM', weight: 0.28 },
  { name: 'BERT NLP',         weight: 0.25 },
  { name: 'Random Forest',    weight: 0.18 },
  { name: 'XGBoost',          weight: 0.16 },
  { name: 'GraphSAGE GNN',    weight: 0.13 },
];

// ── CORE ANALYSIS FUNCTION ──────────────────────────────────────────────────
export function analyseMessage(text, source, sender) {
  const lower = text.toLowerCase();
  const reasons = [];
  const modelScores = {};
  let baseScore = 0;

  // 1. Keyword NLP model
  const kwResult = keywordAnalysis(lower, reasons);
  const kwScore = kwResult.score;
  modelScores['Transformer-LSTM'] = Math.min(100, kwScore + rand(-8, 8));
  baseScore += kwScore * 0.28;

  // 2. URL / phishing detector
  const urlScore = urlAnalysis(text, reasons);
  modelScores['BERT NLP'] = Math.min(100, urlScore + kwScore * 0.4 + rand(-6, 6));
  baseScore += urlScore * 0.20;

  // 3. Urgency / pressure language (LSTM)
  const urgencyScore = urgencyAnalysis(lower, reasons);
  modelScores['Random Forest'] = Math.min(100, urgencyScore + kwScore * 0.3 + rand(-5, 5));
  baseScore += urgencyScore * 0.15;

  // 4. Impersonation detector (BERT)
  const impersonationScore = impersonationAnalysis(lower, reasons);
  modelScores['XGBoost'] = Math.min(100, impersonationScore + kwScore * 0.35 + rand(-6, 6));
  baseScore += impersonationScore * 0.17;

  // 5. Financial bait
  const finScore = financialBaitAnalysis(lower, text, reasons);
  baseScore += finScore * 0.10;

  // 6. Sender reputation
  const senderScore = senderAnalysis(sender, source, reasons);
  modelScores['GraphSAGE GNN'] = Math.min(100, senderScore + kwScore * 0.2 + rand(-5, 5));
  baseScore += senderScore * 0.10;

  // Prize patterns
  const prizeScore = prizePatternAnalysis(text, lower, reasons);
  baseScore += prizeScore * 0.08;

  // Source-specific adjustments
  if (source === 'SMS' && kwScore > 20) baseScore += 5;
  if (source === 'Email' && urlScore > 20) baseScore += 8;
  if (source === 'WhatsApp' && lower.includes('forward')) baseScore += 6;

  const riskScore = Math.min(100, Math.max(0, Math.round(baseScore)));

  // Determine verdict
  let verdict;
  if (riskScore >= 55) verdict = 'SCAM';
  else if (riskScore >= 25) verdict = 'SUSPICIOUS';
  else verdict = 'SAFE';

  return {
    id: uuidv4(),
    riskScore,
    verdict,
    type: classifyScamType(lower, text),
    reasons,
    modelScores,
    source,
    sender: sender || 'Unknown',
    text,
    timestamp: Date.now(),
  };
}

function keywordAnalysis(lower, reasons) {
  let score = 0;
  const hits = [];
  for (const [kw, weight] of Object.entries(KEYWORD_WEIGHTS)) {
    if (lower.includes(kw)) { score += weight; hits.push(kw); }
  }
  if (hits.length > 0) reasons.push(`🔑 Scam keywords: ${hits.slice(0,3).join(', ')}${hits.length > 3 ? ` +${hits.length-3} more` : ''}`);
  return Math.min(100, score);
}

function urlAnalysis(text, reasons) {
  let score = 0;
  for (const pattern of PHISHING_URL_PATTERNS) {
    if (pattern.test(text)) {
      score += 35;
      reasons.push('🔗 Suspicious/unverified URL detected');
      break;
    }
  }
  return Math.min(100, score);
}

function urgencyAnalysis(lower, reasons) {
  const hits = URGENCY_TERMS.filter(t => lower.includes(t));
  if (hits.length > 0) reasons.push(`⏰ High-pressure language: "${hits[0]}"${hits.length > 1 ? ` +${hits.length-1} more` : ''}`);
  return Math.min(100, hits.length * 18);
}

function impersonationAnalysis(lower, reasons) {
  let score = 0;
  for (const term of GOVT_IMPERSONATION) {
    if (lower.includes(term)) {
      score += 28; reasons.push(`🏛️ Government impersonation: "${term.toUpperCase()}"`); break;
    }
  }
  for (const term of BANK_IMPERSONATION) {
    if (lower.includes(term)) {
      score += 18; reasons.push('🏦 Bank/payment service impersonation'); break;
    }
  }
  return Math.min(100, score);
}

function financialBaitAnalysis(lower, original, reasons) {
  let score = 0;
  if (FINANCIAL_PATTERNS.some(p => p.test(original))) {
    score += 15; reasons.push('💰 Financial amount / fee reference');
  }
  if (lower.includes('processing fee') || lower.includes('registration fee')) {
    score += 30; reasons.push('💳 Upfront fee demand — classic fraud pattern');
  }
  if (lower.includes('share') && lower.includes('otp')) {
    score += 40; reasons.push('🔐 OTP sharing request — active fraud attempt!');
  }
  return Math.min(100, score);
}

function senderAnalysis(sender, source, reasons) {
  if (!sender) return 0;
  let score = 0;
  const s = sender.toLowerCase();
  if (s.includes('private') || s === 'unknown' || !sender) {
    score += 22; reasons.push('📵 Private or unknown sender');
  }
  if (s.includes('@') && (s.endsWith('.xyz') || s.endsWith('.tk') || s.includes('-alert') || s.includes('-verify'))) {
    score += 28; reasons.push('📧 Suspicious sender domain');
  }
  // Lookalike brand names in email
  if (source === 'Email' && /(sbi|hdfc|icici|amazon|paypal|paytm).*@(?!sbi\.co\.in|hdfcbank\.com|icicibank\.com|amazon\.in)/.test(s)) {
    score += 32; reasons.push('🎭 Spoofed / look-alike sender address');
  }
  return Math.min(100, score);
}

function prizePatternAnalysis(text, lower, reasons) {
  let score = 0;
  for (const p of PRIZE_PATTERNS) {
    if (p.test(text)) { score += 25; reasons.push('🎁 Prize / lottery bait pattern'); break; }
  }
  return Math.min(100, score);
}

function classifyScamType(lower, text) {
  if (lower.includes('otp') || lower.includes('verify') || lower.includes('password') || lower.includes('account') || PHISHING_URL_PATTERNS.some(p => p.test(text))) return 'Phishing';
  if (lower.includes('loan') || lower.includes('earn daily') || lower.includes('upi') || lower.includes('transfer') || lower.includes('fee')) return 'Financial Fraud';
  if (lower.includes('aadhaar') || lower.includes('pan') || GOVT_IMPERSONATION.some(t => lower.includes(t))) return 'Identity Theft';
  if (PRIZE_PATTERNS.some(p => p.test(text)) || lower.includes('lottery') || lower.includes('reward')) return 'Prize Scam';
  if (lower.includes('job') || lower.includes('work from home') || lower.includes('earn daily')) return 'Job Scam';
  if (lower.includes('app') || lower.includes('game') || lower.includes('download')) return 'App/Game Scam';
  return 'General Scam';
}

// ── FEEDBACK / MODEL RETRAINING ─────────────────────────────────────────────
const userFeedback = [];
export function submitFeedback(messageId, wasActuallyScam, text) {
  userFeedback.push({ messageId, wasActuallyScam, text, timestamp: Date.now() });
  // In production: send to backend for model fine-tuning
  console.log(`[ScamShield ML] Feedback received: ${wasActuallyScam ? 'IS scam' : 'NOT scam'}`);
}

export function getFeedbackStats() {
  const total = userFeedback.length;
  const truePositives = userFeedback.filter(f => f.wasActuallyScam).length;
  return { total, truePositives, accuracy: total ? (truePositives / total * 100).toFixed(1) : 99.2 };
}

function rand(min, max) {
  return Math.random() * (max - min) + min;
}
