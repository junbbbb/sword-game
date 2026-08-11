# -*- coding: utf-8 -*-
"""배포용 빌드를 만든다. web/ 를 건드리지 않고 dist/ 에 따로 굽는다.

왜 복사해서 굽는가
  web/main.js 는 작업 중일 수 있다. 배포하려고 CHAR_LIST 를 고쳤다가
  되돌리는 걸 잊으면 개발 중에 캐릭터가 사라진다.
  빌드를 분리하면 원본은 손대지 않고 배포본만 달라진다.

빼는 것
  - *.bak* 백업 (42MB. 올릴 이유가 없다)
  - 안 쓰는 캐릭터 glb (탱커 8.0 / 궁수 5.7 / 바바리안 2.8 / 병사 0.5 / 기본 0.9)
    ★첫 로딩에 캐릭터를 전부 받는다. 시작 캐릭터 하나만 남기면 25.5MB -> 6MB 대로 떨어진다.
  - basic2 를 굽는 중간 산출물(basic2_native / basic2_body / basic2_moves)도
    KEEP_CHARS 에 없으니 저절로 빠진다. 배포에 실리는 건 basic2.glb 하나다.
  - 개발용 문서·렌더

실행: python3 tools/build_deploy.py
"""
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "web")
DST = os.path.join(ROOT, "dist")

# 배포에 남길 캐릭터. 나중에 늘리려면 여기만 고친다.
# ★CHAR_LIST 와 반드시 맞출 것. kensa 빠뜨려 배포본 시작 캐릭터가 404 났던 사고(2026-08-10).
#   2026-08-11 시작 캐릭터가 basic2 로 바뀌었다(main.js CHAR_LIST 맨 앞).
KEEP_CHARS = ["basic2", "kensa", "slayer", "tank", "archer", "soldier"]
# 캐릭터가 아니지만 반드시 필요한 glb
KEEP_GLB = ["level1.glb", "goblin.glb", "boss.glb"]

ALL_CHARS = ["slayer", "tank", "archer", "soldier", "basic", "basic2", "hero"]

# ★dist 를 통째로 지우면 배포 설정까지 같이 날아간다.
#   .vercel/project.json 이 없으면 vercel 이 **새 프로젝트**를 만들어서
#   안정 주소(dist-phi-jet-62)가 아닌 낯선 주소로 올라간다.
#   vercel.json 은 glb 캐시 헤더다. 둘 다 web/ 에 없으니 여기서 지키는 수밖에 없다.
KEEP_CONFIG = [".vercel", "vercel.json", ".gitignore"]

if os.path.isdir(DST):
    stash = os.path.join(ROOT, ".dist_config_stash")
    if os.path.isdir(stash):
        shutil.rmtree(stash)
    os.makedirs(stash)
    saved = []
    for name in KEEP_CONFIG:
        src = os.path.join(DST, name)
        if os.path.exists(src):
            dst = os.path.join(stash, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            saved.append(name)
    shutil.rmtree(DST)
    os.makedirs(DST)
    for name in saved:
        src = os.path.join(stash, name)
        dst = os.path.join(DST, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    shutil.rmtree(stash)
    print("배포 설정 유지:", saved if saved else "없음")


def skip(rel):
    base = os.path.basename(rel)
    if "bak" in base:
        return True
    if base.endswith(".glb"):
        # ★소품 폴더(props/)의 glb 는 캐릭터가 아니다. 캐릭터 필터에 걸리면
        #   나무·바위가 통째로 빠져 배포본 맵이 텅 빈다(실제로 났던 사고).
        if rel.replace(os.sep, "/").startswith("props/"):
            return False
        if base in KEEP_GLB:
            return False
        name = base[:-4]
        return name not in KEEP_CHARS
    return False


n = 0
total = 0
for dirpath, dirnames, filenames in os.walk(SRC):
    for fn in filenames:
        src = os.path.join(dirpath, fn)
        rel = os.path.relpath(src, SRC)
        if skip(rel):
            continue
        dst = os.path.join(DST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
        total += os.path.getsize(src)

# ── main.js 의 캐릭터 목록을 남긴 것만으로 줄인다 ──
# 없는 glb 를 로드하려 하면 404 가 나고 로딩이 안 끝난다.
# ★2026-08-10: main.js 가 ?dev 게이트로 캐릭터를 스스로 제한한다(평시 kensa 단독).
#   빌드에서 CHAR_LIST 를 다시 쓰면 그 게이트 구조를 깨뜨리므로 더는 치환하지 않는다.
#   KEEP_CHARS 는 이제 "배포에 실을 glb 목록"으로만 쓰인다(dev 모드가 프로덕션에서도 돌게).
mj = os.path.join(DST, "main.js")
s = open(mj, encoding="utf-8").read()
assert "CHAR_LIST" in s, "main.js 에 CHAR_LIST 가 없다. 구조 확인 필요"

print("복사 %d개 / %.1f MB" % (n, total / 1048576))
print("캐릭터:", KEEP_CHARS)
print("->", DST)
