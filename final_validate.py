import urllib.request, json, os
from collections import defaultdict

os.environ['NO_PROXY'] = 'ifzq.gtimg.cn'
p = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(p)

# === TENCENT DAILY ===
t = json.loads(p.open('https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600519,day,,,500,qfq', timeout=15).read().decode())
trows = t['data']['sh600519']['qfqday']
T = {}
for r in trows:
    T[r[0]] = {'o':float(r[1]),'c':float(r[2]),'h':float(r[3]),'l':float(r[4])}

# === SINA 60min → DAILY ===
sdata = json.loads(p.open('http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=60&ma=no&datalen=4000', timeout=20).read().decode())
g=defaultdict(list)
for b in sdata: g[b['day'].split(' ')[0]].append(b)
sd=sorted(g.keys())
S={}
for i,d in enumerate(sd):
    grp=g[d]; prev=g[sd[i-1]][-1]['close'] if i>0 else grp[0]['open']
    S[d]={'o':float(grp[0]['open']),'c':float(grp[-1]['close']),'h':float(max(x['high'] for x in grp)),'l':float(min(x['low'] for x in grp)),'pc':float(prev)}

DATES=['2026-04-03','2026-04-02','2026-04-01','2026-03-31','2026-02-28',
        '2026-01-23','2025-12-31','2025-11-28','2025-10-31']

def pd(a,b): return abs(a-b)/a*100 if a else 0

print("="*90)
print("  腾讯日线 vs 新浪60分钟衍生日线 — 贵州茅台(600519)")
print(f"  Tencent: {len(T)} days | Sina60: {len(S)} days ({sd[0]}~{sd[-1]})")
print("="*90)
print(f"  {'Date':<12}│{'OpenΔ%':>9}{'CloseΔ%':>10}{'HighΔ%':>9}{'LowΔ%':>9}│{'Gap%':>8}│{'T_Open':>10}{'S60_Open':>10}")
print("  "+"─"*85)

ALL=[]
for td in DATES:
    tt=T.get(td); ss=S.get(td)
    if not tt or not ss: continue
    o=pd(tt['o'],ss['o']); c=pd(tt['c'],ss['c']); h=pd(tt['h'],ss['h']); l=pd(tt['l'],ss['l'])
    gap=((tt['o']-ss['pc'])/ss['pc']*100) if ss['pc']>0 else 0
    fl="✅" if max(o,c,h,l)<0.3 else ("⚠️" if max(o,c,h,l)<1.0 else "❌")
    print(f"  {td:<12}│{o:>8.4f}% {c:>9.4f}% {h:>8.4f}% {l:>8.4f}%│{gap:>7.3f}%│{tt['o']:>10.2f}{ss['o']:>10.2f} {fl}")
    ALL.append((o,c,h,l,gap))

print("\n"+"="*90)
print("  SUMMARY")
print("="*90)
for lab,i in [("Open",0),("Close",1),("High",2),("Low",3)]:
    v=[x[i] for x in ALL]
    print(f"  {lab}: avg={sum(v)/len(v):.4f}%  max={max(v):.4f}%  min={min(v):.4f}%")
gaps=[x[4] for x in ALL]
print(f"  Gap%: avg={sum(gaps)/len(gaps):.4f}%  max_abs={max(abs(x) for x in gaps):.4f}%")
for th,lb in [(0.1,"<0.1%"),(0.3,"<0.3%"),(0.5,"<0.5%"),(1.0,"<1.0%")]:
    cnt=sum(1 for x in ALL if max(x[:4])<th)
    print(f"  All fields {lb}: {cnt}/{len(ALL)} ({cnt/len(ALL)*100:.0f}%)")
