src = r"""import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

CLASSES = {
    "Sehat":        {"base": (80,120,60),  "red":0,"spots":0, "fuzz":0,"dark":0},
    "Aeromonas":    {"base": (90,80,50),   "red":6,"spots":15,"fuzz":0,"dark":4},
    "Bercak_Merah": {"base": (100,70,55),  "red":8,"spots":8, "fuzz":0,"dark":0},
    "Jamur":        {"base": (70,90,70),   "red":0,"spots":0, "fuzz":4,"dark":0},
    "Parasit":      {"base": (75,95,65),   "red":0,"spots":18,"fuzz":0,"dark":4},
}
IMG_SIZE = 224
SAMPLES_PER_CLASS = 200

def make_fish_mask(size):
    cx,cy = size//2, size//2
    rx,ry = int(size*0.38), int(size*0.22)
    Y,X = np.ogrid[:size,:size]
    return ((X-cx)/rx)**2 + ((Y-cy)/ry)**2 <= 1.0

def generate_fish_image(class_name, seed):
    rng = np.random.default_rng(seed)
    cfg = CLASSES[class_name]
    br,bg,bb = cfg["base"]
    S = IMG_SIZE
    img = rng.integers(20, 80, (S,S,3), dtype=np.uint8)
    img[:,:,2] = np.clip(img[:,:,2].astype(int)+30, 0, 255).astype(np.uint8)
    mask = make_fish_mask(S)
    noise = rng.integers(-15, 15, (S,S,3))
    body = np.clip(np.array([br,bg,bb], dtype=np.int16)+noise, 0, 255).astype(np.uint8)
    img[mask] = body[mask]
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    cx,cy = S//2, S//2
    rx = int(S*0.38)
    hx = cx-rx+20
    draw.ellipse([hx-30,cy-30,hx+30,cy+30], fill=(min(br+10,255),min(bg+5,255),bb))
    draw.polygon([(cx+rx-10,cy),(cx+rx+35,cy-25),(cx+rx+35,cy+25)], fill=(max(br-10,0),max(bg-10,0),max(bb-5,0)))
    draw.ellipse([hx-2,cy-14,hx+10,cy-2], fill=(10,10,10))
    for _ in range(cfg["red"]):
        px=int(rng.integers(cx-rx+20,cx+rx-20)); py=int(rng.integers(cy-20,cy+20)); pr=int(rng.integers(8,18))
        draw.ellipse([px-pr,py-pr,px+pr,py+pr], fill=(int(rng.integers(160,210)),int(rng.integers(20,45)),int(rng.integers(20,45))))
    for _ in range(cfg["spots"]):
        sx=int(rng.integers(cx-rx+10,cx+rx-10)); sy=int(rng.integers(cy-18,cy+18)); sr=int(rng.integers(3,7)); v=int(rng.integers(20,55))
        draw.ellipse([sx-sr,sy-sr,sx+sr,sy+sr], fill=(v,v,v))
    for _ in range(cfg["fuzz"]):
        fx=int(rng.integers(cx-rx+30,cx+rx-30)); fy=int(rng.integers(cy-18,cy+18))
        for _ in range(int(rng.integers(12,22))):
            ffx=fx+int(rng.integers(-22,22)); ffy=fy+int(rng.integers(-12,12)); fr=int(rng.integers(4,11)); v=int(rng.integers(180,255))
            draw.ellipse([ffx-fr,ffy-fr,ffx+fr,ffy+fr], fill=(v,v,v))
    for _ in range(cfg["dark"]):
        dpx=int(rng.integers(cx-rx+20,cx+rx-20)); dpy=int(rng.integers(cy-18,cy+18)); dpr=int(rng.integers(10,20)); v=int(rng.integers(15,40))
        draw.ellipse([dpx-dpr,dpy-dpr,dpx+dpr,dpy+dpr], fill=(v,v,v))
    pil = pil.filter(ImageFilter.GaussianBlur(radius=0.6))
    if rng.random() > 0.5:
        pil = pil.transpose(Image.FLIP_LEFT_RIGHT)
    pil = pil.rotate(float(rng.uniform(-12,12)), fillcolor=(30,50,70))
    return pil

def generate_dataset(output_dir, samples_per_class=SAMPLES_PER_CLASS):
    p = Path(output_dir)
    total = 0
    print(f"Generating synthetic dataset -> {p}")
    for cls in CLASSES:
        d = p/cls
        d.mkdir(parents=True, exist_ok=True)
        ex = list(d.glob("*.jpg"))
        if len(ex) >= samples_per_class:
            print(f"  {cls}: {len(ex)} already exist.")
            total += len(ex); continue
        print(f"  {cls}: generating {samples_per_class}...", end=" ", flush=True)
        for i in range(samples_per_class):
            seed = abs(hash(f"{cls}_{i}")) % (2**30)
            img = generate_fish_image(cls, seed)
            img.save(d/f"{cls}_{i:04d}.jpg", quality=85)
        print("done")
        total += samples_per_class
    print(f"\nTotal: {total} images in {p}")
    return str(p)

if __name__ == "__main__":
    import argparse
    pa = argparse.ArgumentParser()
    pa.add_argument("--output", default="./dataset/fish_disease")
    pa.add_argument("--samples", type=int, default=SAMPLES_PER_CLASS)
    args = pa.parse_args()
    generate_dataset(args.output, args.samples)
"""
import os
with open("core/ai/generate_synthetic_dataset.py", "w", encoding="utf-8") as f:
    f.write(src)
print("Written:", os.path.getsize("core/ai/generate_synthetic_dataset.py"), "bytes")
