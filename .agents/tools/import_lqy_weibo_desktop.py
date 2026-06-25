import argparse
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path


ROOT = Path(r"F:\Git\investment")
OUT_ROOT = ROOT / "docs" / "卢麒元微博"
RAW_DIR = OUT_ROOT / "raw"
RECORDS_PATH = RAW_DIR / "investment-records-partial.json"
MANIFEST_PATH = OUT_ROOT / "manifest.json"

INVESTMENT_KEYWORDS = [
    "投资", "资本", "金融", "财政", "货币", "美元", "人民币", "港币", "日元", "美债", "国债",
    "利率", "加息", "降息", "通胀", "恶通", "实质负利率", "汇率", "股", "股票", "A股",
    "港股", "美股", "日股", "黄金", "白银", "金银", "铜", "石油", "原油", "油价", "油气",
    "天然气", "粮", "粮食", "能源", "化工", "AI", "Token", "稳定币", "电币", "绿电",
    "短股长金", "金转油", "油粮", "向心坍缩", "速冻", "资本三流", "美联储", "沃什",
    "财政部", "关税", "债务", "房地产", "资产", "泡沫", "国储", "战略资源", "霍尔木兹",
    "伊朗", "日本", "套息",
]

ASSET_KEYWORDS = {
    "黄金/白银": ["黄金", "白银", "金银", "实质负利率"],
    "原油/能源": ["石油", "原油", "油价", "油气", "能源", "天然气", "化工", "霍尔木兹", "伊朗", "油粮"],
    "美元/美债": ["美元", "美债", "美国国债", "财政", "债务", "美联储", "沃什", "利率"],
    "人民币/港币": ["人民币", "港币", "绿电", "电币"],
    "日元/日本": ["日元", "日本", "套息", "日股"],
    "股票/风险资产": ["股票", "A股", "港股", "美股", "股市", "AI", "泡沫"],
    "粮食/必需品": ["粮", "粮食", "食品"],
    "Token/稳定币": ["Token", "稳定币", "数字资产"],
}


def strip_html(text: str) -> str:
    text = text or ""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).replace("\u200b", "").strip()


def contains_investment(text: str) -> bool:
    low = text.lower()
    return any(k.lower() in low for k in INVESTMENT_KEYWORDS)


def asset_tags(text: str) -> str:
    low = text.lower()
    tags = []
    for name, keys in ASSET_KEYWORDS.items():
        if any(k.lower() in low for k in keys):
            tags.append(name)
    return "、".join(tags) if tags else "宏观/投资"


def load_json_payload(path: Path):
    text = path.read_text(encoding="utf-8")
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"{path} does not contain a JSON object")
    return json.loads(text[start : end + 1])


def iter_posts(payload):
    if isinstance(payload, list):
        yield from payload
        return
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        for key in ("list", "statuses", "cards"):
            value = data.get(key)
            if isinstance(value, list):
                for item in value:
                    yield item.get("mblog", item) if isinstance(item, dict) else item
        return
    for key in ("list", "statuses", "cards"):
        value = payload.get(key) if isinstance(payload, dict) else None
        if isinstance(value, list):
            for item in value:
                yield item.get("mblog", item) if isinstance(item, dict) else item


def parse_created_at(value: str) -> datetime:
    value = (value or "").strip()
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            parsed = datetime.strptime(value, fmt)
            if parsed.tzinfo:
                return parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except ValueError:
            pass
    year = datetime.now().year
    for fmt in ("%m-%d %H:%M", "%m月%d日 %H:%M"):
        try:
            return datetime.strptime(f"{year}-{value}", f"%Y-{fmt}")
        except ValueError:
            pass
    raise ValueError(f"unsupported created_at: {value!r}")


def collect_image_urls(post: dict):
    urls = []
    pic_infos = post.get("pic_infos")
    if isinstance(pic_infos, dict):
        for info in pic_infos.values():
            if not isinstance(info, dict):
                continue
            for key in ("largest", "original", "large", "bmiddle", "thumbnail"):
                item = info.get(key)
                if isinstance(item, dict) and item.get("url"):
                    urls.append(item["url"].replace("\\/", "/"))
                    break
    for pic in post.get("pics") or []:
        if not isinstance(pic, dict):
            continue
        for key in ("large", "largest", "original", "bmiddle", "thumbnail"):
            item = pic.get(key)
            if isinstance(item, dict) and item.get("url"):
                urls.append(item["url"].replace("\\/", "/"))
                break
    return list(dict.fromkeys(urls))


def normalize_post(post: dict):
    if not isinstance(post, dict):
        return None
    mid = str(post.get("mid") or post.get("id") or post.get("mblogid") or "").strip()
    if not mid:
        return None
    created_at = parse_created_at(post.get("created_at", ""))
    plain = strip_html(post.get("text_raw") or post.get("text") or "")
    retweeted = post.get("retweeted_status") or {}
    repost = strip_html(retweeted.get("text_raw") or retweeted.get("text") or "")
    joined = f"{plain}\n{repost}"
    if not contains_investment(joined):
        return None
    image_urls = collect_image_urls(post) + collect_image_urls(retweeted)
    image_urls = list(dict.fromkeys(image_urls))
    return {
        "date": created_at.strftime("%Y-%m-%d %H:%M"),
        "month": created_at.strftime("%m"),
        "id": mid,
        "kind": "转发/评论" if retweeted else "原创",
        "assets": asset_tags(joined),
        "plain_text": plain,
        "repost_text": repost,
        "url": f"https://weibo.com/{post.get('user', {}).get('id') or '1245732825'}/{post.get('mblogid') or mid}",
        "image_urls": image_urls,
        "image_files": [],
        "truncated": bool(post.get("isLongText") or "全文" in plain),
        "source": "desktop_weibo_ajax",
    }


def write_summary(records, summary_path: Path):
    lines = [
        "---",
        'title: "卢麒元微博电脑端增量导入"',
        f'date: "{datetime.now().strftime("%Y-%m-%d")}"',
        'source: "微博电脑端 ajax"',
        'analysis_type: "微博增量整理"',
        "tags:",
        "  - 卢麒元",
        "  - 微博",
        "  - 宏观",
        "  - 投资",
        "---",
        "",
        "# 卢麒元微博电脑端增量导入",
        "",
        f"本次新增投资相关微博 `{len(records)}` 条。",
        "",
        "| 日期 | 类型 | 涉及资产 | 原文摘要 | 来源 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for rec in records:
        short = rec["plain_text"].replace("\n", " ")[:120]
        if len(rec["plain_text"]) > 120:
            short += "..."
        lines.append(f"| {rec['date']} | {rec['kind']} | {rec['assets']} | {short} | {rec['url']} |")
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Import Lu Mingyuan desktop Weibo ajax JSON into the repo archive.")
    parser.add_argument("input", type=Path, help="Path to a saved weibo.com/ajax/statuses/mymblog JSON response")
    parser.add_argument("--summary", type=Path, default=OUT_ROOT / f"{datetime.now().strftime('%Y-%m-%d')}_电脑端微博增量导入.md")
    args = parser.parse_args()

    payload = load_json_payload(args.input)
    imported_raw = RAW_DIR / f"desktop-import-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    imported_raw.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    existing = []
    if RECORDS_PATH.exists():
        existing = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
    existing_ids = {str(item.get("id")) for item in existing}

    new_records = []
    for post in iter_posts(payload):
        rec = normalize_post(post)
        if rec and rec["id"] not in existing_ids:
            existing_ids.add(rec["id"])
            new_records.append(rec)

    merged = existing + new_records
    merged.sort(key=lambda item: item.get("date", ""), reverse=True)
    RECORDS_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(new_records, args.summary)

    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    else:
        manifest = {}
    manifest["last_incremental_check"] = datetime.now().strftime("%Y-%m-%d")
    manifest["investment_records"] = len(merged)
    manifest["last_desktop_import"] = str(imported_raw)
    manifest["last_desktop_import_new_records"] = len(new_records)
    manifest["last_desktop_import_summary"] = str(args.summary)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "imported_raw": str(imported_raw),
        "new_records": len(new_records),
        "total_records": len(merged),
        "summary": str(args.summary),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
