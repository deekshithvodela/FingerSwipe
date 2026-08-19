import os
import io
import cairosvg
from PIL import Image, ImageDraw, ImageFont

SVG_PATH = "web/assets/logo.svg"

# Palette: Pine & Mint & Pine Obsidian
# Canvas: #0b1617 (11, 22, 23) -> #152d30 (21, 45, 48)
# Accents: #51ba9a (81, 186, 154), #3ea183 (62, 161, 131), #176966 (23, 105, 102)
# Text: #f0fdf9 (240, 253, 249), #cbdad5 (203, 218, 213), #7f9f97 (127, 159, 151)

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

# =========================================================================
# 1. 1200x630 Wide OpenGraph Banner (Rendered at 2400x1260 for Crisp 2x HiDPI)
# =========================================================================
SCALE = 2
W_WIDE = 1200 * SCALE
H_WIDE = 630 * SCALE

base_wide = Image.new("RGBA", (W_WIDE, H_WIDE), (11, 22, 23, 255))
draw_base_wide = ImageDraw.Draw(base_wide)

# Smooth vertical Pine Obsidian gradient
for y in range(H_WIDE):
    factor = y / H_WIDE
    r = int(11 + 10 * factor)
    g = int(22 + 23 * factor)
    b = int(23 + 25 * factor)
    draw_base_wide.line([(0, y), (W_WIDE, y)], fill=(r, g, b, 255))

# Soft luminous radial Mint Jade glow behind logo
glow_layer_wide = Image.new("RGBA", (W_WIDE, H_WIDE), (0, 0, 0, 0))
draw_glow_wide = ImageDraw.Draw(glow_layer_wide)
glow_cx, glow_cy = 270 * SCALE, 315 * SCALE
for radius in range(240 * SCALE, 0, -4):
    alpha = int(48 * (1 - (radius / (240 * SCALE))**2))
    draw_glow_wide.ellipse(
        [glow_cx - radius, glow_cy - radius, glow_cx + radius, glow_cy + radius],
        fill=(81, 186, 154, alpha)
    )

comp_wide = Image.alpha_composite(base_wide, glow_layer_wide)
draw_wide = ImageDraw.Draw(comp_wide)

# Outer and Inner Glass Borders
draw_wide.rounded_rectangle(
    [36 * SCALE, 36 * SCALE, W_WIDE - 36 * SCALE, H_WIDE - 36 * SCALE],
    radius=24 * SCALE,
    outline=(81, 186, 154, 60),
    width=2 * SCALE
)

# Rasterize actual logo.svg at 2x resolution
logo_size_wide = 290 * SCALE
png_bytes_wide = cairosvg.svg2png(url=SVG_PATH, output_width=logo_size_wide, output_height=logo_size_wide)
logo_img_wide = Image.open(io.BytesIO(png_bytes_wide)).convert("RGBA")
comp_wide.paste(logo_img_wide, (120 * SCALE, 170 * SCALE), logo_img_wide)

# Typography
draw_wide = ImageDraw.Draw(comp_wide)
font_pill_wide = find_font(bold=True, size=15 * SCALE)
font_title_wide = find_font(bold=True, size=54 * SCALE)
font_sub_wide = find_font(bold=False, size=24 * SCALE)
font_badge_wide = find_font(bold=True, size=16 * SCALE)
font_author_wide = find_font(bold=False, size=18 * SCALE)

# Version Pill Tag
pill_text = "v1.1.0 RELEASE"
p_bbox = draw_wide.textbbox((0, 0), pill_text, font=font_pill_wide)
p_w = p_bbox[2] - p_bbox[0]
p_x1, p_y1 = 440 * SCALE, 135 * SCALE
p_x2, p_y2 = p_x1 + p_w + 32 * SCALE, p_y1 + 34 * SCALE
draw_wide.rounded_rectangle([p_x1, p_y1, p_x2, p_y2], radius=17 * SCALE, fill=(23, 105, 102, 230), outline=(81, 186, 154, 220), width=2 * SCALE)
draw_wide.text((p_x1 + 16 * SCALE, p_y1 + 7 * SCALE), pill_text, fill=(240, 253, 249, 255), font=font_pill_wide)

# Title
draw_wide.text((440 * SCALE, 185 * SCALE), "FingerSwipe", fill=(240, 253, 249, 255), font=font_title_wide)

# Subtitle
draw_wide.text(
    (440 * SCALE, 275 * SCALE),
    "Fluid Touchpad Gestures for Linux\nVolume & Display Brightness Daemon",
    fill=(203, 218, 213, 255),
    font=font_sub_wide,
    spacing=10 * SCALE
)

# Badges
badges = ["PipeWire 0.3", "C23 Native ABI", "Zero Root", "KDE OSD"]
bx = 440 * SCALE
by = 385 * SCALE
for b in badges:
    bbox = draw_wide.textbbox((0, 0), b, font=font_badge_wide)
    bw = bbox[2] - bbox[0] + 28 * SCALE
    draw_wide.rounded_rectangle([bx, by, bx + bw, by + 36 * SCALE], radius=8 * SCALE, fill=(21, 45, 48, 240), outline=(81, 186, 154, 75), width=int(1.5 * SCALE))
    draw_wide.text((bx + 14 * SCALE, by + 8 * SCALE), b, fill=(240, 253, 249, 255), font=font_badge_wide)
    bx += bw + 12 * SCALE

# Author Line
draw_wide.text((440 * SCALE, 465 * SCALE), "by Deekshith Vodela  •  MIT License", fill=(127, 159, 151, 255), font=font_author_wide)

# Downscale to exact 1200x630 with high-quality Lanczos antialiasing
final_wide = comp_wide.resize((1200, 630), Image.Resampling.LANCZOS).convert("RGB")
os.makedirs("web/assets", exist_ok=True)
final_wide.save("web/assets/og-image.png", "PNG", optimize=True)
print(f"Saved Pine & Mint web/assets/og-image.png (1200x630, {os.path.getsize('web/assets/og-image.png') // 1024} KB)")


# =========================================================================
# 2. 800x800 Square Social Card (Rendered at 1600x1600 for Crisp 2x HiDPI)
# =========================================================================
W_SQ = 800 * SCALE
H_SQ = 800 * SCALE

base_sq = Image.new("RGBA", (W_SQ, H_SQ), (11, 22, 23, 255))
draw_base_sq = ImageDraw.Draw(base_sq)

# Pine Obsidian Gradient
for y in range(H_SQ):
    factor = y / H_SQ
    r = int(11 + 10 * factor)
    g = int(22 + 23 * factor)
    b = int(23 + 25 * factor)
    draw_base_sq.line([(0, y), (W_SQ, y)], fill=(r, g, b, 255))

# Soft Center Glow
glow_layer_sq = Image.new("RGBA", (W_SQ, H_SQ), (0, 0, 0, 0))
draw_glow_sq = ImageDraw.Draw(glow_layer_sq)
glow_cx_sq, glow_cy_sq = 400 * SCALE, 260 * SCALE
for radius in range(270 * SCALE, 0, -4):
    alpha = int(52 * (1 - (radius / (270 * SCALE))**2))
    draw_glow_sq.ellipse(
        [glow_cx_sq - radius, glow_cy_sq - radius, glow_cx_sq + radius, glow_cy_sq + radius],
        fill=(81, 186, 154, alpha)
    )

comp_sq = Image.alpha_composite(base_sq, glow_layer_sq)
draw_sq = ImageDraw.Draw(comp_sq)

# Inner Glass Border
draw_sq.rounded_rectangle(
    [30 * SCALE, 30 * SCALE, W_SQ - 30 * SCALE, H_SQ - 30 * SCALE],
    radius=24 * SCALE,
    outline=(81, 186, 154, 60),
    width=2 * SCALE
)

# Rasterize Logo at 2x
logo_size_sq = 290 * SCALE
png_bytes_sq = cairosvg.svg2png(url=SVG_PATH, output_width=logo_size_sq, output_height=logo_size_sq)
logo_img_sq = Image.open(io.BytesIO(png_bytes_sq)).convert("RGBA")
comp_sq.paste(logo_img_sq, ((W_SQ - logo_size_sq) // 2, 110 * SCALE), logo_img_sq)

# Typography for Square Card
draw_sq = ImageDraw.Draw(comp_sq)
font_pill_sq = find_font(bold=True, size=15 * SCALE)
font_title_sq = find_font(bold=True, size=52 * SCALE)
font_sub_sq = find_font(bold=False, size=23 * SCALE)
font_badge_sq = find_font(bold=True, size=16 * SCALE)
font_author_sq = find_font(bold=False, size=18 * SCALE)

# Pill Tag (Centered)
pill_text_sq = "v1.1.0 RELEASE"
p_bbox_sq = draw_sq.textbbox((0, 0), pill_text_sq, font=font_pill_sq)
pw_sq = p_bbox_sq[2] - p_bbox_sq[0]
px1_sq = (W_SQ - (pw_sq + 32 * SCALE)) // 2
py1_sq = 435 * SCALE
draw_sq.rounded_rectangle(
    [px1_sq, py1_sq, px1_sq + pw_sq + 32 * SCALE, py1_sq + 34 * SCALE],
    radius=17 * SCALE,
    fill=(23, 105, 102, 230),
    outline=(81, 186, 154, 220),
    width=2 * SCALE
)
draw_sq.text((px1_sq + 16 * SCALE, py1_sq + 7 * SCALE), pill_text_sq, fill=(240, 253, 249, 255), font=font_pill_sq)

# Title (Centered)
title_text = "FingerSwipe"
t_bbox = draw_sq.textbbox((0, 0), title_text, font=font_title_sq)
t_w = t_bbox[2] - t_bbox[0]
draw_sq.text(((W_SQ - t_w) // 2, 495 * SCALE), title_text, fill=(240, 253, 249, 255), font=font_title_sq)

# Subtitle (Centered)
sub_text = "Linux 3-Finger Gesture Daemon"
s_bbox = draw_sq.textbbox((0, 0), sub_text, font=font_sub_sq)
s_w = s_bbox[2] - s_bbox[0]
draw_sq.text(((W_SQ - s_w) // 2, 575 * SCALE), sub_text, fill=(203, 218, 213, 255), font=font_sub_sq)

# Badges (Centered)
sq_badges = "PipeWire 0.3  •  C23 ABI  •  Zero Root"
b_bbox = draw_sq.textbbox((0, 0), sq_badges, font=font_badge_sq)
b_w = b_bbox[2] - b_bbox[0]
draw_sq.text(((W_SQ - b_w) // 2, 635 * SCALE), sq_badges, fill=(240, 253, 249, 255), font=font_badge_sq)

# Author (Centered)
auth_text = "by Deekshith Vodela  •  MIT License"
a_bbox = draw_sq.textbbox((0, 0), auth_text, font=font_author_sq)
a_w = a_bbox[2] - a_bbox[0]
draw_sq.text(((W_SQ - a_w) // 2, 700 * SCALE), auth_text, fill=(127, 159, 151, 255), font=font_author_sq)

# Downscale to exact 800x800 with high-quality Lanczos antialiasing
final_sq = comp_sq.resize((800, 800), Image.Resampling.LANCZOS).convert("RGB")
final_sq.save("web/assets/og-image-square.png", "PNG", optimize=True)
print(f"Saved Pine & Mint web/assets/og-image-square.png (800x800, {os.path.getsize('web/assets/og-image-square.png') // 1024} KB)")
