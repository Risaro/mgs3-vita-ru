import os
import struct
import sys
import zlib
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from atlas_cyr import build as atlas_build
from codec import codec_rebuild, gcx_rebuild, learn_legacy, parse_block
from credits import add_credits
from gcx_extra import table as gcx_extra_table
from psarc import Psarc
from transplant import exact_sdt
from vtex import encode as vtex_encode

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "dump/dec/mgs3_eu.psp2arc"
PC = ROOT / "pc-rus/x"
OUT = ROOT / "out/rePatch/PCSB00176"
GROUPS = ("codec", "gcx", "vox", "demo", "movie", "textures")
ATLASES = {"001cee1b", "003e24e2", "0053c115", "0060327e", "0063051d", "007becbf", "00cc6191", "00bafb6e", "00da570c"}
STYLED_ATLASES = {"00bafb6e", "00da570c"}
PIXEL_ATLASES = {"00da570c"}
LOGOS = {"007a861b.ctxr", "00e11a3e.ctxr"}


def arg(name, default=None):
    return next((a.split("=", 1)[1] for a in sys.argv if a.startswith(f"--{name}=")), default)


def wanted():
    only = arg("only")
    return set(only.split(",")) if only else set(GROUPS)


def read_txtr(path):
    d = path.read_bytes()
    w, h = struct.unpack(">HH", d[8:12])
    px = np.frombuffer(d, np.uint8, w * h * 4, 160).reshape(h, w, 4)
    return Image.fromarray(px, "RGBA")


def legacy_table(arc, read):
    pairs = []
    for n in arc.names:
        if "/codec/" in n and n.endswith(".sdt"):
            p = parse_block(read(n))
            pairs += zip(p["s1"], p["s2"])
    return learn_legacy(pairs)


def collect(arc):
    index = {n: i for i, n in enumerate(arc.names)}

    def read(n):
        return arc.read_entry(arc.entries[index[n]])

    groups = wanted()
    new = {}
    stats = Counter()
    if "codec" in groups:
        table = legacy_table(arc, read)
        for f in sorted(os.listdir(PC / "fr/codec/_bp")):
            n = "/fr/codec/_bp/" + f
            a = (PC / n[1:]).read_bytes()
            v = read(n)
            if a == v:
                continue
            o, s = codec_rebuild(a, v, table)
            if o is None:
                raise SystemExit(f"{n}: {s}")
            new[n] = o
            stats["codec"] += 1
    if "gcx" in groups:
        extra = gcx_extra_table()
        for f in sorted(os.listdir(PC / "assets/gcx/fr/_bp")):
            n = "/assets/gcx/fr/" + f
            a = (PC / "assets/gcx/fr/_bp" / f).read_bytes()
            v = read(n)
            if a == v:
                continue
            o, s = gcx_rebuild(a, v, extra)
            if o is None:
                raise SystemExit(f"{n}: {s}")
            new[n] = o
            stats["gcx"] += 1
    for g in ("vox", "demo", "movie"):
        if g not in groups:
            continue
        for f in sorted(os.listdir(PC / f"us/{g}/_bp")):
            n = f"/us/{g}/_bp/_vta/{f}"
            o, s = exact_sdt((PC / f"us/{g}/_bp" / f).read_bytes(), read(n))
            if o is None:
                stats[g + " skipped"] += 1
                continue
            new[n] = o
            stats[g] += 1
    if "textures" in groups:
        for p in sorted((PC / "textures/flatlist/_win").iterdir()):
            n = "/textures/flatlist/_vta/" + p.name
            if n not in index:
                continue
            key = p.name[:8]
            if key in ATLASES:
                _, o = atlas_build(read(n), key in STYLED_ATLASES, key in PIXEL_ATLASES)
                new[n] = o
                stats["atlas"] += 1
                continue
            img = read_txtr(p)
            if p.name in LOGOS:
                img = add_credits(img)
            o = vtex_encode(img, read(n))
            if o is None:
                stats["texture bad layout"] += 1
                continue
            new[n] = o
            stats["texture"] += 1
    return new, stats


def compress_entry(data, block):
    out = bytearray()
    sizes = []
    for i in range(0, len(data), block):
        chunk = data[i : i + block]
        z = zlib.compress(chunk, 9)
        if len(z) >= len(chunk) and len(chunk) == block:
            out += chunk
            sizes.append(0)
        else:
            out += z
            sizes.append(len(z))
    return bytes(out), sizes


def write_archive(arc, new, path):
    tmp = path.with_suffix(".tmp")
    index = {n: i for i, n in enumerate(arc.names)}
    replace = {index[n]: d for n, d in new.items()}
    order = sorted(range(len(arc.entries)), key=lambda i: (arc.entries[i]["offset"], i))
    blocks = []
    records = {}
    seen = {}
    with open(tmp, "wb") as out:
        out.write(b"\0" * arc.toc_len)
        for i in order:
            e = arc.entries[i]
            if i in replace:
                z, sz = compress_entry(replace[i], arc.block)
                records[i] = (e["md5"], len(blocks), len(replace[i]), out.tell())
                blocks.extend(sz)
                out.write(z)
                continue
            key = (e["offset"], e["first_block"], e["size"])
            if key in seen:
                first, off = seen[key]
                records[i] = (e["md5"], first, e["size"], off)
                continue
            if e["size"] == 0:
                sz, span = [0], 0
            else:
                n = (e["size"] + arc.block - 1) // arc.block
                sz = arc.sizes[e["first_block"] : e["first_block"] + n]
                span = sum(s or arc.block for s in sz)
            records[i] = (e["md5"], len(blocks), e["size"], out.tell())
            seen[key] = (len(blocks), out.tell())
            blocks.extend(sz)
            arc.f.seek(e["offset"])
            out.write(arc.f.read(span))
    toc_len = 32 + arc.entry_size * len(arc.entries) + 2 * len(blocks)
    shift = toc_len - arc.toc_len
    toc = bytearray()
    for i in range(len(arc.entries)):
        md5, first, size, off = records[i]
        toc += bytes.fromhex(md5) + first.to_bytes(4, "big") + size.to_bytes(5, "big") + (off + shift).to_bytes(5, "big")
    for s in blocks:
        toc += s.to_bytes(2, "big")
    head = struct.pack(">4sHH4sIIIII", arc.magic, arc.vmaj, arc.vmin, arc.comp, toc_len, arc.entry_size, arc.count, arc.block, arc.flags)
    with open(path, "wb") as final, open(tmp, "rb") as body:
        final.write(head)
        final.write(toc)
        body.seek(arc.toc_len)
        while chunk := body.read(1 << 24):
            final.write(chunk)
    tmp.unlink()


def verify(path, arc, new):
    p = Psarc(path)
    idx = {n: i for i, n in enumerate(p.names)}
    assert p.names == arc.names
    for n, d in new.items():
        assert p.read_entry(p.entries[idx[n]]) == d, n
    checked = 0
    for i, n in enumerate(p.names):
        if i == 0 or n in new or i % 40:
            continue
        assert p.read_entry(p.entries[i]) == arc.read_entry(arc.entries[i]), n
        checked += 1
    print("verified replaced", len(new), "sampled unchanged", checked)


def main():
    arc = Psarc(SRC)
    new, stats = ({}, {}) if "--none" in sys.argv else collect(arc)
    print(dict(stats))
    out = Path(arg("out", OUT))
    out.mkdir(parents=True, exist_ok=True)
    path = out / "mgs3_eu.psp2arc"
    write_archive(arc, new, path)
    print("archive", path.stat().st_size)
    verify(path, arc, new)


if __name__ == "__main__":
    main()
