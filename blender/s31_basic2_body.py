# -*- coding: utf-8 -*-
"""알몸 기본2(basic2)의 오른 주먹에 우리 칼 7자루를 꿰어 web/basic2_body.glb 를 만든다.

    blender -b -P blender/s31_basic2_body.py
    -> web/basic2_body.glb   (액션 없음. 모션은 이어서 s24_moveset.py 가 이식한다)

전체 공정 다섯 줄(이 순서대로 다시 돌리면 언제든 재현된다. 2026-08-11 실행 기록.
1~4 는 2026-08-11 재실행에서 **바이트 단위로 같은 파일**이 다시 나왔다)

    # 1) 알몸 basic2 + 칼 7자루
    blender -b -P blender/s31_basic2_body.py
    # 2) slayer 무브셋 7종 이식 (레스트 관절 각도차 5.9~10.4도. kensa 보다 작다)
    SRC_GLB=web/slayer.glb DST_GLB=web/basic2_body.glb OUT_GLB=web/basic2_moves.glb \
      DST_SWORD=SW_baekah.001 SWORD_FIT=0 GRIP_K=1.0 KEEP_ORIG=1 \
      OUTDIR=renders/history/v97_wave11/char_basic2/moveset blender -b -P blender/s24_moveset.py
    # 3) 걷기·달리기만 basic2 네이티브로 교체(+오른팔 감쇠·손목 보정)
    DST_GLB=web/basic2_moves.glb OUT_GLB=web/basic2.glb CLIPS=Walk,Run \
      NAT_DIR=incoming/meshy4/Meshy_AI_game_character_8k_biped \
      NAT_STEM=Meshy_AI_game_character_8k_biped \
      OUTDIR=renders/history/v97_wave11/char_basic2/native blender -b -P blender/s27_kensa_native.py
    # 4) 이름의 .001 떼기 (안 하면 1~7 칼 교체가 죽는다)
    python3 tools/glb_rename.py web/basic2.glb
    # 5) 오너가 준 옷(벨트+모피 치마+어깨끈) 입히기. ★4번까지는 web/basic2.glb 가
    #    **알몸**이다. 이 줄이 같은 파일을 옷 입은 것으로 제자리 교체한다
    #    (임시파일에 쓰고 os.replace. 이미 옷이 있으면 멈춘다)
    BODY_GLB=web/basic2.glb OUT_GLB=web/basic2.glb \
      OUTDIR=renders/history/v98_wave12/cloth blender -b -P blender/s33_basic2_cloth.py

  ★2번에서 GRIP_K 를 1.0 으로 둔 근거: s24 가 찍는 손 크기가 소스 0.0853 /
    타깃 0.0823 로 3.4% 차이뿐이다(kensa 는 36% 차이라 0.64 를 줬다).
  ★3번을 하는 이유는 **보폭**이다. slayer 걷기를 이식하면 발 속도가 1.09 라
    이동 1.71 을 내려고 재생속도 1.57 이 필요하고, 한 걸음이 0.30초짜리
    종종걸음이 된다. 네이티브는 발 속도 1.412 → 재생속도 1.21 로 한 걸음 0.44초다.

왜 새로 만드나 (s26 을 다시 못 쓰는 이유)
  s26_swordsman.py 는 kensa 전용이다. Meshy 가 어깨 뒤로 물려 놓은 **막대 무기를
  잘라내고 주먹 구멍을 메우는** 수술이 몸통의 절반이고, 그 좌표가 kensa 메시에
  묶여 있다. basic2 는 애초에 빈손(꽉 쥔 주먹)이라 수술할 것이 없다.
  여기서 필요한 것은 "이미 정합이 끝난 칼 7자루를 다른 Meshy 손으로 옮기는 일"뿐이다.

★칼은 새로 꽂지 않는다. **kensa 의 칼을 좌표계째 옮긴다**
  kensa 의 7자루는 s26 이 이미 slayer 레스트 월드 칼 방향에 맞춰 꽂아 둔 것이다
  (그 정합이 s24 의 SWORD_FIT 이 하는 일과 같다). 그러니 각도를 다시 고를 이유가 없다.
  옮길 때 지켜야 하는 것은 **레스트에서의 월드 방향**이다:

      v_b(손뼈로컬) = FC_b + R @ ((v_k(손뼈로컬) - FC_k) * S)
      R = Rot(HM_b)^-1 @ Rot(HM_k)        HM = 손뼈 레스트 월드행렬

  이러면 HM_b @ v_b 의 방향이 HM_k @ v_k 와 정확히 같아진다. 즉 두 캐릭터가
  레스트에서 칼을 **같은 월드 각도로** 든다. 이 성질이 있어야 이어지는 s24 의
  레스트 델타 리타게팅이 칼끝 궤적을 그대로 옮긴다(s24 가 SWORD_FIT=0 으로도
  "레스트 자루축 각도차 0.0도" 를 찍어 검산해 준다).
  ★손뼈 로컬 축은 두 리그가 서로 46~74도 어긋나 있다(실측). 그래서 손뼈 로컬
    좌표를 그냥 복사하면 칼이 딱 그만큼 돌아간 채 박힌다. R 이 그걸 되돌린다.

★크기 S = (basic2 몸 키) / (kensa 몸 키)
  게임은 캐릭터를 CHAR_CFG.h(1.75)로 정규화한다. 원본 키가 kensa 1.700 / basic2 1.500
  이라 칼을 원본 크기로 옮기면 게임 화면에서 13% 더 긴 칼이 된다. 사거리 판정이
  칼 메시 실측(measureBlade)이라 그대로 두면 basic2 만 리치가 길어진다. 그래서
  **게임 화면에서 같은 길이가 되도록** 원본 단계에서 미리 줄인다.

★자리는 주먹 중심(손뼈에 웨이트 0.5 초과인 몸 정점의 무게중심)에 맞춘다
  basic2 손은 구멍 없는 꽉 쥔 주먹이라 자루가 살을 지난다. hero(s15)·kensa(s26)에서
  이미 쓰던 관례 그대로다 — 주먹이 닫힌 덩어리면 관통해도 '쥔 것'으로 보인다.

★함정 (표준 파이프라인. 하나라도 밟으면 조용히 망가진다)
  1) fps: 임포트 **전에** 30 고정
  2) 임포트 순서: **타깃(basic2)을 먼저**. 나중에 읽으면 char1 이 char1.001 이 되어
     그대로 내보내진다
  3) 스키닝은 REST 에서 굽는다. 포즈 상태로 재면 애니에서 어긋난다
  4) Icosphere: glTF 임포터가 뼈 표시용으로 만드는 반지름 1 구. glb 엔 없다.
     안 지우면 게임이 전 메시로 박스를 재므로 키가 망가진다
  5) 게임은 SW_ 로 시작하는 메시를 키 계산에서 뺀다. 칼 이름은 반드시 SW_<키>
  6) 게임은 재질 이름 앞자리(bd_/bv_/ht_/sp_)로 발광 부위를 가른다. 재질 이름을
     건드리지 말 것(kensa 것을 그대로 데려온다)
  7) 부모를 지우기 전에 정점을 월드로 굳혀 둘 것. 지운 뒤에는 matrix_world 가 변한다

손잡이(환경변수)
  DST_GLB   몸(타깃)          기본 web/basic2_native.glb
            ★basic2.glb 는 파이프라인의 **결과물**이다(칼 7자루 + 전투 7클립).
              그걸 다시 넣으면 칼 위에 칼을 꽂는다. 그래서 s14 가 구운 알몸 원본을
              web/basic2_native.glb 로 남겨 두고 그쪽을 기본값으로 쓴다.
              (백업 확장자 .bak_* 로 두면 glTF 임포터가 못 읽는다)
              SW_ 메시가 이미 있는 파일을 주면 멈춘다.
  SRC_GLB   칼을 가져올 원본   기본 web/kensa.glb
  OUT_GLB   결과              기본 web/basic2_body.glb
  KEEP_ANIM 1(기본) 타깃 원본 액션(Idle/Walk/Run)을 남긴다 / 0 지운다
            ★네이티브 걷기·달리기가 여기 들어 있다. s31_basic2_native.py 가 쓴다
  GRIP_ALIGN 1(기본) 손목 기준 칼날 축을 원본에 맞춰 조인다 / 0 자루 중심만 맞춤
  SW_SCALE  칼 배율에 곱하는 여유  기본 1.0
  RENDER    1(기본) 검산 렌더 / 0 생략
  OUTDIR    렌더 폴더  기본 renders/history/v97_wave11/char_basic2
  TEX_FORMAT/TEX_QUALITY  기본 AUTO(원본 포맷 유지) / 90
"""
import bpy
import os
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")

DST_GLB = os.environ.get("DST_GLB") or os.path.join(WEB, "basic2_native.glb")
SRC_GLB = os.environ.get("SRC_GLB") or os.path.join(WEB, "kensa.glb")
OUT_GLB = os.environ.get("OUT_GLB") or os.path.join(WEB, "basic2_body.glb")
KEEP_ANIM = os.environ.get("KEEP_ANIM", "1") == "1"
GRIP_ALIGN = os.environ.get("GRIP_ALIGN", "1") == "1"
SW_SCALE = float(os.environ.get("SW_SCALE", "1.0"))
RENDER = os.environ.get("RENDER", "1") == "1"
OUTDIR = os.environ.get("OUTDIR") or os.path.join(
    ROOT, "renders", "history", "v97_wave11", "char_basic2")
TEX_FORMAT = os.environ.get("TEX_FORMAT", "AUTO").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))

HAND_R = "Bip001 R Hand"

print("=" * 78)
print("[설정] 몸  %s" % DST_GLB)
print("       칼  %s" % SRC_GLB)
print("       결과 %s" % OUT_GLB)


def drop_junk():
    """glTF 임포터가 뼈를 그리려고 만드는 Icosphere(★함정 4)."""
    for o in list(bpy.data.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)


def rest(arm):
    """레스트로 고정하고 포즈 basis 를 지운다(★함정 3)."""
    for b in arm.pose.bones:
        b.rotation_mode = "QUATERNION"
        b.matrix_basis = Matrix()
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()


def fist(arm, body, tag):
    """손뼈 레스트 월드행렬 HM 과 주먹 중심 FC(손뼈 로컬)를 잰다."""
    A2W = arm.matrix_world.copy()
    HM = A2W @ arm.data.bones[HAND_R].matrix_local
    HMi = HM.inverted()
    vg = body.vertex_groups.get(HAND_R)
    assert vg is not None, "%s 에 %s 정점그룹이 없다" % (tag, HAND_R)
    P = []
    for v in body.data.vertices:
        for g in v.groups:
            if g.group == vg.index and g.weight > 0.5:
                P.append(HMi @ (body.matrix_world @ v.co))
                break
    assert len(P) > 20, "%s 손 정점이 %d 개뿐이다" % (tag, len(P))
    n = len(P)
    FC = Vector((sum(p.x for p in P) / n, sum(p.y for p in P) / n,
                 sum(p.z for p in P) / n))
    W = [body.matrix_world @ v.co for v in body.data.vertices]
    H = max(p.z for p in W) - min(p.z for p in W)
    FLOOR = min(p.z for p in W)
    print("\n[%s] 몸 정점 %d / 키 %.4f (바닥 %.4f)" % (tag, len(W), H, FLOOR))
    print("       주먹 정점 %d  중심(뼈로컬) (%+.3f, %+.3f, %+.3f)"
          % (n, FC.x, FC.y, FC.z))
    print("       주먹 bbox x %+.3f~%+.3f y %+.3f~%+.3f z %+.3f~%+.3f"
          % (min(p.x for p in P), max(p.x for p in P),
             min(p.y for p in P), max(p.y for p in P),
             min(p.z for p in P), max(p.z for p in P)))
    rr = max((p - FC).length for p in P)
    print("       주먹 반경(중심->최원점) %.3f (뼈로컬) = %.4f m"
          % (rr, rr * A2W.to_scale().x))
    return HM, FC, H, FLOOR, P


# ================================================================ 1) 임포트
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30                                    # ★함정 1
sc.render.fps_base = 1.0

# ★함정 2: 타깃을 먼저 읽는다
bpy.ops.import_scene.gltf(filepath=DST_GLB)
drop_junk()
arm_b = next(o for o in sc.objects if o.type == "ARMATURE")
body_b = max((o for o in sc.objects if o.type == "MESH"),
             key=lambda o: len(o.data.vertices))
rest(arm_b)
# ★결과물을 다시 넣으면 칼 위에 칼을 꽂는다. 알몸 원본만 받는다.
dup = [o.name for o in sc.objects if o.name.startswith("SW_")]
assert not dup, ("타깃에 이미 칼이 있다(%s). DST_GLB 는 알몸 원본"
                 " web/basic2_native.glb 여야 한다" % dup)
keep_objs = {o.name for o in sc.objects}
keep_acts = [a.name for a in bpy.data.actions]
print("\n[몸] 아마추어 %s (스케일 %.4f) / 뼈 %d / 메시 %s %d정점 / 액션 %s"
      % (arm_b.name, arm_b.matrix_world.to_scale().x, len(arm_b.data.bones),
         body_b.name, len(body_b.data.vertices), keep_acts))

bpy.ops.import_scene.gltf(filepath=SRC_GLB)
drop_junk()
arm_k = next(o for o in sc.objects
             if o.type == "ARMATURE" and o is not arm_b)
new_objs = [o for o in sc.objects if o.name not in keep_objs]
body_k = max((o for o in new_objs
              if o.type == "MESH" and not o.name.startswith("SW_")),
             key=lambda o: len(o.data.vertices))
sword_objs = [o for o in new_objs if o.type == "MESH" and o.name.startswith("SW_")]
rest(arm_k)
print("[칼] 아마추어 %s (스케일 %.4f) / 몸 %s / 칼 %d자루: %s"
      % (arm_k.name, arm_k.matrix_world.to_scale().x, body_k.name,
         len(sword_objs), sorted(o.name for o in sword_objs)))
assert sword_objs, "%s 에 SW_ 메시가 없다" % SRC_GLB

# ================================================================ 2) 실측
HM_b, FC_b, H_b, FLOOR_b, HP_b = fist(arm_b, body_b, "몸 basic2")
HM_k, FC_k, H_k, FLOOR_k, HP_k = fist(arm_k, body_k, "칼 kensa")

# 손뼈 축 어긋남(정보). R 이 이걸 되돌린다.
Rb = HM_b.to_quaternion().to_matrix()
Rk = HM_k.to_quaternion().to_matrix()
R = Rb.inverted() @ Rk
print("\n[정합] 손뼈 레스트 축 각도차(월드)")
for k, nm in enumerate("XYZ"):
    a = Vector((HM_b[0][k], HM_b[1][k], HM_b[2][k])).normalized()
    c = Vector((HM_k[0][k], HM_k[1][k], HM_k[2][k])).normalized()
    print("       %s축  %6.2f 도" % (nm, math.degrees(math.acos(
        max(-1.0, min(1.0, a.dot(c)))))))
print("       보정 R 회전각 %.2f 도" % math.degrees(R.to_quaternion().angle))

ARM_K_UNIT = arm_k.matrix_world.to_scale().x   # 뼈로컬 1 단위 = 몇 m (검산 출력용.
# ★아래에서 kensa 아마추어를 지우므로 지금 값을 빼 둔다. 지운 뒤 만지면 ReferenceError)
S = (H_b / H_k) * SW_SCALE
print("\n[크기] 칼 배율 S = %.4f / %.4f = %.4f (여유 %.3f 포함)"
      % (H_b, H_k, S, SW_SCALE))
print("       게임 정규화 뒤 칼 길이는 kensa 와 같아진다"
      " (원본 배율 1.0 이면 %.1f%% 길어진다)" % ((H_k / H_b - 1) * 100))

# ================================================================ 3) 칼 옮기기
# ★함정 7: 부모(kensa 아마추어)를 지우기 전에 월드로 굳힌다.
#
# ★★칼날 축은 **손목 원점 기준**으로 맞춘다. 자루 중심 기준이 아니다.
#   main.js measureBlade 와 s24 [자루] 절이 둘 다 "손 본 로컬에서 원점에서 가장 먼
#   정점"으로 칼날 방향을 정한다(= 손목 원점 기준). 그런데 두 리그의 주먹 중심이
#   손목에서 서로 다른 자리에 있어(실측 2.5cm 차) 자루 중심만 맞춰 옮기면 그 방향이
#   5.2도 어긋난다. 5도면 90cm 칼끝이 8cm 옆에 있는 것이라 궤적·사거리가 그만큼 밀린다.
#   그래서 옮긴 뒤 **자루 중심을 축으로** 미세 회전해 손목 기준 방향을 다시 맞춘다.
#   회전축(자루 중심)과 측정 기준점(손목)이 달라 한 번에 안 맞으므로 반복해서 조인다
#   (s26 이 kensa 에 쓴 것과 같은 방식. kensa 는 이 값이 slayer 대비 0.01도다).
GRIP_W = HM_b @ FC_b
tip_before = {}      # 칼 이름 -> (칼끝 정점 번호, 손목기준 목표 월드방향, 길이)
for o in sword_objs:
    MW = o.matrix_world.copy()
    KL = [HM_k.inverted() @ (MW @ v.co) for v in o.data.vertices]   # kensa 손뼈 로컬
    ti = max(range(len(KL)), key=lambda i: KL[i].length_squared)    # 손목 기준 최원점
    tgt = (HM_k.to_3x3() @ KL[ti]).normalized()
    tip_before[o.name] = (ti, tgt, KL[ti].length)
    loc = [HM_b @ (FC_b + R @ ((vk - FC_k) * S)) for vk in KL]      # 월드
    o.parent = None
    o.matrix_world = Matrix()
    for v, p in zip(o.data.vertices, loc):
        v.co = p
    o.data.update()

if GRIP_ALIGN:
    WRIST = HM_b.to_translation()
    print("\n[조임] 손목 기준 칼날 축을 원본에 맞춘다 (자루 중심 둘레 미세 회전)")
    for o in sorted(sword_objs, key=lambda x: x.name):
        tgt = tip_before[o.name][1]
        first = None
        for it in range(40):
            far = max((v.co for v in o.data.vertices),
                      key=lambda p: (p - WRIST).length_squared)
            cur = (far - WRIST).normalized()
            ang = cur.angle(tgt)
            if first is None:
                first = math.degrees(ang)
            if ang < 1e-4:
                break
            ax = cur.cross(tgt)
            if ax.length < 1e-9:
                break
            q = Matrix.Rotation(ang, 3, ax.normalized())
            for v in o.data.vertices:
                v.co = GRIP_W + q @ (v.co - GRIP_W)
            o.data.update()
        print("       %-14s %5.2f도 -> %.4f도 (%d회)"
              % (o.name, first, math.degrees(ang), it + 1))

# ================================================================ 4) kensa 정리
for o in list(sc.objects):
    if o is arm_b or o is body_b or o in sword_objs:
        continue
    if o.name in keep_objs:
        continue
    bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions):
    if a.name not in keep_acts:
        bpy.data.actions.remove(a)
if not KEEP_ANIM:
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    if arm_b.animation_data:
        arm_b.animation_data_clear()
for a in bpy.data.actions:
    a.use_fake_user = True                              # 안 켜면 export 에서 빠진다

# ================================================================ 5) 스키닝
for o in sword_objs:
    for vg in list(o.vertex_groups):
        o.vertex_groups.remove(vg)
    vg = o.vertex_groups.new(name=HAND_R)               # ★손뼈 100%
    vg.add(range(len(o.data.vertices)), 1.0, "REPLACE")
    for md in list(o.modifiers):
        o.modifiers.remove(md)
    md = o.modifiers.new("Armature", "ARMATURE")
    md.object = arm_b
    o.parent = arm_b
    o.matrix_parent_inverse = arm_b.matrix_world.inverted()

# ================================================================ 6) 검산
print("\n[검산] 손목 기준 칼날 축(레스트 월드). 옮기기 전후가 같아야 한다")
print("       %-14s %8s %10s %10s %10s" %
      ("칼", "각도차", "길이(kensa)", "길이(basic2)", "최저z"))
WRIST_W = HM_b.to_translation()
worst = 0.0
for o in sorted(sword_objs, key=lambda x: x.name):
    ti, d_k, len_k = tip_before[o.name]
    far = max((v.co for v in o.data.vertices),
              key=lambda p: (p - WRIST_W).length_squared)
    d_b = (far - WRIST_W).normalized()
    ang = math.degrees(math.acos(max(-1.0, min(1.0, d_b.dot(d_k)))))
    worst = max(worst, ang)
    len_b = (far - WRIST_W).length
    len_km = len_k * ARM_K_UNIT                        # ★뼈로컬 단위 -> m
    zlo = min(v.co.z for v in o.data.vertices)
    print("       %-14s %6.3f도 %10.4f %11.4f %11.4f (바닥 %+.4f)"
          % (o.name, ang, len_km, len_b, zlo, FLOOR_b))
print("       최악 %.3f 도 (0.1 미만이면 방향이 그대로 옮겨진 것이다)" % worst)
print("       게임 정규화(키 1.75) 뒤 손목->칼끝: kensa %.4f m / basic2 %.4f m"
      % (len_km * 1.75 / H_k, len_b * 1.75 / H_b))

# 자루가 주먹을 지나는가(= 쥔 것처럼 보이는가)
hw = [HM_b @ p for p in HP_b]
for o in sorted(sword_objs, key=lambda x: x.name):
    inside = 0
    for p in hw:
        d = min((p - v.co).length for v in o.data.vertices)
        if d < 0.02:
            inside += 1
    print("       %-14s 칼 표면 2cm 안의 손 정점 %d/%d" % (o.name, inside, len(hw)))

# ================================================================ 7) 내보내기
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
sc.frame_set(1)
bpy.context.view_layer.update()
bpy.ops.object.select_all(action="DESELECT")
kw = dict(filepath=OUT_GLB, export_format="GLB", use_selection=False,
          export_apply=True, export_yup=True,
          export_animations=KEEP_ANIM, export_animation_mode="ACTIONS",
          export_nla_strips=False, export_bake_animation=True,
          export_frame_range=False)
if TEX_FORMAT not in ("AUTO", ""):
    kw.update(export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
              export_jpeg_quality=TEX_QUALITY)
bpy.ops.export_scene.gltf(**kw)
sz = os.path.getsize(OUT_GLB)
print("\nEXPORTED %s  %d bytes (%.2f MB)  칼 %d자루  액션 %s"
      % (OUT_GLB, sz, sz / 1e6, len(sword_objs),
         [a.name for a in bpy.data.actions]))

# ================================================================ 8) 렌더
if not RENDER:
    print("DONE (렌더 생략)")
    raise SystemExit(0)

os.makedirs(OUTDIR, exist_ok=True)
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                    else "BLENDER_EEVEE")
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = 620, 800
wd = bpy.data.worlds.new("W")
sc.world = wd
wd.use_nodes = True
wd.node_tree.nodes["Background"].inputs[0].default_value = (0.06, 0.065, 0.08, 1)
for eul, en, col in (((58, 0, -30), 4.0, (1, 1, 1)),
                     ((-40, 0, 130), 1.8, (0.7, 0.82, 1.0))):
    li = bpy.data.lights.new("S", "SUN")
    li.energy = en
    li.color = col
    so = bpy.data.objects.new("S", li)
    so.rotation_euler = tuple(math.radians(a) for a in eul)
    sc.collection.objects.link(so)
bpy.ops.mesh.primitive_plane_add(size=H_b * 6, location=(0, 0, FLOOR_b))
cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam

# 게임 기본 칼(백아)만 켠다. 7자루가 다 보이면 겹쳐서 아무 판정도 안 된다.
for o in sword_objs:
    o.hide_render = (o.name != "SW_baekah")

CEN = Vector((0, 0, FLOOR_b + H_b * 0.55))
GRIP = HM_b @ FC_b


def look(cam, eye, tgt):
    cam.location = eye
    d = (tgt - eye)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


for nm, eye, tgt, res in (
        ("body_front", CEN + Vector((0, -H_b * 1.9, H_b * 0.10)), CEN, (620, 800)),
        ("body_side", CEN + Vector((-H_b * 1.9, 0, H_b * 0.10)), CEN, (620, 800)),
        ("grip", GRIP + Vector((-0.18, -0.30, 0.12)), GRIP, (800, 620)),
        ("grip2", GRIP + Vector((0.10, -0.22, 0.22)), GRIP, (800, 620))):
    sc.render.resolution_x, sc.render.resolution_y = res
    look(cam, eye, tgt)
    sc.render.filepath = os.path.join(OUTDIR, "s31_%s.png" % nm)
    bpy.ops.render.render(write_still=True)
    print("   렌더 %s" % sc.render.filepath)
print("DONE")
