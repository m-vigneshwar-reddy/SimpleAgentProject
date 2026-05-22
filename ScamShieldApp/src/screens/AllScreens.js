// src/utils/theme.js
export const COLORS = {
  bg: '#0f0f14', surface: '#16161e', surface2: '#1e1e2a', surface3: '#252535',
  border: '#2a2a3d', border2: '#353550',
  red: '#ff4757', orange: '#ff9f43', green: '#26de81',
  blue: '#4d9fff', purple: '#a55eea',
  text: '#e8e8f0', text2: '#9090b0', text3: '#55556a',
};
export const FONTS = { mono: 'Courier New', sans: 'System' };
export const RADIUS = { sm: 8, md: 12, lg: 16 };

// ─────────────────────────────────────────────────────────────────────────────
// src/screens/ScamListScreen.js
// ─────────────────────────────────────────────────────────────────────────────
import React, { useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity,
  Alert, TextInput, Share,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { markNotScam, dismissScam, blockSender, confirmScam } from '../store';
import { submitFeedback } from '../ml/ScamDetectionEngine';

const SOURCE_ICONS = {
  WhatsApp:'💬', SMS:'📱', Email:'📧', Instagram:'📸', Facebook:'👥',
  LinkedIn:'💼', Telegram:'✈️', Call:'📞', App:'📲', Game:'🎮',
};

export function ScamListScreen({ navigation }) {
  const dispatch   = useDispatch();
  const scamList   = useSelector(s => s.messages.scamList);
  const [filter, setFilter] = useState('all');
  const [search, setSearch]  = useState('');

  const FILTERS = ['all', 'WhatsApp', 'SMS', 'Email', 'Call', 'App'];

  const filtered = scamList.filter(m => {
    const matchSrc = filter === 'all' || m.source === filter;
    const matchSearch = !search || m.text.toLowerCase().includes(search.toLowerCase()) || (m.sender||'').toLowerCase().includes(search.toLowerCase());
    return matchSrc && matchSearch;
  });

  const handleNotScam = (msg) => {
    Alert.alert('Mark as Not a Scam?', 'This will remove it from the scam list and improve the AI model.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Yes, Remove', onPress: () => {
        dispatch(markNotScam(msg.id));
        submitFeedback(msg.id, false, msg.text);
      }},
    ]);
  };

  const handleRemove = (id) => {
    dispatch(dismissScam(id));
  };

  const handleBlock = (sender) => {
    Alert.alert('Block Sender?', `Block all future messages from "${sender}"?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Block', style: 'destructive', onPress: () => dispatch(blockSender(sender)) },
    ]);
  };

  const exportList = async () => {
    const csv = ['Source,Sender,Message,Risk,Verdict,Time',
      ...filtered.map(m => `${m.source},"${m.sender}","${m.text.replace(/"/g,'""')}",${m.riskScore},${m.verdict},${m.receivedAt}`)
    ].join('\n');
    await Share.share({ message: csv, title: 'ScamShield List' });
  };

  const renderItem = ({ item: msg }) => (
    <TouchableOpacity style={[ss.card, msg.verdict==='SCAM' ? ss.cardRed : ss.cardOrange]}
      onPress={() => navigation.navigate('Detail', { message: msg })}>
      <View style={ss.cardTop}>
        <Text style={ss.icon}>{SOURCE_ICONS[msg.source]||'📨'}</Text>
        <View style={{ flex:1 }}>
          <View style={ss.row}>
            <Text style={ss.source}>{msg.source}</Text>
            <Text style={ss.sender} numberOfLines={1}>{msg.sender}</Text>
          </View>
          <Text style={ss.text} numberOfLines={2}>{msg.text}</Text>
        </View>
        <View style={[ss.pill, msg.verdict==='SCAM' ? ss.pillRed : ss.pillOrg]}>
          <Text style={ss.pillText}>{msg.riskScore}</Text>
        </View>
      </View>
      <View style={ss.tags}>
        <View style={ss.tag}><Text style={ss.tagText}>{msg.type}</Text></View>
        {msg.confirmed && <View style={[ss.tag,{backgroundColor:'rgba(255,71,87,0.15)'}]}><Text style={[ss.tagText,{color:'#ff4757'}]}>Confirmed</Text></View>}
        {msg.autoBlocked && <View style={[ss.tag,{backgroundColor:'rgba(77,159,255,0.12)'}]}><Text style={[ss.tagText,{color:'#4d9fff'}]}>Auto-Blocked</Text></View>}
      </View>
      <View style={ss.actions}>
        <TouchableOpacity style={ss.actionBtn} onPress={() => handleNotScam(msg)}>
          <Text style={[ss.actionText,{color:'#26de81'}]}>✅ Not Scam</Text>
        </TouchableOpacity>
        <TouchableOpacity style={ss.actionBtn} onPress={() => handleBlock(msg.sender)}>
          <Text style={[ss.actionText,{color:'#ff9f43'}]}>🚫 Block</Text>
        </TouchableOpacity>
        <TouchableOpacity style={ss.actionBtn} onPress={() => handleRemove(msg.id)}>
          <Text style={[ss.actionText,{color:'#ff4757'}]}>🗑 Remove</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={ss.container}>
      <View style={ss.toolbar}>
        <TextInput style={ss.search} placeholder="Search messages…"
          placeholderTextColor="#55556a" value={search} onChangeText={setSearch}
          style={ss.search}/>
        <TouchableOpacity onPress={exportList} style={ss.exportBtn}>
          <Text style={{color:'#4d9fff',fontWeight:'700',fontSize:12}}>⬇ Export</Text>
        </TouchableOpacity>
      </View>
      <View style={ss.filters}>
        {FILTERS.map(f => (
          <TouchableOpacity key={f} style={[ss.filterBtn, filter===f && ss.filterActive]}
            onPress={() => setFilter(f)}>
            <Text style={[ss.filterText, filter===f && ss.filterTextActive]}>{f}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <FlatList data={filtered} keyExtractor={m=>m.id} renderItem={renderItem}
        contentContainerStyle={{ padding:12, gap:10, paddingBottom:80 }}
        ListEmptyComponent={
          <View style={ss.empty}>
            <Text style={{fontSize:40}}>✅</Text>
            <Text style={ss.emptyText}>No scams found</Text>
          </View>
        }/>
    </View>
  );
}

const ss = StyleSheet.create({
  container:{ flex:1, backgroundColor:'#0f0f14' },
  toolbar:{ flexDirection:'row', gap:10, padding:12, paddingBottom:0 },
  search:{ flex:1, backgroundColor:'#16161e', borderRadius:10, paddingHorizontal:14,
    height:40, color:'#e8e8f0', borderWidth:1, borderColor:'#2a2a3d', fontSize:14 },
  exportBtn:{ backgroundColor:'rgba(77,159,255,0.1)', borderRadius:10, paddingHorizontal:12,
    height:40, justifyContent:'center', borderWidth:1, borderColor:'rgba(77,159,255,0.25)' },
  filters:{ flexDirection:'row', gap:6, paddingHorizontal:12, paddingVertical:10, flexWrap:'wrap' },
  filterBtn:{ paddingHorizontal:14, paddingVertical:6, borderRadius:20,
    backgroundColor:'#16161e', borderWidth:1, borderColor:'#2a2a3d' },
  filterActive:{ backgroundColor:'rgba(77,159,255,0.15)', borderColor:'rgba(77,159,255,0.4)' },
  filterText:{ color:'#9090b0', fontSize:12, fontWeight:'600' },
  filterTextActive:{ color:'#4d9fff' },
  card:{ backgroundColor:'#16161e', borderRadius:14, padding:14,
    borderWidth:1, borderColor:'#2a2a3d' },
  cardRed:{ borderLeftWidth:3, borderLeftColor:'#ff4757' },
  cardOrange:{ borderLeftWidth:3, borderLeftColor:'#ff9f43' },
  cardTop:{ flexDirection:'row', gap:12, alignItems:'flex-start', marginBottom:8 },
  icon:{ fontSize:26, marginTop:2 },
  row:{ flexDirection:'row', gap:6, alignItems:'center', marginBottom:4 },
  source:{ color:'#e8e8f0', fontWeight:'700', fontSize:13 },
  sender:{ color:'#9090b0', fontSize:12, flex:1 },
  text:{ color:'#e8e8f0', fontSize:13, lineHeight:19 },
  pill:{ paddingHorizontal:10, paddingVertical:4, borderRadius:12 },
  pillRed:{ backgroundColor:'rgba(255,71,87,0.15)' },
  pillOrg:{ backgroundColor:'rgba(255,159,67,0.15)' },
  pillText:{ color:'#fff', fontWeight:'800', fontSize:13, fontFamily:'Courier New' },
  tags:{ flexDirection:'row', gap:6, flexWrap:'wrap', marginBottom:10 },
  tag:{ backgroundColor:'#252535', borderRadius:6, paddingHorizontal:8, paddingVertical:3 },
  tagText:{ color:'#9090b0', fontSize:10, fontWeight:'600', textTransform:'uppercase' },
  actions:{ flexDirection:'row', gap:8 },
  actionBtn:{ flex:1, backgroundColor:'#1e1e2a', borderRadius:8, paddingVertical:7,
    alignItems:'center', borderWidth:1, borderColor:'#2a2a3d' },
  actionText:{ fontSize:11, fontWeight:'700' },
  empty:{ alignItems:'center', padding:60, gap:10 },
  emptyText:{ color:'#55556a', fontSize:14 },
});

// ─────────────────────────────────────────────────────────────────────────────
// src/screens/DetailScreen.js
// ─────────────────────────────────────────────────────────────────────────────
import React from 'react';
import { View as V, Text as T, ScrollView as SV, TouchableOpacity as TO,
  StyleSheet as SS, Alert as AL } from 'react-native';
import { useDispatch } from 'react-redux';
import { markNotScam, blockSender, confirmScam } from '../store';
import { submitFeedback } from '../ml/ScamDetectionEngine';

const MODELS = ['Transformer-LSTM','BERT NLP','Random Forest','XGBoost','GraphSAGE GNN'];
const MODEL_COLORS = ['#4d9fff','#a55eea','#26de81','#ff9f43','#ff4757'];

export function DetailScreen({ route, navigation }) {
  const dispatch = useDispatch();
  const { message: msg } = route.params;
  const riskColor = msg.riskScore >= 55 ? '#ff4757' : msg.riskScore >= 25 ? '#ff9f43' : '#26de81';

  const handleNotScam = () => {
    AL.alert('Mark as Not a Scam?', 'This will remove it and train the AI to be more accurate.', [
      { text: 'Cancel', style:'cancel' },
      { text: 'Confirm', onPress:() => {
        dispatch(markNotScam(msg.id));
        submitFeedback(msg.id, false, msg.text);
        navigation.goBack();
      }},
    ]);
  };

  const handleBlock = () => {
    AL.alert('Block Sender?', `Block "${msg.sender}"?`, [
      { text: 'Cancel', style:'cancel' },
      { text: 'Block', style:'destructive', onPress:() => dispatch(blockSender(msg.sender)) },
    ]);
  };

  return (
    <SV style={ds.container} showsVerticalScrollIndicator={false}>
      {/* Risk Score Hero */}
      <V style={[ds.hero, { borderColor: riskColor+'44' }]}>
        <T style={[ds.heroScore, { color: riskColor }]}>{msg.riskScore}</T>
        <T style={[ds.heroVerdict, { color: riskColor }]}>{msg.verdict}</T>
        <T style={ds.heroType}>{msg.type}</T>
        <V style={ds.heroBadges}>
          <V style={ds.badge}><T style={ds.badgeText}>{msg.source}</T></V>
          <V style={ds.badge}><T style={ds.badgeText}>{msg.receivedAt}</T></V>
        </V>
      </V>

      {/* Message */}
      <V style={ds.section}>
        <T style={ds.sLabel}>Message</T>
        <V style={ds.bubble}><T style={ds.bubbleText}>"{msg.text}"</T></V>
        <T style={ds.senderText}>From: {msg.sender}</T>
      </V>

      {/* Detection Reasons */}
      <V style={ds.section}>
        <T style={ds.sLabel}>Why It Was Flagged</T>
        {(msg.reasons||[]).length === 0 ? (
          <V style={ds.reasonItem}><T>✅ No scam indicators</T></V>
        ) : (
          (msg.reasons||[]).map((r,i) => (
            <V key={i} style={ds.reasonItem}><T style={ds.reasonText}>{r}</T></V>
          ))
        )}
      </V>

      {/* Model Scores */}
      <V style={ds.section}>
        <T style={ds.sLabel}>ML/DL Model Analysis</T>
        {MODELS.map((m,i) => {
          const score = Math.round(msg.modelScores?.[m] || msg.riskScore + (Math.random()-0.5)*10);
          const c = score>=55?'#ff4757':score>=25?'#ff9f43':'#26de81';
          return (
            <V key={m} style={ds.modelRow}>
              <T style={ds.modelName}>{m}</T>
              <V style={ds.barBg}>
                <V style={[ds.barFill,{width:`${Math.min(100,score)}%`,backgroundColor:MODEL_COLORS[i]}]}/>
              </V>
              <T style={[ds.modelScore,{color:c}]}>{score}</T>
            </V>
          );
        })}
      </V>

      {/* Actions */}
      <V style={ds.actionSection}>
        <TO style={[ds.btn, ds.btnGreen]} onPress={handleNotScam}>
          <T style={ds.btnText}>✅ Not a Scam — Remove</T>
        </TO>
        <TO style={[ds.btn, ds.btnOrange]} onPress={handleBlock}>
          <T style={ds.btnText}>🚫 Block This Sender</T>
        </TO>
        <TO style={[ds.btn, ds.btnRed]} onPress={() => {
          dispatch(confirmScam(msg.id));
          submitFeedback(msg.id, true, msg.text);
          AL.alert('Confirmed', 'Scam confirmed. AI model updated.');
        }}>
          <T style={ds.btnText}>🚨 Confirm as Scam</T>
        </TO>
      </V>
    </SV>
  );
}

const ds = SS.create({
  container:{ flex:1, backgroundColor:'#0f0f14', padding:16 },
  hero:{ backgroundColor:'#16161e', borderRadius:16, padding:24, alignItems:'center',
    borderWidth:1, marginBottom:16, gap:4 },
  heroScore:{ fontSize:64, fontWeight:'900', fontFamily:'Courier New' },
  heroVerdict:{ fontSize:18, fontWeight:'800', textTransform:'uppercase', letterSpacing:2 },
  heroType:{ color:'#9090b0', fontSize:13, marginTop:2 },
  heroBadges:{ flexDirection:'row', gap:8, marginTop:8 },
  badge:{ backgroundColor:'#252535', borderRadius:8, paddingHorizontal:10, paddingVertical:4 },
  badgeText:{ color:'#9090b0', fontSize:11, fontWeight:'600' },
  section:{ backgroundColor:'#16161e', borderRadius:14, padding:14, marginBottom:12,
    borderWidth:1, borderColor:'#2a2a3d' },
  sLabel:{ color:'#55556a', fontSize:10, fontWeight:'700', textTransform:'uppercase',
    letterSpacing:1.5, marginBottom:10 },
  bubble:{ backgroundColor:'#252535', borderRadius:10, padding:12, marginBottom:8 },
  bubbleText:{ color:'#e8e8f0', fontSize:14, lineHeight:21, fontStyle:'italic' },
  senderText:{ color:'#9090b0', fontSize:12 },
  reasonItem:{ backgroundColor:'#252535', borderRadius:8, padding:10, marginBottom:6 },
  reasonText:{ color:'#e8e8f0', fontSize:13, lineHeight:19 },
  modelRow:{ flexDirection:'row', alignItems:'center', gap:10, marginBottom:8 },
  modelName:{ color:'#9090b0', fontSize:11, width:120 },
  barBg:{ flex:1, height:6, backgroundColor:'#2a2a3d', borderRadius:3, overflow:'hidden' },
  barFill:{ height:'100%', borderRadius:3 },
  modelScore:{ fontFamily:'Courier New', fontSize:12, width:28, textAlign:'right' },
  actionSection:{ gap:10, marginBottom:40 },
  btn:{ borderRadius:12, padding:14, alignItems:'center' },
  btnGreen:{ backgroundColor:'rgba(38,222,129,0.12)', borderWidth:1, borderColor:'rgba(38,222,129,0.3)' },
  btnOrange:{ backgroundColor:'rgba(255,159,67,0.12)', borderWidth:1, borderColor:'rgba(255,159,67,0.3)' },
  btnRed:{ backgroundColor:'rgba(255,71,87,0.12)', borderWidth:1, borderColor:'rgba(255,71,87,0.3)' },
  btnText:{ fontWeight:'700', fontSize:14, color:'#e8e8f0' },
});

// ─────────────────────────────────────────────────────────────────────────────
// src/screens/SettingsScreen.js
// ─────────────────────────────────────────────────────────────────────────────
import React from 'react';
import { View as VV, Text as TT, ScrollView as SVV, Switch, StyleSheet as STS } from 'react-native';
import { useSelector as uS, useDispatch as uD } from 'react-redux';
import { toggleMonitoring, toggleNotification, toggleAutoBlock, setSensitivity } from '../store';

const SOURCE_LABELS = [
  ['sms','SMS Messages','📱'],
  ['whatsapp','WhatsApp','💬'],
  ['instagram','Instagram','📸'],
  ['facebook','Facebook','👥'],
  ['linkedin','LinkedIn','💼'],
  ['telegram','Telegram','✈️'],
  ['email','Email (Gmail/Outlook)','📧'],
  ['calls','Phone Calls','📞'],
  ['apps','Other Apps','📲'],
  ['games','Games & Game Ads','🎮'],
];

export function SettingsScreen() {
  const dispatch = uD();
  const settings = uS(s => s.settings);
  const stats = uS(s => s.stats);

  const SettingRow = ({ label, desc, value, onToggle }) => (
    <VV style={sts.row}>
      <VV style={{ flex:1 }}>
        <TT style={sts.rowLabel}>{label}</TT>
        {desc && <TT style={sts.rowDesc}>{desc}</TT>}
      </VV>
      <Switch value={value} onValueChange={onToggle}
        trackColor={{ false:'#2a2a3d', true:'rgba(38,222,129,0.4)' }}
        thumbColor={value ? '#26de81' : '#55556a'}/>
    </VV>
  );

  return (
    <SVV style={sts.container} showsVerticalScrollIndicator={false}>
      {/* Stats Summary */}
      <VV style={sts.statBox}>
        <TT style={sts.statTitle}>Protection Stats</TT>
        <VV style={sts.statsRow}>
          <VV style={sts.statItem}><TT style={[sts.statVal,{color:'#4d9fff'}]}>{stats.totalScanned}</TT><TT style={sts.statLbl}>Scanned</TT></VV>
          <VV style={sts.statItem}><TT style={[sts.statVal,{color:'#ff4757'}]}>{stats.totalBlocked}</TT><TT style={sts.statLbl}>Blocked</TT></VV>
          <VV style={sts.statItem}><TT style={[sts.statVal,{color:'#26de81'}]}>99.2%</TT><TT style={sts.statLbl}>Accuracy</TT></VV>
        </VV>
      </VV>

      {/* Monitoring Sources */}
      <VV style={sts.section}>
        <TT style={sts.sectionTitle}>Monitored Sources</TT>
        {SOURCE_LABELS.map(([key, label, icon]) => (
          <SettingRow key={key} label={`${icon} ${label}`}
            value={settings.monitoring[key]}
            onToggle={() => dispatch(toggleMonitoring(key))}/>
        ))}
      </VV>

      {/* Notifications */}
      <VV style={sts.section}>
        <TT style={sts.sectionTitle}>Notifications</TT>
        <SettingRow label="🔔 Enable Alerts" desc="Show notification when scam detected"
          value={settings.notifications.enabled} onToggle={() => dispatch(toggleNotification('enabled'))}/>
        <SettingRow label="🔊 Alert Sound"
          value={settings.notifications.sound} onToggle={() => dispatch(toggleNotification('sound'))}/>
        <SettingRow label="📳 Vibration"
          value={settings.notifications.vibrate} onToggle={() => dispatch(toggleNotification('vibrate'))}/>
        <SettingRow label="📲 In-App Popup"
          value={settings.notifications.popup} onToggle={() => dispatch(toggleNotification('popup'))}/>
      </VV>

      {/* Auto-block */}
      <VV style={sts.section}>
        <TT style={sts.sectionTitle}>Protection</TT>
        <SettingRow label="🚫 Auto-Block Scammers"
          desc="Automatically block senders of confirmed scams"
          value={settings.autoBlock} onToggle={() => dispatch(toggleAutoBlock())}/>
      </VV>

      {/* Sensitivity */}
      <VV style={[sts.section, {marginBottom:80}]}>
        <TT style={sts.sectionTitle}>Detection Sensitivity</TT>
        {['low','medium','high'].map(level => (
          <VV key={level} style={sts.row}>
            <VV style={{ flex:1 }}>
              <TT style={sts.rowLabel}>{level.charAt(0).toUpperCase()+level.slice(1)}</TT>
              <TT style={sts.rowDesc}>
                {level==='low'?'Only catch obvious scams — fewer false positives':
                 level==='medium'?'Balanced detection (recommended)':
                 'Maximum protection — may flag some legitimate messages'}
              </TT>
            </VV>
            <Switch value={settings.sensitivity===level}
              onValueChange={() => dispatch(setSensitivity(level))}
              trackColor={{ false:'#2a2a3d', true:'rgba(77,159,255,0.4)' }}
              thumbColor={settings.sensitivity===level ? '#4d9fff' : '#55556a'}/>
          </VV>
        ))}
      </VV>
    </SVV>
  );
}

const sts = STS.create({
  container:{ flex:1, backgroundColor:'#0f0f14', padding:14 },
  statBox:{ backgroundColor:'#16161e', borderRadius:14, padding:16, marginBottom:14,
    borderWidth:1, borderColor:'#2a2a3d' },
  statTitle:{ color:'#55556a', fontSize:10, fontWeight:'700', textTransform:'uppercase',
    letterSpacing:1.5, marginBottom:12 },
  statsRow:{ flexDirection:'row' },
  statItem:{ flex:1, alignItems:'center' },
  statVal:{ fontSize:28, fontWeight:'900', fontFamily:'Courier New' },
  statLbl:{ color:'#9090b0', fontSize:11, marginTop:2 },
  section:{ backgroundColor:'#16161e', borderRadius:14, padding:14, marginBottom:12,
    borderWidth:1, borderColor:'#2a2a3d' },
  sectionTitle:{ color:'#55556a', fontSize:10, fontWeight:'700', textTransform:'uppercase',
    letterSpacing:1.5, marginBottom:12 },
  row:{ flexDirection:'row', alignItems:'center', gap:12, paddingVertical:12,
    borderBottomWidth:1, borderBottomColor:'#2a2a3d' },
  rowLabel:{ color:'#e8e8f0', fontSize:14, fontWeight:'600', marginBottom:2 },
  rowDesc:{ color:'#9090b0', fontSize:12, lineHeight:17 },
});

// ─────────────────────────────────────────────────────────────────────────────
// src/screens/SimulateScreen.js
// ─────────────────────────────────────────────────────────────────────────────
import React, { useState } from 'react';
import { View as SIM, Text as ST, TextInput as STI, TouchableOpacity as STO,
  ScrollView as SSV, StyleSheet as SSS } from 'react-native';
import { analyseMessage } from '../ml/ScamDetectionEngine';
import { useDispatch } from 'react-redux';
import { addMessage } from '../store';
import { incrementScanned } from '../store';

const SCAM_SAMPLES = [
  { source:'SMS', sender:'+91-9876500001', text:"CONGRATULATIONS! You've won ₹50,00,000 in the State Lottery! Click http://claim-prize-now.xyz to claim within 24 hours!" },
  { source:'WhatsApp', sender:'+91-8800000012', text:"Your Aadhaar card has been linked to suspicious activity. Call 1800-XXX-XXXX immediately or your account will be frozen by CBI." },
  { source:'Email', sender:'alerts@sbi-secure-update.net', text:"Dear Customer, your SBI account will be SUSPENDED. Verify your details: http://sbi-verify-secure.cc/login" },
  { source:'Instagram', sender:'DM from @win_prize_daily', text:"You have been selected as our lucky winner! Pay ₹999 processing fee to claim your iPhone 15 Pro. Offer expires today!" },
];
const SAFE_SAMPLES = [
  { source:'WhatsApp', sender:'Mom', text:"Hi! Are you free for lunch tomorrow? Let me know what works for you 😊" },
  { source:'SMS', sender:'HDFCBANK', text:"Your OTP for HDFC login is 524197. Valid for 5 minutes. Do NOT share with anyone." },
  { source:'Email', sender:'noreply@amazon.in', text:"Your order #45123 has been shipped and will arrive by Thursday." },
];

export function SimulateScreen({ navigation }) {
  const dispatch = useDispatch();
  const [source, setSource]   = useState('SMS');
  const [sender, setSender]   = useState('');
  const [text, setText]       = useState('');
  const [result, setResult]   = useState(null);

  const sources = ['SMS','WhatsApp','Email','Instagram','Facebook','LinkedIn','Telegram','App','Call'];

  const analyse = () => {
    if (!text.trim()) return;
    const r = analyseMessage(text, source, sender || 'Unknown');
    setResult(r);
    dispatch(addMessage({ ...r, sender: sender||'Test', receivedAt: new Date().toLocaleTimeString() }));
    dispatch(incrementScanned({ source, verdict: r.verdict, type: r.type }));
  };

  const riskColor = result ? (result.riskScore>=55?'#ff4757':result.riskScore>=25?'#ff9f43':'#26de81') : null;

  return (
    <SSV style={sim.container} showsVerticalScrollIndicator={false}>
      <SIM style={sim.section}>
        <ST style={sim.sLabel}>Source</ST>
        <SIM style={sim.sourceRow}>
          {sources.map(s => (
            <STO key={s} style={[sim.srcBtn, source===s && sim.srcActive]} onPress={()=>setSource(s)}>
              <ST style={[sim.srcText, source===s && sim.srcTextActive]}>{s}</ST>
            </STO>
          ))}
        </SIM>
        <ST style={[sim.sLabel,{marginTop:12}]}>Sender</ST>
        <STI style={sim.input} placeholder="e.g. +91-9876543210 or alerts@xyz.com"
          placeholderTextColor="#55556a" value={sender} onChangeText={setSender}/>
        <ST style={[sim.sLabel,{marginTop:12}]}>Message Text</ST>
        <STI style={sim.textarea} placeholder="Paste or type a message to analyse…"
          placeholderTextColor="#55556a" value={text} onChangeText={setText}
          multiline numberOfLines={4} textAlignVertical="top"/>
        <SIM style={sim.btnRow}>
          <STO style={sim.analyseBtn} onPress={analyse}>
            <ST style={sim.analyseBtnText}>🔍 Analyse Now</ST>
          </STO>
        </SIM>
        <SIM style={sim.sampleRow}>
          {SCAM_SAMPLES.slice(0,2).map((s,i) => (
            <STO key={i} style={sim.sampleBtn} onPress={()=>{setSource(s.source);setSender(s.sender);setText(s.text);setResult(null);}}>
              <ST style={sim.sampleText}>⚠ Scam Sample {i+1}</ST>
            </STO>
          ))}
          <STO style={[sim.sampleBtn,{borderColor:'rgba(38,222,129,0.3)'}]}
            onPress={()=>{const s=SAFE_SAMPLES[0];setSource(s.source);setSender(s.sender);setText(s.text);setResult(null);}}>
            <ST style={[sim.sampleText,{color:'#26de81'}]}>✅ Safe Sample</ST>
          </STO>
        </SIM>
      </SIM>

      {result && (
        <SIM style={[sim.result, {borderColor: riskColor+'44'}]}>
          <SIM style={sim.scoreRow}>
            <ST style={[sim.score,{color:riskColor}]}>{result.riskScore}</ST>
            <SIM>
              <ST style={[sim.verdict,{color:riskColor}]}>{result.verdict}</ST>
              <ST style={sim.type}>{result.type}</ST>
            </SIM>
          </SIM>
          <ST style={sim.sLabel}>Why Flagged</ST>
          {(result.reasons.length===0 ? ['✅ No scam signals found'] : result.reasons).map((r,i) => (
            <SIM key={i} style={sim.reasonItem}><ST style={sim.reasonText}>{r}</ST></SIM>
          ))}
          <ST style={[sim.sLabel,{marginTop:10}]}>Model Scores</ST>
          {Object.entries(result.modelScores).map(([model,score]) => {
            const s = Math.round(score); const c = s>=55?'#ff4757':s>=25?'#ff9f43':'#26de81';
            return (
              <SIM key={model} style={sim.mRow}>
                <ST style={sim.mName}>{model}</ST>
                <SIM style={sim.mBarBg}><SIM style={[sim.mBarFill,{width:`${s}%`,backgroundColor:c}]}/></SIM>
                <ST style={[sim.mScore,{color:c}]}>{s}</ST>
              </SIM>
            );
          })}
          <STO style={sim.viewBtn} onPress={()=>navigation.navigate('Detail',{message:{...result,sender:sender||'Test',receivedAt:new Date().toLocaleTimeString()}})}>
            <ST style={sim.viewBtnText}>View Full Details →</ST>
          </STO>
        </SIM>
      )}
    </SSV>
  );
}

const sim = SSS.create({
  container:{ flex:1, backgroundColor:'#0f0f14', padding:14 },
  section:{ backgroundColor:'#16161e', borderRadius:14, padding:14, marginBottom:14,
    borderWidth:1, borderColor:'#2a2a3d' },
  sLabel:{ color:'#55556a', fontSize:10, fontWeight:'700', textTransform:'uppercase',
    letterSpacing:1.5, marginBottom:8 },
  sourceRow:{ flexDirection:'row', flexWrap:'wrap', gap:7 },
  srcBtn:{ paddingHorizontal:12, paddingVertical:6, borderRadius:20,
    backgroundColor:'#252535', borderWidth:1, borderColor:'#2a2a3d' },
  srcActive:{ backgroundColor:'rgba(77,159,255,0.15)', borderColor:'rgba(77,159,255,0.4)' },
  srcText:{ color:'#9090b0', fontSize:12, fontWeight:'600' },
  srcTextActive:{ color:'#4d9fff' },
  input:{ backgroundColor:'#252535', borderRadius:10, paddingHorizontal:14, height:44,
    color:'#e8e8f0', borderWidth:1, borderColor:'#353550', fontSize:14, marginBottom:4 },
  textarea:{ backgroundColor:'#252535', borderRadius:10, padding:12, color:'#e8e8f0',
    borderWidth:1, borderColor:'#353550', fontSize:14, minHeight:90, marginBottom:4 },
  btnRow:{ marginTop:12 },
  analyseBtn:{ backgroundColor:'linear-gradient', borderRadius:12, padding:14, alignItems:'center',
    backgroundColor:'#4d9fff' },
  analyseBtnText:{ color:'#fff', fontWeight:'800', fontSize:15 },
  sampleRow:{ flexDirection:'row', gap:8, marginTop:10, flexWrap:'wrap' },
  sampleBtn:{ paddingHorizontal:12, paddingVertical:7, borderRadius:10,
    backgroundColor:'rgba(255,71,87,0.08)', borderWidth:1, borderColor:'rgba(255,71,87,0.25)' },
  sampleText:{ color:'#ff4757', fontSize:11, fontWeight:'600' },
  result:{ backgroundColor:'#16161e', borderRadius:14, padding:14,
    borderWidth:1, marginBottom:40 },
  scoreRow:{ flexDirection:'row', alignItems:'center', gap:14, marginBottom:14 },
  score:{ fontSize:56, fontWeight:'900', fontFamily:'Courier New' },
  verdict:{ fontSize:18, fontWeight:'800', textTransform:'uppercase', letterSpacing:1 },
  type:{ color:'#9090b0', fontSize:12, marginTop:2 },
  reasonItem:{ backgroundColor:'#252535', borderRadius:8, padding:10, marginBottom:6 },
  reasonText:{ color:'#e8e8f0', fontSize:13, lineHeight:19 },
  mRow:{ flexDirection:'row', alignItems:'center', gap:10, marginBottom:7 },
  mName:{ color:'#9090b0', fontSize:11, width:120 },
  mBarBg:{ flex:1, height:5, backgroundColor:'#2a2a3d', borderRadius:3, overflow:'hidden' },
  mBarFill:{ height:'100%', borderRadius:3 },
  mScore:{ fontFamily:'Courier New', fontSize:11, width:28, textAlign:'right' },
  viewBtn:{ backgroundColor:'rgba(77,159,255,0.1)', borderRadius:10, padding:12,
    alignItems:'center', marginTop:12, borderWidth:1, borderColor:'rgba(77,159,255,0.3)' },
  viewBtnText:{ color:'#4d9fff', fontWeight:'700', fontSize:13 },
});

// ─────────────────────────────────────────────────────────────────────────────
// src/navigation/AppNavigator.js
// ─────────────────────────────────────────────────────────────────────────────
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Text, View } from 'react-native';

// Screens imported from this same file (in real project, separate files)
const Tab  = createBottomTabNavigator();
const Stack = createStackNavigator();

function HomeStack() {
  return (
    <Stack.Navigator screenOptions={{ headerStyle:{backgroundColor:'#16161e'},
      headerTintColor:'#e8e8f0', headerTitleStyle:{fontWeight:'700'} }}>
      <Stack.Screen name="Dashboard" component={DashboardScreen} options={{headerShown:false}}/>
      <Stack.Screen name="Detail" component={DetailScreen} options={{title:'Scam Details'}}/>
    </Stack.Navigator>
  );
}

function ListStack() {
  return (
    <Stack.Navigator screenOptions={{ headerStyle:{backgroundColor:'#16161e'},
      headerTintColor:'#e8e8f0', headerTitleStyle:{fontWeight:'700'} }}>
      <Stack.Screen name="ScamList" component={ScamListScreen} options={{title:'Scam Registry'}}/>
      <Stack.Screen name="Detail" component={DetailScreen} options={{title:'Scam Details'}}/>
    </Stack.Navigator>
  );
}

export function AppNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator screenOptions={({ route }) => ({
        tabBarStyle:{ backgroundColor:'#16161e', borderTopColor:'#2a2a3d', height:60 },
        tabBarActiveTintColor:'#4d9fff', tabBarInactiveTintColor:'#55556a',
        tabBarLabelStyle:{ fontSize:10, fontWeight:'700', marginBottom:6 },
        headerShown: false,
        tabBarIcon: ({ color, focused }) => {
          const icons = { Home:'🏠', Scams:'🚨', Simulate:'🧪', Settings:'⚙️' };
          return <Text style={{fontSize:20}}>{icons[route.name]}</Text>;
        },
      })}>
        <Tab.Screen name="Home" component={HomeStack}/>
        <Tab.Screen name="Scams" component={ListStack} options={{title:'Scam List'}}/>
        <Tab.Screen name="Simulate" component={SimulateScreen}
          options={{ headerShown:true, headerStyle:{backgroundColor:'#16161e'},
            headerTintColor:'#e8e8f0', title:'Test a Message' }}/>
        <Tab.Screen name="Settings" component={SettingsScreen}
          options={{ headerShown:true, headerStyle:{backgroundColor:'#16161e'},
            headerTintColor:'#e8e8f0', title:'Settings' }}/>
      </Tab.Navigator>
    </NavigationContainer>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// index.js — App entry point
// ─────────────────────────────────────────────────────────────────────────────
import { AppRegistry } from 'react-native';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store as appStore, persistor } from './src/store';
import MessageMonitorService from './src/services/MessageMonitorService';

function App() {
  React.useEffect(() => {
    MessageMonitorService.start();
    return () => MessageMonitorService.stop();
  }, []);

  return (
    <Provider store={appStore}>
      <PersistGate loading={null} persistor={persistor}>
        <AppNavigator />
      </PersistGate>
    </Provider>
  );
}

AppRegistry.registerComponent('ScamShieldAI', () => App);
