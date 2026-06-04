"""Generate Rentify favicon assets (run once: python scripts/generate_favicons.py)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent / 'static' / 'branding'
ROOT.mkdir(parents=True, exist_ok=True)

BG = (5, 5, 16)
GREEN = (0, 208, 132)
GOLD = (245, 158, 11)


def draw_icon(size):
    img = Image.new('RGBA', (size, size), BG + (255,))
    d = ImageDraw.Draw(img)
    margin = max(2, size // 8)
    d.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 5,
        fill=(16, 20, 40, 255),
        outline=(0, 208, 132, 180),
        width=max(1, size // 32),
    )
    # Letter R
    try:
        font = ImageFont.truetype('arialbd.ttf', int(size * 0.42))
    except OSError:
        font = ImageFont.load_default()
    text = 'R'
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - tw) / 2 - size * 0.04, (size - th) / 2 - size * 0.06), text, fill=GREEN, font=font)
    # Yellow dot
    dot_r = max(2, size // 14)
    cx, cy = int(size * 0.78), int(size * 0.28)
    d.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=GOLD)
    return img


def main():
    sizes = {'favicon-16x16.png': 16, 'favicon-32x32.png': 32, 'apple-touch-icon.png': 180}
    icons = []
    for name, sz in sizes.items():
        im = draw_icon(sz)
        path = ROOT / name
        im.save(path, 'PNG')
        icons.append(im)
        print('Wrote', path)
    # favicon.ico multi-size
    ico_path = ROOT / 'favicon.ico'
    icons[0].save(
        ico_path,
        format='ICO',
        sizes=[(16, 16), (32, 32)],
        append_images=[icons[1]] if len(icons) > 1 else [],
    )
    print('Wrote', ico_path)


if __name__ == '__main__':
    main()
