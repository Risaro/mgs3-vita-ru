from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SEG1_FILE = 0x99F000
SEG1_VA = 0x8199E000
SEG0_VA = 0x81000000

HELP = {
    "Adjust aspect ratio for Real-Time Cutscenes.": "Соотношение сторон для роликов на движке.",
    "Return to the title screen.": "Вернуться на титульный экран.",
    "For beginners.": "Для новичков.",
    "For non action-experts.": "Для тех, кто не мастер экшена.",
    "Standard difficulty level.": "Стандартный уровень сложности.",
    "For confident players.": "Для уверенных игроков.",
    "For action game experts.": "Для знатоков экшен-игр.",
    "Game ends when being seen by enemy.": "Игра окончена, если враг вас заметит.",
    "Damaged": "Повреждено",
    "Save failed": "Ошибка сохранения",
    "Are you sure you wish to overwrite this save data?\nYes or No": "Перезаписать это сохранение?\nДа или Нет",
    "Save Successful": "Сохранено",
    "Loading data": "Загрузка данных",
    "Load Successful": "Загружено",
    "Load failed!": "Ошибка загрузки!",
    "Saving...": "Сохранение...",
    "Checking memory card": "Проверка карты памяти",
    "No data present on the memory card.": "На карте памяти нет данных.",
    "Create new save?\nYes or No": "Создать новое сохранение?\nДа или Нет",
}


def file_to_va(fo):
    return fo - 0x1000 + SEG0_VA if fo < SEG1_FILE else fo - SEG1_FILE + SEG1_VA


def collect(eboot, table=HELP, lo=0x960000, hi=0x99ED88):
    words = np.frombuffer(eboot[: len(eboot) // 4 * 4], "<u4")
    seg1 = (np.arange(len(words)) * 4 >= SEG1_FILE)
    items = []
    missing = []
    for en, ru in table.items():
        needle = b"\0" + en.encode() + b"\0"
        i = eboot.find(needle, lo, hi)
        if i < 0:
            missing.append(en)
            continue
        va = file_to_va(i + 1)
        refs = np.nonzero((words == va) & seg1)[0] * 4
        if not len(refs):
            missing.append(en + " (no refs)")
            continue
        items.append((ru.encode("utf-8"), [file_to_va(int(r)) for r in refs]))
    return items, missing


def write_header(path, items):
    lines = ["#include <stdint.h>"]
    refs = []
    for k, (data, rs) in enumerate(items):
        lines.append(f"static const char r{k}[] = {{{', '.join(str(x) for x in data + b'\\0')}}};")
        for r in rs:
            refs.append(f"{{0x{r:X}u, r{k}}}")
    lines.append("typedef struct { uint32_t va; const char *str; } reloc_t;")
    lines.append("static const reloc_t relocs[] = {" + ", ".join(refs) + "};")
    lines.append(f"#define RELOC_COUNT {len(refs)}")
    Path(path).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    eboot = (ROOT / "dump/elf/eboot.bin.elf").read_bytes()
    items, missing = collect(eboot)
    write_header(ROOT / "tools/plugin/relocs.h", items)
    print("strings", len(items), "refs", sum(len(r) for _, r in items))
    print("missing", missing)
