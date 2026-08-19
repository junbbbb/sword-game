# -*- coding: utf-8 -*-
"""궁수가 **손에 드는 활**(BW_bow)을 절차로 만든다. s10_shield.py 의 방패와 같은 자리.

★배치 원리 (s10_shield.py 헤더가 정본. 여기서도 그대로 쓴다)
  REST(T포즈)에서 눈대중으로 놓으면 안 된다. 활은 손 뼈에 웨이트 1.0 으로 강체 부착되므로
  **가장 중요한 포즈에서 똑바로 보이도록** 맞춰야 한다. 그래서
      L = M_pose⁻¹ @ target ,  REST 에 구울 자리 = M_rest @ L
  을 푼다. 스키닝이 M_pose @ M_rest⁻¹ 를 곱해 주므로 그 포즈에서 정확히 target 이 된다.
  ★방패는 기준 포즈가 Idle 이었지만 **활은 Attack 만작**이다. 활은 쏠 때 손에 있는
    물건이고 그 프레임이 이 캐릭터의 캡처컷이다(오너 기준: "딱 봤을 때 캡처할 만한가").

★이름은 BW_bow 다. SW_ 를 쓰면 안 된다
  main.js:3352 가 SW_ 로 시작하는 스킨메시를 **칼 목록**으로 모으고 equipSword·
  measureBlade·칼날 발광 셰이더가 전부 거기에 걸린다. 활이 칼로 오인되면 판정이 꼬인다.
  SH_ 도 안 쓴다(방패 뜻이고, 탱커 쪽 규칙이다).

★키 정규화 - 여기가 이 작업에서 가장 미끄러운 자리다
  main.js:3340 은 SW_·SH_ 로 시작하지 **않는** 메시를 전부 모아 캐릭터 키를 잰다.
  BW_ 는 거기 안 걸리므로 **활이 키 상자에 들어간다.** 몸통(0~키) 밖으로 삐져나오면
  캐릭터가 쪼그라들고 발이 뜬다(탱커 Icosphere 사고와 같은 증상).
  ★실측: 캔트 0도면 REST 활 z 가 1.730 이라 몸통 1.700 을 넘어 캐릭터가 1.7% 준다.
    **캔트 -15도**면 0.839~1.636 으로 들어온다. 그래서 s11 의 기본값이 -15 다.
    (활 길이를 줄여도 되지만 0.567H = 0.96m 까지 내려야 해서 그림이 손해다)
  그래서 build() 는 REST 바운딩을 항상 돌려주고 s11 이 몸통 상자와 대조해 찍는다.
  삐져나오는 값으로 바꾸려면 main.js:3340 에 `&& !o.name.startsWith('BW_')` 를 넣어야 한다.

좌표계(프로젝트 규약): glTF -> Blender 임포트 후 정면 = -Y, 위 = +Z, 캐릭터 오른쪽 = -X.

활 로컬 좌표(target 기준)
  +Z = 활채가 뻗는 방향(위/아래)      +Y = 시위를 당기는 쪽(궁수 몸 쪽)
  +X = 활 평면의 법선(캐릭터 바깥쪽)   원점 = 손아귀(grip)
"""
import math
import os
import bpy
from mathutils import Vector, Matrix


def _env(k, d):
    try:
        return float(os.environ.get(k, d))
    except Exception:
        return d


def mat(name, hexs, rough=0.75):
    """glTF 로 나가는 단순 Principled. build_scenes.cel_mat 은 노드 구성이 안 나간다.
    게임(main.js)은 어차피 MeshToonMaterial 로 갈아끼우고 베이스 컬러만 읽는다."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    h = hexs.lstrip("#")
    c = tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))
    b.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = 0.0
    nt.links.new(b.outputs[0], o.inputs[0])
    return m


def geometry(H, draw_len):
    """활 지오메트리를 **활 로컬 좌표**로 만든다. (정점, 면, 재질인덱스, 스무스)

    H        캐릭터 키(m). 모든 치수를 여기에 비례시킨다(눈대중 금지).
    draw_len 만작에서 활 쥔 손 -> 시위 손 거리(m). 실측값이 들어온다.
    """
    # ---- 치수 (전부 실측 비율에서) ----
    # 활 길이: 실물 롱보우는 사수 키의 65~72%. 여기선 0.68H.
    #   키 1.700 -> 1.156m. 게임 카메라(pitch 49.3도)에서 월드 1m = 화면 43px 이므로
    #   화면에서 약 50px 로 읽힌다(캐릭터 전신이 73px). 충분히 보인다.
    BL = _env("BW_LEN", 0.68) * H
    HL = BL / 2
    # 만작에서 활채 끝이 손아귀보다 얼마나 몸 쪽으로 물러나 있나.
    #   실물 비율: 완전히 당긴 활의 활고자는 손아귀 뒤 0.165*활길이 근처.
    TIPY = 0.135 * BL
    # 시위 매듭(화살 오늬)이 있는 자리. 실측 손-손 거리에서 손가락 길이(약 8cm)를 뺀다.
    #   손 뼈는 손목이라 시위를 쥔 손끝은 그만큼 활 쪽에 있다.
    NOCK = max(0.18, draw_len - 0.08)
    # 활채 단면(가로=활 평면 안, 세로=평면 법선 방향). 손아귀가 굵고 끝이 가늘다.
    WG, WT = 0.038 * (H / 1.70), 0.015 * (H / 1.70)     # 가로: 손아귀 -> 끝
    DG, DT = 0.044 * (H / 1.70), 0.015 * (H / 1.70)     # 세로: 손아귀 -> 끝
    # 시위 굵기. 실물은 3mm 지만 게임 카메라(월드 1m = 화면 43px)에서 3mm 는 0.13px 라
    # 아예 안 보인다. 9mm 로 키워야 화면에서 1px 안팎으로 읽힌다(2배 해상도 기준).
    SR = 0.009 * (H / 1.70)                             # 시위 굵기(반지름)
    NSEG = 5                                            # 활채 한 팔당 마디 수

    V, F, MI, SM = [], [], [], []

    def quad(a, b, c, d, mi, sm=True):
        F.append((a, b, c, d))
        MI.append(mi)
        SM.append(sm)

    def tri(a, b, c, mi, sm=True):
        F.append((a, b, c))
        MI.append(mi)
        SM.append(sm)

    # ---- 활채: (z, y) 평면 위의 곡선을 따라가는 사각 단면 막대 ----
    # y(t) = TIPY * |t|^1.7  (t = -1..1). 손아귀가 0, 끝이 TIPY. 지수 1.7 이
    # "손아귀 근처는 곧고 끝으로 갈수록 휜다" 는 실물 곡률에 가깝다.
    ts = []
    for k in range(-NSEG, NSEG + 1):
        ts.append(k / NSEG)
    rings = []
    for t in ts:
        z = t * HL
        y = TIPY * (abs(t) ** 1.7)
        f = abs(t)
        w = (WG + (WT - WG) * f) / 2
        d = (DG + (DT - DG) * f) / 2
        # 단면 네 점: (x, y, z) 로컬. x = 평면 법선 방향(두께), y 는 곡선 오프셋
        ring = []
        for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            ring.append(len(V))
            V.append((sx * d, y + sy * w, z))
        rings.append(ring)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(4):
            n = (k + 1) % 4
            quad(a[k], a[n], b[n], b[k], 0)
    # 끝 마개
    for r, flip in ((rings[0], True), (rings[-1], False)):
        if flip:
            quad(r[3], r[2], r[1], r[0], 0, False)
        else:
            quad(r[0], r[1], r[2], r[3], 0, False)

    # ---- 손아귀 감개(가죽): 활채보다 조금 굵은 상자 ----
    gz = 0.075 * (H / 1.70)
    gw, gd = WG * 0.62, DG * 0.60
    n0 = len(V)
    for sz in (-gz, gz):
        for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            V.append((sx * (DG / 2 + gd * 0.18), sy * (WG / 2 + gw * 0.18), sz))
    for k in range(4):
        n = (k + 1) % 4
        quad(n0 + k, n0 + n, n0 + 4 + n, n0 + 4 + k, 1, False)

    # ---- 시위: 위 활고자 -> 오늬 -> 아래 활고자 (만작이라 V 자) ----
    # ★기준 포즈가 만작이므로 시위도 당겨진 모양으로 굽는다. Idle 에서도 이 모양이지만
    #   게임 거리에서 시위는 1~2px 라 "당겨져 있다"가 눈에 띄지 않는다.
    #   (반대로 만작에서 시위가 곧으면 시위 손이 허공을 쥔 그림이 된다 - 그게 더 나쁘다)
    def strand(p0, p1, seg):
        # p0->p1 을 잇는 삼각 단면 가는 막대
        d = Vector(p1) - Vector(p0)
        L = d.length
        d = d.normalized()
        up = Vector((1, 0, 0))
        if abs(d.dot(up)) > 0.9:
            up = Vector((0, 1, 0))
        e1 = d.cross(up).normalized()
        e2 = d.cross(e1).normalized()
        prev = None
        for s in range(seg + 1):
            p = Vector(p0) + d * (L * s / seg)
            ring = []
            for k in range(3):
                a = 2 * math.pi * k / 3
                q = p + e1 * (SR * math.cos(a)) + e2 * (SR * math.sin(a))
                ring.append(len(V))
                V.append((q.x, q.y, q.z))
            if prev is not None:
                for k in range(3):
                    n = (k + 1) % 3
                    quad(prev[k], prev[n], ring[n], ring[k], 2)
            prev = ring

    top = (0.0, TIPY, HL)
    bot = (0.0, TIPY, -HL)
    nk = (0.0, NOCK, 0.0)
    strand(top, nk, 2)
    strand(nk, bot, 2)

    info = dict(BL=BL, TIPY=TIPY, NOCK=NOCK, WG=WG, DG=DG, SR=SR)
    return V, F, MI, SM, info


def build(arm, hand_bone, M_rest, M_pose, H, draw_len, name="BW_bow",
          extra_rot=None, offset=(0.0, 0.0, 0.0), basis=None, origin=None):
    """활 오브젝트를 만들어 씬에 붙이고 손 뼈에 웨이트 1.0 으로 묶는다.

    basis  (ex, ey, ez) 월드 벡터 3개. target 의 회전이 된다.
    origin 월드 좌표. target 의 원점(손아귀).
    """
    V, F, MI, SM, info = geometry(H, draw_len)
    ex, ey, ez = basis
    R = Matrix(((ex.x, ey.x, ez.x, 0.0),
                (ex.y, ey.y, ez.y, 0.0),
                (ex.z, ey.z, ez.z, 0.0),
                (0.0, 0.0, 0.0, 1.0)))
    P = Vector(origin) + ex * offset[0] + ey * offset[1] + ez * offset[2]
    target = Matrix.Translation(P) @ R
    if extra_rot is not None:
        target = target @ extra_rot
    L = M_pose.inverted() @ target          # 손 뼈 로컬 오프셋
    FINAL = M_rest @ L                      # REST 에 구울 자리

    VW = [FINAL @ Vector(v) for v in V]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in VW], [], F)
    me.validate(verbose=False)
    for k, p in enumerate(me.polygons):
        p.material_index = MI[k]
        p.use_smooth = SM[k]
    me.update()
    me.materials.append(mat("BW_wood", "7A5334", 0.80))    # 활채(따뜻한 나무)
    me.materials.append(mat("BW_grip", "3E3026", 0.85))    # 손아귀 가죽
    me.materials.append(mat("BW_string", "7A6E5C", 0.60))  # 시위(바랜 힘줄색)

    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = Matrix()              # 정점이 이미 월드 좌표
    vg = ob.vertex_groups.new(name=hand_bone)
    vg.add(range(len(me.vertices)), 1.0, "REPLACE")
    md = ob.modifiers.new("Armature", "ARMATURE")
    md.object = arm

    tri_n = sum(len(p.vertices) - 2 for p in me.polygons)
    info.update(tris=tri_n, verts=len(me.vertices),
                target=target, L=L, FINAL=FINAL, obj=ob,
                rest_bb=(min(p.x for p in VW), max(p.x for p in VW),
                         min(p.y for p in VW), max(p.y for p in VW),
                         min(p.z for p in VW), max(p.z for p in VW)))
    return info
