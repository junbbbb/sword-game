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

넣는 것 (dist/ 에만 생기고 web/ 에는 안 남는다)
  - glb 내용 해시 표: dist/*.js 의 `const GLB_VER = {};` 한 줄을 md5 8자 표로 바꾼다.
    ★2026-08-12 사고. vercel.json 이 glb 에 `max-age=31536000, immutable` 을 주는데
      배포는 **같은 URL 에 내용만 갈아끼운다.** 한 번 다녀간 브라우저는 옛 glb 를
      1년 동안 재검증 없이 쓴다(크롬 hard reload 로도 안 뚫린다). 실제로 8월 초 판이
      남은 브라우저에서 시작 캐릭터가 알몸·맨손으로 떴다. 내용 해시를 URL 에 박으면
      내용이 바뀔 때 URL 이 바뀌므로 옛 캐시를 볼 일이 없다(그제서야 immutable 이 안전).
    ★표를 web/ 에 두지 않는 이유는 이 스크립트의 존재 이유와 같다 - 개발 중에는
      무버전 URL 이 편하다(로컬 서버는 어차피 immutable 을 안 준다).
  - vercel.json: 정본은 tools/deploy_config/vercel.json 이다(git 추적).
    ★html·js·json 은 vercel 기본이 `public, max-age=0, must-revalidate` 였고(실측)
      그게 맞는 값이라, 바뀌지 않게 같은 값을 명시만 해 둔다. glb 만 immutable 이다.

실행: python3 tools/build_deploy.py
"""
import hashlib
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
KEEP_GLB = ["level1.glb", "level2.glb", "goblin.glb", "boss.glb"]

ALL_CHARS = ["slayer", "tank", "archer", "soldier", "basic", "basic2", "hero"]

# ★dist 를 통째로 지우면 배포 설정까지 같이 날아간다.
#   .vercel/project.json 이 없으면 vercel 이 **새 프로젝트**를 만들어서
#   안정 주소(dist-phi-jet-62)가 아닌 낯선 주소로 올라간다.
#   ★vercel.json 은 2026-08-12 부터 여기서 지키지 않는다. 정본이 tools/deploy_config/
#     로 올라가 git 이 지키고, 아래에서 매번 새로 복사한다(캐시 헤더가 git 밖에 있어서
#     이 목록 한 줄에 목숨이 달려 있던 상태를 끝낸다).
KEEP_CONFIG = [".vercel", ".gitignore"]

# 배포 설정 정본. dist 는 굽을 때마다 지워지므로 여기서 매번 복사한다.
CONFIG_SRC = os.path.join(ROOT, "tools", "deploy_config")

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

# ── glb 내용 해시를 dist 의 js 에 박는다 ──────────────────────────────────
# 배포에 실린 glb 를 **복사가 끝난 뒤** 실제 파일로 잰다. 원본(web/)이 아니라 dist/ 를
# 재는 이유: 배포되는 바이트와 표가 어긋날 여지를 없앤다(사이에 필터가 하나 있다).
MARK = "const GLB_VER = {};"


def md5_8(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:8]


ver = {}
for dirpath, dirnames, filenames in os.walk(DST):
    if os.path.relpath(dirpath, DST).split(os.sep)[0] in (".vercel",):
        continue
    for fn in filenames:
        if not fn.endswith(".glb"):
            continue
        p = os.path.join(dirpath, fn)
        # 키는 web/ 기준 상대경로다. 'basic2.glb' / 'props/tree.glb' / 'props/low/tree.glb'
        # (파일 이름만 쓰면 props/ 와 props/low/ 가 부딪힌다)
        ver[os.path.relpath(p, DST).replace(os.sep, "/")] = md5_8(p)

table = "const GLB_VER = " + json.dumps(ver, sort_keys=True, separators=(",", ":")) + ";"
stamped = []
for dirpath, dirnames, filenames in os.walk(DST):
    for fn in filenames:
        if not fn.endswith(".js"):
            continue
        p = os.path.join(dirpath, fn)
        with open(p, encoding="utf-8") as f:
            js = f.read()
        if MARK not in js:
            continue
        with open(p, "w", encoding="utf-8") as f:
            f.write(js.replace(MARK, table))
        stamped.append(os.path.relpath(p, DST))

# ★표식이 사라지면 배포본이 조용히 무버전으로 돌아간다(= 옛 캐시 사고 재발).
#   그러느니 빌드가 죽는 게 낫다.
for must in ("main.js", "level.js"):
    assert must in stamped, must + " 에 '" + MARK + "' 표식이 없다. 캐시 버저닝이 깨진다"

# ── 배포 설정 복사 ────────────────────────────────────────────────────────
for fn in sorted(os.listdir(CONFIG_SRC)):
    shutil.copy2(os.path.join(CONFIG_SRC, fn), os.path.join(DST, fn))

print("복사 %d개 / %.1f MB" % (n, total / 1048576))
print("캐릭터:", KEEP_CHARS)
print("glb 버전 %d개 -> %s" % (len(ver), ", ".join(stamped)))
print("배포 설정:", ", ".join(sorted(os.listdir(CONFIG_SRC))))
print("->", DST)
