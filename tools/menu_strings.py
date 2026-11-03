import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPL = ROOT / "pc-rus/x/replacements_en_ru.txt"
REGION = (0x960000, 0x990000)
CYR = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

MAIN = {
    "NEW GAME": "НОВАЯ ИГРА",
    "OPTIONS": "ОПЦИИ",
    "SPECIAL": "БОНУСЫ",
    "BRIEFING FILES": "ДОСЬЕ БРИФИНГА",
    "DIFFICULTY": "СЛОЖНОСТЬ",
    "LOAD GAME": "ЗАГРУЗИТЬ",
    "SNAKE VS MONKEY": "ЛОВЛЯ ОБЕЗЬЯН",
    "DUEL": "ДУЭЛЬ",
    "DEMO THEATER": "ДЕМО-ТЕАТР",
    "VERY EASY": "ОЧЕНЬ ЛЕГКО",
    "EASY": "ЛЕГКО",
    "NORMAL": "СРЕДНЕ",
    "HARD": "СЛОЖНО",
    "EXTREME": "ЭКСТРИМ",
    "EUROPEAN EXTREME": "ЕВРО-ЭКСТРИМ",
    "VIRTUOUS MISSION": "МИССИЯ ДОБРОДЕТЕЛЬ",
    "OPERATION SNAKE EATER": "ОП. ПОЖИРАТЕЛЬ ЗМЕЙ",
    "EXIT": "ВЫХОД",
    "BACK TO GAME SELECT": "К ВЫБОРУ ИГРЫ",
    "ONLINE MODE": "ОНЛАЙН",
    "SECRET THEATER": "ТАЙНЫЙ ТЕАТР",
    "SCREEN ADJUSTMENT": "НАСТРОЙКА ЭКРАНА",
    "BRIGHTNESS ADJUSTMENT": "НАСТРОЙКА ЯРКОСТИ",
    ": DEFAULT": ": СБРОС",
    ": CANCEL": ": ОТМЕНА",
    "FULL-FRAME HUD": "ПОЛНЫЙ HUD",
    "ON": "ВКЛ",
    "OFF": "ВЫК",
    "BLOOD": "КРОВЬ",
    "CAPTIONS": "СУБТИТРЫ",
    "OWN VIEW": "ВИД ОТ 1-ГО",
    "REVERSE": "ИНВЕРС.",
    "REAL-TIME CUTSCENES": "РОЛИКИ НА ДВИЖКЕ",
    "FULL SCREEN": "ВЕСЬ ЭКРАН",
    "LETTERBOX": "ПОЛОСЫ",
    "PRESS START BUTTON": "НАЖМИТЕ START",
    "MENU": "МЕНЮ",
    "CHAPTER SELECT": "ВЫБОР ГЛАВЫ",
    "CAPTION": "ТИТРЫ",
    "CLEAR DATA": "ПРОЙДЕНО",
    "ORIGINAL": "ОРИГИНАЛ",
    "WARNING": "ВАЖНО",
    "YES": "ДА",
    "NO": "НЕТ",
    "MEMORY CARD slot 2": "КАРТА ПАМЯТИ 2",
    "DISC 1": "ДИСК 1",
    "DISC 2": "ДИСК 2",
    "SAVE": "СОХРАН.",
    "ALERT PHASE": "ТРЕВОГИ",
    "PLANTS & ANIMALS CAPTURED": "ФЛОРА И ФАУНА",
    "NOT USED": "НЕ ИСПОЛЬЗ.",
    "INFINITY FACE PAINT": "РАСКР. БЕСКОНЕЧН.",
    "PAGE": "СТР.",
    "CAMERA MODE": "РЕЖ. КАМЕРЫ",
    "GIANT PANDA": "ПАНДА",
    "FLYING FOX": "ЛЕТ. ЛИСИЦА",
    "CUT": "РЕЗ",
    "ARROW WOUND": "СТРЕЛА",
}
for i in range(1, 9):
    MAIN[f"CHAPTER 0{i}"] = f"ГЛАВА 0{i}"

def parse_pc():
    text = REPL.read_text("utf-8-sig").replace("\r\n", "\n")
    items = []
    for block in re.split(r"\n\s*\n", text):
        lines = [l for l in block.split("\n") if not l.startswith("#")]
        if len(lines) < 3 or not re.fullmatch(r"[0-9A-Fa-f]{5,8}", lines[0].strip()):
            continue
        body = lines[1:]
        half = len(body) // 2
        items.append(("\n".join(body[:half]), "\n".join(body[half:])))
    return items


def slot_size(data, start, length):
    end = start + length
    while end < len(data) and data[end] == 0:
        end += 1
    return end - start


ASCII_FIX = {"«": '"', "»": '"', "—": "-", "–": "-", "…": "...", "№": "N", "ё": "е", "Ё": "Е"}


def encode(ru):
    out = bytearray()
    for ch in ru:
        ch = ASCII_FIX.get(ch, ch)
        for c in ch:
            u = c.upper()
            if u in CYR:
                out.append(0x60 + CYR.index(u))
            elif 0x20 <= ord(u) < 0x60:
                out.append(ord(u))
            else:
                return None
    return bytes(out)


def collect(eboot):
    pairs = dict(p for p in parse_pc() if p[0] == p[0].upper() and "%" not in p[0])
    pairs.update(MAIN)
    lo, hi = REGION
    patches = {}
    report = {"ok": 0, "long": [], "bad": [], "missing": []}
    for en, ru in pairs.items():
        needle = b"\0" + en.encode() + b"\0"
        pos = []
        i = eboot.find(needle, lo, hi)
        while i >= 0:
            pos.append(i + 1)
            i = eboot.find(needle, i + 1, hi)
        if not pos:
            report["missing"].append(en)
            continue
        data = encode(ru)
        if data is None:
            report["bad"].append((en, ru))
            continue
        for p in pos:
            room = slot_size(eboot, p, len(en))
            if len(data) + 1 > room:
                report["long"].append((en, ru, room))
                continue
            patches[p] = data + b"\0" * (room - len(data))
            report["ok"] += 1
    return patches, report


def ranges(eboot, patches, gap=48):
    buf = bytearray(eboot)
    for p, d in patches.items():
        buf[p : p + len(d)] = d
    spans = []
    for p in sorted(patches):
        e = p + len(patches[p])
        if spans and p - spans[-1][1] <= gap:
            spans[-1][1] = max(spans[-1][1], e)
        else:
            spans.append([p, e])
    return [(a, bytes(buf[a:b])) for a, b in spans]


def write_header(path, spans, seg0_file=0x1000):
    lines = ["#include <stdint.h>", "typedef struct { uint32_t off; uint32_t size; const uint8_t *data; } str_patch_t;"]
    tab = []
    for k, (a, d) in enumerate(spans):
        lines.append(f"static const uint8_t s{k}[] = {{{', '.join(str(x) for x in d)}}};")
        tab.append(f"{{0x{a - seg0_file:x}, {len(d)}, s{k}}}")
    lines.append("static const str_patch_t str_patches[] = {" + ", ".join(tab) + "};")
    lines.append(f"#define STR_PATCH_COUNT {len(tab)}")
    Path(path).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    eboot = (ROOT / "dump/elf/eboot.bin.elf").read_bytes()
    patches, rep = collect(eboot)
    spans = ranges(eboot, patches)
    write_header(ROOT / "tools/plugin/strings.h", spans)
    print("patched", rep["ok"], "spans", len(spans), "bytes", sum(len(d) for _, d in spans))
    print("long", rep["long"])
    print("bad", rep["bad"])
    print("missing", rep["missing"])
