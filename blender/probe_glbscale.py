# -*- coding: utf-8 -*-
"""glb 를 **직접 파싱**해서 액션별 scale 채널 범위를 찍는다. Blender 없이 돈다.

왜 필요한가
  뼈 스케일이 1 이 아니면 그 뼈의 하위 전체가 곱해져 커진다. 골반처럼 뿌리에
  가까운 뼈에 스케일이 박히면 캐릭터가 통째로 부풀어 오른다(궁수 Walk 17.65%).
  Blender 안에서는 임포터가 알아서 먹여버려 눈에 안 띄므로 glb 원본을 본다.

실행: python3 blender/probe_glbscale.py web/archer.glb [web/tank.glb ...]
"""
import json
import struct
import sys
import os


def parse(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[12:16])[0]
    j = json.loads(d[20:20 + n])
    off = 20 + n
    bl = struct.unpack("<I", d[off:off + 4])[0]
    bin_ = d[off + 8:off + 8 + bl]

    def acc(i):
        a = j["accessors"][i]
        bv = j["bufferViews"][a["bufferView"]]
        st = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        nc = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]
        return struct.unpack_from("<%df" % (a["count"] * nc), bin_, st)

    print("=== %s (%d bytes) ===" % (path, len(d)))
    print("  액션 %d개: %s" % (len(j.get("animations", [])),
                             [a.get("name") for a in j.get("animations", [])]))
    bad = 0
    for a in j.get("animations", []):
        lo, hi = 9e9, -9e9
        offenders = []
        for c in a["channels"]:
            if c["target"]["path"] != "scale":
                continue
            v = acc(a["samplers"][c["sampler"]]["output"])
            lo = min(lo, min(v))
            hi = max(hi, max(v))
            if max(v) > 1.001 or min(v) < 0.999:
                offenders.append((j["nodes"][c["target"]["node"]].get("name"),
                                  min(v), max(v)))
        if lo > 8e9:
            print("  %-8s scale 채널 없음" % a.get("name"))
            continue
        mark = "OK " if not offenders else "★NG"
        print("  %s %-8s scale %.4f ~ %.4f" % (mark, a.get("name"), lo, hi))
        for nm, mn, mx in offenders:
            print("        └ %-24s %.4f ~ %.4f" % (nm, mn, mx))
            bad += 1
    return bad


if __name__ == "__main__":
    args = sys.argv[1:] or ["web/archer.glb"]
    root = "/Users/lbj/Documents/gameproject"
    tot = 0
    for p in args:
        tot += parse(p if os.path.isabs(p) else os.path.join(root, p))
    print("\n스케일 오염 채널 총 %d개" % tot)
