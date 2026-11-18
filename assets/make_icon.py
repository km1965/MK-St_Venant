import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 1024
UP = 4
W = H = S * UP


def sc(v):
    return int(round(v * UP))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def rounded_rect_mask(size, radius, inset=0):
    m = Image.new('L', size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([inset, inset, size[0] - 1 - inset, size[1] - 1 - inset], radius=radius, fill=255)
    return m


def make_background():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    t = 0.72 * y + 0.28 * x
    c0 = np.array([6, 16, 38], dtype=np.float32)
    c1 = np.array([8, 44, 74], dtype=np.float32)
    c2 = np.array([10, 72, 96], dtype=np.float32)
    col = c0 * (1 - t)[..., None] + c1 * t[..., None]
    # diagonal teal sweep
    sweep = np.clip(1 - np.abs((x + y * 0.8) - 1.0) / 0.7, 0, 1) ** 2
    col = col * (1 - 0.35 * sweep[..., None]) + c2 * (0.35 * sweep[..., None])
    # central glow
    cx, cy = 0.56, 0.46
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    glow = np.clip(1 - r / 0.75, 0, 1) ** 2.2
    col += np.array([0, 90, 120], dtype=np.float32) * (0.22 * glow[..., None])
    # vignette
    vx = (x - 0.5) * 1.25
    vy = (y - 0.5) * 1.25
    vig = np.clip(1 - (vx * vx + vy * vy), 0, 1) ** 0.55
    col *= (0.72 + 0.28 * vig[..., None])
    col = np.clip(col, 0, 255).astype(np.uint8)
    return Image.fromarray(col, 'RGB').convert('RGBA')


def bezier_cubic(p0, p1, p2, p3, n=200):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0]
        y = u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]
        pts.append((x, y))
    return pts


def polyline(draw, pts, fill, width):
    if len(pts) < 2:
        return
    w = int(width)
    draw.line(pts, fill=fill, width=w, joint='curve')
    r = w / 2
    for p in (pts[0], pts[-1]):
        draw.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], fill=fill)


def draw_glow_line(base, pts, color, width, blur, alpha):
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    polyline(d, pts, (*color, alpha), width)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def draw_profile(base):
    # main longitudinal/profile path
    p0 = (sc(70), sc(640))
    p1 = (sc(280), sc(760))
    p2 = (sc(420), sc(700))
    p3 = (sc(560), sc(500))
    p4 = (sc(690), sc(360))
    p5 = (sc(820), sc(430))
    p6 = (sc(960), sc(470))
    pts = bezier_cubic(p0, p1, p2, p3, 120)[:-1] + bezier_cubic(p3, p4, p5, p6, 140)

    # outer glow
    draw_glow_line(base, pts, (0, 220, 255), sc(54), sc(22), 70)
    draw_glow_line(base, pts, (60, 255, 230), sc(26), sc(10), 90)

    # pipe body (dark metallic)
    pipe = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(pipe)
    polyline(d, pts, (30, 70, 95, 255), sc(44))
    polyline(d, pts, (70, 120, 150, 220), sc(34))
    polyline(d, pts, (140, 210, 235, 120), sc(16))
    pipe = pipe.filter(ImageFilter.GaussianBlur(sc(0.6)))
    base.alpha_composite(pipe)

    # inner hydraulic wave (Saint-Venant feel)
    wave_pts = []
    for i, (x, y) in enumerate(pts):
        tt = i / max(1, len(pts)-1)
        off = math.sin(tt * math.pi * 5.2 - 0.8) * sc(7) + math.sin(tt * math.pi * 11 + 1.4) * sc(2.5)
        wave_pts.append((x, y + off - sc(2)))
    draw_glow_line(base, wave_pts, (120, 255, 245), sc(10), sc(5), 110)
    d2 = ImageDraw.Draw(base)
    polyline(d2, wave_pts, (210, 255, 255, 230), sc(4))

    # high point marker for vent
    high = pts[int(len(pts)*0.58)]
    low = pts[int(len(pts)*0.28)]
    return pts, high, low


def draw_vent_and_bubble(base, high_pt):
    hx, hy = high_pt
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # vent stem
    stem_w = sc(10)
    stem_h = sc(46)
    x0 = hx - stem_w/2
    y0 = hy - sc(30) - stem_h
    d.rounded_rectangle([x0, y0 + sc(10), x0 + stem_w, hy - sc(18)], radius=sc(4), fill=(170, 220, 235, 230))
    d.rounded_rectangle([hx - sc(22), y0 + sc(4), hx + sc(22), y0 + sc(18)], radius=sc(6), fill=(120, 200, 225, 235))
    # cap
    d.ellipse([hx - sc(9), y0 - sc(2), hx + sc(9), y0 + sc(16)], fill=(210, 245, 255, 240))
    base.alpha_composite(layer)

    # rising air bubbles
    bubbles = [(hx + sc(6), y0 - sc(28), sc(26)), (hx + sc(34), y0 - sc(78), sc(17)), (hx + sc(14), y0 - sc(118), sc(10))]
    for bx, by, br in bubbles:
        b = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(b)
        bd.ellipse([bx-br, by-br, bx+br, by+br], fill=(120, 235, 255, 55), outline=(210, 255, 255, 180), width=sc(3))
        # highlight
        hr = br*0.32
        bd.ellipse([bx-br*0.35-hr, by-br*0.45-hr, bx-br*0.35+hr, by-br*0.45+hr], fill=(255,255,255,210))
        b = b.filter(ImageFilter.GaussianBlur(sc(0.4)))
        base.alpha_composite(b)


def draw_drain_marker(base, low_pt):
    lx, ly = low_pt
    m = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(m)
    # small drain outlet below low point
    d.rounded_rectangle([lx - sc(10), ly + sc(18), lx + sc(10), ly + sc(54)], radius=sc(4), fill=(150, 205, 225, 220))
    d.polygon([(lx - sc(16), ly + sc(52)), (lx + sc(16), ly + sc(52)), (lx, ly + sc(78))], fill=(90, 210, 230, 200))
    base.alpha_composite(m)


def droplet_path(cx, cy, w, h, n=240):
    pts = []
    for i in range(n):
        t = (i / n) * math.pi * 2
        # parametric teardrop: circle bottom + pointed top
        # use superformula-like blend
        ang = t
        x = math.sin(ang)
        y = math.cos(ang)
        # taper top (ang around pi -> top in this coords? adjust)
        # We'll build in local coords where top is -y
        # easier: standard droplet param
        pass
    # easier explicit: top point and circular bottom using two beziers per side
    top = (cx, cy - h*0.62)
    left = (cx - w*0.5, cy + h*0.08)
    right = (cx + w*0.5, cy + h*0.08)
    bottom = (cx, cy + h*0.52)
    pts = []
    pts += bezier_cubic(top, (cx - w*0.18, cy - h*0.58), (cx - w*0.55, cy - h*0.18), left, 80)[:-1]
    pts += bezier_cubic(left, (cx - w*0.56, cy + h*0.42), (cx - w*0.20, cy + h*0.54), bottom, 80)[:-1]
    pts += bezier_cubic(bottom, (cx + w*0.20, cy + h*0.54), (cx + w*0.56, cy + h*0.42), right, 80)[:-1]
    pts += bezier_cubic(right, (cx + w*0.55, cy - h*0.18), (cx + w*0.18, cy - h*0.58), top, 80)
    return pts


def draw_droplet(base):
    cx, cy = sc(585), sc(585)
    w, h = sc(250), sc(330)
    pts = droplet_path(cx, cy, w, h)

    # shadow
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    spts = [(x + sc(10), y + sc(18)) for (x, y) in pts]
    sd.polygon(spts, fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(sc(18)))
    base.alpha_composite(sh)

    # droplet body with gradient fill via mask
    mask = Image.new('L', (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.polygon(pts, fill=255)

    # gradient layer
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    # localize gradient around droplet
    t = np.clip((yy - (cy / H - 0.18)) / 0.38, 0, 1) + 0 * xx
    topc = np.array([40, 220, 255], dtype=np.float32)
    midc = np.array([0, 150, 210], dtype=np.float32)
    botc = np.array([0, 95, 150], dtype=np.float32)
    col = np.where(
        t[..., None] < 0.5,
        topc * (1 - t * 2)[..., None] + midc * (t * 2)[..., None],
        midc * (1 - (t - 0.5) * 2)[..., None] + botc * ((t - 0.5) * 2)[..., None],
    )
    # internal highlight
    rx = (xx - (cx / W - 0.03)) / 0.10
    ry = (yy - (cy / H - 0.10)) / 0.14
    hl = np.clip(1 - (rx * rx + ry * ry), 0, 1) ** 1.7
    col = col + np.array([120, 230, 255], dtype=np.float32) * (0.35 * hl[..., None])
    col = np.clip(col, 0, 255).astype(np.uint8)
    alpha = np.full((H, W), 235, dtype=np.uint8)
    grad = Image.fromarray(np.dstack([col, alpha]), 'RGBA')

    body = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    body.paste(grad, (0,0), mask)
    base.alpha_composite(body)

    # rim highlight and outline
    rim = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.line(pts, fill=(230, 255, 255, 200), width=sc(4), joint='curve')
    rd.line(pts, fill=(255, 255, 255, 90), width=sc(8), joint='curve')
    rim = rim.filter(ImageFilter.GaussianBlur(sc(1.2)))
    base.alpha_composite(rim)

    # specular shine
    shine = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sdd = ImageDraw.Draw(shine)
    sdd.ellipse([cx - sc(55), cy - sc(115), cx - sc(5), cy - sc(35)], fill=(255,255,255,210))
    sdd.ellipse([cx - sc(38), cy - sc(8), cx - sc(10), cy + sc(28)], fill=(255,255,255,70))
    shine = shine.filter(ImageFilter.GaussianBlur(sc(3)))
    # clip to droplet
    shine.putalpha(ImageChops.multiply(shine.split()[3], mask))
    base.alpha_composite(shine)

    # small inner wave refracted
    wave = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wave)
    wpts = []
    for i in range(60):
        tt = i/59
        x = cx - w*0.28 + tt*w*0.56
        y = cy + h*0.05 + math.sin(tt*math.pi*2.2)*sc(5)
        wpts.append((x,y))
    wd.line(wpts, fill=(220,255,255,120), width=sc(3), joint='curve')
    wave.putalpha(ImageChops.multiply(wave.split()[3], mask))
    base.alpha_composite(wave)


def add_top_highlight(base):
    # subtle top-left gloss on tile
    hl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(hl)
    d.ellipse([-sc(120), -sc(220), sc(700), sc(420)], fill=(255,255,255,26))
    hl = hl.filter(ImageFilter.GaussianBlur(sc(60)))
    base.alpha_composite(hl)


def main():
    out_png = r'D:\MK_PROJETS\MK-St_Venant\assets\mk-st-venant-icon.png'
    out_ico = r'D:\MK_PROJETS\MK-St_Venant\assets\mk-st-venant-icon.ico'
    os.makedirs(os.path.dirname(out_png), exist_ok=True)

    img = make_background()
    add_top_highlight(img)
    pts, high, low = draw_profile(img)
    draw_drain_marker(img, low)
    draw_vent_and_bubble(img, high)
    draw_droplet(img)

    # rounded corners mask with slight inset antialias
    mask = rounded_rect_mask((W, H), radius=sc(228))
    final = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    final.paste(img, (0, 0), mask)

    # subtle border
    border = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle([sc(6), sc(6), W-1-sc(6), H-1-sc(6)], radius=sc(222), outline=(180, 240, 255, 40), width=sc(4))
    final.alpha_composite(border)

    icon = final.resize((S, S), Image.LANCZOS)
    icon.save(out_png, 'PNG')

    # ICO sizes
    sizes = [(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]
    icon.save(out_ico, format='ICO', sizes=sizes)

    # also export smaller preview set? 512
    icon.resize((512,512), Image.LANCZOS).save(out_png.replace('.png','-512.png'), 'PNG')
    print('OK', out_png)

if __name__ == '__main__':
    main()
