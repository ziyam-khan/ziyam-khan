"""The profile card: my ASCII portrait beside a neofetch-style readout (key, dotted leader, value), drawn as two SVGs.

Standard library only, so the daily workflow runs it without installing anything. With GITHUB_TOKEN set it
refreshes the GitHub numbers into stats.json; without it, it reuses the last ones.
    python3 card.py
"""
import html, json, os, urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
USER = 'ziyam-khan'
WIDTH = 58                                            # the readout's width in characters

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

def since(start, today=None):
    """'2 years, 4 months' from a (year, month) to today."""
    today = today or date.today()
    y, m = divmod((today.year - start[0]) * 12 + today.month - start[1], 12)
    return ', '.join(p for p in [f'{y} year{"s" * (y != 1)}' if y else '', f'{m} month{"s" * (m != 1)}' if m else ''] if p) or 'this month'

def readout(s):
    """The card's lines: 'title', a (key, value) field, two fields side by side, a section heading, None for a gap."""
    return [
        'title',
        ('Name', 'Ziyam Khan'),
        ('Role', 'Assistant Professor, IT'),
        ('Host', 'Parul University'),
        ('Location', 'Vadodara, India'),
        ('Uptime', f'{since((2024, 7))} teaching'),
        ('OS', 'EndeavourOS, KDE Plasma'),
        None,
        ('Languages', 'Python, TypeScript, Rust, C/C++'),
        ('IDE', 'Neovim (AstroNvim)'),
        ('Terminal', 'Konsole, CyberpunkNeon'),
        None,
        ('Research', 'Adversarial federated learning'),
        ('Papers', '2 published, 1 accepted, 2 in progress'),
        ('Building', 'runets, Dept Ops, fieldbook'),
        None,
        'Contact',
        ('Email', 'ziyamkhan39@gmail.com'),
        ('Website', 'ziyamkhan.com'),
        ('X', '@zimeckus'),
        ('LinkedIn', 'in/ziyam-khan'),
        ('ORCID', '0009-0000-1943-8481'),
        None,
        'GitHub Stats',
        (('Repos', f"{s['repos']}"), ('Contributions', f"{s['contributions']:,}")),
        None,
        'colors',
    ]

# CyberpunkNeon, my terminal's theme: pink keys, cyan values, orange headings, leaders in its deep blue.
THEMES = {
    'dark': dict(bg='#000b1e', line='#133e7c', top='#ea00d9', bottom='#0abdc6', key='#ff4fd8', value='#3ee6f0', head='#ff9e3d', dim='#2f4f86', ink='#d7d7d5',
                 dots=['#133e7c', '#ff0000', '#ea00d9', '#f57800', '#3ee6f0', '#711c91', '#0abdc6', '#d7d7d5']),
    'light': dict(bg='#ffffff', line='#d0d7de', top='#b0009f', bottom='#007c84', key='#b0009f', value='#006d75', head='#c25f00', dim='#b8c2cc', ink='#1f2328',
                  dots=['#133e7c', '#cf2020', '#b0009f', '#c25f00', '#006d75', '#711c91', '#007c84', '#57606a']),
}
FONT, SIZE, LINE, CHAR = "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', monospace", 13, 16, 7.8
PAD, GAP = 24, 3
RAMP, TONES = ['.:', '-=', '+*', '#%@'], [0.4, 0.6, 0.85, 1]   # portrait characters by density, and their opacity

def mix(a, b, t):
    pa, pb = (tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in (a, b))
    return '#' + ''.join(f'{round(x + (y - x) * t):02x}' for x, y in zip(pa, pb))

def field(key, value, width, t):
    """'. Key: ....... value', the value flush right at width."""
    lead = max(1, width - len(key) - len(value) - 5)
    return [('. ', t['dim']), (key, t['key']), (':', t['dim']), (' ' + '.' * lead + ' ', t['dim']), (value, t['value'])]

def parts(item, t):
    if item == 'title':
        return [('ziyam', t['key']), ('@', t['ink']), ('github', t['value']), (' ' + '-' * (WIDTH - 13), t['dim'])]
    if item is None:
        return [('.', t['dim'])]
    if isinstance(item, str):
        return [('- ', t['dim']), (item, t['head']), (' ' + '-' * (WIDTH - len(item) - 3), t['dim'])]
    if isinstance(item[0], tuple):                    # two fields side by side
        half = (WIDTH - 3) // 2
        return field(*item[0], half, t) + [(' | ', t['dim'])] + field(*item[1], WIDTH - half - 1, t)[1:]   # the right one drops its '. '
    return field(*item, WIDTH, t)

def svg(theme, art, items):
    t = THEMES[theme]
    x0 = PAD + (max(map(len, art)) + GAP) * CHAR
    w, h = round(x0 + WIDTH * CHAR + PAD), PAD * 2 + max(len(art), len(items)) * LINE
    y = lambda k: PAD + (k + 1) * LINE - 4
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}" font-size="{SIZE}">',
           f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="{t["bg"]}" stroke="{t["line"]}"/>',
           '<text xml:space="preserve">']
    top = max(0, len(items) - len(art)) // 2
    for k, row in enumerate(art):                     # the portrait shades from pink at the hair to cyan at the chin
        colour, x, runs = mix(t['top'], t['bottom'], k / max(1, len(art) - 1)), PAD, []
        for ch in row:   # runs of one tone: sparse characters dim, dense ones full, so the face has depth
            tone = TONES[next(i for i, s in enumerate(RAMP) if ch in s)] if ch != ' ' else None
            if runs and runs[-1][0] == tone: runs[-1][1] += ch
            else: runs.append([tone, ch])
        for tone, text in runs:
            if tone is not None: out.append(f'<tspan x="{x:.1f}" y="{y(k + top)}" fill="{colour}" fill-opacity="{tone}">{html.escape(text)}</tspan>')
            x += len(text) * CHAR
    out.append('</text>')
    for k, item in enumerate(items):
        if item == 'colors':
            out += [f'<circle cx="{x0 + CHAR + i * 2 * CHAR:.1f}" cy="{y(k) - 4}" r="4.5" fill="{c}"/>' for i, c in enumerate(t['dots'])]
        else:
            out.append(f'<text x="{x0:.1f}" y="{y(k)}" xml:space="preserve">' + ''.join(f'<tspan fill="{c}">{html.escape(s)}</tspan>' for s, c in parts(item, t)) + '</text>')
    out.append('</svg>')
    return '\n'.join(out) + '\n'

if __name__ == '__main__':
    assert since((2024, 7), date(2026, 11, 11)) == '2 years, 4 months' and since((2024, 7), date(2024, 7, 2)) == 'this month'
    art = (HERE / 'portrait.txt').read_text().rstrip('\n').split('\n')
    items = readout(stats())
    for theme in THEMES:
        (HERE / f'{theme}.svg').write_text(svg(theme, art, items))
