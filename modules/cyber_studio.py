# -*- coding: utf-8 -*-
"""
AI Cyber Cafe Document Studio
Passport Photo with Name & Date Stamp, Printable Sheet, Signature Cleaner, and PDF Compressor.
"""

import io
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps
import img2pdf


def _get_font(size: int = 24):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in font_paths:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def make_stamped_passport(photo_bytes: bytes, candidate_name: str, dop_date: str) -> tuple[io.BytesIO, int]:
    """
    Creates standard 3.5cm x 4.5cm Govt Exam Passport Photo with:
    - Official Bottom White Box with Black Border
    - Uppercase Candidate Name & Date of Photo (DOP)
    - Compressed to 20KB - 50KB range
    """
    img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    
    # Standard 3.5 x 4.5 ratio (700 x 900 px)
    w, h = 700, 900
    passport = ImageOps.fit(img, (w, h), centering=(0.5, 0.35))
    
    # Draw bottom white stamp box (18% of height)
    box_h = int(h * 0.18)
    draw = ImageDraw.Draw(passport)
    draw.rectangle([(0, h - box_h), (w, h)], fill=(255, 255, 255))
    draw.line([(0, h - box_h), (w, h - box_h)], fill=(0, 0, 0), width=4)
    # Outer photo border
    draw.rectangle([(0, 0), (w - 1, h - 1)], outline=(0, 0, 0), width=3)
    
    # Fonts for Name and Date
    font_name = _get_font(26)
    font_date = _get_font(22)
    
    name_str = candidate_name.strip().upper()[:28]
    date_str = f"DOP : {dop_date.strip()}"
    
    y_center = h - box_h + (box_h // 2)
    draw.text((w // 2, y_center - 16), name_str, fill=(0, 0, 0), anchor="mm", font=font_name)
    draw.text((w // 2, y_center + 18), date_str, fill=(0, 0, 0), anchor="mm", font=font_date)
    
    # Compress to 20KB - 50KB (govt portals 20KB se kam file accept nahi karte —
    # isliye quality ladder: pehle badi quality try karo, jo 20-50 window me aaye wahi lo.
    # Koi quality window me na aaye to window ke SABSE PAAS wali lo:
    #   • sab >50KB  → chhoti quality (50 ke sabse paas)
    #   • sab <20KB  → badi quality  (20 ke sabse paas)
    ladder = (95, 88, 82, 75, 68, 60, 52, 45, 38, 32)
    sizes = {}
    chosen = None
    for q in ladder:
        out = io.BytesIO()
        passport.save(out, format="JPEG", quality=q, optimize=True)
        sizes[q] = len(out.getvalue()) / 1024
        if chosen is None and 20 <= sizes[q] <= 50:
            chosen = q
    if chosen is None:
        if sizes[ladder[-1]] > 50:
            chosen = ladder[-1]   # sabse chhoti quality bhi 50KB se badi — wahi lo (paas wali)
        else:
            chosen = ladder[0]    # sabse badi quality bhi 20KB se chhoti — wahi lo (paas wali)

    out = io.BytesIO()
    passport.save(out, format="JPEG", quality=chosen, optimize=True)
    out.seek(0)
    return out, int(sizes[chosen])


def make_printable_sheet(photo_bytes: bytes, copies: int = 8) -> io.BytesIO:
    """
    v50: EXACT 3.5 × 4.5 cm passport photos on a standard 6×4 inch lab sheet
    (1800×1200 px @ 300 DPI). Per photo = 413×532 px — dukaan par bilkul
    standard passport size hi print hoga (purana 350×450 chhota padta tha).
    4 columns × 2 rows = 8 copies, soft cut lines ke saath.
    """
    img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    pw, ph = 413, 532  # 3.5×4.5 cm @ 300 DPI
    single = ImageOps.fit(img, (pw, ph), centering=(0.5, 0.35))

    # Add border & cut line around single photo
    draw_s = ImageDraw.Draw(single)
    draw_s.rectangle([(0, 0), (pw - 1, ph - 1)], outline=(150, 150, 150), width=2)

    # 6×4 inch lab canvas @ 300 DPI = 1800 x 1200 px (landscape — standard 8-up sheet)
    sheet = Image.new("RGB", (1800, 1200), color=(255, 255, 255))

    # Arrange 8 photos (4 columns x 2 rows)
    cols, rows = 4, 2
    spacing_x = (1800 - (cols * pw)) // (cols + 1)
    spacing_y = (1200 - (rows * ph)) // (rows + 1)

    for r in range(rows):
        for c in range(cols):
            x = spacing_x + c * (pw + spacing_x)
            y = spacing_y + r * (ph + spacing_y)
            sheet.paste(single, (x, y))

    # Sheet border (lab ko pata chale yahan tak print karna hai)
    dr = ImageDraw.Draw(sheet)
    dr.rectangle([(10, 10), (1789, 1189)], outline=(205, 205, 205), width=2)

    out = io.BytesIO()
    sheet.save(out, format="JPEG", quality=95, dpi=(300, 300))
    out.seek(0)
    return out


def compress_document_pdf(image_bytes_list: list[bytes], max_kb: int = 300, grayscale: bool = False) -> io.BytesIO:
    """
    Marksheet/certificate photos ko ek clean PDF me badalta hai, max_kb (100/200/300/500) se kam.
    grayscale=True → Black & White PDF (aur chhota + govt portal friendly).
    """
    processed_images = []
    for b in image_bytes_list:
        im = Image.open(io.BytesIO(b)).convert("RGB")
        if grayscale:
            im = im.convert("L").convert("RGB")   # B&W (grey) — text sharp, size kam
        if im.width > 1400 or im.height > 1800:
            im.thumbnail((1400, 1800), Image.Resampling.LANCZOS)
        sharp = ImageEnhance.Sharpness(im).enhance(1.4 if not grayscale else 1.6)
        # target size ke hisaab se quality
        q = 45 if max_kb <= 100 else (55 if max_kb <= 200 else (65 if max_kb <= 300 else 75))
        buf = io.BytesIO()
        sharp.save(buf, format="JPEG", quality=(q - 10 if grayscale else q), optimize=True)
        processed_images.append(buf.getvalue())
        
    pdf_bytes = img2pdf.convert(processed_images)
    out = io.BytesIO(pdf_bytes)
    out.seek(0)
    return out
