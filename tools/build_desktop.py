# -*- coding: utf-8 -*-
"""설치형 데스크톱 앱(스팀식)을 한 방에 굽는다.

    python3 tools/build_desktop.py            # 맥 .app + .dmg
    python3 tools/build_desktop.py --win      # 윈도우 설치본(.exe) + zip
    python3 tools/build_desktop.py --all      # 맥 + 윈도우
    python3 tools/build_desktop.py --dir      # 포장 없이 .app 만(빠름, 개발 확인용)
    python3 tools/build_desktop.py --skip-web # dist/ 재생성 없이 지금 dist 를 그대로 담는다

공정
    1) tools/build_deploy.py 를 돌려 dist/ 를 새로 굽는다 (웹 배포본과 **같은 파이프라인**)
    2) dist/ -> desktop/game/ 으로 복사한다 (배포 설정 파일은 뺀다)
    3) desktop/ 에서 electron-builder 를 돌린다 -> desktop/out/

★게임 자산을 웹과 갈라 놓지 않는다. 웹판과 화질·내용이 같아야 한다는 게 전제라
  중간에 압축하거나 덜어내는 단계를 넣지 않았다. dist 를 통째로 담는다.
★web/ 은 읽지도 않는다. 자산의 출처는 오로지 dist/ 다(build_deploy.py 소관).
"""
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
DESKTOP = os.path.join(ROOT, "desktop")
GAME = os.path.join(DESKTOP, "game")
OUT = os.path.join(DESKTOP, "out")

# dist 에는 있지만 앱에 실을 이유가 없는 것들(전부 웹 배포 설정이다)
SKIP_TOP = {".vercel", "vercel.json", ".gitignore", ".DS_Store"}

args = sys.argv[1:]
WANT_WIN = "--win" in args or "--all" in args
WANT_MAC = "--mac" in args or "--all" in args or not WANT_WIN
DIR_ONLY = "--dir" in args
SKIP_WEB = "--skip-web" in args


def run(cmd, cwd=None, env=None):
    print("\n$ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, env=env)
    if r.returncode != 0:
        sys.exit("실패: " + " ".join(cmd))


def dirsize(p):
    n = 0
    for dp, _dn, fns in os.walk(p):
        for fn in fns:
            fp = os.path.join(dp, fn)
            if not os.path.islink(fp):
                n += os.path.getsize(fp)
    return n


def mb(n):
    return "%.1f MB" % (n / 1048576.0)


t0 = time.time()

# ── 1) 웹 배포본 굽기 ─────────────────────────────────────────────────────────
if SKIP_WEB:
    print("[1/3] dist/ 재생성 건너뜀 (--skip-web)")
    if not os.path.isdir(DIST):
        sys.exit("dist/ 가 없다. --skip-web 을 빼고 돌려라.")
else:
    print("[1/3] dist/ 굽는 중 (tools/build_deploy.py)")
    run([sys.executable, os.path.join(ROOT, "tools", "build_deploy.py")], cwd=ROOT)

# ── 2) dist -> desktop/game ─────────────────────────────────────────────────
print("\n[2/3] dist/ -> desktop/game/ 복사")
if os.path.isdir(GAME):
    shutil.rmtree(GAME)
os.makedirs(GAME)
n = 0
for name in sorted(os.listdir(DIST)):
    if name in SKIP_TOP:
        continue
    src = os.path.join(DIST, name)
    dst = os.path.join(GAME, name)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    n += 1
if not os.path.isfile(os.path.join(GAME, "index.html")):
    sys.exit("game/index.html 이 없다. dist/ 를 확인해라.")
print("항목 %d개 / %s" % (n, mb(dirsize(GAME))))

# ── 3) electron-builder ─────────────────────────────────────────────────────
print("\n[3/3] electron-builder")
if not os.path.isdir(os.path.join(DESKTOP, "node_modules")):
    print("node_modules 가 없다. npm install 부터 돌린다(desktop/ 안에서만).")
    run(["npm", "install", "--no-audit", "--no-fund"], cwd=DESKTOP)

env = dict(os.environ)
# ★맥 정식 서명은 안 한다(로컬 실행용). 개발자 인증서를 자동으로 찾아 쓰다가
#   만료·불일치로 빌드가 통째로 죽는 사고를 막는다. 대신 아래에서 ad-hoc 서명을
#   직접 붙인다. 스팀·배포 단계에서 정식 서명·공증으로 바꾼다(docs/desktop.md).
env["CSC_IDENTITY_AUTO_DISCOVERY"] = "false"

APP_ASCII = "SwordGame.app"   # electron-builder 가 만드는 이름(productName)
APP_KR = "검 게임.app"          # 오너가 파인더에서 볼 이름

if WANT_MAC:
    # ── 맥은 2단이다 ──────────────────────────────────────────────────────
    # ①.app 만 굽고 ②ad-hoc 서명하고 ③한글 이름으로 바꾼 뒤 ④그걸로 dmg 를 만다.
    # 한 번에 못 하는 이유가 둘 있다.
    #   ★productName 을 한글로 두면 헬퍼 앱 이름까지 한글이 되고, 그러면 맥 빌드가
    #     실행 즉시 SIGTRAP 으로 죽는다(ready 도 못 간다). 그래서 ASCII 로 굽고
    #     **번들 이름만** 나중에 바꾼다. 번들 이름은 서명에 안 묶여서 바꿔도 검증이 통과한다.
    #   ★electron-builder 가 서명을 건너뛴다(인증서가 없으니까). 서명이 없으면
    #     arm64 맥에서 앱이 안 뜬다. dmg 를 말기 **전에** 서명해야 dmg 안엣것도 성하다.
    run(["npx", "--no-install", "electron-builder", "--dir", "--mac", "--arm64"],
        cwd=DESKTOP, env=env)

    macdir = os.path.join(OUT, "mac-arm64")
    src = os.path.join(macdir, APP_ASCII)
    dst = os.path.join(macdir, APP_KR)
    if not os.path.isdir(src) and os.path.isdir(dst):
        src = dst   # 이미 바뀐 뒤라면 그대로 쓴다
    run(["codesign", "--force", "--deep", "--sign", "-", src])
    run(["codesign", "--verify", "--deep", "--strict", src])
    if src != dst:
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        os.rename(src, dst)
        print("이름 바꿈:", APP_ASCII, "->", APP_KR)

    if not DIR_ONLY:
        # ★dmg 안에 들어갈 앱 이름도 한글이라야 한다. --prepackaged 는 앱을 다시 굽지 않고
        #   productName 으로 **이름만** 지어 담으므로, 이 단계에서만 한글 이름을 준다.
        #   (앱 속 CFBundleName 은 ASCII 그대로다. 그게 죽고 사는 갈림길이다.)
        run(["npx", "--no-install", "electron-builder", "--mac", "dmg", "--arm64",
             "--prepackaged", dst, "-c.productName=검 게임"], cwd=DESKTOP, env=env)

if WANT_WIN:
    # 윈도우는 이 맥에서 교차 빌드한다. nsis 도구는 electron-builder 가 맥용 바이너리로
    # 받아 쓰므로 wine 이 없어도 대개 된다. 막히면 zip 만 나온다(docs/desktop.md).
    cmd = ["npx", "--no-install", "electron-builder", "--win", "--x64"]
    if DIR_ONLY:
        cmd.append("--dir")
    run(cmd, cwd=DESKTOP, env=env)

# ── 보고 ────────────────────────────────────────────────────────────────────
print("\n== 산출물 (%s) ==" % OUT)
if os.path.isdir(OUT):
    for name in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, name)
        if name.endswith(".app") or (os.path.isdir(p) and not name.startswith(".")):
            print("  %-46s %s" % (name + "/", mb(dirsize(p))))
        elif os.path.isfile(p) and not name.endswith((".yml", ".yaml", ".blockmap")):
            print("  %-46s %s" % (name, mb(os.path.getsize(p))))
print("\n%.0f초 걸렸다." % (time.time() - t0))
