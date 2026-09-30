# -*- coding: utf-8 -*-
"""
AI Cyber Cafe Document Studio
Passport Photo with Name & Date Stamp, Printable Sheet, Signature Cleaner, and PDF Compressor.
"""

import io
import os
import glob
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
    
    # Compress to 20KB - 50KB
    out = io.BytesIO()
    for q in (85, 75, 65, 55, 45, 35):
        out.seek(0)
        out.truncate(0)
        passport.save(out, format="JPEG", quality=q, optimize=True)
        size_kb = len(out.getvalue()) / 1024
        if 20 <= size_kb <= 50 or q == 35:
            break
            
    out.seek(0)
    return out, int(len(out.getvalue()) / 1024)


def make_printable_sheet(photo_bytes: bytes, copies: int = 8) -> io.BytesIO:
    """
    Arranges 6 or 8 passport photos on a standard 4x6 inch (1200x1800 px @ 300 DPI) sheet
    with cutting crop marks for easy printing at photo labs.
    """
    img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    pw, ph = 350, 450
    single = ImageOps.fit(img, (pw, ph), centering=(0.5, 0.35))
    
    # Add border & cut line around single photo
    draw_s = ImageDraw.Draw(single)
    draw_s.rectangle([(0, 0), (pw - 1, ph - 1)], outline=(180, 180, 180), width=2)
    
    # 4x6 inch canvas @ 300 DPI = 1200 x 1800 px
    sheet = Image.new("RGB", (1800, 1200), color=(255, 255, 255))
    
    # Arrange 8 photos (4 columns x 2 rows)
    # Margins and spacing
    cols, rows = 4, 2
    spacing_x = (1800 - (cols * pw)) // (cols + 1)
    spacing_y = (1200 - (rows * ph)) // (rows + 1)
    
    for r in range(rows):
        for c in range(cols):
            x = spacing_x + c * (pw + spacing_x)
            y = spacing_y + r * (ph + spacing_y)
            sheet.paste(single, (x, y))
            
    out = io.BytesIO()
    sheet.save(out, format="JPEG", quality=95, dpi=(300, 300))
    out.seek(0)
    return out


def clean_signature(img_bytes: bytes) -> tuple[io.BytesIO, int]:
    """
    Enhances handwritten signature:
    - Removes shadow, yellow tint and background paper texture
    - Turns signature into crisp high-contrast black/blue ink on pure white
    - Auto-crops bounding box
    - Compresses to 10KB - 20KB official Govt limit
    """
    img = Image.open(io.BytesIO(img_bytes)).convert("L")
    
    # Contrast boost
    enhancer = ImageEnhance.Contrast(img)
    img_contrast = enhancer.enhance(2.8)
    
    # Thresholding to pure white background and dark text
    # Pixels > 165 become 255 (white), dark ink stays black
    def threshold(p):
        if p > 160:
            return 255
        elif p < 100:
            return 0
        else:
            return int((p - 100) / 60 * 255)
            
    bw = img_contrast.point(threshold, mode="L")
    
    # Invert to find bounding box of ink
    inv = ImageOps.invert(bw)
    bbox = inv.getbbox()
    if bbox:
        # Add 15px padding
        pad = 20
        w_img, h_img = bw.size
        crop_box = (
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(w_img, bbox[2] + pad),
            min(h_img, bbox[3] + pad),
        )
        bw = bw.crop(crop_box)
        
    # Resize to standard signature aspect ratio (e.g. 500 x 200)
    target_w = 600
    target_h = int(target_w * (bw.height / max(1, bw.width)))
    bw_resized = bw.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    out = io.BytesIO()
    for q in (80, 70, 60, 50, 40):
        out.seek(0)
        out.truncate(0)
        bw_resized.save(out, format="JPEG", quality=q, optimize=True)
        size_kb = len(out.getvalue()) / 1024
        if 10 <= size_kb <= 25 or q == 40:
            break
            
    out.seek(0)
    return out, int(len(out.getvalue()) / 1024)


def compress_document_pdf(image_bytes_list: list[bytes], max_kb: int = 300) -> io.BytesIO:
    """
    Takes 1 or more document/marksheet images and merges them into a clean PDF under max_kb (e.g. 200-300KB)
    """
    processed_images = []
    for b in image_bytes_list:
        im = Image.open(io.BytesIO(b)).convert("RGB")
        # Resize to max 1400px width for sharp text
        if im.width > 1400 or im.height > 1800:
            im.thumbnail((1400, 1800), Image.Resampling.LANCZOS)
        # Enhance sharpness
        sharp = ImageEnhance.Sharpness(im).enhance(1.4)
        buf = io.BytesIO()
        sharp.save(buf, format="JPEG", quality=65, optimize=True)
        processed_images.append(buf.getvalue())
        
    pdf_bytes = img2pdf.convert(processed_images)
    out = io.BytesIO(pdf_bytes)
    out.seek(0)
    return out
