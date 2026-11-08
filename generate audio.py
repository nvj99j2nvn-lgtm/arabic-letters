# يولّد أصوات لعبة الحروف عبر Speko ويحفظها في مجلد audio
import os, sys, time, wave
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


def sniff(b):
    if b[:4] == b"RIFF": return "wav"
    if b[:3] == b"ID3" or (len(b) > 1 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0): return "mp3"
    return None

def save(out_dir, key, sp):
    data = sp.audio
    kind = sniff(data)
    if kind is None:  # raw PCM: wrap as 16-bit mono WAV
        rate = getattr(sp, "sample_rate", None) or 24000
        p = out_dir / f"{key}.wav"
        with wave.open(str(p), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(int(rate)); w.writeframes(data)
        return "wav(pcm)"
    (out_dir / f"{key}.{kind}").write_bytes(data)
    return kind

def existing_ok(out_dir, key):
    for p in out_dir.glob(key + ".*"):
        kind = sniff(p.read_bytes()[:4] + b"\x00\x00")
        if kind is None:
            p.unlink(); continue
        if p.suffix[1:] != kind:
            p.rename(p.with_suffix("." + kind))
        return True
    return False

def main():
    speko = Speko(api_key=os.environ["SPEKO_API_KEY"])
    out_dir = Path("audio")
    out_dir.mkdir(exist_ok=True)
    made = skipped = failed = 0
    for i in parse(os.environ.get("LETTERS", "0")):
        for key, text in items(i).items():
            if existing_ok(out_dir, key):
                skipped += 1
                continue
            for attempt in range(3):
                try:
                    sp = synth(speko, text)
                    ct = sp.content_type or ""
                    kind = save(out_dir, key, sp)
                    made += 1
                    print("OK", key, text, ct, kind)
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
