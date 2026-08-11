# -*- coding: utf-8 -*-
"""탱커(Crimson Centurion)에 로마 스쿠툼을 만들어 왼팔에 붙이고 web/tank.glb 를 다시 굽는다.

설계
  세로로 긴 직사각형을 원통으로 휜 판 + 금색 테두리 + 은색 보스 + 세로 문양 2줄.
  왼손 뼈(Bip001 L Hand)에 웨이트 1.0 으로 묶는다(칼 붙이는 방식과 동일, s6_export_game.py).

★크기는 전부 실측에서 나온 비율이다(눈대중 금지).
  키 1.700 / 왼손 REST (0.616, 0.014, 1.209) / 팔뚝 0.222(키의 13.0%).

★배치를 REST(T포즈)에서 눈대중으로 잡으면 안 된다
  방패는 손 뼈에 강체로 붙으므로, **가장 오래 보이는 포즈(Idle)** 에서 똑바로 서도록
  맞춰야 한다. 그래서 아래 순서를 쓴다.
    1) POSE + Idle 프레임에서 손 뼈 행렬 M_idle 을 읽는다
    2) "Idle 때 이렇게 보였으면 좋겠다"는 월드 행렬 target 을 만든다(수직 + 정면)
    3) 손 로컬 오프셋 L = M_idle⁻¹ @ target 을 구한다
    4) REST 로 되돌려 M_rest 를 읽고, 지오메트리를 M_rest @ L 위치에 굽는다
  스키닝(웨이트 1.0)이 M_idle @ M_rest⁻¹ 를 곱해주므로 Idle 에서 정확히 target 이 된다.
  (초안은 REST 팔 방향으로 basis 를 만들어 T포즈 기준으로 세웠다. T포즈에서만 맞고
   실제 애니에서는 방패가 눕는다. 그게 초안의 결정적 오류였다.)

★좌표계(프로젝트 규약): glTF -> Blender 임포트 후 정면 = -Y, 위 = +Z, 캐릭터 오른쪽 = -X.
  방패 로컬축도 그 Idle 목표와 같게 잡았다. +X = 캐릭터의 왼쪽(바깥), +Y = 뒤, +Z = 위.
  따라서 볼록면(적 방향)은 -Y 를 본다.

★머티리얼은 cel_mat 을 안 쓴다
  build_scenes.cel_mat 은 Diffuse+ShaderToRGB+Emission 노드 구성이라 glTF 로 안 나간다
  (s6_export_game.py 가 내보내기 직전에 Principled 로 갈아끼우는 이유가 이것).
  게임(main.js)은 어차피 MeshToonMaterial 로 갈아끼우고 베이스 컬러만 읽으므로
  처음부터 단순 Principled 로 만든다.

이 스크립트 한 번이면 **방패 부착 + 왼팔 캐리 자세 굽기 + export** 가 전부 끝난다.
중간 산출물(방패만 붙은 glb 같은 것)에 의존하지 않는다. 항상 tank.glb.bak 에서 시작.

실행: blender --background --python s10_shield.py
환경변수로 미세조정: SH_DX/SH_DY/SH_DZ(오프셋 m), SH_YAW(도),
                    SH_CARRY_W(왼팔 고정 강도 0~1), SH_OUT(시험용 출력 경로)
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import carry_pose as CP                       # noqa: E402

OUT_DEFAULT = os.path.join(WEB, "tank.glb")
# 가중치 비교처럼 시험 삼아 구울 때만 SH_OUT 으로 딴 데 뺀다(정상 실행은 tank.glb).
OUT = os.environ.get("SH_OUT", OUT_DEFAULT)
# ★이미 방패가 붙은 glb 를 다시 읽으면 방패가 두 개가 된다.
#   그래서 항상 **방패 없는 원본 백업**을 읽는다. s9_meshy.py 로 몸을 다시 구웠다면
#   tank.glb.bak 을 새 원본으로 갱신할 것(안 하면 옛 몸에 방패를 붙여 덮어쓴다).
SRC = os.path.join(WEB, "tank.glb.bak")
if not os.path.exists(SRC):
    SRC = OUT_DEFAULT

IDLE_F = 17          # Idle 은 f1~f50 이 거의 동일(숨쉬기만) - 중간 프레임 하나면 충분
BONE = "Bip001 L Hand"


def env(k, d):
    try:
        return float(os.environ.get(k, d))
    except Exception:
        return d


# ---------------------------------------------------------------- 로드
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
print("원본:", SRC)
print("read_homefile 직후 오브젝트:", [o.name for o in sc.objects])
bpy.ops.import_scene.gltf(filepath=SRC)
print("임포트 후 오브젝트:", [(o.name, o.type) for o in sc.objects])

arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = next(o for o in sc.objects if o.type == "MESH" and o.name.startswith("char"))
# 임포트와 무관하게 씬에 섞여 있는 잡 메시(Icosphere 등)는 내보내기 전에 치운다.
for o in list(sc.objects):
    if o.type == "MESH" and o is not body:
        print("잡 메시 제거:", o.name)
        bpy.data.objects.remove(o, do_unlink=True)

for a in bpy.data.actions:
    a.use_fake_user = True     # ★참조 없는 액션은 export 에서 빠진다
print("액션:", [a.name for a in bpy.data.actions])

A2W = arm.matrix_world
if arm.animation_data is None:
    arm.animation_data_create()


def pose_bone(name):
    return arm.pose.bones[name]


# ---------------------------------------------------------------- 실측
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
ws = [body.matrix_world @ v.co for v in body.data.vertices]
H = max(p.z for p in ws) - min(p.z for p in ws)
M_rest = A2W @ pose_bone(BONE).matrix
hand_r = M_rest.translation.copy()
elb_r = (A2W @ pose_bone("Bip001 L Forearm").matrix).translation
sho_r = (A2W @ pose_bone("Bip001 L UpperArm").matrix).translation
print("[실측] 키 %.4f" % H)
print("[실측] REST 어깨(%.3f,%.3f,%.3f) 팔꿈치(%.3f,%.3f,%.3f) 손(%.3f,%.3f,%.3f)"
      % (sho_r.x, sho_r.y, sho_r.z, elb_r.x, elb_r.y, elb_r.z,
         hand_r.x, hand_r.y, hand_r.z))
print("[실측] 위팔 %.4f(키의 %.1f%%)  팔뚝 %.4f(키의 %.1f%%)"
      % ((elb_r - sho_r).length, (elb_r - sho_r).length / H * 100,
         (hand_r - elb_r).length, (hand_r - elb_r).length / H * 100))

# ---------------------------------------------------------------- 치수 결정
# 실제 스쿠툼: 높이 약 사람 키의 55%, 폭(호 길이)은 높이의 56%.
SH_H = H * 0.55                    # 방패 높이
SH_ARC = SH_H * 0.56               # 판을 편 길이(호)
R = SH_ARC * 0.76                  # 원통 반지름 - 실물 스쿠툼의 휨 정도
A_MAX = (SH_ARC / 2) / R           # 반각
CHORD = 2 * R * math.sin(A_MAX)    # 정면에서 본 실제 폭
DEPTH = R * (1 - math.cos(A_MAX))  # 휨 깊이
THICK = H * 0.011                  # 판 두께
print("[치수] 높이 %.4f(키의 %.1f%%)  호 %.4f  정면폭 %.4f(높이의 %.1f%%)"
      % (SH_H, SH_H / H * 100, SH_ARC, CHORD, CHORD / SH_H * 100))
print("[치수] 반지름 %.4f 반각 %.1f도 휨깊이 %.4f 두께 %.4f"
      % (R, math.degrees(A_MAX), DEPTH, THICK))

# ---------------------------------------------------------------- Idle 기준 목표 자세
arm.data.pose_position = "POSE"
idle = bpy.data.actions["Idle"]
arm.animation_data.action = idle
try:
    slots = list(getattr(idle, "slots", []))
    if slots:
        arm.animation_data.action_slot = slots[0]
except Exception as ex:
    print("action_slot 지정 실패(구버전이면 무시):", ex)
sc.frame_set(IDLE_F)
bpy.context.view_layer.update()

M_idle = A2W @ pose_bone(BONE).matrix
hand_i = M_idle.translation.copy()
elb_i = (A2W @ pose_bone("Bip001 L Forearm").matrix).translation
print("[Idle] 손(%.3f,%.3f,%.3f) 팔꿈치(%.3f,%.3f,%.3f)"
      % (hand_i.x, hand_i.y, hand_i.z, elb_i.x, elb_i.y, elb_i.z))

# 몸이 방패를 뚫는지 실제로 계산해서 가로 오프셋을 정한다(눈대중 금지).
# 왼팔에 실린 버텍스는 뺀다. 팔은 원래 방패 뒤에 있어야 하므로 기준이 아니다.
# 쇄골(Clavicle)은 빼면 안 된다. 가슴 갑옷이 쇄골에 실려 있어서 같이 빠지면
# "몸통이 방패를 뚫는지" 검사가 가슴을 통째로 놓친다.
ARM_G = [g.index for g in body.vertex_groups
         if g.name in ("Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand")]
skip = set()
for v in body.data.vertices:
    for g in v.groups:
        if g.group in ARM_G and g.weight > 0.15:
            skip.add(v.index)
            break
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg)
me_ev = ev.to_mesh()
BODY, LARM = [], []
for i, v in enumerate(me_ev.vertices):
    p = body.matrix_world @ v.co
    if (p - hand_i).length > 1.0:      # 방패가 닿을 수 없는 곳은 애초에 뺀다(속도)
        continue
    (LARM if i in skip else BODY).append((p.x, p.y, p.z))
ev.to_mesh_clear()
print("[실측] Idle 근처 버텍스 - 몸통 %d개 / 왼팔 %d개" % (len(BODY), len(LARM)))


SLAB = -0.09          # 판 앞면보다 9cm 이상 앞이면 "뚫은 것"이 아니라 그냥 방패보다 앞


def hits_of(pts, dx, dy, dz, yaw):
    """방패를 뚫고 나온 지점들. (깊이, 월드좌표) 목록.

    ★판정 기준을 두 번 고쳐서 여기까지 왔다. 남겨 둔다.
      1) 같은 x 에서 y 비교(평면 근사) -> 가장자리가 뒤로 말리는 스쿠툼에는 안 맞다.
      2) 곡률중심 기준 각도로 덮이는지 판정 -> 앞으로 내디딘 다리처럼 **방패보다 훨씬
         앞에 있는 것**까지 전부 관통으로 잡혔다(쐐기가 무한히 뻗으므로).
      3) 지금: 가림 여부는 판의 실제 가로/세로 범위로, 깊이는 곡률중심 거리로,
         그리고 판 앞 9cm 밖은 제외. 이게 눈으로 본 것과 일치한다."""
    px, py, pz = hand_i.x + dx, hand_i.y - dy, hand_i.z + dz
    c, s = math.cos(yaw), math.sin(yaw)
    inner = R - THICK
    out = []
    for (x, y, z) in pts:
        lz = z - pz
        if lz > SH_H / 2 or lz < -SH_H / 2:
            continue
        ax, ay = x - px, y - py
        lx = c * ax + s * ay
        if abs(lx) > CHORD / 2:
            continue                    # 판 옆 = 안 가림
        ly = -s * ax + c * ay
        if ly < SLAB:
            continue                    # 방패보다 한참 앞 = 관통 아님
        d = math.hypot(lx, R - ly)
        if d > inner:
            out.append((d - inner, x, y, z))
    return out


def pierce(pts, dx, dy, dz, yaw):
    h = hits_of(pts, dx, dy, dz, yaw)
    return len(h), (max(v[0] for v in h) if h else 0.0)


def where(tag, pts, dx, dy, dz, yaw_d):
    """어떤 부위가 방패를 뚫는지 찍어 본다(막힌 원인을 눈대중으로 넘기지 않으려고)."""
    hits = hits_of(pts, dx, dy, dz, math.radians(yaw_d))
    hits.sort(reverse=True)
    if not hits:
        print("   [%s] DX%+.2f DY%.2f DZ%+.2f YAW%2d -> 관통 0" % (tag, dx, dy, dz, yaw_d))
        return
    print("   [%s] DX%+.2f DY%.2f DZ%+.2f YAW%2d -> %d개, z %.2f~%.2f, 최악 %.3f @ (%.3f,%.3f,%.3f)"
          % (tag, dx, dy, dz, yaw_d, len(hits),
             min(h[3] for h in hits), max(h[3] for h in hits),
             hits[0][0], hits[0][1], hits[0][2], hits[0][3]))


def hand_gap(dx, dy, dz, yaw):
    """손 중심에서 방패 안쪽(오목) 면까지의 거리와, 손이 보스에서 벗어난 정도.
    떠 있으면 방패가 공중에 뜬 것처럼 보이고, 보스에서 벗어나면 센터그립이 아니라
    가장자리를 쥔 것처럼 보인다. 둘 다 어색하므로 둘 다 잰다."""
    c, s = math.cos(yaw), math.sin(yaw)
    ax, ay = -dx, dy
    lx = c * ax + s * ay
    ly = -s * ax + c * ay
    return (R - THICK) - math.hypot(lx, R - ly), lx


# 배치 후보 탐색(고정 목록, 무한 루프 없음).
#  DX 가로(+ = 몸 바깥) / DY 앞 / DZ 위 / YAW 바깥으로 튼 각도
#  이 탐색은 **제약이 어디에서 걸리는지 보려고** 돌린다. 최종값은 아래에서 렌더를 보고
#  고정한다. 후보들의 비용이 좁은 구간에 몰려 1등이 격자 끝으로만 밀렸기 때문이다.
#  (팔이 몸 옆에 내려온 Idle 이라 "몸 안 뚫기 / 손에 붙이기 / 정면 보기" 셋이 동시에
#   성립하지 않는다. 어느 하나를 포기해야 하고, 그 판단은 눈이 해야 한다.)
TOL_BODY, TOL_ARM = 0.008, 0.012      # 8mm/12mm 겹침은 눈에 안 띈다
print("[진단] 후보 몇 개를 찍어 무엇이 막는지 본다")
for a in ((0.14, 0.07, 0.02, 0), (0.16, 0.07, 0.02, 24)):
    where("몸통", BODY, *a)
    where("왼팔", LARM, *a)
GAP_MAX = 0.17        # 손잡이 막대로 이을 수 있는 한계. 이보다 뜨면 방패가 공중에 뜬다
best = []
for yaw_d in (0, 8, 16, 24, 32):
    for dy in (0.06, 0.09, 0.12, 0.15, 0.18):
        for dz in (0.02, -0.04, -0.10):
            for k in range(12):
                dx = 0.02 + 0.02 * k
                yaw = math.radians(yaw_d)
                cb, wb = pierce(BODY, dx, dy, dz, yaw)
                if wb > TOL_BODY:
                    continue
                ca, wa = pierce(LARM, dx, dy, dz, yaw)
                if wa > TOL_ARM:
                    continue
                gap, hlx = hand_gap(dx, dy, dz, yaw)
                if gap > GAP_MAX:
                    continue
                bottom = hand_i.z + dz - SH_H / 2
                # ★손과 방패 사이는 실제 스쿠툼처럼 **손잡이 막대**로 잇는다.
                #   그래서 뜬 거리 자체보다 "손이 보스에서 벗어난 정도"와
                #   "정면을 안 보는 각도"에 더 무게를 준다.
                cost = (2.0 * max(0.0, gap)
                        + 4.0 * abs(hlx)             # 손이 보스에서 좌우로 벗어난 정도
                        + 1.4 * yaw                  # 정면을 덜 보는 각도
                        + 0.9 * abs(dz)
                        + 1.5 * max(0.0, 0.26 - bottom))   # 바닥에 끌리는 정도
                best.append((cost, dx, dy, dz, yaw_d, gap, hlx, wb, wa))
best.sort()
print("[탐색] 조건 통과 %d개. 상위 8개:" % len(best))
for b in best[:8]:
    print("   비용 %.3f  DX %+.2f DY %.3f DZ %+.2f YAW %2d도  손틈 %.3f 손좌우 %+.3f 몸%.3f 팔%.3f"
          % (b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7], b[8]))
seen = set()
print("[탐색] YAW 각도별 최선:")
for b in best:
    if b[4] in seen:
        continue
    seen.add(b[4])
    print("   YAW %2d도 -> 비용 %.3f DX %+.2f DY %.3f DZ %+.2f 손틈 %.3f 손좌우 %+.3f"
          % (b[4], b[0], b[1], b[2], b[3], b[5], b[6]))
# ★최종값은 위 탐색의 1등이 아니라 **렌더를 보고** 고른 것이다.
#   비용함수는 여러 후보가 1.3~1.5 로 몰려 우열이 없었고, 격자 끝으로만 밀렸다.
#   눈으로 보니 "손이 보스 정중앙(손좌우 0.001) + 몸 안 뚫음 + 정면에서 방패가 잘 보임"
#   조합이 가장 자연스러웠다. 탐색 출력은 제약이 어떻게 생겼는지 남기려고 유지한다.
#   YAW 32도는 바깥으로 튼 각도. 팔이 몸 옆으로 내려온 Idle 에서 스쿠툼의 말린
#   안쪽 모서리가 몸을 안 뚫으려면 이만큼은 틀어야 한다(0도로 두면 앞으로 20cm 가까이
#   밀어야 하고, 그러면 손에서 떠 버린다).
DX, DY, DZ, YAW_D = 0.08, 0.13, 0.02, 32
if not best:
    print("!! 조건 통과 없음 - 고정값 그대로 사용")
DX = env("SH_DX", DX)
DY = env("SH_DY", DY)
DZ = env("SH_DZ", DZ)
YAW = math.radians(env("SH_YAW", YAW_D))
print("[배치] DX %.3f DY %.3f DZ %.3f YAW %.1f도"
      % (DX, DY, DZ, math.degrees(YAW)))

P = Vector((hand_i.x + DX, hand_i.y - DY, hand_i.z + DZ))
target = Matrix.Translation(P) @ Matrix.Rotation(YAW, 4, "Z")
L = M_idle.inverted() @ target        # 손 뼈 로컬 오프셋

# 손이 방패 뒤 어디쯤에 있는지(중앙 = 센터그립이 자연스럽다). 손잡이 막대가 여기까지 온다.
HL = target.inverted() @ hand_i
print("[검산] Idle 에서 손의 방패 로컬좌표 (%.3f, %.3f, %.3f)  판 반폭 %.3f"
      % (HL.x, HL.y, HL.z, CHORD / 2))

arm.data.pose_position = "REST"
bpy.context.view_layer.update()
M_rest = A2W @ pose_bone(BONE).matrix
FINAL = M_rest @ L
print("[배치] Idle 목표 원점 (%.3f,%.3f,%.3f) / REST 에 구울 원점 (%.3f,%.3f,%.3f)"
      % (P.x, P.y, P.z, FINAL.translation.x, FINAL.translation.y,
         FINAL.translation.z))

# ---------------------------------------------------------------- 지오메트리
# 모디파이어(Solidify)를 쓰지 않고 앞면/뒷면/옆면을 직접 만든다.
# 배경 실행에서 modifier_apply 는 컨텍스트를 타는 데다, 감기(winding)를 내가
# 통제해야 앞면이 뒤집히지 않는다(three.js 기본이 FrontSide 라 뒤집히면 사라진다).
V, F, MI, SM = [], [], [], []


def cyl(x, z, out=0.0):
    """원통 표면 위의 점. out>0 이면 앞(볼록쪽)으로 더 나온다."""
    r = R + out
    x = max(-r * 0.999, min(r * 0.999, x))
    return (x, R - math.sqrt(r * r - x * x), z)


def quad(a, b, c, d, mi, sm):
    F.append((a, b, c, d))
    MI.append(mi)
    SM.append(sm)


def tri(a, b, c, mi, sm):
    F.append((a, b, c))
    MI.append(mi)
    SM.append(sm)


NIN, NJ = 8, 4               # 안쪽 격자(가로 8칸, 세로 4칸) + 테두리 각 1칸
a_in = A_MAX * 0.91
cols = [-A_MAX] + [-a_in + 2 * a_in * k / NIN for k in range(NIN + 1)] + [A_MAX]
z_in = 0.5 * SH_H * 0.91
rows = ([-0.5 * SH_H] + [-z_in + 2 * z_in * k / NJ for k in range(NJ + 1)]
        + [0.5 * SH_H])
NC, NR = len(cols) - 1, len(rows) - 1

front, back = [], []
for i, a in enumerate(cols):
    fc, bc = [], []
    for z in rows:
        fc.append(len(V))
        V.append((R * math.sin(a), R - R * math.cos(a), z))
        bc.append(len(V))
        rb = R - THICK
        V.append((rb * math.sin(a), R - rb * math.cos(a), z))
    front.append(fc)
    back.append(bc)

for i in range(NC):
    for j in range(NR):
        rim = (i == 0 or i == NC - 1 or j == 0 or j == NR - 1)
        mi = 1 if rim else 0
        # 앞면: +x -> +z 순서면 법선이 -y(정면)
        quad(front[i][j], front[i + 1][j], front[i + 1][j + 1], front[i][j + 1],
             mi, True)
        # 뒷면: 반대로 감아 법선이 +y
        quad(back[i][j], back[i][j + 1], back[i + 1][j + 1], back[i + 1][j],
             mi, True)
# 옆면(테두리 두께). 전부 금색.
for i in range(NC):
    quad(front[i][NR], front[i + 1][NR], back[i + 1][NR], back[i][NR], 1, False)
    quad(front[i][0], back[i][0], back[i + 1][0], front[i + 1][0], 1, False)
for j in range(NR):
    quad(front[NC][j], back[NC][j], back[NC][j + 1], front[NC][j + 1], 1, False)
    quad(front[0][j], front[0][j + 1], back[0][j + 1], back[0][j], 1, False)

# ---- 보스(가운데 은색 돌기) ----
NB = 12
RB = CHORD * 0.18
y0 = -0.002                     # 판 표면보다 아주 조금 앞
base, mid = [], []
for k in range(NB):
    t = 2 * math.pi * k / NB
    x, z = RB * math.cos(t), RB * math.sin(t)
    base.append(len(V))
    V.append(cyl(x, z, 0.002))
    mid.append(len(V))
    V.append((x * 0.60, y0 - RB * 0.42, z * 0.60))
apex = len(V)
V.append((0.0, y0 - RB * 0.66, 0.0))
for k in range(NB):
    n = (k + 1) % NB
    quad(base[k], base[n], mid[n], mid[k], 2, True)
    tri(mid[k], mid[n], apex, 2, True)

# ---- 손잡이(가로 막대) + 보스 뒤 받침 ----
# ★실물 스쿠툼은 보스 뒤의 가로 막대를 주먹으로 쥔다. 팔이 몸 옆으로 내려온 Idle 에서는
#   방패를 몸 앞으로 빼야 몸을 안 뚫는데, 그러면 손과 판 사이가 뜬다.
#   그 사이를 손잡이로 잇는 것이 실제 구조이자 "떠 보임"의 해결책이다.
def box(x0, x1, y0, y1, z0, z1, mi):
    n = len(V)
    for (x, y, z) in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                      (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)):
        V.append((x, y, z))
    quad(n + 1, n + 2, n + 6, n + 5, mi, False)   # +x
    quad(n + 0, n + 4, n + 7, n + 3, mi, False)   # -x
    quad(n + 0, n + 1, n + 5, n + 4, mi, False)   # -y(앞)
    quad(n + 3, n + 7, n + 6, n + 2, mi, False)   # +y(뒤)
    quad(n + 4, n + 5, n + 6, n + 7, mi, False)   # +z
    quad(n + 0, n + 3, n + 2, n + 1, mi, False)   # -z


GX, GY, GZ = HL.x, HL.y, HL.z
y_shell = R - math.sqrt(max(0.0, R * R - GX * GX)) + THICK   # 그 x 에서 판 안쪽 면
bar_y0, bar_y1 = GY - 0.013, GY + 0.013
box(GX - 0.075, GX + 0.075, bar_y0, bar_y1, GZ - 0.013, GZ + 0.013, 2)  # 쥐는 막대
if bar_y0 - y_shell > 0.006:                                  # 뜬 만큼만 받침을 세운다
    box(GX - 0.030, GX + 0.030, y_shell, bar_y0 + 0.004,
        GZ - 0.024, GZ + 0.024, 1)
print("[결과] 손잡이 막대 로컬 (%.3f,%.3f,%.3f), 판 안쪽면 y %.3f, 받침 길이 %.3f"
      % (GX, GY, GZ, y_shell, max(0.0, bar_y0 - y_shell)))

# ---- 세로 문양 띠 2줄(금색) ----
BW = CHORD * 0.045
for sgn in (-1, 1):
    xb = sgn * CHORD * 0.28
    zt = SH_H * 0.40
    p = [len(V) + n for n in range(4)]
    V.append(cyl(xb - BW / 2, -zt, 0.004))
    V.append(cyl(xb + BW / 2, -zt, 0.004))
    V.append(cyl(xb + BW / 2, zt, 0.004))
    V.append(cyl(xb - BW / 2, zt, 0.004))
    quad(p[0], p[1], p[2], p[3], 1, False)

# 로컬 -> 월드(REST 기준)로 구워 넣는다
VW = [FINAL @ Vector(v) for v in V]

me = bpy.data.meshes.new("SH_scutum")
me.from_pydata([tuple(v) for v in VW], [], F)
me.validate(verbose=False)
for k, p in enumerate(me.polygons):
    p.material_index = MI[k]
    p.use_smooth = SM[k]
me.update()


def mat(name, hexs):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    h = hexs.lstrip("#")
    c = tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))
    b.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1.0)
    b.inputs["Roughness"].default_value = 0.9 if name.endswith("plate") else 0.45
    b.inputs["Metallic"].default_value = 0.0
    nt.links.new(b.outputs[0], o.inputs[0])
    return m


me.materials.append(mat("SH_plate", "8E2B2B"))    # 붉은 판(Crimson Centurion)
me.materials.append(mat("SH_rim", "C8A24A"))      # 금 테두리 + 문양
me.materials.append(mat("SH_boss", "D8D4CC"))     # 은 보스

shield = bpy.data.objects.new("SH_scutum", me)
sc.collection.objects.link(shield)
shield.matrix_world = Matrix()                    # 정점이 이미 월드 좌표

vg = shield.vertex_groups.new(name=BONE)
vg.add(range(len(me.vertices)), 1.0, "REPLACE")
md = shield.modifiers.new("Armature", "ARMATURE")
md.object = arm

tri_n = sum(len(p.vertices) - 2 for p in me.polygons)
bb = [Vector(c) for c in shield.bound_box]
print("[결과] SH_scutum  버텍스 %d  면 %d  삼각형 %d"
      % (len(me.vertices), len(me.polygons), tri_n))
print("[결과] REST 바운딩 x %.3f~%.3f  y %.3f~%.3f  z %.3f~%.3f"
      % (min(p.x for p in VW), max(p.x for p in VW),
         min(p.y for p in VW), max(p.y for p in VW),
         min(p.z for p in VW), max(p.z for p in VW)))

# ------------------------------------------------- 왼팔 캐리 자세(Walk/Run)
# ★Meshy 원본 달리기는 **맨손 기준**이라 양팔을 크게 휘두른다. 방패는 손 뼈에 강체로
#   붙으므로 그 스윙을 그대로 받아 머리 위로 들린다(실측: Run f09 에서 방패 최고점이
#   어깨보다 +37.9cm). 현실에서 방패 든 팔은 몸 앞에 붙여 고정하고 반대팔만 흔든다.
#   그래서 **왼팔 3뼈만** Idle 의 캐리 자세 쪽으로 끌어당긴다.
#   오른팔·다리·척추·Attack·Idle 은 손대지 않는다(뛰는 느낌은 그쪽이 만든다).
#
# 가중치는 0.6/0.75/0.9/1.0 을 다 구워 보고 골랐다(probe_carry_w.py 가 그 비교 도구,
# 렌더는 renders/history/v44_carry/).
#   ★기준선을 먼저 잡아야 한다: Idle 에서도 방패 최고점은 어깨 **관절**보다 +9.6cm 다.
#     방패가 크니 당연한 값이고, 이게 "제대로 든" 상태다. 0 을 목표로 삼으면 안 된다.
#                     Run 최악 높이      Run 에 남은 손 스윙
#     w 0     +37.9cm (원본)          142도   방패가 헬멧 위로 솟음
#     w 0.60  +18.0cm (기준+8.4)       58도   렌더에서 방패가 15도쯤 기울어 턱까지 올라옴
#     w 0.75  +14.6cm (기준+5.0)       36도   아직 눈에 띄게 기울고 밑동이 정강이를 가로지름
#     w 0.90  +12.2cm (기준+2.6)       14도   렌더에서 수직. 미세한 흔들림이 남아 살아 있다
#     w 1.00  +10.7cm (기준+1.1)        0도   완전히 굳음. 0.9 와 눈으로 구분 안 됨
#   0.9 를 고른 이유: 방패 높이는 1.0 과 1.5cm 차이(1.7m 캐릭터에서 안 보임)인데
#   손에 14도의 스윙이 남아 팔이 죽지 않는다. 방패를 세우는 목적은 이미 달성됐고,
#   더 조여봐야 얻는 게 없다.
CARRY_W = env("SH_CARRY_W", 0.9)
CARRY_CLIPS = ("Walk", "Run")

arm.data.pose_position = "POSE"
bpy.context.view_layer.update()
top_of = CP.shield_sampler(arm, shield)


def carry_table(tag):
    """방패 최고점 z 와 어깨 z 의 차이. 고쳤다는 객관 증거로 남긴다(단위 cm)."""
    for clip in CARRY_CLIPS + ("Idle",):
        act = CP.use_action(arm, clip)
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        vals = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            vals.append((top_of() - CP.shoulder_z(arm)) * 100)
        print("  [%s] %-5s f%d~%d  어깨 대비 최악 %+.1fcm (f%d), 평균 %+.1fcm, 폭 %.1fcm"
              % (tag, clip, f0, f1, max(vals), f0 + vals.index(max(vals)),
                 sum(vals) / len(vals), max(vals) - min(vals)))


print("[캐리] 굽기 전")
carry_table("전")
REF = CP.read_reference(arm, "Idle", IDLE_F)     # 기준 = Idle f17 왼팔(아마추어 공간)
print("[캐리] 가중치 %.2f 로 %s 굽는다" % (CARRY_W, "/".join(CARRY_CLIPS)))
for clip in CARRY_CLIPS:
    CP.bake(arm, clip, REF, CARRY_W)
print("[캐리] 굽은 후")
carry_table("후")

# 굽는 동안 왼팔 스케일이 살아 있는지 확인한다(★과거에 손이 39배가 된 적이 있다).
for nm in CP.L_CHAIN:
    s = arm.pose.bones[nm].matrix.decompose()[2]
    print("  [검산] %-20s 스케일 (%.4f, %.4f, %.4f)" % (nm, s.x, s.y, s.z))

# ---------------------------------------------------------------- 내보내기
CP.use_action(arm, "Idle")
arm.data.pose_position = "POSE"
bpy.context.view_layer.update()
for a in bpy.data.actions:
    a.use_fake_user = True
print("내보내기 직전 액션:", [a.name for a in bpy.data.actions])
print("내보내기 직전 오브젝트:", [(o.name, o.type) for o in sc.objects])

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT, export_format="GLB", use_selection=False,
    export_animations=True, export_animation_mode="ACTIONS",
    export_nla_strips=False, export_bake_animation=True,
    export_frame_range=False, export_yup=True)
print("EXPORTED", OUT, os.path.getsize(OUT))
