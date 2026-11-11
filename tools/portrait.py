"""Make portrait.txt from a photo: cut the person out (GrabCut), crop head and shoulders, drop the neck and collar
below the chin, give each eye its own contrast with the iris darkened into an almond, and turn it into ASCII.

Needs OpenCV (pip install opencv-python-headless numpy, in a venv). The photo itself stays out of this repo.
    python tools/portrait.py pfp.jpeg > portrait.txt
The rectangles are in the photo's own pixels and fit the current photo; the eye centres came from OpenCV's YuNet
face detector. Move them for another photo.
"""
import sys, cv2, numpy as np

PERSON = (500, 740, 1400, None)                       # GrabCut's search box (None: to the bottom edge)
SURE_PERSON = [(820, 840, 1000, 1080), (700, 1250, 1250, None)]                                  # face, jacket
SURE_SCENE = [(640, 760, 782, 1075), (1036, 760, 1360, 1050), (1270, 1050, 1400, 1300), (500, 1150, 560, 1600)]
CROP, COLS, RAMP = (745, 755, 1085, 1150), 56, ' .:-=+*#%@'
EYES = [(854, 940), (951, 934)]
JAW, CHIN = (1030, (905, 985), (112, 118)), 1102      # below JAW[0] only the jaw ellipse stays; nothing below CHIN

def cut(img):
    h, w = img.shape[:2]; k = 0.5
    small = cv2.resize(img, (int(w * k), int(h * k)))
    box = lambda x0, y0, x1, y1: (int(x0 * k), int(y0 * k), int(x1 * k), int((y1 or h) * k))
    mask = np.full(small.shape[:2], cv2.GC_PR_BGD, np.uint8)
    x0, y0, x1, y1 = box(*PERSON); mask[y0:y1, x0:x1] = cv2.GC_PR_FGD
    for r in SURE_PERSON: a, b, c, d = box(*r); mask[b:d, a:c] = cv2.GC_FGD
    for r in SURE_SCENE: a, b, c, d = box(*r); mask[b:d, a:c] = cv2.GC_BGD
    mask[:y0, :] = cv2.GC_BGD; mask[:, :x0] = cv2.GC_BGD; mask[:, x1:] = cv2.GC_BGD
    cv2.grabCut(small, mask, None, np.zeros((1, 65)), np.zeros((1, 65)), 8, cv2.GC_INIT_WITH_MASK)
    m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    _, lab, stats, _ = cv2.connectedComponentsWithStats(m)          # keep only the largest piece: the person
    return cv2.resize(np.where(lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8), (w, h))

def ascii_art(img, mask):
    x0, y0, x1, y1 = CROP
    rows = round(COLS * (y1 - y0) / (x1 - x0) * 0.5)                # a character is about twice as tall as wide
    jaw = np.zeros(mask.shape, np.uint8); cv2.ellipse(jaw, JAW[1], JAW[2], 0, 0, 360, 255, -1)
    jaw[:JAW[0]] = 255; jaw[CHIN:] = 0                # the head untouched; under the mouth, the jaw and nothing beside it
    gray, m, drawn = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY), mask[y0:y1, x0:x1], cv2.bitwise_and(mask, jaw)[y0:y1, x0:x1]
    gray = cv2.addWeighted(gray, 1.8, cv2.GaussianBlur(gray, (0, 0), 6), -0.8, 0)   # unsharp: glasses survive the downscale
    lo, hi = np.percentile(gray[m > 127], [2, 98])                  # stretch the person's own range, not the scene's
    eq = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(3, 3)).apply((np.clip((gray - lo) / (hi - lo), 0, 1) ** 1.15 * 255).astype(np.uint8))
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 40, 110)
    eq, lens, iris = eq.astype(float) / 255, np.zeros(gray.shape, np.float32), np.zeros(gray.shape, np.float32)
    for ex, ey in EYES:                               # each lens: its own stretch, brighter mids, no edge carving
        cv2.ellipse(lens, (ex - x0, ey - y0), (40, 26), 0, 0, 360, 1, -1)
        box = (slice(ey - y0 - 26, ey - y0 + 26), slice(ex - x0 - 40, ex - x0 + 40))
        roi = gray[box].astype(float); a, b = np.percentile(roi, [3, 85])
        eq[box] = np.where(lens[box] > 0, np.clip((roi - a) / (b - a), 0, 1) ** 0.6, eq[box])
        cv2.ellipse(iris, (ex - x0, ey - y0 + 4), (17, 6), 0, 0, 360, 0.45, -1)   # the opening, darkest at the iris
        cv2.ellipse(iris, (ex - x0, ey - y0 + 4), (8, 6), 0, 0, 360, 0.8, -1)
    eq = np.rint(eq * (1 - cv2.GaussianBlur(iris, (0, 0), 1.5)) * 255).astype(np.uint8)
    lens = cv2.GaussianBlur(lens, (0, 0), 3)
    cell = lambda a: cv2.resize(a, (COLS, rows), interpolation=cv2.INTER_AREA).astype(float) / 255
    lum, edge, cov, inside = cell(eq), cell(edges), cell(drawn), cell((lens * 255).astype(np.uint8))   # tones from the whole cut-out; cells only above the chin
    out = []
    for r in range(rows):
        line = ''
        for c in range(COLS):
            v = min(1, 0.05 + 0.95 * lum[r, c] - 0.6 * edge[r, c] * (1 - inside[r, c]))  # edges carve dark lines, the way a pencil would
            line += ' ' if cov[r, c] < 0.45 else RAMP[max(1, min(len(RAMP) - 1, int(v * (len(RAMP) - 1))))]
        out.append(line.rstrip())
    while out and not out[-1]: out.pop()
    return '\n'.join(out)

if __name__ == '__main__':
    img = cv2.imread(sys.argv[1])
    print(ascii_art(img, cut(img)))
