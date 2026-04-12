"""Tencent Daily vs Sina 60min-derived-daily direct comparison."""
import urllib.request, json, os
from collections import defaultdict

# Tencent needs NO_PROXY for VPN compatibility
os.environ['NO_PROXY'] = 'ifzq.gtimg.cn,stock.gtimg.cn,gtimg.cn'
PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))

STOCKS = [("sh600519","600519"),("sz000001","000001"),("sz002594","002594")]
DATES = ["2026-04-03","2026-04-02","2026-04-01","2026-03-31","2026-02-28",
         "2026-01-23","2025-12-31","2025-11-28","2025-10-31"]

def fetch_tencent(code, n=320):
    url=f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,{n},qfq"
    try:
        data=json.loads(PROXY.open(url,timeout=15).read().decode())
        rows=data['data'][code]['qfqday']
        return [{'date':r[0],'open':float(r[1]),'close':float(r[2]),'high':float(r[3]),'low':float(r[4]),'vol':float(r[5])} for r in rows]
    except Exception as e:
        print(f"  Tencent err: {e}")
        return []

def fetch_sina60(code, n=4000):
    url=f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={code}&scale=60&ma=no&datalen={n}"
    try:
        raw=PROXY.open(url,timeout=20).read().decode()
        if not raw.strip() or 'null' in raw: return []
        return [{'day':b['day'],'open':float(b['open']),'high':float(b['high']),'low':float(b['low']),'close':float(b['close']),'volume':float(b['volume'])} for b in json.loads(raw)]
    except: return []

def to_daily(bars):
    g=defaultdict(list)
    for b in bars: g[b['day'].split(' ')[0]].append(b)
    sd=sorted(g.keys())
    r={}
    for i,d in enumerate(sd):
        grp=g[d]; prev=g[sd[i-1]][-1]['close'] if i>0 else grp[0]['open']
        r[d]={'o':grp[0]['open'],'c':grp[-1]['close'],'h':max(x['high'] for x in grp),'l':min(x['low'] for x in grp),'v':sum(x['volume'] for x in grp),'pc':prev}
    return r

def pdiff(a,b): return abs(a-b)/a*100 if a else 0

print("="*95)
print("  腾讯日线 vs 新浪60分钟衍生日线 — 直接对比")
print("="*95)

ALL=[]
for tc, name in STOCKS:
    print(f"\n{'─'*95}")
    print(f"  {name} (tc={tc})")
    
    tdata=fetch_tencent(tc); sdata=fetch_sina60(tc.replace('sh','').replace('sz',''),4000)
    print(f"  DEBUG: tdata={len(tdata)} items, sdata={len(sdata)} bars")
    if not tdata:
        print(f"  DEBUG: Trying direct tencent call...")
        # Direct fallback
        try:
            url=f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tc},day,,,500,qfq"
            raw=PROXY.open(url,timeout=15).read().decode()
            d2=json.loads(raw)
            rows=d2['data'][tc]['qfqday']
            tdata=[{'date':r[0],'open':float(r[1]),'close':float(r[2]),'high':float(r[3]),'low':float(r[4]),'vol':float(r[5])} for r in rows]
            print(f"  DEBUG: fallback got {len(tdata)} rows")
        except Exception as e2:
            print(f"  DEBUG: fallback also failed: {e2}")
    sd=to_daily(sdata)
    
    # Normalize tencent dates: "2026-04-03"
    tlookup={}
    for r in tdata:
        d=r['date'].replace('-','')
        key=f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        tlookup[key]=r
    
    print(f"  Tencent: {len(tdata)} days | Sina60→daily: {len(sd)} days")
    print(f"\n  {'Date':<12}│{'OpenΔ%':>9}{'CloseΔ%':>10}{'HighΔ%':>9}{'LowΔ%':>9}│{'Gap%':>8}│{'T_O':>10}{'S60_O':>10}│{'Match?':>7}")
    print('  '+'─'*50)
    
    for td in DATES:
        t=tlookup.get(td)
        s=sd.get(td)
        if not t or not s: continue
        
        o=pdiff(t['open'],s['o']); c=pdiff(t['close'],s['c']); h=pdiff(t['high'],s['h']); l=pdiff(t['low'],s['l'])
        gap=((t['open']-s['pc'])/s['pc']*100) if s['pc']>0 else 0
        ok="✅" if max(o,c,h,l)<0.3 else ("⚠️" if max(o,c,h,l)<1.0 else "❌")
        
        print(f"  {td:<12}│{o:>8.4f}% {c:>9.4f}% {h:>8.4f}% {l:>8.4f}%│{gap:>7.3f}%│{t['open']:>10.2f}{s['o']:>10.2f}│{ok:>7}")
        ALL.append({'stock':name,'d':td,'o':o,'c':c,'h':h,'l':l,'gap':gap})

print("\n\n"+"="*95)
print("  SUMMARY — 腾讯日线 vs 新浪60分钟线")
print("="*95)
for lab,k in [("Open","o"),("Close","c"),("High","h"),("Low","l")]:
    v=[r[k] for r in ALL]
    print(f"  {lab}: avg={sum(v)/len(v):.4f}%  max={max(v):.4f}%  min={min(v):.4f}%")
gaps=[r['gap'] for r in ALL]
print(f"  Gap%: avg={sum(gaps)/len(gaps):.4f}%  max_abs={max(abs(x) for x in gaps):.4f}%")
for thresh,label in [(0.1,"<0.1%"),(0.3,"<0.3%"),(0.5,"<0.5%"),(1.0,"<1.0%")]:
    cnt=sum(1 for r in ALL if max(r['o'],r['c'],r['h'],r['l'])<thresh)
    print(f"  All fields {label}: {cnt}/{len(ALL)} ({cnt/len(ALL)*100:.0f}%)")

# Show any outliers >0.5%
outliers=[r for r in ALL if max(r['o'],r['c'],r['h'],r['l'])>=0.5]
if outliers:
    print(f"\n  ⚠️ Outliers (>0.5%):")
    for r in outliers:
        print(f"    {r['stock']}@{r['d']}: O={r['o']:.3f}% C={r['c']:.3f}% H={r['h']:.3f}% L={r['l']:.3f}%")
