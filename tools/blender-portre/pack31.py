"""Composite the Blender renders onto a painted backdrop, encode WebP and write portraits31.txt.
usage: python3 pack31.py RENDER_DIR OUT_DIR [quality]
Backdrop: the character's accent colour as a soft round disc (sun-washed centre, darker rim), a few loose brush
strokes, paper grain; the figure keeps its ink outline. Output 320x320 WebP per key/mood."""
import sys, os, glob, base64, io, json, random, math
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
LOOKS = None
def looks():
    global LOOKS
    if LOOKS is None:
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'char31.py')).read()
        a = src.index('LOOKS = {'); b = src.index('\n}\n', a) + 2
        ns = {}; exec(src[a:b], ns); LOOKS = ns['LOOKS']
    return LOOKS
def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def backdrop(key, n=320):
    L = looks().get(key, {}); base = hexc(L.get('bg', '#F3E2B8')); acc = hexc(L.get('acc', '#D9A43A'))
    S = 2; N = n * S; rnd = random.Random(sum(map(ord, key)))
    im = Image.new('RGBA', (N, N), mix(base, (255, 248, 232), 0.35) + (255,))
    g = ImageDraw.Draw(im)
    # disc with a darker rim
    for i in range(40):
        t = i / 39; r = N * (0.47 - 0.2 * t); c = mix(mix(base, acc, 0.35), mix(base, (255, 250, 236), 0.55), t ** 1.4)
        g.ellipse([N / 2 - r, N * 0.46 - r, N / 2 + r, N * 0.46 + r], fill=c + (255,))
    # loose brush strokes across the disc
    lay = Image.new('RGBA', (N, N), (0, 0, 0, 0)); gl = ImageDraw.Draw(lay)
    for j in range(9):
        y = N * (0.18 + 0.07 * j) + rnd.uniform(-8, 8); x0 = rnd.uniform(-0.1, 0.25) * N; x1 = x0 + rnd.uniform(0.4, 0.8) * N
        col = (255, 250, 236, rnd.randint(14, 28)) if j % 2 else mix(base, acc, 0.6) + (rnd.randint(12, 24),)
        gl.rounded_rectangle([x0, y, x1, y + rnd.uniform(6, 16) * S], radius=12 * S, fill=col)
    lay = lay.filter(ImageFilter.GaussianBlur(2 * S))
    disc = Image.new('L', (N, N), 0); ImageDraw.Draw(disc).ellipse([N * 0.03, N * -0.01, N * 0.97, N * 0.93], fill=255)
    im.paste(lay, (0, 0), ImageChops.multiply(lay.split()[3], disc))
    # thin ink ring and a gold inner ring
    g.ellipse([N * 0.03, N * -0.01, N * 0.97, N * 0.93], outline=mix(acc, (43, 29, 20), 0.5) + (255,), width=3 * S)
    # paper grain
    gr = Image.effect_noise((N, N), 18).convert('L'); im = Image.composite(im, Image.blend(im, Image.new('RGBA', (N, N), (90, 60, 40, 255)), 0.06), gr.point(lambda v: 255 if v > 128 else 0))
    return im.resize((n, n), Image.LANCZOS)

def compose(png, key, n=320):
    fg = Image.open(png).convert('RGBA').resize((n, n), Image.LANCZOS)
    bg = backdrop(key, n)
    # a soft ground shadow behind the figure
    sh = fg.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.22))
    bg.paste(Image.new('RGBA', (n, n), (60, 35, 25, 255)), (5, 4), sh)
    bg.alpha_composite(fg)
    return bg.convert('RGB')

def webp(img, q):
    b = io.BytesIO(); img.save(b, 'WEBP', quality=q, method=6); return b.getvalue()

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]; q = int(sys.argv[3]) if len(sys.argv) > 3 else 80
    os.makedirs(out, exist_ok=True)
    P = {}; total = 0
    for f in sorted(glob.glob(os.path.join(src, '*.png'))):
        name = os.path.basename(f)[:-4]
        if name.count('_') < 1 or name.startswith(('logo', 'icon')): continue
        key, mood = name.rsplit('_', 1)
        img = compose(f, key); data = webp(img, q); total += len(data)
        open(os.path.join(out, name + '.webp'), 'wb').write(data)
        P.setdefault(key, {})[mood] = 'data:image/webp;base64,' + base64.b64encode(data).decode()
    extra = {}
    lp = os.path.join(src, 'logo31.webp')
    if os.path.exists(lp): extra['_logo'] = 'data:image/webp;base64,' + base64.b64encode(open(lp, 'rb').read()).decode()
    js = '  /* ================= portraits31: pre-rendered Blender character portraits (320x320 WebP) =================\n'
    js += '     PORTRAITS[key][mood] = data URL; keys = hero/merchant/CAST keys, moods neutral happy angry sly surprised thinking\n'
    js += '     (minor characters have neutral/happy/angry). PORTRAITS._logo = the title emblem. portraitURL(key, mood) falls back\n'
    js += '     to neutral and returns \'\' when the key is missing. */\n'
    js += '  const PORTRAITS = {\n'
    items = [(k, P[k]) for k in sorted(P, key=lambda k: (not k.startswith('h_'), k))]
    for k, mm in items:
        js += '    ' + json.dumps(str(k)) + ':{ ' + ', '.join(m + ':' + json.dumps(u) for m, u in sorted(mm.items(), key=lambda x: (x[0] != 'neutral', x[0]))) + ' },\n'
    for k, u in extra.items(): js += '    ' + k + ':' + json.dumps(u) + ',\n'
    js += '  };\n'
    js += "  function portraitURL(key, mood) { const p = PORTRAITS[String(key)]; if (!p || typeof p !== 'object') return ''; return p[mood || 'neutral'] || p.neutral || ''; }\n"
    open(os.path.join(out, 'portraits31.txt'), 'w').write(js)
    print('images', sum(len(v) for v in P.values()), 'webp bytes', total, 'module bytes', len(js))
