import struct


def find_block(x):
    i = 8
    while i + 24 <= len(x):
        if x[i : i + 4] == b"\xff\xff\xff\xff":
            b = i + 4
            size, tab2, str2, end, zero = struct.unpack("<5I", x[b : b + 20])
            if size <= len(x) - b and tab2 <= str2 <= end <= size and zero == 0:
                return i, b, size
        i += 4
    return None


def iter_chunks(x):
    pos = 0
    while pos + 32 <= len(x):
        h = struct.unpack("<8I", x[pos : pos + 32])
        if h[0] != 0x10 or h[1] != 0x10:
            return
        size = h[5]
        yield pos, size, x[pos + 32 : pos + 36]
        pos += 32 + size


def pacb_entries(chunk):
    size = struct.unpack("<I", chunk[4:8])[0]
    p = 8
    out = []
    end = 8 + size
    while p + 16 <= end and p + 16 <= len(chunk):
        start, dur, extra = struct.unpack("<III", chunk[p : p + 12])
        length, lang = struct.unpack("<HH", chunk[p + 12 : p + 16])
        if length < 16:
            break
        out.append((start, dur, extra, lang, chunk[p + 16 : p + length]))
        p += length
    return out


def clip_utf8(text, limit):
    body = text.rstrip(b"\0")
    if len(body) + 1 <= limit:
        return body + b"\0"
    cut = limit - 1
    while cut > 0 and (body[cut] & 0xC0) == 0x80:
        cut -= 1
    return body[:cut] + b"\0"


def exact_sdt(pc, vita, lang=1):
    pc_chunks = [(o, s) for o, s, m in iter_chunks(pc) if m == b"PACB"]
    v_chunks = [(o, s) for o, s, m in iter_chunks(vita) if m == b"PACB"]
    if not pc_chunks or len(pc_chunks) != len(v_chunks):
        return None, f"pacb count pc={len(pc_chunks)} vita={len(v_chunks)}"
    out = bytearray(vita)
    for (po, ps), (vo, vs) in zip(pc_chunks, v_chunks):
        pe = pacb_entries(pc[po + 32 : po + 32 + ps])
        ve = pacb_entries(vita[vo + 32 : vo + 32 + vs])
        if [e[3] for e in pe] != [e[3] for e in ve]:
            return None, f"lang layout pc={len(pe)} vita={len(ve)}"
        budget = struct.unpack("<I", vita[vo + 36 : vo + 40])[0]
        ru = [p[4] for p, v in zip(pe, ve) if v[3] == lang]
        others = [v[4] for v in ve if v[3] != lang]
        room = budget - 16 * len(ve) - sum(len(t) for t in ru)
        if room < 2 * len(others):
            return None, f"no room {room}"
        cap = max(len(t) for t in others) if others else 0
        while cap > 2 and sum(min(len(t), cap) for t in others) > room:
            cap -= 1
        texts = []
        for p, v in zip(pe, ve):
            if v[3] == lang:
                texts.append(p[4])
            else:
                texts.append(v[4] if len(v[4]) <= cap else clip_utf8(v[4], cap))
        slack = budget - 16 * len(ve) - sum(len(t) for t in texts)
        if slack < 0:
            return None, f"overflow {slack}"
        last = max(i for i, v in enumerate(ve) if v[3] != lang)
        texts[last] = texts[last] + b"\0" * slack
        body = bytearray()
        for t, v in zip(texts, ve):
            body += struct.pack("<IIIHH", v[0], v[1], v[2], 16 + len(t), v[3]) + t
        out[vo + 40 : vo + 40 + budget] = body
    return bytes(out), "ok"
