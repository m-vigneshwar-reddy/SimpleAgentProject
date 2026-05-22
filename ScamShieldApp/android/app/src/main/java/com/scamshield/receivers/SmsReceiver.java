package com.scamshield.receivers;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;
import android.util.Log;

import com.facebook.react.bridge.Arguments;
import com.facebook.react.bridge.WritableMap;
import com.scamshield.services.ScamMonitorService;
import com.scamshield.utils.EventEmitter;

/**
 * SmsReceiver — intercepts ALL incoming SMS messages in real time.
 * Highest priority (Integer.MAX_VALUE) so we get first access.
 * Passes the message to ScamMonitorService for ML/DL analysis.
 */
public class SmsReceiver extends BroadcastReceiver {

    private static final String TAG = "ScamShield::SMS";
    private static final String SMS_RECEIVED = "android.provider.Telephony.SMS_RECEIVED";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (!SMS_RECEIVED.equals(intent.getAction())) return;

        Bundle bundle = intent.getExtras();
        if (bundle == null) return;

        try {
            Object[] pdus = (Object[]) bundle.get("pdus");
            String format = bundle.getString("format");

            if (pdus == null) return;

            StringBuilder fullMessage = new StringBuilder();
            String sender = "";
            long timestamp = System.currentTimeMillis();

            for (Object pdu : pdus) {
                SmsMessage sms = SmsMessage.createFromPdu((byte[]) pdu, format);
                fullMessage.append(sms.getMessageBody());
                sender = sms.getOriginatingAddress();
                timestamp = sms.getTimestampMillis();
            }

            String messageText = fullMessage.toString();
            Log.d(TAG, "SMS received from: " + sender);

            // Build payload for JS layer
            WritableMap payload = Arguments.createMap();
            payload.putString("source", "SMS");
            payload.putString("sender", sender != null ? sender : "Unknown");
            payload.putString("text", messageText);
            payload.putDouble("timestamp", timestamp);
            payload.putString("id", java.util.UUID.randomUUID().toString());

            // Emit to React Native for ML analysis
            EventEmitter.emit(context, "onIncomingMessage", payload);

            // Also start service for background processing
            Intent serviceIntent = new Intent(context, ScamMonitorService.class);
            serviceIntent.putExtra("source", "SMS");
            serviceIntent.putExtra("sender", sender);
            serviceIntent.putExtra("text", messageText);
            serviceIntent.putExtra("timestamp", timestamp);
            context.startForegroundService(serviceIntent);

        } catch (Exception e) {
            Log.e(TAG, "Error processing SMS: " + e.getMessage());
        }
    }
}
