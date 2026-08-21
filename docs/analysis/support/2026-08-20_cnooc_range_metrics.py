"""Recompute the 2026-08-20 CNOOC A-share range metrics from a fixed snapshot.

Source snapshots:
- Sina daily K-line, completed sessions through 2026-08-19.
- Sina HQ and 5-minute K-line, captured 2026-08-20 14:10:51 Asia/Shanghai.
"""

from __future__ import annotations

import json
from statistics import fmean


DAILY_ROWS = json.loads(
    r'''[
      {"date":"2026-07-23","open":32.80,"high":33.30,"low":32.40,"close":32.99,"volume":81349712},
      {"date":"2026-07-24","open":33.67,"high":33.83,"low":31.81,"close":31.91,"volume":101079075},
      {"date":"2026-07-27","open":30.55,"high":31.80,"low":30.00,"close":31.55,"volume":107389567},
      {"date":"2026-07-28","open":30.42,"high":31.53,"low":30.42,"close":31.32,"volume":54000021},
      {"date":"2026-07-29","open":31.60,"high":32.18,"low":31.44,"close":31.48,"volume":44911865},
      {"date":"2026-07-30","open":32.08,"high":32.72,"low":31.89,"close":32.55,"volume":61887731},
      {"date":"2026-07-31","open":31.54,"high":32.27,"low":31.54,"close":32.26,"volume":47873736},
      {"date":"2026-08-03","open":31.80,"high":32.58,"low":31.75,"close":31.85,"volume":49792705},
      {"date":"2026-08-04","open":31.81,"high":32.00,"low":31.55,"close":31.56,"volume":38155475},
      {"date":"2026-08-05","open":30.92,"high":31.19,"low":30.56,"close":30.69,"volume":68020642},
      {"date":"2026-08-06","open":30.51,"high":30.99,"low":30.42,"close":30.96,"volume":41578789},
      {"date":"2026-08-07","open":31.30,"high":31.49,"low":31.02,"close":31.33,"volume":43458348},
      {"date":"2026-08-10","open":31.60,"high":32.38,"low":31.38,"close":32.00,"volume":46468834},
      {"date":"2026-08-11","open":32.73,"high":33.75,"low":32.28,"close":33.70,"volume":80111856},
      {"date":"2026-08-12","open":33.53,"high":33.53,"low":32.81,"close":32.85,"volume":48981761},
      {"date":"2026-08-13","open":32.47,"high":32.93,"low":31.90,"close":32.63,"volume":48573813},
      {"date":"2026-08-14","open":32.15,"high":32.78,"low":31.93,"close":32.67,"volume":36127680},
      {"date":"2026-08-17","open":32.68,"high":33.15,"low":32.55,"close":32.89,"volume":35066096},
      {"date":"2026-08-18","open":33.35,"high":33.84,"low":33.25,"close":33.58,"volume":49532866},
      {"date":"2026-08-19","open":33.78,"high":33.98,"low":33.35,"close":33.35,"volume":44351585}
    ]'''
)

LIVE = {
    "captured_at": "2026-08-20T14:10:51+08:00",
    "open": 33.26,
    "previous_close": 33.35,
    "last": 33.17,
    "high": 33.73,
    "low": 32.80,
    "hq_volume": 36_783_013,
    "volume_to_1410": 36_718_013,
    "amount": 1_223_117_031,
    "previous_same_time_volume": 35_956_859,
}


def mean_last(field: str, periods: int) -> float:
    return fmean(row[field] for row in DAILY_ROWS[-periods:])


def atr(periods: int = 14) -> float:
    true_ranges: list[float] = []
    previous_close: float | None = None
    for row in DAILY_ROWS:
        if previous_close is None:
            value = row["high"] - row["low"]
        else:
            value = max(
                row["high"] - row["low"],
                abs(row["high"] - previous_close),
                abs(row["low"] - previous_close),
            )
        true_ranges.append(value)
        previous_close = row["close"]
    return fmean(true_ranges[-periods:])


RESULTS = {
    "last_completed_date": DAILY_ROWS[-1]["date"],
    "last_completed_close": DAILY_ROWS[-1]["close"],
    "ma5": round(mean_last("close", 5), 3),
    "ma10": round(mean_last("close", 10), 3),
    "ma20": round(mean_last("close", 20), 3),
    "atr14": round(atr(), 3),
    "avg_volume_5": round(mean_last("volume", 5)),
    "avg_volume_10": round(mean_last("volume", 10)),
    "avg_volume_20": round(mean_last("volume", 20)),
    "high_5": max(row["high"] for row in DAILY_ROWS[-5:]),
    "low_5": min(row["low"] for row in DAILY_ROWS[-5:]),
    "high_10": max(row["high"] for row in DAILY_ROWS[-10:]),
    "low_10": min(row["low"] for row in DAILY_ROWS[-10:]),
    "intraday_vwap": round(LIVE["amount"] / LIVE["hq_volume"], 3),
    "same_time_volume_change_pct": round(
        (LIVE["volume_to_1410"] / LIVE["previous_same_time_volume"] - 1) * 100, 2
    ),
}


if __name__ == "__main__":
    print(json.dumps(RESULTS, ensure_ascii=False, indent=2))
