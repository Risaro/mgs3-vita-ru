import struct

from transplant import find_block

TRANSLIT = dict(zip("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя—–…№", "ABVGDEEJZIYKLMNOPRSTUFHC4WW'Y'EUAabvgdeejziyklmnoprstufhc4ww'y'eua--.N"))
BUTTONS = ""


def parse_block(x):
    _, b, _ = find_block(x)
    size, tab2, str2, end, _ = struct.unpack("<5I", x[b : b + 20])
    blk = x[b : b + size]
    t1 = struct.unpack("<I", blk[20:24])[0]
    cnt = struct.unpack("<I", blk[t1 : t1 + 4])[0]
    o1 = struct.unpack(f"<{cnt}I", blk[t1 + 4 : t1 + 4 + 4 * cnt])
    s1 = [None if o == 0xFFFFFFFF else blk[t1 + o : blk.index(b"\0", t1 + o)] for o in o1]
    o2 = struct.unpack(f"<{(str2 - tab2) // 4}I", blk[tab2:str2])
    s2 = [None if o == 0xFFFFFFFF else blk[str2 + (o & 0x7FFFFFFF) : blk.index(b"\0", str2 + (o & 0x7FFFFFFF))] for o in o2]
    return dict(b=b, size=size, tab2=tab2, str2=str2, end=end, t1=t1, s1=s1, o2=o2, s2=s2, blk=blk)


def to_utf8(s):
    try:
        s.decode("utf-8")
        return s
    except UnicodeDecodeError:
        return s.decode("cp1251").encode("utf-8")


def pack_strings(strings, base):
    data = bytearray()
    offs = []
    for s in strings:
        if s is None:
            offs.append(0xFFFFFFFF)
            continue
        offs.append(base + len(data))
        data += s + b"\0"
    return offs, data


def build_block(p, s1, s2):
    head = p["blk"][20 : p["t1"]]
    offs, strs = pack_strings(s1, 4 + 4 * len(s1))
    tab1 = struct.pack("<I", len(s1)) + struct.pack(f"<{len(s1)}I", *offs) + bytes(strs)
    tab2 = 20 + len(head) + len(tab1)
    offs2, strs2 = pack_strings(s2, 0)
    offs2 = [o if o == 0xFFFFFFFF else (flag & 0x80000000) | o for o, flag in zip(offs2, p["o2"])]
    strs2 += b"\0" * (-len(strs2) % 4)
    str2 = tab2 + 4 * len(s2)
    end = str2 + len(strs2)
    trailer = p["blk"][p["end"] : p["size"]]
    return struct.pack("<5I", end + len(trailer), tab2, str2, end, 0) + head + tab1 + struct.pack(f"<{len(s2)}I", *offs2) + bytes(strs2) + trailer


def learn_legacy(pairs):
    table = {}
    for s1, s2 in pairs:
        if s1 is None or s2 is None:
            continue
        try:
            text = s1.decode("utf-8")
        except UnicodeDecodeError:
            continue
        j = 0
        found = {}
        for ch in text:
            if ord(ch) < 0x80:
                if j >= len(s2) or s2[j] != ord(ch):
                    found = None
                    break
                j += 1
            else:
                if j + 2 > len(s2):
                    found = None
                    break
                found[ch] = s2[j : j + 2]
                j += 2
        if found is not None and j == len(s2):
            for k, v in found.items():
                table.setdefault(k, v)
    table = {k: v for k, v in table.items() if v[:1] == b"\x1f" or k in BUTTONS}
    for k, v in TRANSLIT.items():
        table[k] = v.encode()
    return table


def legacy(s1, table, fallback=b"\x1f\x0f"):
    out = bytearray()
    for ch in s1.decode("utf-8"):
        out += bytes([ord(ch)]) if ord(ch) < 0x80 else table.get(ch, fallback)
    return bytes(out)


def codec_rebuild(pc, vita, table):
    pp = parse_block(pc)
    vp = parse_block(vita)
    if len(pp["s1"]) != len(vp["s1"]) or len(vp["s1"]) != len(vp["s2"]):
        return None, "count"
    if pc[: pp["b"]] != vita[: vp["b"]]:
        return None, "header differs"
    s1 = [None if s is None else to_utf8(s) for s in pp["s1"]]
    s2 = [vs2 if (a == vs1 or a is None or vs2 is None) else legacy(a, table) for a, vs1, vs2 in zip(s1, vp["s1"], vp["s2"])]
    blk = build_block(vp, s1, s2)
    return vita[: vp["b"]] + blk + vita[vp["b"] + vp["size"] :], "ok"


def gcx_rebuild(pc, vita, extra):
    pp = parse_block(pc)
    vp = parse_block(vita)
    if len(pp["s1"]) != len(vp["s1"]):
        return None, "count"
    if pc[: pp["b"]] != vita[: vp["b"]]:
        return None, "header differs"
    s1 = [None if s is None else to_utf8(s) for s in pp["s1"]]
    s1 = [extra.get(s, s) if s is not None and s == v else s for s, v in zip(s1, vp["s1"])]
    blk = vp["blk"]
    head = blk[20 : vp["t1"]]
    offs, strs = pack_strings(s1, 4 + 4 * len(s1))
    tab1 = struct.pack("<I", len(s1)) + struct.pack(f"<{len(s1)}I", *offs) + bytes(strs)
    tab2 = 20 + len(head) + len(tab1)
    delta = tab2 - vp["tab2"]
    new = struct.pack("<5I", vp["size"] + delta, tab2, vp["str2"] + delta, vp["end"] + delta, 0) + head + tab1 + blk[vp["tab2"] : vp["size"]]
    return vita[: vp["b"]] + new + vita[vp["b"] + vp["size"] :], "ok"
