"""Draw fictional specimen documents for the demo dataset (marksheet, ID card, category certificate).

Every page carries a large "SPECIMEN - FICTIONAL" watermark and names only made-up issuing
offices, so the files look like the real thing in a demo but can never pass as genuine.
Pillow draws the page and saves it as a one-page PDF.
"""
import functools
import random
from io import BytesIO

from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 1190, 1684  # A4 at 144 dpi
INK = (24, 32, 48)
MUTED = (96, 108, 128)
NAVY = (18, 44, 92)
SAFFRON = (214, 120, 24)
LINE = (190, 198, 210)
SUBJECTS = ("English", "Kannada", "Physics", "Chemistry", "Mathematics", "Computer Science")


@functools.lru_cache(maxsize=32)
def _font(size, bold=False):
    for name in (("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
                 ("arialbd.ttf" if bold else "arial.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _page(title, subtitle):
    image = Image.new("RGB", (WIDTH, HEIGHT), (252, 251, 247))
    draw = ImageDraw.Draw(image)
    draw.rectangle([40, 40, WIDTH - 40, HEIGHT - 40], outline=NAVY, width=4)
    draw.rectangle([56, 56, WIDTH - 56, HEIGHT - 56], outline=LINE, width=2)
    draw.rectangle([56, 56, WIDTH - 56, 210], fill=NAVY)
    draw.rectangle([56, 210, WIDTH - 56, 220], fill=SAFFRON)
    draw.ellipse([90, 82, 190, 182], outline=(255, 255, 255), width=4)
    draw.text((140, 132), "D", font=_font(56, True), fill=(255, 255, 255), anchor="mm")
    draw.text((220, 92), title, font=_font(38, True), fill=(255, 255, 255))
    draw.text((220, 146), subtitle, font=_font(24), fill=(214, 224, 244))
    return image, draw


def _row(draw, y, label, value, x=110):
    draw.text((x, y), label, font=_font(24), fill=MUTED)
    draw.text((x + 330, y), str(value), font=_font(27, True), fill=INK)


@functools.lru_cache(maxsize=1)
def _watermark_layer():
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    text = Image.new("RGBA", (1500, 140), (0, 0, 0, 0))
    ImageDraw.Draw(text).text((750, 70), "SPECIMEN · FICTIONAL", font=_font(108, True),
                              fill=(194, 36, 36, 70), anchor="mm")
    text = text.rotate(52, expand=True)
    layer.paste(text, ((WIDTH - text.width) // 2, (HEIGHT - text.height) // 2), text)
    return layer


def _watermark(image):
    return Image.alpha_composite(image.convert("RGBA"), _watermark_layer()).convert("RGB")


def _footer(draw, reference):
    draw.line([110, HEIGHT - 190, WIDTH - 110, HEIGHT - 190], fill=LINE, width=2)
    draw.text((110, HEIGHT - 170), "This is a fictional specimen made for a software-engineering demo.",
              font=_font(22), fill=MUTED)
    draw.text((110, HEIGHT - 136), "It is not issued by any real authority and has no legal value.",
              font=_font(22), fill=MUTED)
    draw.text((WIDTH - 110, HEIGHT - 136), reference, font=_font(22, True), fill=MUTED, anchor="ra")


def marksheet(info):
    image, draw = _page("Demo Pre-University Examination Board", "Statement of Marks · II PUC (Specimen)")
    _row(draw, 280, "Candidate name", info["name"])
    _row(draw, 330, "Register number", f"DPU-{info['number']:06d}")
    _row(draw, 380, "Board", info["board"])
    _row(draw, 430, "Examination", "March 2026 (fictional)")

    rng = random.Random(f"marks:{info['number']}")
    target = info["percentage"]
    marks = [max(35, min(100, round(target + rng.uniform(-8, 8)))) for _ in SUBJECTS]
    top, left, right = 520, 110, WIDTH - 110
    draw.rectangle([left, top, right, top + 56], fill=(232, 237, 246))
    for x, label in ((left + 20, "Subject"), (right - 360, "Max"), (right - 200, "Obtained")):
        draw.text((x, top + 14), label, font=_font(24, True), fill=NAVY)
    y = top + 56
    for subject, mark in zip(SUBJECTS, marks):
        draw.line([left, y, right, y], fill=LINE, width=1)
        draw.text((left + 20, y + 16), subject, font=_font(25), fill=INK)
        draw.text((right - 360, y + 16), "100", font=_font(25), fill=MUTED)
        draw.text((right - 200, y + 16), f"{mark:03d}", font=_font(25, True), fill=INK)
        y += 62
    draw.rectangle([left, top, right, y], outline=NAVY, width=2)
    total = sum(marks)
    _row(draw, y + 40, "Total", f"{total} / {100 * len(SUBJECTS)}")
    _row(draw, y + 90, "Percentage", f"{total / len(SUBJECTS):.2f}%")
    _row(draw, y + 140, "Result", "PASS · First Class" if total / len(SUBJECTS) >= 60 else "PASS")
    draw.text((WIDTH - 110, y + 280), "Controller of Examinations (fictional)", font=_font(22),
              fill=MUTED, anchor="ra")
    _footer(draw, f"DPU-{info['number']:06d}")
    return image


def id_card(info):
    image, draw = _page("Demo Identity Card Office", "Student Identity Card (Specimen)")
    card = [110, 300, WIDTH - 110, 860]
    draw.rounded_rectangle(card, radius=18, outline=NAVY, width=3, fill=(255, 255, 255))
    draw.rectangle([card[0], card[1], card[2], card[1] + 70], fill=NAVY)
    draw.text((card[0] + 30, card[1] + 18), "IDENTITY CARD · FICTIONAL", font=_font(28, True), fill=(255, 255, 255))
    photo = [card[0] + 40, card[1] + 110, card[0] + 290, card[1] + 420]
    draw.rectangle(photo, fill=(226, 232, 242), outline=LINE, width=2)
    cx = (photo[0] + photo[2]) // 2
    draw.ellipse([cx - 60, photo[1] + 50, cx + 60, photo[1] + 170], fill=(170, 182, 202))
    draw.pieslice([cx - 110, photo[1] + 190, cx + 110, photo[1] + 410], 180, 360, fill=(170, 182, 202))
    x = card[0] + 330
    for i, (label, value) in enumerate((("Name", info["name"]), ("ID number", f"DID {info['number']:04d} {info['number'] * 7919 % 10000:04d}"),
                                        ("Category", info["category"]), ("City", info["city"]), ("Valid until", "31-12-2030"))):
        draw.text((x, card[1] + 110 + i * 62), label, font=_font(22), fill=MUTED)
        draw.text((x, card[1] + 136 + i * 62), str(value), font=_font(27, True), fill=INK)
    draw.text((110, 920), "Issued for demonstration only by a fictional office.", font=_font(24), fill=MUTED)
    _footer(draw, f"DID-{info['number']:06d}")
    return image


def category_certificate(info):
    image, draw = _page("Demo Revenue Office, Karnataka (fictional)", "Caste / Category Certificate (Specimen)")
    lines = [
        "This is to certify that",
        f"{info['name']}",
        f"resident of {info['city']}, Karnataka (fictional address),",
        f"belongs to the {info['category']} category for the purpose of",
        "engineering admission counselling.",
        "",
        "This certificate is a specimen created for a classroom software",
        "project. It must not be used for any real purpose.",
    ]
    y = 320
    for index, text in enumerate(lines):
        bold = index in (1, 3)
        draw.text((WIDTH // 2, y), text, font=_font(34 if index == 1 else 27, bold), fill=INK if bold else MUTED, anchor="mm")
        y += 78 if index == 1 else 58
    _row(draw, y + 60, "Certificate number", f"DRO/{info['number']:05d}/2026")
    _row(draw, y + 110, "Date of issue", "15-04-2026 (fictional)")
    draw.text((WIDTH - 110, y + 260), "Issuing officer (fictional)", font=_font(22), fill=MUTED, anchor="ra")
    _footer(draw, f"DRO-{info['number']:05d}")
    return image


BUILDERS = {"marksheet": marksheet, "id-proof": id_card, "category-certificate": category_certificate}


def render_pdf(slug, info, blurred=False):
    """One-page PDF bytes for the document type ``slug``; blurred copies stand in for rejected scans."""
    image = _watermark(BUILDERS[slug](info))
    if blurred:
        image = image.filter(ImageFilter.GaussianBlur(5))
    output = BytesIO()
    image.save(output, "PDF", resolution=144, title=f"Fictional specimen - {slug}")
    return output.getvalue()
