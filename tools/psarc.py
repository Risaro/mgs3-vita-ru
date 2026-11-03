import argparse
import hashlib
import os
import struct
import sys
import zlib
from pathlib import Path

HEADER = struct.Struct(">4sHH4sIIIII")


class Psarc:
    def __init__(self, path):
        self.f = open(path, "rb")
        h = HEADER.unpack(self.f.read(HEADER.size))
        self.magic, self.vmaj, self.vmin, self.comp, self.toc_len, self.entry_size, self.count, self.block, self.flags = h
        if self.magic != b"PSAR":
            raise ValueError("not a PSARC file")
        toc = self.f.read(self.toc_len - HEADER.size)
        self.entries = []
        for i in range(self.count):
            e = toc[i * self.entry_size : (i + 1) * self.entry_size]
            self.entries.append(
                {
                    "md5": e[:16].hex(),
                    "first_block": int.from_bytes(e[16:20], "big"),
                    "size": int.from_bytes(e[20:25], "big"),
                    "offset": int.from_bytes(e[25:30], "big"),
                }
            )
        raw = toc[self.count * self.entry_size :]
        b = 2
        limit = self.block
        while limit > 256 ** b:
            b += 1
        if self.block == 65536:
            b = 2
        self.block_width = b
        self.sizes = [int.from_bytes(raw[i : i + b], "big") for i in range(0, len(raw) - len(raw) % b, b)]
        manifest = self.read_entry(self.entries[0])
        self.names = [""] + manifest.decode("utf-8", "replace").split("\n")

    def read_entry(self, e):
        out = bytearray()
        self.f.seek(e["offset"])
        idx = e["first_block"]
        while len(out) < e["size"]:
            z = self.sizes[idx]
            if z == 0:
                out += self.f.read(self.block)
            else:
                chunk = self.f.read(z)
                if chunk[:1] == b"\x78":
                    try:
                        out += zlib.decompress(chunk)
                    except zlib.error:
                        out += chunk
                else:
                    out += chunk
            idx += 1
        return bytes(out[: e["size"]])


def safe_target(root, name):
    target = (root / name.lstrip("/\\")).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"unsafe path: {name}")
    return target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("-o", "--out")
    ap.add_argument("-f", "--filter", default="")
    a = ap.parse_args()
    p = Psarc(a.archive)
    print(f"v{p.vmaj}.{p.vmin} comp={p.comp.decode()} files={p.count} block={p.block} flags={p.flags} toc={p.toc_len}")
    for i, e in enumerate(p.entries[1:], 1):
        name = p.names[i] if i < len(p.names) else f"unnamed_{i}"
        if a.filter and a.filter.lower() not in name.lower():
            continue
        print(f"{e['size']:>12} {name}")
        if a.out:
            data = p.read_entry(e)
            check = hashlib.md5(name.encode()).hexdigest() == e["md5"]
            if not check:
                print(f"  name md5 mismatch: {name}", file=sys.stderr)
            t = safe_target(Path(a.out), name)
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_bytes(data)


if __name__ == "__main__":
    main()
