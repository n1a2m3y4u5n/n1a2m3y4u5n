"""깃허브 화면 요소(잔디, 고정 저장소 카드)를 흉내 낸 프로필용 SVG. 다크·라이트 두 벌을 만든다."""
import datetime as dt, os, sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic',Helvetica,Arial,sans-serif"

THEME = {
    'dark': dict(bg='#0d1117', fg='#e6edf3', muted='#7d8590', border='#30363d', link='#4493f8',
                 lv=['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353'], cell_stroke='#1b1f2380'),
    'light': dict(bg='#ffffff', fg='#1f2328', muted='#59636e', border='#d1d9e0', link='#0969da',
                  lv=['#eff2f5', '#aceebb', '#4ac26b', '#2da44e', '#116329'], cell_stroke='#1f232810'),
}

LEVEL = {'장려상': 1, '입상': 1, '선발': 1, '동상': 1, '은상': 2, '우수상': 2, '금상': 3, '최우수상': 3, '대상': 4}

AWARDS = [
    ('2025-04-15', '은상'), ('2025-08-01', '우수상'), ('2025-10-15', '금상'), ('2025-10-25', '입상'),
    ('2025-11-08', '우수상'), ('2025-12-31', '장려상'),
    ('2026-02-26', '동상'), ('2026-04-18', '장려상'), ('2026-04-22', '은상'), ('2026-07-21', '선발'),
    ('2026-08-07', '최우수상'), ('2026-08-08', '대상'), ('2026-08-08', '대상'), ('2026-08-14', '대상'),
    ('2026-08-26', '최우수상'), ('2026-08-26', '우수상'), ('2026-08-29', '금상'), ('2026-08-31', '최우수상'),
    ('2026-09-05', '우수상'), ('2026-09-18', '동상'),
]


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;')


def calendar(theme):
    t = THEME[theme]
    C, G = 11, 3
    S = C + G
    left, top = 34, 54
    year_h = 7 * S + 58
    W = left + 53 * S + 16
    H = top + 2 * year_h + 30
    days = {}
    for d, tier in AWARDS:
        days.setdefault(d, []).append(tier)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<rect width="{W}" height="{H}" rx="6" fill="{t["bg"]}" stroke="{t["border"]}"/>',
           f'<text x="16" y="30" font-size="16" font-weight="600" fill="{t["fg"]}">수상 {len(AWARDS)}건 <tspan fill="{t["muted"]}" font-weight="400" font-size="14">· 2025년 4월 ~ 2026년 9월</tspan></text>']
    order = 0
    for yi, year in enumerate((2025, 2026)):
        y0 = top + yi * year_h
        n = sum(1 for d, _ in AWARDS if d.startswith(str(year)))
        out.append(f'<text x="16" y="{y0}" font-size="13" fill="{t["muted"]}"><tspan fill="{t["fg"]}" font-weight="600">{year}</tspan>  수상 {n}건</text>')
        gy = y0 + 28
        start = dt.date(year, 1, 1)
        offset = (start.weekday() + 1) % 7  # 일요일 시작
        d = start
        while d.year == year:
            idx = (d - start).days + offset
            col, row = idx // 7, idx % 7
            x, y = left + col * S, gy + row * S
            if d.day == 1:
                lx_ = left + (col + (1 if row > 3 else 0)) * S
                out.append(f'<text x="{lx_}" y="{gy - 7}" font-size="11" fill="{t["fg"]}">{d.month}월</text>')
            key = d.isoformat()
            if key in days:
                lv = max(LEVEL[x_] for x_ in days[key])
                label = ', '.join(days[key])
                begin = 0.3 + order * 0.12
                order += 1
                out.append(f'<rect x="{x}" y="{y}" width="{C}" height="{C}" rx="2" fill="{t["lv"][0]}"/>')
                out.append(f'<rect x="{x}" y="{y}" width="{C}" height="{C}" rx="2" fill="{t["lv"][lv]}" stroke="{t["cell_stroke"]}"><title>{key} {label}</title></rect>')
                if len(days[key]) > 1:
                    out.append(f'<circle cx="{x + C - 1}" cy="{y + 1}" r="2.6" fill="{t["fg"]}" stroke="{t["bg"]}" stroke-width="1"/>')
            else:
                out.append(f'<rect x="{x}" y="{y}" width="{C}" height="{C}" rx="2" fill="{t["lv"][0]}" stroke="{t["cell_stroke"]}"/>')
            d += dt.timedelta(days=1)
        for r, lab in ((1, '월'), (3, '수'), (5, '금')):
            out.append(f'<text x="14" y="{gy + r * S + 9}" font-size="10" fill="{t["muted"]}">{lab}</text>')
    # 범례
    ly = H - 18
    lx = W - 16
    items = [('대상', 4), ('최우수·금상', 3), ('우수·은상', 2), ('그 외', 1)]
    parts = []
    for lab, lv in items:
        tw = len(lab) * 11 + 6
        lx -= tw
        parts.append(f'<text x="{lx}" y="{ly + 9}" font-size="11" fill="{t["muted"]}">{lab}</text>')
        lx -= C + 5
        parts.append(f'<rect x="{lx}" y="{ly}" width="{C}" height="{C}" rx="2" fill="{t["lv"][lv]}"/>')
        lx -= 12
    out += parts
    out.append(f'<text x="16" y="{ly + 9}" font-size="11" fill="{t["muted"]}">● 같은 날 두 개</text>')
    out.append('</svg>')
    open(os.path.join(OUT, f'awards-{theme}.svg'), 'w').write(''.join(out))


REPO_ICON = 'M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z'
TROPHY = 'M3.217 6.962A3.75 3.75 0 0 1 0 3.25v-.5C0 1.784.784 1 1.75 1h1.356c.228-.585.796-1 1.462-1h6.864c.647 0 1.227.397 1.462 1h1.356c.966 0 1.75.784 1.75 1.75v.5a3.75 3.75 0 0 1-3.217 3.712 5.014 5.014 0 0 1-2.771 3.117l.144 1.446c.05.5.284.954.65 1.282l.52.465c.36.322.56.788.551 1.27l-.02.958a.75.75 0 0 1-.75.75H4.857a.75.75 0 0 1-.75-.75l-.02-.958a1.75 1.75 0 0 1 .55-1.27l.52-.465c.367-.328.6-.782.65-1.282l.145-1.446a5.016 5.016 0 0 1-2.77-3.117ZM4.5 1.568V5.5a3.5 3.5 0 1 0 7 0V1.568a.069.069 0 0 0-.068-.068H4.568a.069.069 0 0 0-.068.068ZM13.5 2.5v2.86a2.25 2.25 0 0 0 1-1.86v-.5a.25.25 0 0 0-.25-.25Zm-11 0h-.75a.25.25 0 0 0-.25.25v.5c0 .73.348 1.38.888 1.79A2.25 2.25 0 0 0 2.5 5.36Z'

LANG = {'JavaScript': '#f1e05a', 'TypeScript': '#3178c6', 'Python': '#3572A5', 'HTML': '#e34c26'}

CARDS = [
    ('liplab', 'liplab', '청각장애인을 위한 한국어 독화·발음·청능 훈련 웹앱', 'JavaScript', 'K-AI 콘텐츠 공모전 대상'),
    ('snapcare', 'snapcare', '처방전을 찍으면 픽토그램·음성·다국어로 바꿔 주는 웹앱', 'Python', 'e-ICON 세계대회 최우수상 (고등부 2위)'),
    ('rundata', 'rundata', '러닝 경로에 공공 점검 미션을 배치하는 데이터 수집 플랫폼', 'TypeScript', '세계발명학교엑스포 대상'),
    ('meonbada', 'meonbada-titan-sim', '타이탄 메테인 바다를 항해하는 극저온 탐사선 시뮬레이터', 'JavaScript', '미래바다 아이디어 공모전 우수상'),
    ('reloop', 'reloop', '도시 음식물 쓰레기를 자원으로 되돌리는 순환형 푸드 플랫폼', 'JavaScript', '전국학생창업발명경진대회 우수상'),
    ('piezo', 'piezo-crowd-sensing', '압전 바닥 센서로 군중 밀집도를 재는 시뮬레이션', 'HTML', '원더차일드 창의발명대회 동상'),
]


def card(theme, c):
    key, repo, desc, lang, award = c
    t = THEME[theme]
    W, H = 420, 124
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" fill="{t["bg"]}" stroke="{t["border"]}"/>',
         f'<path transform="translate(16 16)" fill="{t["muted"]}" d="{REPO_ICON}"/>',
         f'<text x="40" y="28" font-size="14" font-weight="600" fill="{t["link"]}">{esc(repo)}</text>']
    pw = 44
    px = 40 + len(repo) * 8.2 + 8
    o.append(f'<rect x="{px:.0f}" y="15" width="{pw}" height="18" rx="9" fill="none" stroke="{t["border"]}"/>'
             f'<text x="{px + pw / 2:.0f}" y="28" font-size="11" fill="{t["muted"]}" text-anchor="middle">Public</text>')
    o.append(f'<text x="16" y="58" font-size="12.5" fill="{t["muted"]}">{esc(desc)}</text>')
    o.append(f'<circle cx="22" cy="100" r="6" fill="{LANG[lang]}"/><text x="34" y="104" font-size="12" fill="{t["muted"]}">{lang}</text>')
    tx = 34 + len(lang) * 7.2 + 18
    o.append(f'<path transform="translate({tx:.0f} 92)" fill="{t["muted"]}" d="{TROPHY}"/>'
             f'<text x="{tx + 22:.0f}" y="104" font-size="12" fill="{t["muted"]}">{esc(award)}</text>')
    o.append('</svg>')
    open(os.path.join(OUT, f'pin-{key}-{theme}.svg'), 'w').write(''.join(o))


for th in THEME:
    calendar(th)
    for c in CARDS:
        card(th, c)
print('ok')
