from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CYR = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
LOOK = {"А": "A", "Б": "B", "В": "B", "Г": "F", "Д": "D", "Е": "E", "З": "B", "И": "N", "Й": "N", "К": "K", "Л": "N", "Н": "H", "О": "O", "П": "H", "Р": "P", "С": "C", "Т": "T", "У": "Y", "Ф": "O", "Х": "X", "Ц": "U", "Ч": "U", "Ъ": "B", "Ь": "B", "Э": "C", "Я": "R"}
WIDE = "ЖМШЩЫЮ"
TABLES = [0x9EF4F0, 0x9EF550, 0x9EF5B0, 0x9EF610]
SEG1_FILE = 0x99F000
SEG1_VA = 0x8199E000


def build(eboot):
    out = []
    for t in TABLES:
        tab = bytearray(eboot[t : t + 96])
        upper = tab[32:64]
        wide = max(upper[ord(c) - 0x40] for c in "MW")
        for i, ch in enumerate(CYR):
            if ch in WIDE:
                w = wide
            else:
                w = upper[ord(LOOK.get(ch, "H")) - 0x40]
            tab[64 + i] = w
        out.append((t - SEG1_FILE + SEG1_VA + 64, bytes(tab[64:96])))
    return out


def write_header(path, items):
    lines = ["#include <stdint.h>", "typedef struct { uint32_t va; const uint8_t data[32]; } width_patch_t;", "static const width_patch_t width_patches[] = {"]
    for va, d in items:
        lines.append(f"    {{0x{va:X}u, {{{', '.join(str(x) for x in d)}}}}},")
    lines.append("};")
    lines.append(f"#define WIDTH_PATCH_COUNT {len(items)}")
    Path(path).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    eboot = (ROOT / "dump/elf/eboot.bin.elf").read_bytes()
    items = build(eboot)
    for va, d in items:
        print(hex(va), list(d))
    write_header(ROOT / "tools/plugin/widths.h", items)
