import os
import io
import cairosvg
from PIL import Image, ImageDraw, ImageFont

def find_font(bold=False, size=32):
    candidates_bold = [
        "/usr/share/fonts/truetype/quicksand/Quicksand-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    candidates_regular = [
        "/usr/share/fonts/truetype/quicksand/Quicksand-Medium.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    candidates = candidates_bold if bold else candidates_regular
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

THEMES = {
    "pine": {
        "svg": "web/assets/logo.svg",
        "bg_top": (11, 22, 23),
        "bg_bottom": (21, 45, 48),
        "glow_color": (81, 186, 154),
        "border_color": (81, 186, 154, 60),
        "pill_fill": (23, 105, 102, 230),
        "pill_border": (81, 186, 154, 220),
        "pill_text": (240, 253, 249, 255),
        "title_text": (240, 253, 249, 255),
        "sub_text": (203, 218, 213, 255),
        "badge_fill": (21, 45, 48, 240),
        "badge_border": (81, 186, 154, 75),
        "badge_text": (240, 253, 249, 255),
        "author_text": (127, 159, 151, 255),
        "out_wide": "web/assets/og-image.png",
        "out_sq": "web/assets/og-image-square.png",
    },
    "ocean": {
        "svg": "web/assets/logo-ocean.svg",
        "bg_top": (8, 16, 24),
        "bg_bottom": (16, 33, 51),
        "glow_color": (56, 189, 248),
        "border_color": (56, 189, 248, 60),
        "pill_fill": (2, 132, 199, 230),
        "pill_border": (56, 189, 248, 220),
        "pill_text": (240, 249, 255, 255),
        "title_text": (240, 249, 255, 255),
        "sub_text": (186, 230, 253, 255),
        "badge_fill": (16, 33, 51, 240),
        "badge_border": (56, 189, 248, 75),
        "badge_text": (240, 249, 255, 255),
        "author_text": (112, 164, 196, 255),
        "out_wide": "web/assets/og-image-ocean.png",
        "out_sq": "web/assets/og-image-ocean-square.png",
    },
    "burgundy": {
        "svg": "web/assets/logo-burgundy.svg",
        "bg_top": (20, 2, 5),
        "bg_bottom": (40, 5, 12),
        "glow_color": (224, 122, 143),
        "border_color": (224, 122, 143, 60),
        "pill_fill": (120, 16, 40, 230),
        "pill_border": (224, 122, 143, 220),
        "pill_text": (253, 242, 244, 255),
        "title_text": (253, 242, 244, 255),
        "sub_text": (226, 189, 197, 255),
        "badge_fill": (40, 5, 12, 240),
        "badge_border": (224, 122, 143, 75),
        "badge_text": (253, 242, 244, 255),
        "author_text": (168, 125, 134, 255),
        "out_wide": "web/assets/og-image-burgundy.png",
        "out_sq": "web/assets/og-image-burgundy-square.png",
    },
}

SCALE = 2

def render_wide(theme_cfg):
    W = 1200 * SCALE
    H = 630 * SCALE

    base = Image.new("RGBA", (W, H), (*theme_cfg["bg_top"], 255))
    draw_base = ImageDraw.Draw(base)

    r1, g1, b1 = theme_cfg["bg_top"]
    r2, g2, b2 = theme_cfg["bg_bottom"]
    for y in range(H):
        f = y / H
        r = int(r1 + (r2 - r1) * f)
        g = int(g1 + (g2 - g1) * f)
        b = int(b1 + (b2 - b1) * f)
        draw_base.line([(0, y), (W, y)], fill=(r, g, b, 255))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    gcx, gcy = 270 * SCALE, 315 * SCALE
    gr, gg, gb = theme_cfg["glow_color"]
    for radius in range(240 * SCALE, 0, -4):
        alpha = int(48 * (1 - (radius / (240 * SCALE))**2))
        draw_glow.ellipse([gcx - radius, gcy - radius, gcx + radius, gcy + radius], fill=(gr, gg, gb, alpha))

    comp = Image.alpha_composite(base, glow)
    draw = ImageDraw.Draw(comp)

    draw.rounded_rectangle(
        [36 * SCALE, 36 * SCALE, W - 36 * SCALE, H - 36 * SCALE],
        radius=24 * SCALE,
        outline=theme_cfg["border_color"],
        width=2 * SCALE
    )

    logo_size = 290 * SCALE
    png_bytes = cairosvg.svg2png(url=theme_cfg["svg"], output_width=logo_size, output_height=logo_size)
    logo_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    comp.paste(logo_img, (120 * SCALE, 170 * SCALE), logo_img)

    draw = ImageDraw.Draw(comp)
    font_pill = find_font(bold=True, size=15 * SCALE)
    font_title = find_font(bold=True, size=54 * SCALE)
    font_sub = find_font(bold=False, size=24 * SCALE)
    font_badge = find_font(bold=True, size=16 * SCALE)
    font_author = find_font(bold=False, size=18 * SCALE)

    pill_text = "v1.1.0 RELEASE"
    p_bbox = draw.textbbox((0, 0), pill_text, font=font_pill)
    pw = p_bbox[2] - p_bbox[0]
    px1, py1 = 440 * SCALE, 135 * SCALE
    px2, py2 = px1 + pw + 32 * SCALE, py1 + 34 * SCALE
    draw.rounded_rectangle([px1, py1, px2, py2], radius=17 * SCALE, fill=theme_cfg["pill_fill"], outline=theme_cfg["pill_border"], width=2 * SCALE)
    draw.text((px1 + 16 * SCALE, py1 + 7 * SCALE), pill_text, fill=theme_cfg["pill_text"], font=font_pill)

    draw.text((440 * SCALE, 185 * SCALE), "FingerSwipe", fill=theme_cfg["title_text"], font=font_title)
    draw.text(
        (440 * SCALE, 275 * SCALE),
        "Fluid Touchpad Gestures for Linux\nVolume & Display Brightness Daemon",
        fill=theme_cfg["sub_text"],
        font=font_sub,
        spacing=10 * SCALE
    )

    badges = ["PipeWire 0.3", "C23 Native ABI", "Zero Root", "KDE OSD"]
    bx = 440 * SCALE
    by = 385 * SCALE
    for b in badges:
        bbox = draw.textbbox((0, 0), b, font=font_badge)
        bw = bbox[2] - bbox[0] + 28 * SCALE
        draw.rounded_rectangle([bx, by, bx + bw, by + 36 * SCALE], radius=8 * SCALE, fill=theme_cfg["badge_fill"], outline=theme_cfg["badge_border"], width=int(1.5 * SCALE))
        draw.text((bx + 14 * SCALE, by + 8 * SCALE), b, fill=theme_cfg["badge_text"], font=font_badge)
        bx += bw + 12 * SCALE

    draw.text((440 * SCALE, 465 * SCALE), "by Deekshith Vodela  •  MIT License", fill=theme_cfg["author_text"], font=font_author)

    final = comp.resize((1200, 630), Image.Resampling.LANCZOS).convert("RGB")
    final.save(theme_cfg["out_wide"], "PNG", optimize=True)
    print(f"Saved {theme_cfg['out_wide']} (1200x630, {os.path.getsize(theme_cfg['out_wide']) // 1024} KB)")

def render_square(theme_cfg):
    W = 800 * SCALE
    H = 800 * SCALE

    base = Image.new("RGBA", (W, H), (*theme_cfg["bg_top"], 255))
    draw_base = ImageDraw.Draw(base)

    r1, g1, b1 = theme_cfg["bg_top"]
    r2, g2, b2 = theme_cfg["bg_bottom"]
    for y in range(H):
        f = y / H
        r = int(r1 + (r2 - r1) * f)
        g = int(g1 + (g2 - g1) * f)
        b = int(b1 + (b2 - b1) * f)
        draw_base.line([(0, y), (W, y)], fill=(r, g, b, 255))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    gcx, gcy = 400 * SCALE, 260 * SCALE
    gr, gg, gb = theme_cfg["glow_color"]
    for radius in range(270 * SCALE, 0, -4):
        alpha = int(52 * (1 - (radius / (270 * SCALE))**2))
        draw_glow.ellipse([gcx - radius, gcy - radius, gcx + radius, gcy + radius], fill=(gr, gg, gb, alpha))

    comp = Image.alpha_composite(base, glow)
    draw = ImageDraw.Draw(comp)

    draw.rounded_rectangle(
        [30 * SCALE, 30 * SCALE, W - 30 * SCALE, H - 30 * SCALE],
        radius=24 * SCALE,
        outline=theme_cfg["border_color"],
        width=2 * SCALE
    )

    logo_size = 290 * SCALE
    png_bytes = cairosvg.svg2png(url=theme_cfg["svg"], output_width=logo_size, output_height=logo_size)
    logo_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    comp.paste(logo_img, ((W - logo_size) // 2, 110 * SCALE), logo_img)

    draw = ImageDraw.Draw(comp)
    font_pill = find_font(bold=True, size=15 * SCALE)
    font_title = find_font(bold=True, size=52 * SCALE)
    font_sub = find_font(bold=False, size=23 * SCALE)
    font_badge = find_font(bold=True, size=16 * SCALE)
    font_author = find_font(bold=False, size=18 * SCALE)

    pill_text = "v1.1.0 RELEASE"
    p_bbox = draw.textbbox((0, 0), pill_text, font=font_pill)
    pw = p_bbox[2] - p_bbox[0]
    px1 = (W - (pw + 32 * SCALE)) // 2
    py1 = 435 * SCALE
    draw.rounded_rectangle([px1, py1, px1 + pw + 32 * SCALE, py1 + 34 * SCALE], radius=17 * SCALE, fill=theme_cfg["pill_fill"], outline=theme_cfg["pill_border"], width=2 * SCALE)
    draw.text((px1 + 16 * SCALE, py1 + 7 * SCALE), pill_text, fill=theme_cfg["pill_text"], font=font_pill)

    title_text = "FingerSwipe"
    t_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    draw.text(((W - (t_bbox[2] - t_bbox[0])) // 2, 495 * SCALE), title_text, fill=theme_cfg["title_text"], font=font_title)

    sub_text = "Linux 3-Finger Gesture Daemon"
    s_bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    draw.text(((W - (s_bbox[2] - s_bbox[0])) // 2, 575 * SCALE), sub_text, fill=theme_cfg["sub_text"], font=font_sub)

    sq_badges = "PipeWire 0.3  •  C23 ABI  •  Zero Root"
    b_bbox = draw.textbbox((0, 0), sq_badges, font=font_badge)
    draw.text(((W - (b_bbox[2] - b_bbox[0])) // 2, 635 * SCALE), sq_badges, fill=theme_cfg["badge_text"], font=font_badge)

    auth_text = "by Deekshith Vodela  •  MIT License"
    a_bbox = draw.textbbox((0, 0), auth_text, font=font_author)
    draw.text(((W - (a_bbox[2] - a_bbox[0])) // 2, 700 * SCALE), auth_text, fill=theme_cfg["author_text"], font=font_author)

    final = comp.resize((800, 800), Image.Resampling.LANCZOS).convert("RGB")
    final.save(theme_cfg["out_sq"], "PNG", optimize=True)
    print(f"Saved {theme_cfg['out_sq']} (800x800, {os.path.getsize(theme_cfg['out_sq']) // 1024} KB)")

if __name__ == "__main__":
    os.makedirs("web/assets", exist_ok=True)
    for theme_name, cfg in THEMES.items():
        print(f"Generating OpenGraph images for {theme_name.upper()}...")
        render_wide(cfg)
        render_square(cfg)
