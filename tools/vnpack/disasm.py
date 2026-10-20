"""Print the contents of a vn3ds game.bin.

    python3 -m vnpack.disasm build/<id>/game.bin
"""

import struct
import sys

from .compiler import OP

NAMES = {v: k for k, v in OP.items()}
NONE = 0xFFFFFFFF


def load(path):
    data = open(path, "rb").read()
    assert data[:4] == b"VN3D", "not a vn3ds game.bin"
    _, n = struct.unpack_from("<II", data, 4)
    sections = {}
    for i in range(n):
        tag = data[12 + i * 12:16 + i * 12].decode()
        off, size = struct.unpack_from("<II", data, 16 + i * 12)
        sections[tag] = data[off:off + size]
    st = sections["STR "]
    (count,) = struct.unpack_from("<I", st, 0)
    offs = struct.unpack_from(f"<{count}I", st, 4)
    blob = st[4 + 4 * count:]
    strings = [blob[o:blob.index(b"\0", o)].decode() for o in offs]
    return sections, strings


def main():
    sections, strings = load(sys.argv[1])

    def s(i):
        return "-" if i == NONE else repr(strings[i])

    var_sec = sections["VARS"]
    (nv,) = struct.unpack_from("<I", var_sec, 0)
    var_names = [strings[i] for i in struct.unpack_from(f"<{nv}I", var_sec, 4)]
    code = sections["CODE"]
    pc = 0

    def rd(fmt):
        nonlocal pc
        v = struct.unpack_from("<" + fmt, code, pc)
        pc += struct.calcsize("<" + fmt)
        return v if len(v) > 1 else v[0]

    while pc < len(code):
        at = pc
        op = code[pc]
        pc += 1
        name = NAMES.get(op, f"?{op:02x}")
        args = ""
        if name in ("JMP", "JZ", "JNZ", "CALL"):
            args = f"{rd('I'):06x}"
        elif name == "PUSH_NUM":
            args = repr(rd("d"))
        elif name == "PUSH_STR":
            args = s(rd("I"))
        elif name in ("LOAD", "STORE"):
            args = var_names[rd("I")]
        elif name == "CALLF":
            args = "f%d/%d" % rd("BB")
        elif name == "SAY":
            c, who, what, fl = rd("iIIB")
            args = f"char={c} who={s(who)} flags={fl} {s(what)}"
        elif name == "MENU_ITEM":
            t, a = rd("II")
            args = f"{s(t)} -> {a:06x}"
        elif name == "MENU":
            c, who, cap = rd("iII")
            args = f"char={c} who={s(who)} {s(cap)}"
        elif name == "PAUSE":
            args = str(rd("B"))
        elif name in ("SCENE", "SHOW"):
            spec, as_, z, beh, n = rd("IIiIB")
            atl = [rd("i") for _ in range(n)]
            args = f"{s(spec)} as={s(as_)} z={z} behind={s(beh)} atl={atl}"
        elif name in ("HIDE", "SHOW_ATTR"):
            args = s(rd("I"))
        elif name == "WITH":
            args = str(rd("i"))
        elif name == "PLAY":
            ch, res, fl, fi, fo = rd("BiBff")
            args = f"ch={ch} res={res} flags={fl} fadein={fi} fadeout={fo}"
        elif name == "STOP":
            ch, fo = rd("Bf")
            args = f"ch={ch} fadeout={fo}"
        elif name == "WINDOW":
            args = str(rd("B"))
        print(f"{at:06x}  {name:<11} {args}")


if __name__ == "__main__":
    main()
