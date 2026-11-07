# يولّد أصوات لعبة الحروف عبر Speko ويحفظها في مجلد audio
import os, sys, time
from pathlib import Path
from spekoai import Speko

LET = "أبتثجحخدذرزسشصضطظعغفقكلمنهوي"
NAMES = ["ألف","باء","تاء","ثاء","جيم","حاء","خاء","دال","ذال","راء","زاي","سين","شين","صاد","ضاد","طاء","ظاء","عين","غين","فاء","قاف","كاف","لام","ميم","نون","هاء","واو","ياء"]
WORDS = ["أسد","بطة","تمساح","ثعلب","جمل","حصان","خفاش","دب","ذئب","روبيان","زرافة","سلحفاة","شمبانزي","صقر","ضفدع","طاووس","ظبي","عصفور","غراب","فيل","قطة","كلب","لاما","ماعز","نمر","هامستر","وزة","يمامة"]
FATHA, DAMMA, KASRA = "\u064E", "\u064F", "\u0650"

def parse(spec):
    spec = (spec or "0").strip().lower()
    if spec == "all":
        return list(range(28))
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += range(int(a), int(b) + 1)
        elif part.strip():
            out.append(int(part))
    return [i for i in out if 0 <= i < 28]

def items(i):
    c = LET[i]
    return {
        f"n{i}": NAMES[i],
        f"w{i}": WORDS[i],
        f"h{i}_0": c + FATHA,
        f"h{i}_1": c + DAMMA,
        f"h{i}_2": c + KASRA,
        f"m{i}_0": c + FATHA + "ا",
        f"m{i}_1": c + DAMMA + "و",
        f"m{i}_2": c + KASRA + "ي",
    }

def synth(speko, text):
    try:
        return speko.synthesize(text, language="ar-SA", speed=0.8)
    except TypeError:
        return speko.synthesize(text, language="ar-SA")

def main():
    speko = Speko(api_key=os.environ["SPEKO_API_KEY"])
    out_dir = Path("audio")
    out_dir.mkdir(exist_ok=True)
    made = skipped = failed = 0
    for i in parse(os.environ.get("LETTERS", "0")):
        for key, text in items(i).items():
            if any(out_dir.glob(key + ".*")):
                skipped += 1
                continue
            for attempt in range(3):
                try:
                    sp = synth(speko, text)
                    ct = sp.content_type or ""
                    ext = "mp3" if "mpeg" in ct else "wav" if "wav" in ct else "mp3"
                    (out_dir / f"{key}.{ext}").write_bytes(sp.audio)
                    made += 1
                    print("OK", key, text, ct)
                    break
                except Exception as e:
                    print("retry", key, e)
                    time.sleep(2)
            else:
                failed += 1
                print("FAILED", key)
            time.sleep(0.3)
    print(f"done: made={made} skipped={skipped} failed={failed}")

main()
