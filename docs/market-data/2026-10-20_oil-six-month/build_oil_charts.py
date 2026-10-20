"""复现：抓取中国海油(600938)、中曼石油(603619)近半年前复权日线量价，
交叉核对新浪最近5日；若当日日线接口尚未收录，则用收盘后实时快照(腾讯+新浪双源互校)补当日点，
落盘原始数据与核验表，并生成量价静态 SVG 折线图。
运行：仓库根目录执行 `python -I docs/market-data/2026-10-20_oil-six-month/build_oil_charts.py`
注意：实时快照补点为当日实际收盘价(未复权)，后续若除权除息，历史前复权价会被下调。
"""
import json
import urllib.request
from pathlib import Path

REQ_START, REQ_END = "2026-04-20", "2026-10-20"
TODAY = "2026-10-20"
archive = Path("docs/market-data/2026-10-20_oil-six-month")
archive.mkdir(parents=True, exist_ok=True)
stocks = [("600938", "中国海油"), ("603619", "中曼石油")]


def http(url, referer="https://finance.sina.com.cn"):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": referer})
    return urllib.request.urlopen(req, timeout=25).read()


rows = []
realtime_log = {}
for code, name in stocks:
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           f"param=sh{code},day,{REQ_START},{REQ_END},320,qfq")
    raw = http(url)
    data = json.loads(raw)["data"]["sh" + code]["qfqday"]  # date,open,close,high,low,vol(手)
    assert data == sorted(data, key=lambda r: r[0])
    assert len(set(r[0] for r in data)) == len(data)
    for r in data:
        assert float(r[4]) <= float(r[2]) <= float(r[3]) and float(r[5]) >= 0
    # 新浪最近5日交叉核对：成交量必须一致(收盘价差异仅因前复权除权允许)
    surl = (f"https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/"
            f"CN_MarketDataService.getKLineData?symbol=sh{code}&scale=240&ma=no&datalen=5")
    text = http(surl).decode("utf-8")
    recent = json.loads(text[text.index("([") + 1:text.rindex("]);") + 1])
    lookup = {r[0]: r for r in data}
    for r in recent:
        q = lookup[r["day"]]
        assert abs(float(r["volume"]) / 100 - float(q[5])) <= 1.1
    (archive / f"{code}-tencent.json").write_bytes(raw)
    (archive / f"{code}-sina-check.json").write_text(
        json.dumps(recent, ensure_ascii=False, indent=2), encoding="utf-8")

    # 当日日线未收录 -> 用收盘后实时快照补点(腾讯 qt + 新浪 hq 双源互校)
    if data[-1][0] < TODAY:
        t = http(f"https://qt.gtimg.cn/q=sh{code}").decode("gbk").split("~")
        sv = http(f"https://hq.sinajs.cn/list=sh{code}").decode("gbk").split('"')[1].split(",")
        t_date, t_close, t_vol = t[30][:8], float(t[3]), float(t[6])          # 腾讯 成交量=手
        s_date, s_close, s_vol = sv[30].replace("-", ""), float(sv[3]), float(sv[8]) / 100  # 新浪 股->手
        assert t_date == s_date == TODAY.replace("-", ""), f"快照日期非当日: {t_date}/{s_date}"
        assert abs(t_close - s_close) < 0.001 and abs(t_vol - s_vol) <= 1.1, "两源快照不一致"
        data.append([TODAY, t[5], f"{t_close:.3f}", t[33], t[34], f"{t_vol:.3f}"])
        realtime_log[code] = {"date": TODAY, "tencent": {"close": t_close, "vol_手": t_vol},
                              "sina": {"close": s_close, "vol_手": s_vol}, "note": "收盘实时快照补点(未复权)"}

    for r in data:
        rows.append({"日期": r[0], "股票": f"{name} {code}",
                     "收盘价": float(r[2]), "成交量": round(float(r[5]) / 10000, 6)})
    print(code, name, data[0][0], "~", data[-1][0], len(data), "核对通过")

if realtime_log:
    (archive / "realtime-check-1020.json").write_text(
        json.dumps(realtime_log, ensure_ascii=False, indent=2), encoding="utf-8")
rows.sort(key=lambda r: (r["日期"], r["股票"]))
assert ({r["日期"] for r in rows if "600938" in r["股票"]}
        == {r["日期"] for r in rows if "603619" in r["股票"]})
(archive / "reviewed-rows.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- 静态 SVG 折线图 ----
dates = sorted({r["日期"] for r in rows})
series = {}
for r in rows:
    series.setdefault(r["股票"], {})[r["日期"]] = r
names = sorted(series)
colors = {"中国海油 600938": "#2563eb", "中曼石油 603619": "#dc2626"}


def make_svg(metric, title, unit, start_zero):
    W, H, L, R, T, B = 900, 420, 70, 20, 56, 70
    pw, ph = W - L - R, H - T - B
    allv = [series[n][d][metric] for n in names for d in dates]
    vmin = 0 if start_zero else min(allv) * 0.98
    vmax = max(allv) * 1.03

    def x(i): return L + pw * i / (len(dates) - 1)
    def y(v): return T + ph * (1 - (v - vmin) / (vmax - vmin))

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'font-family="system-ui,Segoe UI,Microsoft YaHei,sans-serif">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         f'<text x="{W/2}" y="28" text-anchor="middle" font-size="18" font-weight="700" fill="#111">{title}</text>',
         f'<text x="{W/2}" y="46" text-anchor="middle" font-size="12" fill="#666">2026-04-20 — {dates[-1]} · 日线 · {unit}</text>']
    for k in range(5):
        v = vmin + (vmax - vmin) * k / 4
        yy = y(v)
        o.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{W-R}" y2="{yy:.1f}" stroke="#eee"/>')
        o.append(f'<text x="{L-8}" y="{yy+4:.1f}" text-anchor="end" font-size="11" fill="#888">{v:.1f}</text>')
    step = max(1, len(dates) // 6)
    for i in range(0, len(dates), step):
        o.append(f'<text x="{x(i):.1f}" y="{H-B+18}" text-anchor="middle" font-size="10" fill="#888">{dates[i][5:]}</text>')
    o.append(f'<text x="{x(len(dates)-1):.1f}" y="{H-B+34}" text-anchor="end" font-size="10" fill="#c00">{dates[-1][5:]}</text>')
    for n in names:
        pts = " ".join(f"{x(i):.1f},{y(series[n][d][metric]):.1f}"
                       for i, d in enumerate(dates) if d in series[n])
        o.append(f'<polyline fill="none" stroke="{colors[n]}" stroke-width="1.8" points="{pts}"/>')
    lx = L + 10
    for n in names:
        o.append(f'<rect x="{lx}" y="{T+6}" width="14" height="4" fill="{colors[n]}"/>')
        o.append(f'<text x="{lx+20}" y="{T+12}" font-size="12" fill="#333">{n}</text>')
        lx += 160
    o.append("</svg>")
    return "\n".join(o)


(archive / "chart-price.svg").write_text(
    make_svg("收盘价", "中国海油 vs 中曼石油 ｜ 近半年股价", "前复权收盘价（元）", False), encoding="utf-8")
(archive / "chart-volume.svg").write_text(
    make_svg("成交量", "中国海油 vs 中曼石油 ｜ 近半年成交量", "成交量（万手）", True), encoding="utf-8")
print("done:", len(rows), "rows; last:", dates[-1], "; SVG charts written")
