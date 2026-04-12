"""Sina 60min vs 5min internal consistency validation."""
import urllib.request, json
from collections import defaultdict

PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(PROXY)

STOCKS = [("贵州茅台","sh600519"),("平安银行","sz000001"),("比亚迪","sz002594"),("宁德时代","sz300750"),("中国石油","sh601857")]
DATES = ["2026-04-03","2026-04-02","2026-04-01","2026-03-31","2026-02-28","2026-01-23","2025-12-31","2025-11-28","2025-10-31"]

def fetch(code, scale, n):
    url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={code}&scale={scale}&ma=no&datalen={n}"
    try:
        raw = PROXY.open(url, timeout=20).read().decode()
        if not raw.strip() or 'null' in raw: return []
        return [{'day':b['day'],'open':float(b['open']),'high':float(b['high']),'low':float(b['low']),'close':float(b['close']),'volume':float(b['volume'])} for b in json.loads(raw)]
    except: return []

def to_daily(bars):
    g=defaultdict(list)
    for b in bars: g[b['day'].split(' ')[0]].append(b)
    sd=sorted(g.keys())
    r={}
    for i,d in enumerate(sd):
        grp=g[d]
        r[d]={'o':grp[0]['open'],'c':grp[-1]['close'],'h':max(x['high'] for x in grp),'l':min(x['low'] for x in grp),'v':sum(x['volume'] for x in grp),'pc':g[sd[i-1]][-1]['close'] if i>0 else grp[0]['open']}
    return r

def pdiff(a,b): return abs(a-b)/a*100 if a else 0

print("="*100)
print("  新浪 60min × 5min — 内部一致性验证")
print("="*100)

ALL=[]

for name, code in STOCKS:
    print(f"\n{'─'*100}")
    print(f"  {name} ({code})")
    b60=fetch(code,"60",4000); b5=fetch(code,"5",2000)
    d60=to_daily(b60); d5=to_daily(b5)
    
    days60=sorted(d60.keys())
    from datetime import datetime as dt
    span=(dt.strptime(days60[-1],"%Y-%m-%d")-dt.strptime(days60[0],"%Y-%m-%d")).days if len(days60)>=2 else 0
    print(f"  60min:{len(b60):>5}bars→{len(d60):>4}days | 跨度{span:>5}天≈{span/30.44:.1f}月 | Layer1需580天:{'✅'if span>=580 else '❌'}")
    print(f"  5min: {len(b5):>5}bars→{len(d5):>4}days")
    
    print(f"\n  {'Date':<12}│{'OΔ%':>8}{'CΔ%':>9}{'HΔ%':>8}{'LΔ%':>8}│{'Gap%':>7}│{'#60m':>6}{'#5m':>6}")
    print('  '+'─'*50)
    
    for td in DATES:
        if td not in d60 or td not in d5: continue
        a,b=d60[td],d5[td]
        o=pdiff(a['o'],b['o']); c=pdiff(a['c'],b['c']); h=pdiff(a['h'],b['h']); l=pdiff(a['l'],b['l'])
        gap=((a['o']-a['pc'])/a['pc']*100) if a['pc']>0 else 0
        c60=sum(1 for x in b60 if x['day'].startswith(td))
        c5=sum(1 for x in b5 if x['day'].startswith(td))
        flag="" if max(o,c,h,l)<0.3 else " ⚠️"
        print(f"  {td:<12}│{o:>7.3f}%{flag}{c:>8.3f}%{flag}{h:>7.3f}%{flag}{l:>7.3f}%{flag}│{gap:>6.3f}%│{c60:>6}{c5:>6}")
        ALL.append({'s':name,'d':td,'o':o,'c':c,'h':h,'l':l,'gap':gap})

print("\n\n"+"="*100)
print("  SUMMARY")
print("="*100)
for lab,k in [("Open","o"),("Close","c"),("High","h"),("Low","l")]:
    v=[r[k] for r in ALL]
    print(f"  {lab}: avg={sum(v)/len(v):.4f}%  max={max(v):.4f}%  min={min(v):.4f}%  n={len(v)}")
gaps=[r['gap'] for r in ALL]
print(f"  Gap(prev_close→next_open): avg={sum(gaps)/len(gaps):.4f}%  max_abs={max(abs(x) for x in gaps):.4f}%")
ok=sum(1 for r in ALL if max(r['o'],r['c'],r['h'],r['l'])<0.3)
print(f"\n  ✅ All fields <0.3%: {ok}/{len(ALL)} ({ok/len(ALL)*100:.0f}%)")
