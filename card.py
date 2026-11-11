"""The profile card: a fastfetch-style readout of me beside an ASCII portrait, drawn as two SVGs (dark and light).

Standard library only, so the daily workflow runs it without installing anything. With GITHUB_TOKEN set it
refreshes the GitHub numbers into stats.json; without it, it reuses the last ones.
    python3 card.py
"""
import html, json, os, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
USER = 'ziyam-khan'

def stats():
    file = HERE / 'stats.json'
    token = os.environ.get('GITHUB_TOKEN')
    if token:   # on any failure the last numbers stand, so a bad day on the API never breaks the card
        query = '{ user(login: "%s") { repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) { totalCount } contributionsCollection { contributionCalendar { totalContributions } } } }' % USER
        req = urllib.request.Request('https://api.github.com/graphql', json.dumps({'query': query}).encode(), {'Authorization': f'bearer {token}'})
        try:
            user = json.load(urllib.request.urlopen(req, timeout=30))['data']['user']
            file.write_text(json.dumps({'repos': user['repositories']['totalCount'], 'contributions': user['contributionsCollection']['contributionCalendar']['totalContributions']}) + '\n')
        except Exception as error:
            print(f'stats: kept the last numbers ({error})')
    return json.loads(file.read_text())

def lines(s):
    """The readout, as fastfetch prints it: a title, then groups of short keys and values, then the colours."""
    return [
        [('ziyam', 'c'), ('@', 'v'), ('github', 'c')],
        [],
        ('OS', 'EndeavourOS x86_64 · KDE Plasma · Wayland'),
        ('HOST', 'Parul University, Vadodara, India'),
        ('KER', 'Assistant Professor, Information Technology'),
        ('UP', 'teaching since July 2024'),
        ('SHL', 'bash · Neovim (AstroNvim) · Git'),
        ('TRM', 'Konsole · JetBrains Mono · CyberpunkNeon'),
        [],
        ('RES', 'federated learning when an adversary'),
        ('', 'decides who goes missing'),
        ('PAP', '2 published · 1 accepted · 2 in progress'),
        ('LANG', 'Python · TypeScript · Rust · C/C++ · SQL · GLSL'),
        ('BUILD', 'runets · Dept Ops · fieldbook · Trailblazer'),
        ('GIT', f"{s['repos']} public repos · {s['contributions']:,} contributions this year"),
        [],
        ('WEB', 'ziyamkhan.com'),
        ('MAIL', 'ziyamkhan39@gmail.com'),
        ('X', '@zimeckus'),
        ('IN', 'linkedin.com/in/ziyam-khan'),
        ('ORCID', '0009-0000-1943-8481'),
        [],
        'colors',
    ]

# CyberpunkNeon, the terminal theme this card is drawn from; the light card darkens each hue to read on white.
THEMES = {
    'dark': dict(bg='#000b1e', line='#133e7c', art='#0abdc6', keys=('#ea00d9', '#0abdc6'), v='#d7d7d5', c='#0abdc6', dots=['#133e7c', '#ff0000', '#ea00d9', '#f57800', '#133e7c', '#711c91', '#0abdc6', '#d7d7d5']),
    'light': dict(bg='#f6f8fa', line='#d0d7de', art='#007c84', keys=('#b0009f', '#007c84'), v='#1f2328', c='#007c84', dots=['#133e7c', '#cf2020', '#b0009f', '#c25f00', '#133e7c', '#711c91', '#007c84', '#57606a']),
}
FONT, SIZE, LINE, CHAR = "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', monospace", 13, 16, 7.8
PAD, GAP, KEYW = 24, 4, 7
RAMP, TONES = ['.:', '-=', '+*', '#%@'], [0.4, 0.6, 0.85, 1]   # portrait characters by density, and their opacity

def svg(theme, art, readout):
    t = THEMES[theme]
    artw = max(map(len, art))
    x0 = PAD + (artw + GAP) * CHAR
    rows = max(len(art), len(readout))
    widest = max(KEYW + len(item[1]) if isinstance(item, tuple) else 16 for item in readout)
    w, h = round(x0 + widest * CHAR + PAD), PAD * 2 + rows * LINE
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}" font-size="{SIZE}">',
           f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="{t["bg"]}" stroke="{t["line"]}"/>',
           f'<text fill="{t["art"]}" xml:space="preserve">']
    for k, row in enumerate(art):
        y, x, runs = PAD + (k + 1) * LINE - 4, PAD, []
        for ch in row:   # runs of one tone: sparse characters dim, dense ones full, so the face has depth
            tone = TONES[next(i for i, s in enumerate(RAMP) if ch in s)] if ch != ' ' else None
            if runs and runs[-1][0] == tone: runs[-1][1] += ch
            else: runs.append([tone, ch])
        for tone, text in runs:
            if tone is not None: out.append(f'<tspan x="{x:.1f}" y="{y}" fill-opacity="{tone}">{html.escape(text)}</tspan>')
            x += len(text) * CHAR
    out.append('</text>')
    n, off = 0, max(0, (len(art) - len(readout)) // 2)   # the readout sits level with the middle of the portrait
    for k, item in enumerate(readout):
        y = PAD + (k + 1 + off) * LINE - 4
        if item == 'colors':
            out += [f'<circle cx="{x0 + CHAR + i * 2 * CHAR:.1f}" cy="{y - 4}" r="4.5" fill="{c}"/>' for i, c in enumerate(t['dots'])]
        elif isinstance(item, tuple):
            key, value = item
            if key: n += 1
            fill = t['keys'][(n - 1) % 2]
            out.append(f'<text x="{x0:.1f}" y="{y}" xml:space="preserve"><tspan fill="{fill}" font-weight="700">{html.escape(key.ljust(KEYW))}</tspan><tspan fill="{t["v"]}">{html.escape(value)}</tspan></text>')
        elif item:
            out.append(f'<text x="{x0:.1f}" y="{y}" font-weight="700">' + ''.join(f'<tspan fill="{t[c]}">{html.escape(s)}</tspan>' for s, c in item) + '</text>')
    out.append('</svg>')
    return '\n'.join(out) + '\n'

if __name__ == '__main__':
    art = (HERE / 'portrait.txt').read_text().rstrip('\n').split('\n')
    readout = lines(stats())
    for theme in THEMES:
        (HERE / f'{theme}.svg').write_text(svg(theme, art, readout))
