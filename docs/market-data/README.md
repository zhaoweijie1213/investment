# Market Quote Capture Log

This directory stores quote snapshots captured by the agent for CNOOC `600938`, Zhongman Petroleum `603619`, and related oil / FX indicators. It prevents later analysis from relying only on chat context or screenshots.

## Files

- `oil-stock-quotes.jsonl`: one JSON object per line, appended by capture time.

## Fields

- `captured_at`: time when the agent captured and wrote the snapshot, Asia/Shanghai.
- `source`: quote source.
- `symbols`: stock quote data, including name, code, open, previous close, last price, high, low, volume, amount, and quote time.
- `macro`: related oil / FX indicators, currently Brent, WTI, and USD/JPY.
- `notes`: why the snapshot was captured.

## Rule

Whenever the agent fetches live quotes for `600938` or `603619`, it should append the snapshot to `oil-stock-quotes.jsonl`. Trading analysis should read recent records from this file before fetching and writing a new latest quote.