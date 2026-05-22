package com.scamshield.receivers;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.telephony.TelephonyManager;
import android.util.Log;

import com.facebook.react.bridge.Arguments;
import com.facebook.react.bridge.WritableMap;
import com.scamshield.utils.EventEmitter;

/**
 * CallReceiver — detects incoming & outgoing calls.
 * Checks number against known scam databases and pattern analysis.
 * Flags: private numbers, known scam prefixes, suspicious patterns.
 */
public class CallReceiver extends BroadcastReceiver {

    private static final String TAG = "ScamShield::Call";

    // Known scam call prefixes (India examples)
    private static final String[] SCAM_PREFIXES = {
        "+1900", "+1800", "000", "001"
    };

    // Suspicious number patterns
    private static final String[] SUSPICIOUS_PATTERNS = {
        ".*0000$",   // ends in 4 zeros
        ".*1234$",   // sequential
        ".*9999$",   // repeated digits
    };

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (action == null) return;

        String phoneNumber = intent.getStringExtra(TelephonyManager.EXTRA_INCOMING_NUMBER);
        String state = intent.getStringExtra(TelephonyManager.EXTRA_STATE);

        if (TelephonyManager.ACTION_PHONE_STATE_CHANGED.equals(action)) {
            if (TelephonyManager.EXTRA_STATE_RINGING.equals(state)) {
                handleIncomingCall(context, phoneNumber);
            }
        } else if (Intent.ACTION_NEW_OUTGOING_CALL.equals(action)) {
            phoneNumber = intent.getStringExtra(Intent.EXTRA_PHONE_NUMBER);
            handleOutgoingCall(context, phoneNumber);
        }
    }

    private void handleIncomingCall(Context context, String number) {
        Log.d(TAG, "Incoming call from: " + number);

        boolean isPrivate = (number == null || number.isEmpty());
        boolean isSuspicious = false;
        String reason = "";

        if (!isPrivate) {
            // Check suspicious patterns
            for (String prefix : SCAM_PREFIXES) {
                if (number.startsWith(prefix)) {
                    isSuspicious = true;
                    reason = "Suspicious prefix: " + prefix;
                    break;
                }
            }
            for (String pattern : SUSPICIOUS_PATTERNS) {
                if (number.matches(pattern)) {
                    isSuspicious = true;
                    reason = "Suspicious number pattern";
                    break;
                }
            }
        } else {
            isSuspicious = true;
            reason = "Private/hidden number";
        }

        WritableMap payload = Arguments.createMap();
        payload.putString("id", java.util.UUID.randomUUID().toString());
        payload.putString("source", "Call");
        payload.putString("sender", isPrivate ? "Private Number" : number);
        payload.putString("text", isPrivate
            ? "Incoming call from hidden/private number"
            : "Incoming call from " + number);
        payload.putBoolean("isPrivateNumber", isPrivate);
        payload.putBoolean("isSuspicious", isSuspicious);
        payload.putString("suspiciousReason", reason);
        payload.putDouble("timestamp", System.currentTimeMillis());

        EventEmitter.emit(context, "onIncomingCall", payload);
    }

    private void handleOutgoingCall(Context context, String number) {
        WritableMap payload = Arguments.createMap();
        payload.putString("id", java.util.UUID.randomUUID().toString());
        payload.putString("source", "Call");
        payload.putString("sender", number != null ? number : "Unknown");
        payload.putString("text", "Outgoing call to " + (number != null ? number : "Unknown"));
        payload.putBoolean("isOutgoing", true);
        payload.putDouble("timestamp", System.currentTimeMillis());
        EventEmitter.emit(context, "onOutgoingCall", payload);
    }
}
