"""Render a PPTX to per-slide PNG previews (LibreOffice -> PDF -> pdftoppm) plus a contact sheet.
Previews are for review only; they are never inserted into decks."""
import shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image

def render(pptx, out_dir, dpi=96, sheet=True, timeout=300):
    pptx, out_dir = Path(pptx), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(pptx.stem + "-*.png"): old.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", f"-env:UserInstallation=file://{tmp}/lo", "--convert-to", "pdf",
                        "--outdir", tmp, str(pptx)], check=True, timeout=timeout, capture_output=True)
        pdf = Path(tmp) / (pptx.stem + ".pdf")
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(out_dir / pptx.stem)], check=True, timeout=timeout)
        shutil.copy(pdf, out_dir / (pptx.stem + ".pdf"))
    pngs = sorted(out_dir.glob(pptx.stem + "-*.png"))
    if sheet and pngs:
        contact_sheet(pngs, out_dir / (pptx.stem + "_contact.png"))
    return pngs

def contact_sheet(pngs, dst, cols=3, width=640, gap=12):
    ims = [Image.open(p).convert("RGB") for p in pngs]
    h = int(width * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * width + (cols + 1) * gap, rows * h + (rows + 1) * gap), (210, 214, 219))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((width, h), Image.LANCZOS), (gap + (i % cols) * (width + gap), gap + (i // cols) * (h + gap)))
    sheet.save(dst)
    return dst
