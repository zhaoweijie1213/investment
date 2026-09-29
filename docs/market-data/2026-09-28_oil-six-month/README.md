# 中国海油与中曼石油近半年量价数据

请求区间：2026-03-28 至 2026-09-28。实际区间：2026-03-30 至 2026-09-24。排除 9 月 28 日盘中行情。

腾讯证券前复权日线：`https://web.ifzq.gtimg.cn/appstock/app/fqkline/get`，参数 `param=sh代码,day,2026-03-28,2026-09-28,320,qfq`。原始 qfqday 字段依次为日期、开盘、收盘、最高、最低、成交量（手）。图中成交量除以 10000 转为万手。前复权价不等于历史实际成交价。

新浪最近 5 日用于交叉核对：`https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData`，参数 `symbol=sh代码&scale=240&ma=no&datalen=5`。新浪成交量为股。最近 5 日收盘价一致，成交量差异不超过 1.1 手。

本次仅整理图表，无新的投资判断或长期框架变化。
