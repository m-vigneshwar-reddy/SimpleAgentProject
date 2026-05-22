package com.scamshield.services;

import android.app.Notification;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.util.Log;

import com.facebook.react.bridge.Arguments;
import com.facebook.react.bridge.WritableMap;
import com.scamshield.utils.EventEmitter;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/**
 * NotificationListenerService — captures notifications from ALL apps in real time.
 *
 * Monitored apps include:
 *   WhatsApp, Instagram, Facebook, LinkedIn, Telegram, Signal,
 *   Twitter/X, Snapchat, Gmail, Outlook, banking apps, game apps, etc.
 *
 * User must grant "Notification Access" in device settings.
 * This is the core real-time data pipeline for the scam detection engine.
 */
public class ScamNotificationListenerService extends NotificationListenerService {

    private static final String TAG = "ScamShield::Notif";

    // Monitored social / messaging app packages
    private static final Set<String> MONITORED_PACKAGES = new HashSet<>(Arrays.asList(
        // Messaging
        "com.whatsapp",
        "com.whatsapp.w4b",
        "org.telegram.messenger",
        "org.thoughtcrime.securesms",         // Signal
        "com.snapchat.android",
        "com.viber.voip",
        "com.skype.raider",
        // Social
        "com.instagram.android",
        "com.facebook.katana",
        "com.facebook.lite",
        "com.linkedin.android",
        "com.twitter.android",
        "com.reddit.frontpage",
        "com.pinterest",
        "com.tiktok.android",
        // Email
        "com.google.android.gm",              // Gmail
        "com.microsoft.office.outlook",
        "com.yahoo.mobile.client.android.mail",
        "com.zoho.mail",
        // Banking
        "com.sbi.SBIFreedomPlus",
        "com.hdfc.app",
        "com.axis.mobile",
        "com.icici.ibank",
        "net.one97.paytm",
        "com.google.android.apps.nbu.paisa.user", // Google Pay
        "com.phonepe.app",
        "in.amazon.mShop.android.shopping",   // Amazon Pay
        // Shopping
        "com.flipkart.android",
        "com.amazon.mShop.android.shopping",
        // Games (in-app scam ads / fake rewards)
        "com.gameloft",
        "com.kiloo.subwaysurf",
        // SMS apps
        "com.google.android.apps.messaging",
        "com.samsung.android.messaging"
    ));

    // App display names for better UX
    private static final java.util.Map<String, String> APP_NAMES = new java.util.HashMap<String, String>() {{
        put("com.whatsapp", "WhatsApp");
        put("com.instagram.android", "Instagram");
        put("com.facebook.katana", "Facebook");
        put("com.linkedin.android", "LinkedIn");
        put("org.telegram.messenger", "Telegram");
        put("com.google.android.gm", "Gmail");
        put("com.microsoft.office.outlook", "Outlook");
        put("com.snapchat.android", "Snapchat");
        put("com.twitter.android", "Twitter/X");
        put("net.one97.paytm", "Paytm");
        put("com.google.android.apps.nbu.paisa.user", "Google Pay");
        put("com.phonepe.app", "PhonePe");
        put("com.sbi.SBIFreedomPlus", "SBI");
        put("com.reddit.frontpage", "Reddit");
    }};

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null) return;

        String packageName = sbn.getPackageName();

        // Only process monitored apps
        if (!MONITORED_PACKAGES.contains(packageName)) return;

        try {
            Notification notification = sbn.getNotification();
            Bundle extras = notification.extras;

            if (extras == null) return;

            // Extract notification content
            CharSequence title = extras.getCharSequence(Notification.EXTRA_TITLE);
            CharSequence text = extras.getCharSequence(Notification.EXTRA_TEXT);
            CharSequence bigText = extras.getCharSequence(Notification.EXTRA_BIG_TEXT);

            String content = bigText != null ? bigText.toString()
                           : text != null    ? text.toString()
                           : "";

            if (content.trim().isEmpty()) return;

            // Get friendly app name
            String appName = APP_NAMES.getOrDefault(packageName,
                getAppName(packageName));

            String sender = title != null ? title.toString() : "Unknown";

            Log.d(TAG, "Notification from " + appName + ": " + content.substring(0, Math.min(50, content.length())));

            // Build payload for React Native ML engine
            WritableMap payload = Arguments.createMap();
            payload.putString("id", java.util.UUID.randomUUID().toString());
            payload.putString("source", appName);
            payload.putString("packageName", packageName);
            payload.putString("sender", sender);
            payload.putString("text", content);
            payload.putDouble("timestamp", sbn.getPostTime());
            payload.putBoolean("isOngoing", sbn.isOngoing());

            // Emit to React Native for real-time ML analysis
            EventEmitter.emit(getApplicationContext(), "onIncomingMessage", payload);

        } catch (Exception e) {
            Log.e(TAG, "Error reading notification: " + e.getMessage());
        }
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        // Track when users dismiss notifications — useful for feedback loop
        if (sbn != null && MONITORED_PACKAGES.contains(sbn.getPackageName())) {
            WritableMap payload = Arguments.createMap();
            payload.putString("id", sbn.getKey());
            payload.putString("packageName", sbn.getPackageName());
            EventEmitter.emit(getApplicationContext(), "onNotificationDismissed", payload);
        }
    }

    private String getAppName(String packageName) {
        try {
            PackageManager pm = getPackageManager();
            ApplicationInfo info = pm.getApplicationInfo(packageName, 0);
            return pm.getApplicationLabel(info).toString();
        } catch (PackageManager.NameNotFoundException e) {
            return packageName;
        }
    }
}
