from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "diagrams" / "capital_flow_four_matrix_lqy_2026-06-24.png"
FONT_PATHS = [
    Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf"),
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
]


def get_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    raise FileNotFoundError("No Chinese font found")


def draw_wrapped(draw, xy, text, font, fill, width_chars, line_gap=8):
    x, y = xy
    for para in text.split("\n"):
        for line in textwrap.wrap(para, width=width_chars, break_long_words=False):
            draw.text((x, y), line, font=font, fill=fill)
            y += font.size + line_gap
        y += 5
    return y


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    w, h = 1800, 1250
    image = Image.new("RGB", (w, h), "#f7f3ea")
    draw = ImageDraw.Draw(image)

    f_title = get_font(58)
    f_sub = get_font(28)
    f_axis = get_font(30)
    f_quad = get_font(40)
    f_body = get_font(25)
    f_small = get_font(22)
    f_tag = get_font(24)

    ink = "#1f2933"
    muted = "#59636e"
    line = "#9a8f7a"
    center = "#3d4852"
    colors = {
        "nw": "#d8efe4",
        "ne": "#f4d8cf",
        "sw": "#d7e4f4",
        "se": "#eadcf3",
    }

    draw.rectangle([0, 0, w, h], fill="#f7f3ea")
    draw.rectangle([0, 0, w, 210], fill="#efe7d8")
    draw.text((70, 42), "卢麒元投资学：资本流转四矩阵", font=f_title, fill=ink)
    draw.text(
        (74, 122),
        "基于“资本三流”：流量看水位，流向看归宿，流速看冲击；本图为仓库研究框架化表达",
        font=f_sub,
        fill=muted,
    )

    left, top = 190, 265
    right, bottom = 1610, 1030
    mid_x = (left + right) // 2
    mid_y = (top + bottom) // 2

    quadrants = [
        ("nw", left, top, mid_x, mid_y),
        ("ne", mid_x, top, right, mid_y),
        ("sw", left, mid_y, mid_x, bottom),
        ("se", mid_x, mid_y, right, bottom),
    ]
    for key, x1, y1, x2, y2 in quadrants:
        draw.rounded_rectangle(
            [x1 + 8, y1 + 8, x2 - 8, y2 - 8],
            radius=22,
            fill=colors[key],
            outline="#cabfaa",
            width=2,
        )

    draw.line([mid_x, top, mid_x, bottom], fill=line, width=4)
    draw.line([left, mid_y, right, mid_y], fill=line, width=4)

    draw.line([left, bottom + 55, right, bottom + 55], fill=center, width=5)
    draw.polygon(
        [(right, bottom + 55), (right - 25, bottom + 42), (right - 25, bottom + 68)],
        fill=center,
    )
    draw.text((left, bottom + 76), "流向：离心外流 / 非美扩散", font=f_axis, fill=center)
    draw.text((right - 375, bottom + 76), "流向：向心回流 / 核心区吸纳", font=f_axis, fill=center)

    draw.line([left - 55, bottom, left - 55, top], fill=center, width=5)
    draw.polygon(
        [(left - 55, top), (left - 68, top + 25), (left - 42, top + 25)],
        fill=center,
    )
    draw.text((70, top + 8), "流速：加速", font=f_axis, fill=center)
    draw.text((70, bottom - 38), "流速：速冻/减速", font=f_axis, fill=center)

    def draw_quad(x1, y1, x2, y2, title, tag, body, watch, accent):
        draw.rounded_rectangle([x1 + 28, y1 + 28, x1 + 185, y1 + 72], radius=14, fill=accent)
        draw.text((x1 + 48, y1 + 34), tag, font=f_tag, fill="white")
        draw.text((x1 + 32, y1 + 92), title, font=f_quad, fill=ink)
        draw_wrapped(draw, (x1 + 34, y1 + 158), body, f_body, "#24313b", 24)
        draw.line([x1 + 34, y2 - 96, x2 - 34, y2 - 96], fill="#b5aa98", width=2)
        draw_wrapped(draw, (x1 + 34, y2 - 82), "验证：" + watch, f_small, "#4f5b66", 34, 6)

    draw_quad(
        left,
        top,
        mid_x,
        mid_y,
        "扩张外流：风险偏好阶段",
        "流出快",
        "资本离开核心区，追逐高收益与成长叙事。\n"
        "常见表现：非美资产、权益、商品题材扩散；美元压力下降。\n"
        "风险：一旦美元融资收紧，外流会反向回撤。",
        "DXY走弱、VIX低位、非美股债商品同步扩张、跨境资金流入。",
        "#1f8a5b",
    )
    draw_quad(
        mid_x,
        top,
        right,
        mid_y,
        "向心回流：危机预热阶段",
        "回流快",
        "资本快速回到美元/美债/日本等核心资产池。\n"
        "常见表现：美元走强、套息平仓、亚洲离岸市场先承压。\n"
        "含义：价格下跌未必是基本面错，可能是流向切换。",
        "DXY上行、USD/JPY急跌或波动放大、JGB收益率上行、港股/韩台承压。",
        "#b3442e",
    )
    draw_quad(
        left,
        mid_y,
        mid_x,
        bottom,
        "滞留失速：价值重估等待期",
        "外流慢",
        "资本没有明显回流核心区，但交易速度下降。\n"
        "常见表现：成交萎缩、价格横盘、主题轮动变慢。\n"
        "含义：需要等待新锚或新事件确认，少把静态价格当结论。",
        "成交量、信用利差、ETF资金流、商品期限结构是否重新变陡。",
        "#2f6fab",
    )
    draw_quad(
        mid_x,
        mid_y,
        right,
        bottom,
        "向心速冻：坍缩/防守阶段",
        "回流慢",
        "管理者压低流速，资本被迫收缩到核心区。\n"
        "常见表现：现金为王、风险资产与商品可能同步承压。\n"
        "含义：这是“美元重置前”的防守窗口，不等于长期主线消失。",
        "美元融资利差、TED/OIS、VIX、长债拍卖、黄金/TIPS、油价库存背离。",
        "#7f4aa4",
    )

    panel_y = 1078
    draw.rounded_rectangle([190, panel_y, 1610, 1180], radius=20, fill="#fffaf0", outline="#c7b99d", width=2)
    draw.text((220, panel_y + 22), "第三维：流量（水位/压力）", font=f_axis, fill=ink)
    draw.text(
        (610, panel_y + 25),
        "流量放大：价格更容易失真，冲击更剧烈；流量收缩：流动性溢价上升，现金权重提高。",
        font=f_body,
        fill=muted,
    )
    for i, arrow_width in enumerate([8, 14, 22]):
        x = 1245 + i * 95
        draw.line([x, panel_y + 66, x + 60, panel_y + 66], fill="#9b3d2d", width=arrow_width)
        draw.polygon([(x + 60, panel_y + 66), (x + 44, panel_y + 56), (x + 44, panel_y + 76)], fill="#9b3d2d")

    draw.text(
        (70, 1210),
        "用途：做宏观复盘时先定位资本处于哪个象限，再回到资产价格、利率、汇率、战争与政策数据验证。不是买卖建议。",
        font=f_small,
        fill="#6a6254",
    )

    image.save(OUT, quality=95)
    print(OUT)


if __name__ == "__main__":
    main()
