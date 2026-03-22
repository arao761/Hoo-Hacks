from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

fonts = [
    '/System/Library/Fonts/Supplemental/DevanagariMT.ttc',
    '/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc',
    '/System/Library/Fonts/Supplemental/ITFDevanagari.ttc',
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
    '/System/Library/Fonts/Kohinoor.ttc',
    '/System/Library/Fonts/Supplemental/Arial.ttf',
]
text = 'क्या है JavaScript Basics — आज हम आसान तरीके से सीखेंगे।'
out_dir = Path('/tmp/fonttest')
out_dir.mkdir(parents=True, exist_ok=True)

for i, f in enumerate(fonts, 1):
    img = Image.new('RGB', (1400, 220), '#111111')
    d = ImageDraw.Draw(img)
    d.text((20, 20), Path(f).name, fill='white')
    out = out_dir / f"{i:02d}_{Path(f).name}.png"
    try:
        font = ImageFont.truetype(f, 56)
        d.text((20, 90), text, fill='white', font=font)
        print('OK', out)
    except Exception as e:
        d.text((20, 90), f'ERROR: {e}', fill='red')
        print('ERR', out, e)
    img.save(out)

print('DONE')
