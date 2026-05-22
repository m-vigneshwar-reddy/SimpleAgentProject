package com.scamshield.ml;

import android.content.Context;
import android.util.Log;

import java.util.*;
import java.util.regex.Pattern;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * ScamMLEngine — on-device ML/DL scam analysis engine.
 *
 * Implements a multi-model ensemble approach:
 *   1. NLP Keyword + Pattern Model (simulates TF-IDF + Logistic Regression)
 *   2. URL/Domain Reputation Model
 *   3. Sender Reputation Model
 *   4. Urgency/Pressure Language Model (simulates LSTM)
 *   5. Financial Bait Pattern Model
 *   6. Government Impersonation Detector (simulates BERT fine-tune)
 *
 * In production: integrate TensorFlow Lite models loaded from assets/
 * for the full Transformer-LSTM and BERT NLP models.
 */
public class ScamMLEngine {

    private static final String TAG = "ScamShield::ML";
    private static ScamMLEngine instance;

    private final AtomicInteger totalScanned = new AtomicInteger(0);
    private final AtomicInteger totalBlocked = new AtomicInteger(0);

    // ── SCAM KEYWORD LISTS ──────────────────────────────
    private static final Map<String, Integer> KEYWORD_WEIGHTS = new HashMap<String, Integer>() {{
        // High weight (clear scam signals)
        put("won", 15); put("lottery", 18); put("prize", 15);
        put("claim now", 20); put("click here", 12); put("verify account", 18);
        put("suspended", 16); put("frozen", 14); put("arrested", 20);
        put("otp", 10); put("share otp", 35); put("share your otp", 40);
        put("processing fee", 25); put("advance fee", 28);
        put("act now", 14); put("urgent", 10); put("immediately", 10);
        put("expire", 10); put("expires today", 18); put("limited time", 12);
        put("free money", 22); put("earn daily", 20); put("work from home", 10);
        put("no investment", 16); put("guaranteed", 12);
        put("0% interest", 18); put("zero interest", 16);
        put("government notice", 20); put("legal notice", 18);
        put("send to 10", 30); put("forward to", 12);
        put("congratulations", 12); put("selected", 8);
        put("kyc update", 22); put("kyc verification", 20);
        put("account blocked", 18); put("deactivated", 14);
        // Medium weight
        put("offer", 6); put("deal", 5); put("discount", 5);
        put("reward", 10); put("gift card", 14); put("voucher", 8);
        put("password", 8); put("login", 6); put("username", 6);
        put("bank details", 20); put("card number", 18); put("cvv", 22);
        put("aadhaar", 10); put("pan card", 10);
    }};

    private static final String[] PHISHING_DOMAINS = {
        "xyz", "tk", "ml", "ga", "cf", "click", "download", "free",
        "prize", "win", "claim", "verify", "secure-", "update-",
        "login-", "account-", "bank-", "-secure", "-verify", "-update"
    };

    private static final Pattern[] URL_PATTERNS = {
        Pattern.compile("http://[^\\s]+"),                           // HTTP (not HTTPS)
        Pattern.compile("https?://[^\\s]*\\.xyz[/\\s]"),            // .xyz domains
        Pattern.compile("https?://[^\\s]*\\.(tk|ml|ga|cf)[/\\s]"),  // Free TLDs
        Pattern.compile("bit\\.ly/[^\\s]+"),                         // URL shorteners
        Pattern.compile("tinyurl\\.com/[^\\s]+"),
        Pattern.compile("\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}"), // Raw IP URL
    };

    private static final String[] GOVERNMENT_IMPERSONATION = {
        "trai", "cbi", "police", "income tax", "irdai", "rbi",
        "sebi", "government of india", "ministry", "collector office",
        "cyber crime", "court notice", "fir registered"
    };

    private static final String[] BANK_IMPERSONATION = {
        "sbi", "hdfc", "icici", "axis", "kotak", "paytm",
        "phonepe", "google pay", "upi", "neft", "imps", "rtgs",
        "net banking", "mobile banking"
    };

    // Result class
    public static class Result {
        public String id;
        public int riskScore;       // 0-100
        public String verdict;      // SAFE, SUSPICIOUS, SCAM
        public String type;         // Phishing, Financial Fraud, etc.
        public List<String> reasons;
        public Map<String, Integer> modelScores;
        public long timestamp;
    }

    public static synchronized ScamMLEngine getInstance(Context ctx) {
        if (instance == null) instance = new ScamMLEngine(ctx);
        return instance;
    }

    private ScamMLEngine(Context ctx) {
        Log.d(TAG, "ML Engine initialised");
        // In production: load TFLite models from ctx.getAssets()
    }

    // ── MAIN ANALYSIS METHOD ──────────────────────────────
    public Result analyse(String text, String source, String sender) {
        totalScanned.incrementAndGet();

        Result result = new Result();
        result.id = UUID.randomUUID().toString();
        result.timestamp = System.currentTimeMillis();
        result.reasons = new ArrayList<>();
        result.modelScores = new HashMap<>();

        String lower = text.toLowerCase();
        int totalScore = 0;

        // 1. Keyword model
        int kwScore = keywordModel(lower, result.reasons);
        result.modelScores.put("Keyword NLP", kwScore);
        totalScore += kwScore * 0.25;

        // 2. URL/Phishing model
        int urlScore = urlModel(text, result.reasons);
        result.modelScores.put("URL Detector", urlScore);
        totalScore += urlScore * 0.20;

        // 3. Urgency/LSTM model
        int urgencyScore = urgencyModel(lower, result.reasons);
        result.modelScores.put("Urgency LSTM", urgencyScore);
        totalScore += urgencyScore * 0.15;

        // 4. Impersonation model (BERT-simulated)
        int impersonationScore = impersonationModel(lower, result.reasons);
        result.modelScores.put("BERT Impersonation", impersonationScore);
        totalScore += impersonationScore * 0.20;

        // 5. Financial bait model
        int finScore = financialBaitModel(lower, text, result.reasons);
        result.modelScores.put("Financial Bait", finScore);
        totalScore += finScore * 0.10;

        // 6. Sender reputation model
        int senderScore = senderModel(sender, source, result.reasons);
        result.modelScores.put("Sender Reputation", senderScore);
        totalScore += senderScore * 0.10;

        result.riskScore = Math.min(100, Math.max(0, (int) totalScore));
        result.type = classifyType(lower);

        if (result.riskScore >= 55) {
            result.verdict = "SCAM";
            totalBlocked.incrementAndGet();
        } else if (result.riskScore >= 25) {
            result.verdict = "SUSPICIOUS";
        } else {
            result.verdict = "SAFE";
        }

        Log.d(TAG, source + " message scored: " + result.riskScore + " → " + result.verdict);
        return result;
    }

    private int keywordModel(String lower, List<String> reasons) {
        int score = 0;
        List<String> hits = new ArrayList<>();
        for (Map.Entry<String, Integer> entry : KEYWORD_WEIGHTS.entrySet()) {
            if (lower.contains(entry.getKey())) {
                score += entry.getValue();
                hits.add(entry.getKey());
            }
        }
        if (!hits.isEmpty()) {
            String sample = hits.subList(0, Math.min(3, hits.size())).toString();
            reasons.add("🔑 Scam keywords detected: " + sample);
        }
        return Math.min(100, score);
    }

    private int urlModel(String text, List<String> reasons) {
        int score = 0;
        for (Pattern p : URL_PATTERNS) {
            if (p.matcher(text).find()) {
                score += 30;
                reasons.add("🔗 Suspicious URL or link detected");
                break;
            }
        }
        for (String domain : PHISHING_DOMAINS) {
            if (text.toLowerCase().contains(domain)) {
                score += 15;
                break;
            }
        }
        return Math.min(100, score);
    }

    private int urgencyModel(String lower, List<String> reasons) {
        String[] urgencyTerms = {"urgent", "immediately", "within 24", "24 hours",
            "expires", "act now", "limited time", "today only", "last chance",
            "final warning", "2 hours", "10 minutes", "right now"};
        int hits = 0;
        for (String term : urgencyTerms) {
            if (lower.contains(term)) hits++;
        }
        if (hits > 0) reasons.add("⏰ High pressure / urgency language (" + hits + " signals)");
        return Math.min(100, hits * 18);
    }

    private int impersonationModel(String lower, List<String> reasons) {
        int score = 0;
        for (String term : GOVERNMENT_IMPERSONATION) {
            if (lower.contains(term)) {
                score += 25;
                reasons.add("🏛️ Government agency impersonation: " + term.toUpperCase());
                break;
            }
        }
        for (String term : BANK_IMPERSONATION) {
            if (lower.contains(term)) {
                score += 15;
                reasons.add("🏦 Bank/payment service impersonation detected");
                break;
            }
        }
        return Math.min(100, score);
    }

    private int financialBaitModel(String lower, String original, List<String> reasons) {
        int score = 0;
        if (Pattern.compile("[₹$]\\d").matcher(original).find()) {
            score += 15;
            reasons.add("💰 Financial amount reference detected");
        }
        if (lower.contains("processing fee") || lower.contains("registration fee")) {
            score += 30;
            reasons.add("💳 Upfront fee request — classic fraud pattern");
        }
        if (lower.contains("transfer") && lower.contains("account")) {
            score += 20;
            reasons.add("🔄 Account transfer request detected");
        }
        return Math.min(100, score);
    }

    private int senderModel(String sender, String source, List<String> reasons) {
        if (sender == null) return 0;
        int score = 0;
        String s = sender.toLowerCase();
        // Unknown/private number
        if (s.contains("private") || s.contains("unknown") || s.isEmpty()) {
            score += 20;
            reasons.add("📵 Private or unknown sender");
        }
        // Suspicious email domains
        if (s.contains("@") && (s.endsWith(".xyz") || s.endsWith(".tk") || s.contains("-alert") || s.contains("-verify"))) {
            score += 25;
            reasons.add("📧 Suspicious sender domain");
        }
        // Look-alike domains
        if (s.matches(".*(sbi|hdfc|icici|paytm|amazon|flipkart).*\\.(com|in).*") && !s.endsWith(".com") && !s.endsWith(".in")) {
            score += 30;
            reasons.add("🎭 Look-alike/spoofed sender address");
        }
        return Math.min(100, score);
    }

    private String classifyType(String lower) {
        if (lower.contains("otp") || lower.contains("verify") || lower.contains("account") || lower.contains("password"))
            return "Phishing";
        if (lower.contains("loan") || lower.contains("earn") || lower.contains("upi") || lower.contains("transfer") || lower.contains("fee"))
            return "Financial Fraud";
        if (lower.contains("aadhaar") || lower.contains("pan") || lower.contains("trai") || lower.contains("cbi") || lower.contains("police"))
            return "Identity Theft";
        if (lower.contains("prize") || lower.contains("won") || lower.contains("lottery") || lower.contains("gift") || lower.contains("reward"))
            return "Prize Scam";
        if (lower.contains("job") || lower.contains("work from home") || lower.contains("earn daily"))
            return "Job Scam";
        return "Unknown Scam";
    }

    public int getTotalScanned() { return totalScanned.get(); }
    public int getTotalBlocked() { return totalBlocked.get(); }
}
