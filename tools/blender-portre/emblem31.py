"""Compose logo31.webp (600x300, transparent: the Blender boat over a painted cartouche plaque; the title text is set by
the browser inside the plaque) and icon31.png (512x512 PWA icon). usage: python3 emblem31.py boat.png outdir"""
import sys, os
from PIL import Image, ImageDraw, ImageFilter
boat = Image.open(sys.argv[1]).convert('RGBA'); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
bb = boat.getbbox(); boat = boat.crop(bb)
INK = (43, 29, 20, 255); GOLD = (217, 164, 58, 255); GOLD2 = (242, 198, 90, 255); PAPER = (251, 243, 223, 255)
def plaque(W, H, S=3):
    im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0)); g = ImageDraw.Draw(im); r = H * S // 2
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([10 * S, 14 * S, W * S - 4 * S, H * S - 2 * S], r, fill=(43, 29, 20, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4 * S)))
    g.rounded_rectangle([4 * S, 4 * S, W * S - 18 * S, H * S - 10 * S], r - 8 * S, fill=GOLD, outline=INK, width=3 * S)
    g.rounded_rectangle([4 * S, 4 * S, W * S - 18 * S, (H * 0.5) * S], r - 8 * S, fill=None)
    g.rounded_rectangle([13 * S, 13 * S, W * S - 27 * S, H * S - 19 * S], r - 17 * S, fill=PAPER, outline=INK, width=2 * S)
    # the cartouche's tie bar on the right end
    g.rounded_rectangle([W * S - 20 * S, 10 * S, W * S - 6 * S, H * S - 16 * S], 4 * S, fill=GOLD, outline=INK, width=3 * S)
    # a soft highlight on the gold rim
    g.arc([8 * S, 8 * S, 8 * S + 2 * r - 18 * S, H * S - 14 * S], 120, 230, fill=GOLD2, width=3 * S)
    for k in range(16):   # small turquoise/lapis studs along the rim
        x = (40 + k * (W - 100) / 15) * S; c = (43, 165, 154, 255) if k % 2 else (31, 95, 168, 255)
        g.ellipse([x - 3 * S, 6 * S, x + 3 * S, 12 * S], fill=c)
    return im.resize((W, H), Image.LANCZOS)
# logo 600x300
L = Image.new('RGBA', (600, 300), (0, 0, 0, 0))
pl = plaque(560, 100); L.alpha_composite(pl, (20, 192))
bw = 300; bh = int(boat.height * bw / boat.width)
if bh > 230: bh = 230; bw = int(boat.width * bh / boat.height)
b2 = boat.resize((bw, bh), Image.LANCZOS); L.alpha_composite(b2, ((600 - bw) // 2, 205 - bh + 22))
L.save(os.path.join(out, 'logo31.webp'), 'WEBP', quality=85, method=6); L.save(os.path.join(out, 'logo31.png'))
# icon 512: warm rounded square, sun disc, boat
S = 2; N = 512 * S; I = Image.new('RGBA', (N, N), (0, 0, 0, 0)); g = ImageDraw.Draw(I)
bg = Image.new('RGBA', (N, N)); gb = ImageDraw.Draw(bg)
for y in range(N): t = y / N; gb.line([(0, y), (N, y)], fill=(int(250 - 30 * t), int(214 - 40 * t), int(150 - 50 * t), 255))
m = Image.new('L', (N, N), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, N - 1, N - 1], 110 * S, fill=255)
I.paste(bg, (0, 0), m); g = ImageDraw.Draw(I)
g.ellipse([N * 0.5 - 150 * S, 70 * S, N * 0.5 + 150 * S, 370 * S], fill=(255, 236, 170, 255))
g.ellipse([N * 0.5 - 118 * S, 102 * S, N * 0.5 + 118 * S, 338 * S], fill=(255, 220, 130, 255))
g.rounded_rectangle([6 * S, 6 * S, N - 6 * S, N - 6 * S], 106 * S, outline=INK, width=8 * S)
g.rounded_rectangle([18 * S, 18 * S, N - 18 * S, N - 18 * S], 96 * S, outline=GOLD, width=5 * S)
bw = int(460 * S); bh = int(boat.height * bw / boat.width)
I.alpha_composite(boat.resize((bw, bh), Image.LANCZOS), ((N - bw) // 2, N - bh - 34 * S))
I = I.resize((512, 512), Image.LANCZOS); I.save(os.path.join(out, 'icon31.png'))
print('logo bytes', os.path.getsize(os.path.join(out, 'logo31.webp')), 'icon bytes', os.path.getsize(os.path.join(out, 'icon31.png')))
