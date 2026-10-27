"""复现：抓取中国海油(600938)、中曼石油(603619)近半年前复权日线量价（截至 2026-10-26 收盘），
交叉核对新浪最近5日；抓取上证指数(sh000001)、沪深300(sh000300)近段日线及当前 WTI/Brent 油价做大盘/油价标注；
落盘核验表、近段量价+大盘+油价对照表，并生成量价静态 SVG 折线图。
运行：仓库根目录执行 `python -I docs/market-data/2026-10-26_oil-six-month/build_oil_charts.py`
注意：今日(2026-10-27)为盘中数据，已排除；仅收录到 2026-10-26 收盘。前复权价不等于当时实际成交价。
"""
import json
import urllib.request
from pathlib import Path

REQ_START, REQ_END = "2026-04-27", "2026-10-27"
LAST_CLOSE = "2026-10-26"  # 只收录到此收盘日，排除 10-27 盘中
archive = Path("docs/market-data/2026-10-26_oil-six-month")
archive.mkdir(parents=True, exist_ok=True)
stocks = [("600938", "中国海油"), ("603619", "中曼石油")]


def http(url, referer="https://finance.sina.com.cn"):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": referer})
    return urllib.request.urlopen(req, timeout=25).read()


def fetch_qfqday(code, start, end):
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           f"param=sh{code},day,{start},{end},320,qfq")
    raw = http(url)
    node = json.loads(raw)["data"]["sh" + code]
    return raw, node.get("qfqday") or node["day"]  # 股票=qfqday(前复权)，指数=day(原值)


rows = []
for code, name in stocks:
    raw, data = fetch_qfqday(code, REQ_START, REQ_END)
    data = [r for r in data if r[0] <= LAST_CLOSE]  # 排除盘中当日
    assert data == sorted(data, key=lambda r: r[0])
    assert len(set(r[0] for r in data)) == len(data)
    assert data[-1][0] == LAST_CLOSE, f"{code} 最新日非 {LAST_CLOSE}: {data[-1][0]}"
    for r in data:
        assert float(r[4]) <= float(r[2]) <= float(r[3]) and float(r[5]) >= 0
        rows.append({"日期": r[0], "股票": f"{name} {code}",
                     "收盘价": float(r[2]), "成交量": round(float(r[5]) / 10000, 6)})
    # 新浪最近5日交叉核对：成交量须一致（收盘价差异仅因前复权除权允许）
    surl = (f"https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/"
            f"CN_MarketDataService.getKLineData?symbol=sh{code}&scale=240&ma=no&datalen=6")
    text = http(surl).decode("utf-8")
    recent = json.loads(text[text.index("([") + 1:text.rindex("]);") + 1])
    lookup = {r[0]: r for r in data}
    for r in recent:
        if r["day"] in lookup:
            assert abs(float(r["volume"]) / 100 - float(lookup[r["day"]][5])) <= 1.1
    (archive / f"{code}-tencent.json").write_bytes(raw)
    (archive / f"{code}-sina-check.json").write_text(
        json.dumps(recent, ensure_ascii=False, indent=2), encoding="utf-8")
    print(code, name, data[0][0], "~", data[-1][0], len(data), "量交叉核对通过")

rows.sort(key=lambda r: (r["日期"], r["股票"]))
assert ({r["日期"] for r in rows if "600938" in r["股票"]}
        == {r["日期"] for r in rows if "603619" in r["股票"]})
(archive / "reviewed-rows.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- 大盘指数近段日线（上证、沪深300）----
idx_daily = {}
for icode, iname in [("000001", "上证指数"), ("000300", "沪深300")]:
    _, idata = fetch_qfqday(icode, "2026-10-16", REQ_END)  # 指数 qfq 即原值
    idata = [r for r in idata if r[0] <= LAST_CLOSE]
    idx_daily[iname] = {r[0]: float(r[2]) for r in idata}

# ---- 当前 WTI/Brent 油价快照（作油价标注）----
oil = {}
try:
    s = http("https://hq.sinajs.cn/list=hf_CL,hf_OIL").decode("gbk")
    for line in s.strip().split("\n"):
        nm = line.split("=")[0].split("_")[-1]
        f = line.split('"')[1].split(",")
        oil[nm] = {"price": float(f[0]), "prev_settle": float(f[8]), "time": f[12] + " " + f[6]}
except Exception as e:
    oil = {"error": str(e)}

# ---- 近段量价 + 大盘 + 油价 对照表（10-19 起）----
dates_all = sorted({r["日期"] for r in rows})
ctx_dates = [d for d in dates_all if d >= "2026-10-19"]
S = {}
for r in rows:
    S.setdefault(r["股票"], {})[r["日期"]] = r
def idx_pct(iname, d):
    ser = idx_daily[iname]
    ks = sorted(ser)
    if d not in ser:
        return None
    i = ks.index(d)
    return None if i == 0 else round((ser[d] / ser[ks[i - 1]] - 1) * 100, 2)
recent_context = {"last_close": LAST_CLOSE, "oil_spot": oil, "rows": []}
for d in ctx_dates:
    recent_context["rows"].append({
        "日期": d,
        "中国海油_收": round(S["中国海油 600938"][d]["收盘价"], 3),
        "中国海油_量万手": round(S["中国海油 600938"][d]["成交量"], 2),
        "中曼石油_收": round(S["中曼石油 603619"][d]["收盘价"], 3),
        "中曼石油_量万手": round(S["中曼石油 603619"][d]["成交量"], 2),
        "上证涨跌%": idx_pct("上证指数", d),
        "沪深300涨跌%": idx_pct("沪深300", d),
    })
(archive / "recent-context.json").write_text(
    json.dumps(recent_context, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- 静态 SVG 折线图 ----
dates = dates_all
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
         f'<text x="{W/2}" y="46" text-anchor="middle" font-size="12" fill="#666">{dates[0]} — {dates[-1]} · 日线 · {unit}</text>']
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
print("done:", len(rows), "rows; last:", dates[-1], "; oil:", {k: v.get("price") for k, v in oil.items()} if "error" not in oil else oil)
