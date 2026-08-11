#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glb 안의 노드·메시 이름에서 Blender 가 붙인 중복 접미사(.001)를 떼어낸다.

    python3 tools/glb_rename.py web/kensa.glb

★왜 필요한가
  s24_moveset.py 는 소스(slayer.glb)와 타깃(kensa_body.glb)을 **한 Blender 세션에**
  같이 읽는다. 둘 다 칼 이름이 SW_baekah 라서 나중에 읽은 타깃 쪽이 SW_baekah.001
  로 밀린다. 소스 오브젝트를 지워도 이름은 안 돌아오고, 그대로 내보내진다.
  게임(main.js)은 칼 키를 `name.slice(3).replace(/_\\d+$/, '')` 로 뽑으므로
  "SW_baekah.001" -> "baekah.001" 이 되어 **1~7 칼 교체가 통째로 죽는다.**
  (three.js 는 프리미티브가 여럿인 메시를 SW_baekah_0, _1 로 쪼개므로 뒤의 _숫자만
   떨어진다. .001 은 안 떨어진다)

★왜 다시 굽지 않고 JSON 만 고치나
  glb 를 Blender 로 다시 내보내면 텍스처가 한 번 더 재인코딩되고 애니 키가 다시
  구워진다. 이름 몇 글자 때문에 산출물을 흔들 이유가 없다. glb 는
  [헤더][JSON 청크][BIN 청크] 구조라 JSON 청크만 갈아 끼우고 길이·패딩만 맞추면 된다.
  BIN 은 한 바이트도 안 건드린다.
"""
import json
import os
import re
import struct
import sys

SUFFIX = re.compile(r"\.\d{3}$")


def strip(name):
    return SUFFIX.sub("", name) if isinstance(name, str) else name


def main(path, dry=False):
    raw = open(path, "rb").read()
    if raw[:4] != b"glTF":
        raise SystemExit("glb 가 아니다: %s" % path)
    ver, total = struct.unpack_from("<II", raw, 4)
    off, chunks = 12, []
    while off < len(raw):
        ln, ty = struct.unpack_from("<II", raw, off)
        off += 8
        chunks.append([ty, raw[off:off + ln]])
        off += ln
    if not chunks or chunks[0][0] != 0x4E4F534A:
        raise SystemExit("첫 청크가 JSON 이 아니다")
    doc = json.loads(chunks[0][1].decode("utf-8"))

    hit = []
    for key in ("nodes", "meshes", "materials", "images", "skins", "animations",
                "cameras"):
        for item in doc.get(key, []):
            nm = item.get("name")
            if isinstance(nm, str) and SUFFIX.search(nm):
                item["name"] = strip(nm)
                hit.append("%s: %s -> %s" % (key, nm, item["name"]))
    print("%s: 이름 %d개 정리" % (os.path.basename(path), len(hit)))
    for h in hit[:24]:
        print("   " + h)
    if len(hit) > 24:
        print("   ... 외 %d개" % (len(hit) - 24))
    if not hit:
        return
    if dry:
        print("   (dry-run. 파일은 안 건드렸다)")
        return

    js = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)          # JSON 청크는 공백으로 패딩
    chunks[0][1] = js
    out = bytearray()
    body = bytearray()
    for ty, data in chunks:
        pad = b"\x00" if ty != 0x4E4F534A else b" "
        data = data + pad * ((4 - len(data) % 4) % 4)
        body += struct.pack("<II", len(data), ty) + data
    out += b"glTF" + struct.pack("<II", ver, 12 + len(body)) + body
    tmp = path + ".tmp"
    open(tmp, "wb").write(bytes(out))
    os.replace(tmp, path)
    print("   %s 다시 씀 %d -> %d bytes" % (os.path.basename(path), len(raw), len(out)))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        raise SystemExit(__doc__)
    for p in args:
        main(p, dry="--dry" in sys.argv)
