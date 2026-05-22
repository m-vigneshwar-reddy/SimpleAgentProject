package com.scamshield.services;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;

import androidx.core.app.NotificationCompat;

import com.scamshield.MainActivity;
import com.scamshield.R;
import com.scamshield.ml.ScamMLEngine;

/**
 * ScamMonitorService — persistent foreground service.
 * Runs continuously in the background to:
 *   1. Keep the ML engine loaded and ready
 *   2. Process data from SMS/Call/Notification receivers
 *   3. Show persistent "ScamShield is protecting you" notification
 *   4. Restart on boot (via BootReceiver)
 */
public class ScamMonitorService extends Service {

    private static final String TAG = "ScamShield::Service";
    private static final String CHANNEL_ID = "scamshield_monitor";
    private static final int NOTIF_ID = 1001;

    private ScamMLEngine mlEngine;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "ScamMonitorService created");
        createNotificationChannel();
        startForeground(NOTIF_ID, buildForegroundNotification("ScamShield is active", "Monitoring all incoming messages…"));
        mlEngine = ScamMLEngine.getInstance(this);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            String source = intent.getStringExtra("source");
            String sender = intent.getStringExtra("sender");
            String text   = intent.getStringExtra("text");
            long timestamp = intent.getLongExtra("timestamp", System.currentTimeMillis());

            if (text != null && !text.isEmpty()) {
                // Run ML analysis in background thread
                new Thread(() -> {
                    try {
                        ScamMLEngine.Result result = mlEngine.analyse(text, source, sender);
                        Log.d(TAG, "ML result: " + result.verdict + " (" + result.riskScore + ")");
                        if (result.riskScore >= 50) {
                            showScamAlert(source, sender, text, result);
                        }
                        // Update foreground notification with live stats
                        updateForegroundNotification(mlEngine.getTotalScanned(), mlEngine.getTotalBlocked());
                    } catch (Exception e) {
                        Log.e(TAG, "ML analysis error: " + e.getMessage());
                    }
                }).start();
            }
        }
        return START_STICKY; // Restart if killed
    }

    private void showScamAlert(String source, String sender, String text, ScamMLEngine.Result result) {
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        String preview = text.length() > 80 ? text.substring(0, 80) + "…" : text;

        Notification alert = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_shield_alert)
            .setContentTitle("⚠ Scam Detected from " + source)
            .setContentText(preview)
            .setStyle(new NotificationCompat.BigTextStyle()
                .bigText("From: " + sender + "\n\n" + preview + "\n\nRisk Score: " + result.riskScore + "/100"))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setColor(0xFFFF4757)
            .setAutoCancel(true)
            .setVibrate(new long[]{0, 500, 200, 500})
            .setContentIntent(buildOpenAppIntent())
            .addAction(R.drawable.ic_check, "Not a Scam", buildDismissIntent(result.id))
            .addAction(R.drawable.ic_block, "Block Sender", buildBlockIntent(sender))
            .build();

        nm.notify((int) System.currentTimeMillis(), alert);
    }

    private void updateForegroundNotification(int scanned, int blocked) {
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        nm.notify(NOTIF_ID, buildForegroundNotification(
            "ScamShield is protecting you",
            "Scanned: " + scanned + "  |  Blocked: " + blocked
        ));
    }

    private Notification buildForegroundNotification(String title, String text) {
        return new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle(title)
            .setContentText(text)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .setContentIntent(buildOpenAppIntent())
            .build();
    }

    private PendingIntent buildOpenAppIntent() {
        Intent i = new Intent(this, MainActivity.class);
        return PendingIntent.getActivity(this, 0, i,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    private PendingIntent buildDismissIntent(String id) {
        Intent i = new Intent(this, ScamActionReceiver.class);
        i.setAction("DISMISS_SCAM");
        i.putExtra("scam_id", id);
        return PendingIntent.getBroadcast(this, 0, i,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    private PendingIntent buildBlockIntent(String sender) {
        Intent i = new Intent(this, ScamActionReceiver.class);
        i.setAction("BLOCK_SENDER");
        i.putExtra("sender", sender);
        return PendingIntent.getBroadcast(this, 1, i,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "ScamShield Monitor",
                NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("ScamShield background monitoring service");
            ((NotificationManager) getSystemService(NOTIFICATION_SERVICE))
                .createNotificationChannel(channel);
        }
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onDestroy() {
        super.onDestroy();
        // Restart self — stay alive
        startService(new Intent(this, ScamMonitorService.class));
    }
}
