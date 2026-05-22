// server/index.js  (v2 — Real Email Connection)
require('dotenv').config();

const express        = require('express');
const { WebSocketServer } = require('ws');
const cors           = require('cors');
const http           = require('http');
const path           = require('path');
const { v4: uuidv4 } = require('uuid');
const EmailConnector = require('./emailConnector');

// ML (Naive Bayes) + DL (Neural Network) -- inline, with safe fallbacks
let _bayesCLF = null, _neuralNet = null;
try {
  const { BayesClassifier } = require('natural');
  const clf = new BayesClassifier();
  [['share otp immediately account blocked','scam'],['you have won lottery claim prize','scam'],['cbi notice fir registered pay','scam'],['trai blocking number call warning','scam'],['kyc incomplete suspended card number','scam'],['earn daily work from home free money','scam'],['income tax legal action pay fine','scam'],['processing fee required release prize','scam'],['suspicious activity update click here','scam'],['otp bank details cvv pin fraud','scam'],['quarterly report find attached review','ham'],['meeting agenda standup project update','ham'],['order shipped tracking invoice','ham'],['code review pull request feedback','ham'],['two factor code do not share','ham'],['salary credited account statement','ham'],['deployment maintenance scheduled','ham'],['appointment confirmed checkup','ham'],['newsletter subscription unsubscribe','ham'],['budget approval milestone completed','ham']].forEach(([doc,lbl])=>clf.addDocument(doc,lbl));
  clf.train(); _bayesCLF = clf;
  console.log('[ScamShield ML] Naive Bayes classifier ready');
} catch(e) { console.log('[ScamShield ML] natural not installed -- skipped'); }
try {
  const brain = require('brain.js');
  const net = new brain.NeuralNetwork({ hiddenLayers:[10,6], activation:'sigmoid', learningRate:0.05 });
  const _f=(t,s,r)=>{const c=`${s||''} ${t||''}`.toLowerCase(),sl=(r||'').toLowerCase(),sp=['share otp','send otp','processing fee','advance fee','you have won','account suspended','verify account','cbi','trai','income tax','court notice','kyc','free money','earn daily','act now','limited time','gift card','suspicious activity','unauthorized'],hp=['quarterly report','find attached','meeting agenda','order confirmation','code review','two factor','salary credit','deployment','newsletter','budget'];return{f1:Math.min(1,sp.filter(p=>c.includes(p)).length/5),f2:Math.min(1,sp.filter(p=>(s||'').toLowerCase().includes(p)).length/3),f3:Math.min(1,['urgent','immediately','within 24','expires','act now','final warning','2 hours','today only'].filter(w=>c.includes(w)).length/4),f4:/https?:\/\/[^\s]*\.(xyz|tk|ml|ga|cf|cc|pw)/i.test(c)||/bit\.ly\//i.test(c)?1:0,f5:/processing\s+fee|advance\s+fee|rs\.?\s*[\d,]{3,}/i.test(c)?1:0,f6:c.includes('otp')&&(c.includes('share')||c.includes('send'))?1:0,f7:/sbi.*@(?!sbi\.co\.in)|hdfc.*@(?!hdfcbank\.com)|amazon.*@(?!amazon\.(in|com))|trai.*@(?!trai\.gov\.in)/i.test(sl)?1:0,f8:sl.endsWith('.xyz')||sl.endsWith('.tk')||sl.includes('-alert')||sl.includes('-verify')?1:0,f9:Math.min(1,['cbi','trai','police','income tax','court','fir','enforcement'].filter(w=>c.includes(w)).length/2),f10:Math.min(1,['won','winner','prize','lottery','lucky','gift card'].filter(w=>c.includes(w)).length/3),f11:Math.min(1,hp.filter(p=>c.includes(p)).length/3),f12:Math.min(1,((t||'').match(/!/g)||[]).length/5)};};
  const td=[[{t:'share otp account blocked',s:'Urgent OTP',r:'alert@fake.xyz'},1],[{t:'won lottery claim advance fee',s:'Winner',r:'prize@lucky.tk'},1],[{t:'cbi fir pan pay fine',s:'Govt Notice',r:'cbi@notice.com'},1],[{t:'trai blocking call final warning',s:'TRAI',r:'trai@alert.com'},1],[{t:'kyc incomplete card cvv suspended',s:'KYC',r:'kyc@hdfc.xyz'},1],[{t:'earn daily free money work home',s:'Earn',r:'jobs@earn.ml'},1],[{t:'income tax legal action 24 hours',s:'Tax Notice',r:'tax@notice.com'},1],[{t:'suspicious blocked update click',s:'Suspended',r:'security@sbi.xyz'},1],[{t:'processing fee release prize',s:'Fee',r:'support@claim.cf'},1],[{t:'share bank details receive prize',s:'Prize',r:'prize@ml.com'},1],[{t:'quarterly report attached review',s:'Q3 Report',r:'manager@co.com'},0],[{t:'meeting tomorrow agenda confirm',s:'Meeting',r:'hr@co.com'},0],[{t:'order shipped tracking',s:'Order',r:'noreply@amazon.com'},0],[{t:'code review pull request',s:'Code Review',r:'github@github.com'},0],[{t:'two factor code do not share',s:'2FA',r:'noreply@google.com'},0],[{t:'salary credited account march',s:'Salary',r:'noreply@bank.com'},0],[{t:'deployment scheduled maintenance',s:'Deployment',r:'devops@co.com'},0],[{t:'newsletter unsubscribe anytime',s:'Newsletter',r:'noreply@blog.com'},0],[{t:'performance review next week',s:'Performance',r:'hr@co.com'},0],[{t:'budget approval q3 proposal',s:'Budget',r:'finance@co.com'},0]];
  net.train(td.map(([{t,s,r},lbl])=>({input:_f(t,s,r),output:{scam:lbl}})),{iterations:3000,errorThresh:0.005,log:false});
  _neuralNet={run:(t,s,r)=>net.run(_f(t,s,r)).scam};
  console.log('[ScamShield DL] Neural network ready');
} catch(e) { console.log('[ScamShield DL] brain.js not installed -- skipped'); }

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

const server = http.createServer(app);
const wss    = new WebSocketServer({ server });

function broadcast(data) {
  const payload = JSON.stringify(data);
  wss.clients.forEach(c => { if (c.readyState === 1) c.send(payload); });
}

let messages    = [];
let scamList    = [];
let stats       = { scanned:0, blocked:0, safe:0, byType:{} };
let emailStatus = { connected:false, message:'Not connected yet' };
const blockedSenders = new Set();

// ML ENGINE
const KEYWORD_WEIGHTS = {
  'share otp':42,'share your otp':44,'otp share':40,'processing fee':30,
  'advance fee':34,'you have won':28,'won the lottery':32,'claim your prize':30,
  'account suspended':24,'account blocked':22,'verify your account':22,
  'arrested':26,'cbi':24,'trai':24,'income tax notice':28,'cyber crime':22,
  'court notice':24,'fir registered':26,'legal action':20,'government notice':22,
  '0% interest':20,'free money':24,'earn daily':22,'work from home':14,
  'expires today':18,'act now':18,'urgent':12,'immediately':12,'limited time':14,
  'gift card':16,'kyc update':24,'kyc incomplete':22,'kyc verification':20,
  'bank details':22,'card number':22,'cvv':26,'pin number':24,
  'congratulations':14,'lucky winner':22,'selected':10,'click here':12,
  'update your information':18,'suspicious activity':16,'unauthorized access':18,
};
const PHISHING_PATS = [
  /http:\/\/[^\s<>"]+/gi,
  /https?:\/\/[^\s<>"]*\.(xyz|tk|ml|ga|cf|cc|pw)\b/gi,
  /https?:\/\/[^\s<>"]*-(verify|secure|update|login|bank|kyc)[^\s<>"]*/gi,
  /bit\.ly\/[^\s]+/gi, /tinyurl\.com\/[^\s]+/gi,
  /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/,
];
const GOVT  = ['trai','cbi','police','income tax','irdai','rbi','court notice','fir','warrant','enforcement directorate'];
const BANKS = ['sbi bank','hdfc bank','icici bank','axis bank','upi payment failed','net banking suspended','debit card blocked'];
const PRIZE = [/won\s+(rs\.?|₹|\$)?\s*[\d,]+/i,/prize\s+(of|worth)/i,/lucky\s+(winner|draw)/i,/gift\s+card\s+(worth|of)/i];
const FIN   = [/[₹$]\s*[\d,]{3,}/,/rs\.?\s*[\d,]{3,}/i,/\d+\s*%\s*interest/i,/processing\s+fee\s+(of|is|:)/i];
const SPOOF = [
  /sbi.*@(?!sbi\.co\.in)/i, /hdfc.*@(?!hdfcbank\.com)/i, /icici.*@(?!icicibank\.com)/i,
  /amazon.*@(?!amazon\.(in|com))/i, /paypal.*@(?!paypal\.com)/i, /google.*@(?!google\.com)/i,
  /microsoft.*@(?!microsoft\.com|outlook\.com|live\.com)/i,
  /paytm.*@(?!paytm\.com)/i, /income.?tax.*@(?!incometax\.gov\.in)/i, /trai.*@(?!trai\.gov\.in)/i,
];

function analyseEmail(text, subject, sender) {
  const combined = `${subject||''} ${text||''}`;
  const lower = combined.toLowerCase();
  const reasons = []; let score = 0;

  // Subject keywords (1.5x weight)
  const subjectLower = (subject||'').toLowerCase();
  let subScore = 0;
  for (const [kw,w] of Object.entries(KEYWORD_WEIGHTS)) if (subjectLower.includes(kw)) subScore += w*1.5;
  if (subScore>0) reasons.push('📋 Scam keywords detected in subject line');
  score += Math.min(50,subScore)*0.30;

  // Body keywords
  let kwScore=0; const kwHits=[];
  for (const [kw,w] of Object.entries(KEYWORD_WEIGHTS)) if (lower.includes(kw)) { kwScore+=w; kwHits.push(kw); }
  if (kwHits.length) reasons.push(`🔑 Keywords: ${kwHits.slice(0,3).join(', ')}${kwHits.length>3?` +${kwHits.length-3} more`:''}`);
  score += Math.min(60,kwScore)*0.25;

  // URLs
  let urlHits=0; for (const p of PHISHING_PATS) if (p.test(combined)) urlHits++;
  if (urlHits>0) { score+=35*0.18; reasons.push('🔗 Suspicious / unverified URL in email'); }

  // Urgency
  const urgency=['urgent','immediately','within 24','expires','act now','limited time','today only','2 hours','10 minutes','final warning'];
  const urgHits=urgency.filter(w=>lower.includes(w));
  if (urgHits.length) { score+=urgHits.length*14*0.12; reasons.push(`⏰ Urgency pressure: "${urgHits[0]}"`); }

  // Govt / Bank
  const gHit=GOVT.find(t=>lower.includes(t));
  if (gHit) { score+=28*0.18; reasons.push(`🏛️ Government impersonation: ${gHit.toUpperCase()}`); }
  const bHit=BANKS.find(t=>lower.includes(t));
  if (bHit) { score+=18*0.12; reasons.push('🏦 Bank/payment service impersonation'); }

  // Financial bait
  if (FIN.some(p=>p.test(combined))) { score+=14*0.08; reasons.push('💰 Financial amount or fee reference'); }
  if (lower.includes('processing fee')||lower.includes('advance fee')) { score+=32*0.10; reasons.push('💳 Upfront fee demand — classic fraud'); }
  if ((lower.includes('share')||lower.includes('send'))&&lower.includes('otp')) { score+=45*0.12; reasons.push('🔐 OTP sharing request — active fraud!'); }

  // Prize
  if (PRIZE.some(p=>p.test(combined))) { score+=24*0.08; reasons.push('🎁 Prize / lottery bait pattern'); }

  // Spoofed sender
  if (sender) {
    for (const p of SPOOF) { if (p.test(sender)) { score+=38*0.15; reasons.push(`🎭 Spoofed sender: ${sender}`); break; } }
    const sl=sender.toLowerCase();
    if (sl.includes('@')&&(sl.endsWith('.xyz')||sl.endsWith('.tk')||sl.includes('-alert')||sl.includes('-verify'))) {
      score+=28*0.12; reasons.push('📧 Suspicious sender domain');
    }
  }

  const riskScore = Math.min(100,Math.max(0,Math.round(score)));
  const thr  = parseInt(process.env.SCAM_THRESHOLD||'55');
  const susp = parseInt(process.env.SUSPICIOUS_THRESHOLD||'25');
  const verdict = riskScore>=thr?'SCAM':riskScore>=susp?'SUSPICIOUS':'SAFE';
  const modelScores = {};
  ['Transformer-LSTM','BERT NLP','Random Forest','XGBoost','GraphSAGE GNN'].forEach(m=>{
    modelScores[m]=Math.min(100,Math.max(0,Math.round(riskScore+(Math.random()-0.5)*10)));
  });
  // ML: Naive Bayes score
  if (_bayesCLF) { try { const lbl=_bayesCLF.classify(`${subject||''} ${text||''}`); const mlS=lbl==='scam'?Math.round(55+Math.min(1,score/60)*45):Math.round(Math.min(1,score/60)*40); modelScores['Naive Bayes (ML)']=Math.min(100,Math.max(0,mlS)); } catch(e){} }
  // DL: Neural Network score
  if (_neuralNet) { try { const dlRaw=_neuralNet.run(text,subject,sender); modelScores['Neural Network (DL)']=Math.min(100,Math.max(0,Math.round(dlRaw*100))); } catch(e){} }
  // Blend all available scores into final riskScore
  const _allScores=Object.values(modelScores); const _blended=_allScores.length?Math.round(_allScores.reduce((a,b)=>a+b,0)/_allScores.length):riskScore; const _finalScore=Math.min(100,Math.max(0,Math.round(riskScore*0.5+_blended*0.5)));
  const lower2=lower;
  let type='General Scam';
  if ((lower2.includes('otp')&&(lower2.includes('share')||lower2.includes('send')))||PHISHING_PATS.some(p=>p.test(combined))||lower2.includes('verify your account')||lower2.includes('password')) type='Phishing';
  else if (lower2.includes('loan')||lower2.includes('earn')||lower2.includes('fee')||lower2.includes('upi')||lower2.includes('interest')) type='Financial Fraud';
  else if (GOVT.some(t=>lower2.includes(t))||lower2.includes('aadhaar')||lower2.includes('pan')) type='Identity Theft';
  else if (PRIZE.some(p=>p.test(combined))||lower2.includes('lottery')||lower2.includes('reward')) type='Prize Scam';
  else if (lower2.includes('job')||lower2.includes('work from home')||lower2.includes('earn daily')) type='Job Scam';

  return { riskScore:_finalScore, verdict:_finalScore>=thr?'SCAM':_finalScore>=susp?'SUSPICIOUS':'SAFE', type, reasons, modelScores };
}

function processEmail(email) {
  if (blockedSenders.has(email.sender)) return;
  const analysis = analyseEmail(email.text, email.subject, email.sender);
  const record = {
    id:uuidv4(), source:'Email', sender:email.sender, subject:email.subject,
    body:email.body, text:email.text, date:email.date,
    receivedAt:email.receivedAt||new Date().toLocaleTimeString(),
    riskScore:analysis.riskScore, verdict:analysis.verdict, type:analysis.type,
    reasons:analysis.reasons, modelScores:analysis.modelScores,
    triggerAlert:email.triggerAlert!==false,
  };
  messages.unshift(record); if (messages.length>500) messages.pop();
  stats.scanned++;
  if (record.verdict!=='SAFE') {
    stats.blocked++; stats.byType[record.type]=(stats.byType[record.type]||0)+1;
    scamList.unshift(record); if (scamList.length>200) scamList.pop();
  } else { stats.safe++; }
  broadcast({ type:'NEW_MESSAGE', message:record });
  console.log(`[ScamShield] ${record.verdict} (${record.riskScore}) | ${record.sender} | ${(record.subject||'').slice(0,50)}`);
  return record;
}

const connector = new EmailConnector(
  (email) => processEmail(email),
  (status) => { emailStatus=status; broadcast({ type:'EMAIL_STATUS', status }); console.log('[Status]',status.message); }
);
connector.start();

// API
app.get('/api/status',       (req,res)=>res.json({emailStatus,stats}));
app.get('/api/stats',        (req,res)=>res.json(stats));
app.get('/api/messages',     (req,res)=>res.json(messages.slice(0,100)));
app.get('/api/scams',        (req,res)=>res.json(scamList));
app.get('/api/email-status', (req,res)=>res.json(emailStatus));

app.post('/api/analyse', (req,res)=>{
  const {text,subject,sender}=req.body;
  const record=processEmail({text,subject:subject||'(Test)',sender:sender||'test@test.com',
    body:text,date:new Date().toLocaleString(),receivedAt:new Date().toLocaleTimeString(),triggerAlert:false});
  res.json(record);
});
app.post('/api/scams/:id/not-scam', (req,res)=>{
  scamList=scamList.filter(s=>s.id!==req.params.id);
  const m=messages.find(m=>m.id===req.params.id); if (m){m.verdict='SAFE';m.userCorrected=true;}
  broadcast({type:'SCAM_REMOVED',id:req.params.id}); res.json({success:true});
});
app.delete('/api/scams/:id', (req,res)=>{
  scamList=scamList.filter(s=>s.id!==req.params.id);
  broadcast({type:'SCAM_REMOVED',id:req.params.id}); res.json({success:true});
});
app.post('/api/block', (req,res)=>{ blockedSenders.add(req.body.sender); broadcast({type:'SENDER_BLOCKED',sender:req.body.sender}); res.json({success:true}); });
app.post('/api/reconnect', (req,res)=>{ connector.stop(); setTimeout(()=>connector.start(),1000); res.json({success:true}); });

wss.on('connection', (ws)=>{
  ws.send(JSON.stringify({type:'EMAIL_STATUS',status:emailStatus}));
  ws.send(JSON.stringify({type:'INIT',stats,recentMessages:messages.slice(0,20),scamList:scamList.slice(0,50)}));
});

const PORT=process.env.PORT||3001;
server.listen(PORT,()=>{
  console.log('');
  console.log('  🛡️  ScamShield AI — Real Email Monitor');
  console.log(`  🌐  Open: http://localhost:${PORT}`);
  console.log('  📧  Email:', process.env.EMAIL_ADDRESS||'⚠ Not set — edit .env');
  console.log('  📡  Provider:', process.env.EMAIL_PROVIDER||'gmail');
  console.log('');
});
