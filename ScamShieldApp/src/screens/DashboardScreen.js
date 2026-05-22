// src/screens/DashboardScreen.js
import React, { useEffect, useRef, useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  Animated, RefreshControl, StatusBar, Dimensions,
} from 'react-native';
import { useSelector } from 'react-redux';
import LinearGradient from 'react-native-linear-gradient';
import MessageMonitorService from '../services/MessageMonitorService';
import { COLORS, FONTS, RADIUS } from '../utils/theme';

const { width } = Dimensions.get('window');

const SOURCE_ICONS = {
  WhatsApp:'💬', SMS:'📱', Email:'📧', Instagram:'📸', Facebook:'👥',
  LinkedIn:'💼', Telegram:'✈️', Call:'📞', App:'📲', Game:'🎮',
};

export default function DashboardScreen({ navigation }) {
  const stats      = useSelector(s => s.stats);
  const messages   = useSelector(s => s.messages.all);
  const scamList   = useSelector(s => s.messages.scamList);
  const [liveMsg, setLiveMsg] = useState(null);
  const pulseAnim  = useRef(new Animated.Value(1)).current;
  const alertAnim  = useRef(new Animated.Value(0)).current;

  // Pulse animation for live dot
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.4, duration: 800, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  // Listen for new messages
  useEffect(() => {
    const handler = (msg) => {
      if (msg.verdict !== 'SAFE') {
        setLiveMsg(msg);
        Animated.sequence([
          Animated.timing(alertAnim, { toValue: 1, duration: 300, useNativeDriver: true }),
          Animated.delay(4000),
          Animated.timing(alertAnim, { toValue: 0, duration: 300, useNativeDriver: true }),
        ]).start();
      }
    };
    MessageMonitorService.onMessage(handler);
    return () => MessageMonitorService.offMessage(handler);
  }, []);

  const recentScams = scamList.slice(0, 5);
  const scamRate = stats.totalScanned > 0
    ? ((stats.totalBlocked / stats.totalScanned) * 100).toFixed(1) : '0.0';

  return (
    <View style={s.container}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.bg}/>

      {/* Live Alert Banner */}
      <Animated.View style={[s.alertBanner, { opacity: alertAnim,
          transform: [{ translateY: alertAnim.interpolate({ inputRange:[0,1], outputRange:[-60,0] }) }]
      }]}>
        {liveMsg && (
          <TouchableOpacity style={s.alertInner} onPress={() => navigation.navigate('Detail', { message: liveMsg })}>
            <Text style={s.alertIcon}>{liveMsg.verdict === 'SCAM' ? '🚨' : '⚠️'}</Text>
            <View style={{ flex:1 }}>
              <Text style={s.alertTitle}>{liveMsg.verdict} DETECTED — {liveMsg.source}</Text>
              <Text style={s.alertPreview} numberOfLines={1}>{liveMsg.text}</Text>
            </View>
            <Text style={s.alertAction}>View →</Text>
          </TouchableOpacity>
        )}
      </Animated.View>

      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <LinearGradient colors={['#1a1a2e', '#16213e']} style={s.header}>
          <View style={s.headerTop}>
            <View>
              <Text style={s.headerTitle}>ScamShield AI</Text>
              <View style={s.liveRow}>
                <Animated.View style={[s.liveDot, { transform: [{ scale: pulseAnim }] }]}/>
                <Text style={s.liveText}>Monitoring All Sources</Text>
              </View>
            </View>
            <TouchableOpacity style={s.shieldBtn} onPress={() => navigation.navigate('Settings')}>
              <Text style={{ fontSize:28 }}>⚙️</Text>
            </TouchableOpacity>
          </View>

          {/* Big Risk Counter */}
          <View style={s.bigStats}>
            <View style={s.bigStat}>
              <Text style={[s.bigStatVal, { color: COLORS.blue }]}>{stats.totalScanned}</Text>
              <Text style={s.bigStatLabel}>Scanned</Text>
            </View>
            <View style={s.bigStatDivider}/>
            <View style={s.bigStat}>
              <Text style={[s.bigStatVal, { color: COLORS.red }]}>{stats.totalBlocked}</Text>
              <Text style={s.bigStatLabel}>Blocked</Text>
            </View>
            <View style={s.bigStatDivider}/>
            <View style={s.bigStat}>
              <Text style={[s.bigStatVal, { color: COLORS.green }]}>{scamRate}%</Text>
              <Text style={s.bigStatLabel}>Scam Rate</Text>
            </View>
          </View>
        </LinearGradient>

        {/* Source Grid */}
        <View style={s.section}>
          <Text style={s.sectionTitle}>Monitored Sources</Text>
          <View style={s.sourceGrid}>
            {Object.entries(SOURCE_ICONS).map(([src, icon]) => {
              const count = stats.bySource[src] || 0;
              return (
                <TouchableOpacity key={src} style={s.sourceCard}
                  onPress={() => navigation.navigate('Messages', { filter: src })}>
                  <Text style={s.sourceIcon}>{icon}</Text>
                  <Text style={s.sourceName}>{src}</Text>
                  <Text style={s.sourceCount}>{count}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Recent Scams */}
        <View style={s.section}>
          <View style={s.sectionHeader}>
            <Text style={s.sectionTitle}>Recent Scams</Text>
            <TouchableOpacity onPress={() => navigation.navigate('ScamList')}>
              <Text style={s.seeAll}>See All ({scamList.length})</Text>
            </TouchableOpacity>
          </View>
          {recentScams.length === 0 ? (
            <View style={s.emptyBox}>
              <Text style={{ fontSize:32 }}>✅</Text>
              <Text style={s.emptyText}>No scams detected yet</Text>
            </View>
          ) : (
            recentScams.map(msg => (
              <TouchableOpacity key={msg.id} style={[s.msgCard,
                msg.verdict==='SCAM' ? s.cardScam : s.cardSusp]}
                onPress={() => navigation.navigate('Detail', { message: msg })}>
                <View style={s.msgLeft}>
                  <Text style={s.msgIcon}>{SOURCE_ICONS[msg.source] || '📨'}</Text>
                </View>
                <View style={s.msgBody}>
                  <View style={s.msgHeader}>
                    <Text style={s.msgSource}>{msg.source}</Text>
                    <Text style={s.msgSender} numberOfLines={1}>{msg.sender}</Text>
                    <View style={[s.riskPill, msg.verdict==='SCAM' ? s.pillRed : s.pillOrange]}>
                      <Text style={s.riskPillText}>{msg.riskScore}</Text>
                    </View>
                  </View>
                  <Text style={s.msgText} numberOfLines={2}>{msg.text}</Text>
                  <View style={s.msgFooter}>
                    <Text style={s.msgTime}>{msg.receivedAt}</Text>
                    <Text style={[s.verdict, msg.verdict==='SCAM' ? s.verdictRed : s.verdictOrange]}>
                      {msg.verdict}
                    </Text>
                  </View>
                </View>
              </TouchableOpacity>
            ))
          )}
        </View>

        {/* Model Accuracy */}
        <View style={[s.section, { marginBottom: 100 }]}>
          <Text style={s.sectionTitle}>AI Model Status</Text>
          {[
            { name:'Transformer-LSTM', acc: 98.6, color: COLORS.blue },
            { name:'BERT NLP',         acc: 99.1, color: COLORS.purple },
            { name:'Random Forest',    acc: 96.4, color: COLORS.green },
            { name:'XGBoost',          acc: 97.2, color: COLORS.orange },
            { name:'GraphSAGE GNN',    acc: 97.8, color: COLORS.red },
          ].map(m => (
            <View key={m.name} style={s.modelRow}>
              <Text style={s.modelName}>{m.name}</Text>
              <View style={s.modelBarBg}>
                <View style={[s.modelBarFill, { width: m.acc + '%', backgroundColor: m.color }]}/>
              </View>
              <Text style={[s.modelAcc, { color: m.color }]}>{m.acc}%</Text>
            </View>
          ))}
        </View>
      </ScrollView>

      {/* FAB */}
      <TouchableOpacity style={s.fab} onPress={() => navigation.navigate('Simulate')}>
        <Text style={{ fontSize:22 }}>🧪</Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex:1, backgroundColor: COLORS.bg },
  alertBanner: { position:'absolute', top:0, left:0, right:0, zIndex:999,
    backgroundColor: COLORS.red, margin:12, borderRadius:12, elevation:8 },
  alertInner: { flexDirection:'row', alignItems:'center', padding:12, gap:10 },
  alertIcon: { fontSize:20 },
  alertTitle: { color:'#fff', fontWeight:'700', fontSize:12 },
  alertPreview: { color:'rgba(255,255,255,0.8)', fontSize:11 },
  alertAction: { color:'#fff', fontWeight:'700', fontSize:13 },
  header: { padding:20, paddingTop:50 },
  headerTop: { flexDirection:'row', justifyContent:'space-between', alignItems:'flex-start', marginBottom:24 },
  headerTitle: { color:COLORS.text, fontSize:26, fontWeight:'900', letterSpacing:-0.5 },
  liveRow: { flexDirection:'row', alignItems:'center', gap:6, marginTop:4 },
  liveDot: { width:8, height:8, borderRadius:4, backgroundColor:COLORS.green },
  liveText: { color:COLORS.green, fontSize:12, fontWeight:'600' },
  shieldBtn: { padding:8 },
  bigStats: { flexDirection:'row', backgroundColor:'rgba(255,255,255,0.05)',
    borderRadius:16, padding:20, gap:0 },
  bigStat: { flex:1, alignItems:'center' },
  bigStatDivider: { width:1, backgroundColor:'rgba(255,255,255,0.1)', marginVertical:4 },
  bigStatVal: { fontSize:32, fontWeight:'900', fontFamily: FONTS.mono },
  bigStatLabel: { color:COLORS.text2, fontSize:11, marginTop:4, fontWeight:'600' },
  section: { padding:16, gap:10 },
  sectionHeader: { flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:2 },
  sectionTitle: { color:COLORS.text, fontSize:15, fontWeight:'800', letterSpacing:0.3, marginBottom:10 },
  seeAll: { color:COLORS.blue, fontSize:13, fontWeight:'600' },
  sourceGrid: { flexDirection:'row', flexWrap:'wrap', gap:10 },
  sourceCard: { width:(width-52)/5, backgroundColor:COLORS.surface,
    borderRadius:12, padding:10, alignItems:'center', borderWidth:1, borderColor:COLORS.border },
  sourceIcon: { fontSize:22, marginBottom:4 },
  sourceName: { color:COLORS.text2, fontSize:9, fontWeight:'700', textTransform:'uppercase' },
  sourceCount: { color:COLORS.text, fontSize:14, fontWeight:'800', fontFamily:FONTS.mono, marginTop:2 },
  emptyBox: { alignItems:'center', padding:30, gap:8, backgroundColor:COLORS.surface,
    borderRadius:12, borderWidth:1, borderColor:COLORS.border },
  emptyText: { color:COLORS.text2, fontSize:13 },
  msgCard: { backgroundColor:COLORS.surface, borderRadius:12, padding:14,
    flexDirection:'row', gap:12, borderWidth:1, borderColor:COLORS.border, marginBottom:8 },
  cardScam: { borderLeftWidth:3, borderLeftColor:COLORS.red },
  cardSusp: { borderLeftWidth:3, borderLeftColor:COLORS.orange },
  msgLeft: { justifyContent:'center' },
  msgIcon: { fontSize:24 },
  msgBody: { flex:1 },
  msgHeader: { flexDirection:'row', alignItems:'center', gap:8, marginBottom:6 },
  msgSource: { color:COLORS.text, fontSize:12, fontWeight:'700' },
  msgSender: { color:COLORS.text2, fontSize:11, flex:1 },
  riskPill: { paddingHorizontal:8, paddingVertical:2, borderRadius:10 },
  pillRed: { backgroundColor:'rgba(255,71,87,0.15)' },
  pillOrange: { backgroundColor:'rgba(255,159,67,0.15)' },
  riskPillText: { fontFamily:FONTS.mono, fontSize:11, fontWeight:'700', color:'#fff' },
  msgText: { color:COLORS.text, fontSize:13, lineHeight:19 },
  msgFooter: { flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginTop:6 },
  msgTime: { color:COLORS.text3, fontSize:10, fontFamily:FONTS.mono },
  verdict: { fontSize:10, fontWeight:'800', textTransform:'uppercase', letterSpacing:1 },
  verdictRed: { color:COLORS.red },
  verdictOrange: { color:COLORS.orange },
  modelRow: { flexDirection:'row', alignItems:'center', gap:10, marginBottom:8 },
  modelName: { color:COLORS.text2, fontSize:11, width:130 },
  modelBarBg: { flex:1, height:6, backgroundColor:COLORS.border, borderRadius:3, overflow:'hidden' },
  modelBarFill: { height:'100%', borderRadius:3 },
  modelAcc: { fontFamily:FONTS.mono, fontSize:11, width:44, textAlign:'right' },
  fab: { position:'absolute', bottom:30, right:20, width:56, height:56,
    borderRadius:28, backgroundColor:COLORS.blue, alignItems:'center', justifyContent:'center',
    elevation:8, shadowColor:'#000', shadowOffset:{width:0,height:4}, shadowOpacity:0.3 },
});
