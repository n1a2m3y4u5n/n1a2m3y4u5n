"""GitHub 프로필용 SVG 생성기. 글자는 모두 윤곽선(path)으로 바꿔 어느 기기에서나 같은 모양으로 보이게 한다."""
import math, os, re, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

FONTS = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

BG = '#07080C'; PANEL = '#0D1016'; LINE = '#1E2330'
TEXT = '#F2F4F8'; MUTED = '#9AA3B5'; DIM = '#5B6476'
LIME = '#B8FF3C'; CYAN = '#5CE1E6'

TIER = {  # 상 등급별 색
    '대상': '#FFD54A', '최우수상': '#FF9E3D', '금상': '#F5C46B', '우수상': '#7CC4FF',
    '은상': '#C9D3E3', '동상': '#D9925B', '장려상': '#86C5A8', '입상': '#9AA3B5', '선발': '#B79CFF',
}


class Font:
    def __init__(self, fname, key):
        self.tt = TTFont(os.path.join(FONTS, fname))
        self.gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt['head'].unitsPerEm
        self.hmtx = self.tt['hmtx']
        self.key = key

    def gname(self, ch):
        return self.cmap.get(ord(ch), '.notdef')

    def width(self, s, size, ls=0.0):
        k = size / self.upm
        return sum(self.hmtx[self.gname(c)][0] * k + ls * size for c in s) - (ls * size if s else 0)


F = {
    'black': Font('Pretendard-Black.otf', 'k'),
    'xb': Font('Pretendard-ExtraBold.otf', 'x'),
    'bold': Font('Pretendard-Bold.otf', 'b'),
    'semi': Font('Pretendard-SemiBold.otf', 's'),
    'med': Font('Pretendard-Medium.otf', 'm'),
    'mono': Font('JetBrainsMono-Bold.ttf', 'j'),
    'monom': Font('JetBrainsMono-Medium.ttf', 'n'),
}


class Doc:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.glyphs = {}
        self.defs = []
        self.body = []
        self.styles = []

    def _gid(self, font, g):
        gid = font.key + re.sub(r'[^A-Za-z0-9]', '_', g)
        if gid not in self.glyphs:
            pen = SVGPathPen(font.gs, ntos=lambda v: '%d' % round(v))
            font.gs[g].draw(pen)
            self.glyphs[gid] = pen.getCommands()
        return gid

    def text(self, s, x, y, size, font='bold', fill=TEXT, anchor='start', ls=0.0, maxw=None, extra=''):
        f = F[font]
        w = f.width(s, size, ls)
        if maxw and w > maxw:
            size = size * maxw / w
            w = f.width(s, size, ls)
        if anchor == 'middle':
            x -= w / 2
        elif anchor == 'end':
            x -= w
        k = size / f.upm
        parts, cx = [], x
        for c in s:
            g = f.gname(c)
            if c != ' ':
                gid = self._gid(f, g)
                parts.append(f'<use href="#{gid}" transform="translate({cx:.1f} {y:.1f}) scale({k:.5f} {-k:.5f})"/>')
            cx += f.hmtx[g][0] * k + ls * size
        return f'<g fill="{fill}" {extra}>' + ''.join(parts) + '</g>', w

    def runs(self, items, x, y, size, font='bold', ls=0.0):
        out, cx = [], x
        for s, col in items:
            g, w = self.text(s, cx, y, size, font, col, ls=ls)
            out.append(g)
            cx += w + (F[font].width(' ', size) if False else 0)
        return ''.join(out), cx - x

    def add(self, s):
        self.body.append(s)

    def save(self, name, title):
        glyph_defs = ''.join(f'<path id="{k}" d="{v}"/>' for k, v in self.glyphs.items())
        style = f'<style>{"".join(self.styles)}</style>' if self.styles else ''
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-label="{title}">'
               f'<title>{title}</title>{style}<defs>{glyph_defs}{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')
        with open(os.path.join(OUT, name), 'w') as fp:
            fp.write(svg)
        print(name, f'{len(svg) / 1024:.0f}KB')


def glow_filter(fid, sd=3):
    return (f'<filter id="{fid}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{sd}" result="b"/>'
            f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


def frame(d, rx=24, glows=()):
    d.defs.append(f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="#ffffff" opacity="0.07"/></pattern>')
    d.defs.append(f'<clipPath id="frame"><rect width="{d.w}" height="{d.h}" rx="{rx}"/></clipPath>')
    g = [f'<rect width="{d.w}" height="{d.h}" rx="{rx}" fill="{BG}"/>', f'<rect width="{d.w}" height="{d.h}" fill="url(#dots)"/>']
    for i, (cx, cy, r, col, op) in enumerate(glows):
        d.defs.append(f'<radialGradient id="glow{i}"><stop offset="0" stop-color="{col}" stop-opacity="{op}"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#glow{i})"/>')
    d.add(f'<g clip-path="url(#frame)">{"".join(g)}</g>')


def border(d, rx=24, col=LINE):
    d.add(f'<rect x="0.75" y="0.75" width="{d.w - 1.5}" height="{d.h - 1.5}" rx="{rx}" fill="none" stroke="{col}" stroke-width="1.5"/>')


def shine_defs(d, gid, dur=3.6, begin=0, color='#ffffff', op=0.85, angle=20):
    d.defs.append(
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0" gradientTransform="rotate({angle})">'
        f'<stop offset="0.38" stop-color="{color}" stop-opacity="0"/><stop offset="0.5" stop-color="{color}" stop-opacity="{op}"/>'
        f'<stop offset="0.62" stop-color="{color}" stop-opacity="0"/>'
        f'<animateTransform attributeName="gradientTransform" type="translate" values="-1.2 0;1.2 0;1.2 0" keyTimes="0;0.45;1" dur="{dur}s" begin="{begin}s" repeatCount="indefinite" additive="sum"/>'
        f'</linearGradient>')


def badge(d, x, y, tier, h=36, size=19, shine=False, uid=''):
    col = TIER[tier]
    tw = F['black'].width(tier, size)
    w = tw + 30
    out = [f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{col}"/>']
    if shine:
        cid = f'bc{uid}'
        sid = f'bs{uid}'
        d.defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}"/></clipPath>')
        shine_defs(d, sid, dur=2.8, op=0.9)
        out.append(f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" fill="url(#{sid})" clip-path="url(#{cid})"/>')
        out.append(f'<rect x="{x - 4}" y="{y - 4}" width="{w + 8:.1f}" height="{h + 8}" rx="{h / 2 + 4}" fill="none" stroke="{col}" stroke-width="2" opacity="0.5">'
                   f'<animate attributeName="opacity" values="0.15;0.7;0.15" dur="2s" repeatCount="indefinite"/></rect>')
    g, _ = d.text(tier, x + 15, y + h / 2 + size * 0.36, size, 'black', '#120D00')
    out.append(g)
    return ''.join(out), w


def chip(d, x, y, label, col, h=36, size=16):
    w = F['bold'].width(label, size) + 26
    g, _ = d.text(label, x + 13, y + h / 2 + size * 0.36, size, 'bold', col)
    return f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="none" stroke="{col}" stroke-width="1.6"/>' + g, w


# ───────────────────────── 1. 히어로 ─────────────────────────
def hero():
    d = Doc(1280, 440)
    frame(d, glows=[(1040, 200, 460, LIME, 0.16), (120, 470, 420, CYAN, 0.10)])
    d.defs.append(glow_filter('gl', 3))
    d.defs.append(glow_filter('gl2', 6))

    # 상단 라벨
    d.add(f'<circle cx="70" cy="70" r="6" fill="{LIME}" filter="url(#gl)"><animate attributeName="opacity" values="1;0.25;1" dur="1.4s" repeatCount="indefinite"/></circle>')
    g, _ = d.text('CNSAi  //  TEAM LEAD', 88, 77, 19, 'mono', LIME, ls=0.12); d.add(g)

    # 이름 + 빛 지나가기
    name, nw = d.text('남윤수', 60, 208, 128, 'black', TEXT, ls=-0.02)
    d.add(name)
    white = name.replace('fill="%s"' % TEXT, 'fill="#fff"')
    d.defs.append(f'<mask id="nm"><g>{white}</g></mask>')
    shine_defs(d, 'nshine', dur=4.2, color=LIME, op=1)
    d.add(f'<rect x="50" y="90" width="{nw + 30:.0f}" height="140" fill="url(#nshine)" mask="url(#nm)"/>')
    g, _ = d.text('NAM YUNSU', 66, 250, 22, 'monom', MUTED, ls=0.32); d.add(g)

    # 소개 두 줄 (타자 치듯 나타남, SMIL을 못 읽는 뷰어에서는 기본값으로 다 보임)
    lines = [
        [('기존 기술이 실패하는 사람', TEXT), ('에서 출발해,', MUTED)],
        [('AI', LIME), ('로 그 실패를 우회하는 서비스를 만듭니다.', MUTED)],
    ]
    for i, items in enumerate(lines):
        y = 314 + i * 42
        g, w = d.runs(items, 62, y, 29, 'bold')
        cid = f'ty{i}'
        b = 0.5 + i * 1.5
        d.defs.append(f'<clipPath id="{cid}"><rect x="55" y="{y - 34}" width="{w + 20:.0f}" height="46">'
                      f'<animate attributeName="width" values="0;0;{w + 20:.0f}" keyTimes="0;{b / (b + 1.3):.3f};1" dur="{b + 1.3:.2f}s" fill="freeze" calcMode="linear"/></rect></clipPath>')
        d.add(f'<g clip-path="url(#{cid})">{g}</g>')
    # 깜빡이는 커서
    d.add(f'<rect x="{62 + d.runs(lines[1], 0, 0, 29)[1] + 8:.0f}" y="330" width="14" height="32" fill="{LIME}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></rect>')

    g, _ = d.text('충남삼성고등학교 3학년   ·   한국어 음성 AI · 얼굴·입 비전 · 3D · 웹', 62, 404, 18, 'med', DIM); d.add(g)

    # 오른쪽: 입술 판독 HUD
    x0, y0, x1, y1 = 830, 46, 1226, 396
    L = 26
    br = ''.join([
        f'M{x0} {y0 + L}V{y0}H{x0 + L}', f'M{x1 - L} {y0}H{x1}V{y0 + L}',
        f'M{x0} {y1 - L}V{y1}H{x0 + L}', f'M{x1 - L} {y1}H{x1}V{y1 - L}'])
    d.add(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="6" fill="#0A0D12" opacity="0.72"/>')
    d.add(f'<path d="{br}" fill="none" stroke="{LIME}" stroke-width="3" stroke-linecap="round"/>')
    g, _ = d.text('LIP-READ', x0 + 22, y0 + 34, 15, 'mono', LIME, ls=0.18); d.add(g)
    g, _ = d.text('● REC', x1 - 22, y0 + 34, 15, 'mono', '#FF5A5A', anchor='end', ls=0.1,
                  extra='><animate attributeName="opacity" values="1;0.3;1" dur="1.2s" repeatCount="indefinite"/'); d.add(g)

    cx, cy, W = 1028, 176, 250
    open_seq = [0, 15, 5, 22, 9, 2, 18, 6, 0]
    dur = 2.8
    kt = ';'.join(f'{i / (len(open_seq) - 1):.3f}' for i in range(len(open_seq)))
    ks = ';'.join(['0.45 0 0.55 1'] * (len(open_seq) - 1))

    def pts(n, wscale, fn):
        res = []
        for i in range(n):
            t = -1 + 2 * i / (n - 1)
            res.append((cx + t * W / 2 * wscale, fn(t)))
        return res

    up_out = pts(19, 1, lambda t: cy - 40 * (1 - t * t) ** 0.65 + 13 * math.exp(-(t / 0.16) ** 2))
    lo_out = pts(19, 1, lambda t: cy + 44 * (1 - t * t) ** 0.85)
    up_in = pts(13, 0.74, lambda t: cy - 6 * (1 - t * t))
    lo_in = pts(13, 0.74, lambda t: cy + 5 * (1 - t * t))

    def path_d(ps):
        return 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in ps)

    def moving(ps, gain):
        frames = []
        for o in open_seq:
            frames.append([(x, y + o * gain(i, len(ps))) for i, (x, y) in enumerate(ps)])
        return frames

    def wfac(i, n):
        t = -1 + 2 * i / (n - 1)
        return (1 - t * t)

    lip = []
    for ps, mov in ((up_out, None), (up_in, None), (lo_out, wfac), (lo_in, wfac)):
        if mov is None:
            lip.append(f'<path d="{path_d(ps)}" fill="none" stroke="{LIME}" stroke-width="2" opacity="0.45"/>')
            for x, y in ps:
                lip.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{LIME}"/>')
        else:
            frames = moving(ps, mov)
            vals = ';'.join(path_d(f) for f in frames)
            lip.append(f'<path d="{path_d(ps)}" fill="none" stroke="{LIME}" stroke-width="2" opacity="0.45">'
                       f'<animate attributeName="d" values="{vals}" keyTimes="{kt}" keySplines="{ks}" calcMode="spline" dur="{dur}s" repeatCount="indefinite"/></path>')
            for i, (x, y) in enumerate(ps):
                vv = ';'.join(f'{f[i][1]:.1f}' for f in frames)
                lip.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{LIME}"><animate attributeName="cy" values="{vv}" keyTimes="{kt}" keySplines="{ks}" calcMode="spline" dur="{dur}s" repeatCount="indefinite"/></circle>')
    d.add(f'<g filter="url(#gl)">{"".join(lip)}</g>')

    # 스캔 선
    d.defs.append(f'<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{LIME}" stop-opacity="0"/><stop offset="1" stop-color="{LIME}" stop-opacity="0.35"/></linearGradient>')
    d.add(f'<g><rect x="{x0 + 4}" y="{y0 + 50}" width="{x1 - x0 - 8}" height="34" fill="url(#scan)"/><rect x="{x0 + 4}" y="{y0 + 83}" width="{x1 - x0 - 8}" height="2" fill="{LIME}" opacity="0.8"/>'
          f'<animateTransform attributeName="transform" type="translate" values="0 0;0 196;0 0" dur="3.6s" repeatCount="indefinite"/></g>')

    # 파형
    d.styles.append('.wb{transform-box:fill-box;transform-origin:center;animation:wv 0.9s ease-in-out infinite alternate}'
                    '@keyframes wv{0%{transform:scaleY(0.18)}100%{transform:scaleY(1)}}')
    n = 60
    bars = []
    for i in range(n):
        x = x0 + 26 + i * (x1 - x0 - 52) / (n - 1)
        env = 0.35 + 0.65 * math.sin(math.pi * i / (n - 1)) ** 1.5
        h = 8 + 52 * env * (0.55 + 0.45 * abs(math.sin(i * 1.7)))
        delay = (i * 0.137) % 0.9
        durb = 0.55 + (i * 0.29) % 0.6
        col = LIME if i % 3 else CYAN
        bars.append(f'<rect class="wb" x="{x - 1.6:.1f}" y="{318 - h / 2:.1f}" width="3.2" height="{h:.1f}" rx="1.6" fill="{col}" style="animation-delay:-{delay:.2f}s;animation-duration:{durb:.2f}s"/>')
    d.add(f'<g opacity="0.9">{"".join(bars)}</g>')
    g, _ = d.text('CONV3D→RESNET→BIGRU→CTC', x0 + 22, y1 - 22, 12, 'monom', MUTED, ls=0.04); d.add(g)
    g, _ = d.text('INT8 ONNX · 0.4s', x1 - 22, y1 - 22, 14, 'mono', LIME, anchor='end', ls=0.06); d.add(g)

    border(d)
    d.save('hero.svg', '남윤수 · CNSAi 팀장')


# ───────────────────────── 2. 숫자 띠 ─────────────────────────
def stats():
    d = Doc(1280, 168)
    frame(d, rx=20, glows=[(640, 200, 520, LIME, 0.08)])
    items = [(20, '수상', TEXT), (3, '대상', TIER['대상']), (3, '최우수상', TIER['최우수상']), (10, '라이브 데모', LIME)]
    cw = 1280 / len(items)
    for i, (n, label, col) in enumerate(items):
        cx = cw * i + cw / 2
        if i:
            d.add(f'<line x1="{cw * i:.0f}" y1="36" x2="{cw * i:.0f}" y2="132" stroke="{LINE}" stroke-width="1.5"/>')
        gid = f'ng{i}'
        d.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="{col}"/></linearGradient>')
        cid = f'nc{i}'
        d.defs.append(f'<clipPath id="{cid}"><rect x="{cx - 120:.0f}" y="30" width="240" height="78"/></clipPath>')
        step = 80
        col_items = []
        for k in range(n + 1):
            g, _ = d.text(str(k), cx, 98 - (n - k) * step, 74, 'black', f'url(#{gid})', anchor='middle')
            col_items.append(g)
        d.add(f'<g clip-path="url(#{cid})"><g>{"".join(col_items)}'
              f'<animateTransform attributeName="transform" type="translate" values="0 {n * step};0 {n * step};0 0" keyTimes="0;0.15;1" keySplines="0 0 1 1;0.2 0.8 0.2 1" calcMode="spline" dur="{1.6 + i * 0.25:.2f}s" fill="freeze"/></g></g>')
        g, _ = d.text(label, cx, 140, 19, 'semi', MUTED, anchor='middle'); d.add(g)
    border(d, rx=20)
    d.save('stats.svg', '수상 20, 대상 3, 최우수상 3, 라이브 데모 10')


# ───────────────────────── 3. 프로젝트 카드 ─────────────────────────
def motif(kind, col):
    if kind == 'lips':
        cx, cy = 535, 130
        s = []
        for i in range(13):
            t = -1 + 2 * i / 12
            s.append(f'<circle cx="{cx + t * 70:.1f}" cy="{cy - 22 * (1 - t * t) ** 0.65 + 7 * math.exp(-(t / 0.16) ** 2):.1f}" r="3"/>')
            s.append(f'<circle cx="{cx + t * 70:.1f}" cy="{cy + 24 * (1 - t * t) ** 0.85:.1f}" r="3"/>')
        return f'<g fill="{col}">{"".join(s)}<animateTransform attributeName="transform" type="translate" values="0 0;0 -3;0 0" dur="2s" repeatCount="indefinite"/></g>'
    if kind == 'pill':
        return (f'<g transform="rotate(-30 540 128)"><rect x="480" y="104" width="120" height="48" rx="24" fill="none" stroke="{col}" stroke-width="4"/>'
                f'<path d="M540 104V152" stroke="{col}" stroke-width="4"/><path d="M540 104H576A24 24 0 0 1 576 152H540Z" fill="{col}" opacity="0.35"/></g>'
                f'<g fill="{col}"><circle cx="490" cy="200" r="7"/><circle cx="525" cy="200" r="7" opacity="0.6"/><circle cx="560" cy="200" r="7" opacity="0.3"/></g>')
    if kind == 'route':
        pts = [(470, 200), (500, 150), (545, 170), (575, 110), (610, 128)]
        p = 'M' + ' L'.join(f'{x} {y}' for x, y in pts)
        dots = ''.join(f'<circle cx="{x}" cy="{y}" r="6" fill="{col}"/>' for x, y in pts)
        return (f'<path d="{p}" fill="none" stroke="{col}" stroke-width="3" stroke-dasharray="8 8"><animate attributeName="stroke-dashoffset" values="32;0" dur="1s" repeatCount="indefinite"/></path>{dots}')
    if kind == 'wave':
        out = []
        for j in range(4):
            y = 110 + j * 26
            p = 'M460 %d ' % y + ' '.join(f'Q{475 + 30 * k} {y - 12 if k % 2 == 0 else y + 12} {490 + 30 * k} {y}' for k in range(5))
            out.append(f'<path d="{p}" fill="none" stroke="{col}" stroke-width="3" opacity="{1 - j * 0.2:.1f}"><animateTransform attributeName="transform" type="translate" values="0 0;-30 0;0 0" dur="{3 + j * 0.4:.1f}s" repeatCount="indefinite"/></path>')
        return ''.join(out)
    if kind == 'cycle':
        return (f'<g transform="translate(540 145)"><g><circle r="56" fill="none" stroke="{col}" stroke-width="4" stroke-dasharray="70 18"/>'
                f'<path d="M48 -38 L62 -26 L44 -18 Z" fill="{col}"/><path d="M-48 38 L-62 26 L-44 18 Z" fill="{col}"/>'
                f'<animateTransform attributeName="transform" type="rotate" values="0;360" dur="9s" repeatCount="indefinite"/></g></g>')
    if kind == 'grid':
        out = []
        for r in range(5):
            for c in range(6):
                v = math.exp(-(((c - 3.2) ** 2 + (r - 2) ** 2) / 4.5))
                out.append(f'<rect x="{462 + c * 24}" y="{82 + r * 24}" width="18" height="18" rx="3" fill="{col}" opacity="{0.12 + 0.8 * v:.2f}">'
                           f'<animate attributeName="opacity" values="{0.12 + 0.8 * v:.2f};{0.12 + 0.5 * v:.2f};{0.12 + 0.8 * v:.2f}" dur="{1.6 + (r + c) % 3 * 0.3:.1f}s" repeatCount="indefinite"/></rect>')
        return ''.join(out)
    return ''


CARDS = [
    ('liplab', 'LIPLAB', 'SPEECH AI · ACCESSIBILITY', ['청각장애인을 위한 한국어', '독화·발음·청능 훈련 웹앱'],
     '입술 판독 CNN · D-GOP · three.js · ONNX', '대상', None, 'K-AI 콘텐츠 공모전 Track B', LIME, 'lips', True),
    ('snapcare', 'SnapCare', 'VISION · HEALTH LITERACY', ['처방전을 찍으면 픽토그램·', '음성·다국어로 바꿔 주는 웹앱'],
     'Next.js · Python · 픽토그램 합성 엔진', '최우수상', '고등부 2위', 'e-ICON 세계대회', CYAN, 'pill', True),
    ('rundata', 'RunData', 'CIVIC TECH · ALGORITHM', ['러닝 경로에 공공 점검 미션을', '배치해 행정 사각지대를 채움'],
     'Next.js · React · 커버리지 형평 알고리즘', '대상', None, '세계발명학교엑스포', '#FF8A3D', 'route', False),
    ('meonbada', '먼바다호', 'OCEAN ENGINEERING · SIM', ['타이탄의 메테인 바다를 항해하는', '극저온 유인 탐사선 시뮬레이터'],
     'JavaScript · 부력·파랑 수치해석', '우수상', None, '미래바다 아이디어 공모전', '#5B8CFF', 'wave', False),
    ('reloop', 'Reloop', 'CIRCULAR ECONOMY', ['도시 음식물 쓰레기를 자원으로', '되돌리는 순환형 푸드 플랫폼'],
     'JavaScript · 최적화 시뮬레이션', '우수상', None, '전국학생창업발명 창업부', '#3DDC97', 'cycle', True),
    ('piezo', '압전 군중 감지', 'IoT · CROWD SAFETY', ['CCTV 대신 압전 바닥 센서로', '밀집도를 재고 분산을 유도'],
     'PVDF 센서 · 신호처리 · 시뮬레이션', '동상', None, '원더차일드 창의발명대회', '#A78BFA', 'grid', False),
]


def card(c):
    key, title, tag, desc, stack, tier, rank, award, col, mot, live = c
    d = Doc(640, 340)
    frame(d, rx=22, glows=[(80, 0, 360, col, 0.20), (640, 340, 300, col, 0.07)])
    d.defs.append(glow_filter('gl', 3))
    d.add(f'<g opacity="0.55">{motif(mot, col)}</g>')
    g, _ = d.text(tag, 40, 55, 17, 'mono', col, ls=0.12, maxw=440); d.add(g)
    if live:
        d.add(f'<rect x="510" y="32" width="92" height="30" rx="15" fill="none" stroke="{LIME}" stroke-width="1.6"/>'
              f'<circle cx="530" cy="47" r="5" fill="{LIME}" filter="url(#gl)"><animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite"/></circle>')
        g, _ = d.text('LIVE', 544, 53, 15, 'mono', LIME, ls=0.12); d.add(g)
    g, _ = d.text(title, 38, 124, 50, 'black', TEXT, ls=-0.01, maxw=420); d.add(g)
    for i, line in enumerate(desc):
        g, _ = d.text(line, 40, 168 + i * 31, 22, 'semi', '#B9C1CF', maxw=430); d.add(g)
    g, _ = d.text(stack, 40, 250, 17, 'med', '#7F889B', maxw=560); d.add(g)
    b, bw = badge(d, 40, 272, tier, h=40, size=21, shine=(tier in ('대상', '최우수상')), uid=key)
    d.add(b)
    x = 40 + bw + 12
    if rank:
        r, rw = chip(d, x, 274, rank, TIER[tier], h=36, size=16)
        d.add(r); x += rw + 12
    g, _ = d.text(award, x + 2, 299, 19, 'bold', TEXT, maxw=600 - x); d.add(g)
    border(d, rx=22, col=LINE)
    d.save(f'card-{key}.svg', f'{title}: {tier} {award}')


# ───────────────────────── 4. 수상 타임라인 ─────────────────────────
AWARDS = [
    ('2025', [
        ('', '금상', '1위', '교내 과학발명품 경진대회', '충남삼성고 · LifeDoor'),
        ('', '은상', '2위', '교내 청소년 과학 페어', '충남삼성고 · Reloop'),
        ('', '우수상', None, '제9회 UNIST 청소년 슈퍼컴퓨팅 캠프', 'UNIST 총장상 · MPI 감염병 확산 시뮬레이터'),
        ('', '우수상', None, '제6회 미래바다 아이디어 공모전', '선박해양플랜트연구소장상 · 먼바다호'),
        ('', '입상', None, '제17회 소외이웃과 함께하는 창의설계 경진대회', '나눔과 기술 대표상 · InsuNest'),
        ('', '장려상', None, '제6회 AI·SW 학생 동아리 한마당', '충청남도교육감상 · CNSAi'),
    ]),
    ('2026', [
        ('', '동상', None, '제5회 매일경제 MBN 원더차일드 창의발명대회', '매일경제 회장상 · 압전 군중 밀집도 감지'),
        ('', '장려상', None, '제4회 IT코딩 발명 아이디어 및 에세이 경진대회', '행복일자리운동본부 이사장상 · LIPLAB'),
        ('', '은상', '2위', '교내 청소년 과학 페어', '충남삼성고 · 해양 쓰레기 수거선 경로탐색'),
        ('', '선발', None, '제11회 4차 산업혁명 AI 영재장학생', '한국언론인협회 · 국제 디지털경제3.0포럼'),
        ('07.28', '최우수상', None, '제19회 전국학생창업발명경진대회 환경부', '지식재산처장상 · LifeDoor'),
        ('07.28', '우수상', None, '제19회 전국학생창업발명경진대회 창업부', '한국지식재산보호원장상 · Reloop'),
        ('08.03', '대상', None, '2026 K-AI 콘텐츠 공모전 Track B 솔루션', 'AX 뮤즈상 (KT 지니뮤직 사장상) · LIPLAB'),
        ('08.07', '최우수상', '고등부 2위', '제16회 e-ICON 세계대회', '한국디지털교육협회장상 · SnapCare'),
        ('08.10', '대상', None, '제2회 세계발명학교엑스포 발명 아이디어·시제품', '한국교원단체총연합회장상 · RunData'),
        ('08.10', '대상', None, '제2회 세계발명학교엑스포 AI시대 문제해결 챌린지', '한국교원단체총연합회장상 · 비탑승 주행거리 과금'),
        ('', '우수상', None, '제15회 에너지 환경 탐구대회 중고등부', '(사)환경교육센터이사장상 · 산불 진압 하이드로겔'),
        ('', '동상', None, '제28회 전국학생통계활용대회', '데이터처장상 · 건강정보 AI 생성 실태 분석'),
        ('', '금상', None, '제17회 전국 창의적 문제해결능력 경진대회', '지식재산처장상'),
        ('', '최우수상', None, 'IT 디플로마', '충남삼성고'),
    ]),
]


def timeline():
    STEP, CH, CW = 70, 112, 560
    top = 250
    n_items = sum(len(v) for _, v in AWARDS)
    H = top + sum(96 + len(v) * STEP + CH - STEP + 40 for _, v in AWARDS) + 20
    d = Doc(1280, H)
    frame(d, glows=[(640, 0, 600, LIME, 0.10), (1280, H, 500, TIER['대상'], 0.08)])
    d.defs.append(glow_filter('gl', 4))

    g, _ = d.text('AWARDS TIMELINE', 640, 70, 17, 'mono', LIME, anchor='middle', ls=0.3); d.add(g)
    g, _ = d.text(f'수상 {n_items}', 640, 140, 64, 'black', TEXT, anchor='middle'); d.add(g)
    counts = {}
    for _, items in AWARDS:
        for it in items:
            counts[it[1]] = counts.get(it[1], 0) + 1
    order = ['대상', '최우수상', '금상', '우수상', '은상', '동상', '장려상', '입상', '선발']
    chips = [(t, counts[t]) for t in order if t in counts]
    widths = [F['bold'].width(f'{t} {c}', 17) + 40 for t, c in chips]
    total = sum(widths) + 10 * (len(chips) - 1)
    x = 640 - total / 2
    for (t, c), w in zip(chips, widths):
        d.add(f'<rect x="{x:.0f}" y="168" width="{w:.0f}" height="34" rx="17" fill="{TIER[t]}" fill-opacity="0.12" stroke="{TIER[t]}" stroke-width="1.4"/>'
              f'<circle cx="{x + 17:.0f}" cy="185" r="5" fill="{TIER[t]}"/>')
        g, _ = d.text(f'{t} {c}', x + 29, 191, 17, 'bold', TIER[t]); d.add(g)
        x += w + 10

    spine_top, spine_bot = top, H - 50
    d.defs.append(f'<linearGradient id="sp" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{LIME}" stop-opacity="0.1"/><stop offset="0.5" stop-color="{LIME}" stop-opacity="0.5"/><stop offset="1" stop-color="{TIER["대상"]}" stop-opacity="0.6"/></linearGradient>')
    d.add(f'<rect x="638.5" y="{spine_top}" width="3" height="{spine_bot - spine_top}" fill="url(#sp)"/>')
    # 줄기를 따라 내려가는 빛
    d.add(f'<rect x="636" y="{spine_top}" width="8" height="90" rx="4" fill="{LIME}" opacity="0.9" filter="url(#gl)">'
          f'<animate attributeName="y" values="{spine_top};{spine_bot - 90}" dur="5s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.1;0.85;1" dur="5s" repeatCount="indefinite"/></rect>')

    y = top
    side = 0
    idx = 0
    for year, items in AWARDS:
        d.add(f'<rect x="560" y="{y}" width="160" height="56" rx="28" fill="{BG}" stroke="{LIME}" stroke-width="2"/>')
        g, _ = d.text(year, 640, y + 40, 34, 'black', LIME, anchor='middle', ls=0.04); d.add(g)
        y += 96
        for date, tier, rank, contest, sub in items:
            col = TIER[tier]
            ny = y + CH / 2
            left = (side == 0)
            cx0 = 640 - 44 - CW if left else 640 + 44
            # 연결선과 마디
            lx1, lx2 = (cx0 + CW, 640) if left else (640, cx0)
            d.add(f'<line x1="{lx1}" y1="{ny}" x2="{lx2}" y2="{ny}" stroke="{col}" stroke-width="2" opacity="0.6"/>')
            big = tier in ('대상', '최우수상')
            if big:
                d.add(f'<circle cx="640" cy="{ny}" r="10" fill="none" stroke="{col}" stroke-width="2">'
                      f'<animate attributeName="r" values="10;26" dur="1.8s" begin="{idx * 0.2:.1f}s" repeatCount="indefinite"/>'
                      f'<animate attributeName="opacity" values="0.9;0" dur="1.8s" begin="{idx * 0.2:.1f}s" repeatCount="indefinite"/></circle>')
            d.add(f'<circle cx="640" cy="{ny}" r="{10 if big else 8}" fill="{col}" filter="url(#gl)"/><circle cx="640" cy="{ny}" r="3.5" fill="{BG}"/>')
            # 카드
            d.add(f'<rect x="{cx0}" y="{y}" width="{CW}" height="{CH}" rx="16" fill="{PANEL}" stroke="{col}" stroke-opacity="{0.75 if big else 0.32}" stroke-width="1.5"/>')
            d.add(f'<rect x="{cx0}" y="{y + 16}" width="4" height="{CH - 32}" rx="2" fill="{col}"/>')
            b, bw = badge(d, cx0 + 24, y + 16, tier, h=34, size=18, shine=(tier == '대상'), uid=f't{idx}')
            d.add(b)
            bx = cx0 + 24 + bw + 10
            if rank:
                r, rw = chip(d, bx, y + 17, rank, col, h=32, size=15)
                d.add(r)
            if date:
                g, _ = d.text('2026.' + date, cx0 + CW - 22, y + 39, 16, 'mono', col, anchor='end', ls=0.04); d.add(g)
            g, _ = d.text(contest, cx0 + 26, y + 80, 23, 'bold', TEXT, maxw=CW - 48); d.add(g)
            g, _ = d.text(sub, cx0 + 26, y + 103, 17, 'med', MUTED, maxw=CW - 48); d.add(g)
            y += STEP
            side ^= 1
            idx += 1
        y += CH - STEP + 40
    border(d)
    d.save('awards.svg', f'수상 타임라인: 2025~2026년 {n_items}건')


hero(); stats()
for c in CARDS:
    card(c)
timeline()
