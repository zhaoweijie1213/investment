import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
import subprocess

out = Path(r'C:/Users/HIAPAD/.codex/visualizations/2026/09/28/01a0e6af-5d1a-7ff1-8a28-11be42a439d4')
archive = Path('docs/market-data/2026-09-28_oil-six-month')
archive.mkdir(parents=True, exist_ok=True)
rows = []
for code, name, filename in [('600938', '中国海油', 'cnooc-fetch.json'), ('603619', '中曼石油', 'zhongman-fetch.json')]:
    raw = (Path(filename) if Path(filename).exists() else archive/(code+'-tencent.json')).read_bytes()
    j = json.loads(raw)
    data = j['data']['sh' + code]['qfqday']
    assert data == sorted(data, key=lambda r:r[0])
    assert len(set(r[0] for r in data)) == len(data)
    assert data[0][0] <= '2026-04-01' and data[-1][0] == '2026-09-24'
    for r in data:
        assert float(r[4]) <= float(r[2]) <= float(r[3]) and float(r[5]) >= 0
        rows.append({'日期':r[0], '股票':name+' '+code, '收盘价':float(r[2]), '成交量':round(float(r[5])/10000, 6)})
    # Verify recent unadjusted closes and volume unit against a second provider.
    url = f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData?symbol=sh{code}&scale=240&ma=no&datalen=5'
    text = urllib.request.urlopen(url,timeout=25).read().decode('utf-8')
    recent = json.loads(text[text.index('([')+1:text.rindex(']);')+1])
    lookup = {r[0]:r for r in data}
    for r in recent:
        q = lookup[r['day']]
        assert abs(float(r['close'])-float(q[2])) < 0.001
        assert abs(float(r['volume']) / 100 - float(q[5])) <= 1.1
    (archive/(code+'-tencent.json')).write_bytes(raw)
    (archive/(code+'-sina-check.json')).write_text(json.dumps(recent,ensure_ascii=False,indent=2),encoding='utf-8')
    print(code, len(data), data[0][0], data[-1][0], 'recent cross-check passed')
    if Path(filename).exists():
        Path(filename).unlink()
rows.sort(key=lambda r:(r['日期'],r['股票']))
assert {r['日期'] for r in rows if '600938' in r['股票']} == {r['日期'] for r in rows if '603619' in r['股票']}
(archive/'reviewed-rows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
stamp=datetime.now(timezone.utc).isoformat()
node=r'C:/Users/HIAPAD/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
scripts=Path(r'C:/Users/HIAPAD/.codex/plugins/cache/openai-curated-remote/data-analytics/1.0.11/skills/visualize-data/scripts')
for ident, title, metric, unit in [('oil-price','中国海油与中曼石油｜近半年股价','收盘价','前复权收盘价（元）'),('oil-volume','中国海油与中曼石油｜近半年成交量','成交量','成交量（万手）')]:
    projected=[{k:r[k] for k in ['日期','股票',metric]} for r in rows]
    source={'label':'腾讯证券日线；新浪日线交叉核对', 'filters':['股票：600938、603619','请求区间：2026-03-28 至 2026-09-28','实际日线：2026-03-30 至 2026-09-24'], 'caveats':['不含 2026-09-28 未完成的盘中数据。','前复权历史价格会随后续除权除息变化，不等同于当时实际成交价。' if metric=='收盘价' else '1 手 = 100 股；腾讯日线成交量按手返回，除以 10000 换算为万手。'], 'files':[{'label':'600938-tencent.json'},{'label':'603619-tencent.json'}], 'evidenceFlow':['分别读取两只股票的腾讯前复权日线，核对日期唯一、排序、价格上下界与非负成交量。','两只股票交易日期一致；各自最近 5 个交易日收盘价与新浪一致，成交量换算后的差异不超过 1.1 手。']}
    payload={'schemaVersion':1,'id':ident,'title':title,'description':'2026-03-30 — 2026-09-24 · 日线','chart':{'type':'line','x':'日期','y':metric,'series':'股票','showXAxisLabel':False,'yLabel':unit,'startAtZero':metric=='成交量'},'rows':projected,'source':source,'generatedAt':stamp,'height':380,'theme':'codex-classic'}
    p=out/(ident+'.json');p.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
    subprocess.run([node,str(scripts/'render-inline-chart.mjs'),'--input',str(p),'--output',str(out/(ident+'.html'))],check=True)
    receipt={'schemaVersion':1,'items':[{'id':ident+'-evidence','title':title,'queries':[{'id':ident+'-daily','source':source,'rows':projected,'columns':list(projected[0]),'reportingPeriod':'2026-03-30 至 2026-09-24','capturedAt':stamp}]}]}
    p=out/(ident+'-sources.json');p.write_text(json.dumps(receipt,ensure_ascii=False),encoding='utf-8')
    subprocess.run([node,str(scripts/'render-inline-sources.mjs'),'--input',str(p),'--output',str(out/(ident+'-sources.html'))],check=True)
    assert (out/(ident+'.html')).stat().st_size < 1000000
(archive/'README.md').write_text('# 中国海油与中曼石油近半年量价数据\n\n请求区间：2026-03-28 至 2026-09-28。实际区间：2026-03-30 至 2026-09-24。排除 9 月 28 日盘中行情。\n\n腾讯证券前复权日线：`https://web.ifzq.gtimg.cn/appstock/app/fqkline/get`，参数 `param=sh代码,day,2026-03-28,2026-09-28,320,qfq`。原始 qfqday 字段依次为日期、开盘、收盘、最高、最低、成交量（手）。图中成交量除以 10000 转为万手。前复权价不等于历史实际成交价。\n\n新浪最近 5 日用于交叉核对：`https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData`，参数 `symbol=sh代码&scale=240&ma=no&datalen=5`。新浪成交量为股。最近 5 日收盘价一致，成交量差异不超过 1.1 手。\n\n本次仅整理图表，无新的投资判断或长期框架变化。\n',encoding='utf-8')
