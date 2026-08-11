# -*- coding: utf-8 -*-
"""물의 호흡 이펙트 — 레퍼런스 영상 프레임 실측 기반.

분석에서 확정된 규칙(우선순위):
 1) 모든 물 표면에 **검정 외곽선(#000814) + 바로 옆 흰 선(#F2FFFF)** 페어. 이게 1번 시그니처.
 2) 단일 리본 금지. **여러 가닥이 인접**하고 가닥 사이는 얇은 분리선.
    가닥 폭 = 칼 길이의 0.15~0.2배, 다발 전체 0.5~0.9배.
 3) 단면 비대칭: **바깥(볼록)=흰 거품 / 안쪽=남색으로 딱 끊김.** 거품은 바깥에만.
 4) 두께는 곡률 연동. 궤적이 꺾이는 곳이 선단보다 2~4배 두껍다.
 5) 알파 페이드 없음. 밝기는 **계단식**으로 떨어지고 꼬리는 잘려나간다(분해).

실측 팔레트(두 분석 보고 교차 확인):
"""
import bpy
import math
import random
from mathutils import Vector

# G/f_030 세로 단면 실측 (외곽선1~2px / 흰6 / 시안4 / 중청8 / 2차하이라이트8 / 평면55px+)
# 레퍼런스(water-breathing.mp4 c_04~c_07)에서 채도 0.7 이상 픽셀만 골라
# 실측한 팔레트. 웹 빌드(web/main.js)와 같은 값이니 한쪽만 고치지 말 것.
# 예전 값은 어둡고 탁한 파랑이라 렌더가 희끄무레하게 떴다.
C_OUT = (0.000, 0.000, 0.063)     # #000010 배경보다 더 검게 (외곽선)
C_FOAM = (0.941, 0.941, 0.941)    # #F0F0F0 흰 포말
C_CYAN = (0.275, 0.824, 0.980)    # #46D2FA 제일 밝은 시안
C_MID = (0.157, 0.549, 0.824)     # #288CD2 가장 많이 쓰인 중간 하늘 (10.3%)
C_CYAN2 = (0.235, 0.745, 0.941)   # #3CBEF0 밝은 시안
C_FLAT = (0.078, 0.157, 0.784)    # #1428C8 진한 파랑 (심, 폭의 절반 이상)


def _c(t):
    return (t[0], t[1], t[2], 1.0)


def make_ribbon_material(name, tail=0.34, strength=10.0, sat=1.0):
    """UV.x = 탄생시각(0..1), UV.y = 단면(0=바깥 거품쪽, 1=안쪽 남색쪽)"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.blend_method = "BLEND"
    try:
        m.shadow_method = "NONE"
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    uvn = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uvn.outputs[0], sep.inputs[0])

    # ---- 나이 ----
    nowv = nt.nodes.new("ShaderNodeValue")
    nowv.name = "NOW"
    nowv.outputs[0].default_value = -1.0
    age = nt.nodes.new("ShaderNodeMath")
    age.operation = "SUBTRACT"
    nt.links.new(nowv.outputs[0], age.inputs[0])
    nt.links.new(sep.outputs[0], age.inputs[1])
    born = nt.nodes.new("ShaderNodeMath")
    born.operation = "GREATER_THAN"
    born.inputs[1].default_value = -0.0005
    nt.links.new(age.outputs[0], born.inputs[0])
    alive = nt.nodes.new("ShaderNodeMath")
    alive.operation = "LESS_THAN"
    alive.inputs[1].default_value = tail
    nt.links.new(age.outputs[0], alive.inputs[0])
    vis = nt.nodes.new("ShaderNodeMath")     # 하드 윈도(페이드 아님)
    vis.operation = "MULTIPLY"
    nt.links.new(born.outputs[0], vis.inputs[0])
    nt.links.new(alive.outputs[0], vis.inputs[1])
    agen = nt.nodes.new("ShaderNodeMath")
    agen.operation = "DIVIDE"
    agen.inputs[1].default_value = tail
    agen.use_clamp = True
    nt.links.new(age.outputs[0], agen.inputs[0])

    # 나이에 따른 밝기: 계단식 3단(스무스 페이드 금지)
    agestep = nt.nodes.new("ShaderNodeValToRGB")
    ar = agestep.color_ramp
    ar.interpolation = "CONSTANT"
    ar.elements[0].position = 0.0
    ar.elements[0].color = (1.0, 1.0, 1.0, 1)
    ar.elements[1].position = 0.34
    ar.elements[1].color = (0.62, 0.62, 0.62, 1)
    e = ar.elements.new(0.68)
    e.color = (0.34, 0.34, 0.34, 1)
    nt.links.new(agen.outputs[0], agestep.inputs[0])

    # ---- 단면: 검정외곽선 + 흰선 + 거품 + 시안 + 하늘 + 파랑 + 남색 + 검정외곽선 ----
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    stops = [
        (0.000, C_OUT),     # 바깥 외곽선 2%
        (0.022, C_FOAM),    # 흰 코어 7%
        (0.092, C_CYAN),    # 밝은 시안 5%
        (0.140, C_MID),     # 중청 10%
        (0.240, C_CYAN2),   # 2차 하이라이트 10%
        (0.340, C_FLAT),    # ★평면 로열블루 63% (여기가 대부분)
        (0.972, C_OUT),     # 안쪽 외곽선
    ]
    cr.elements[0].position = stops[0][0]
    cr.elements[0].color = _c(stops[0][1])
    cr.elements[1].position = stops[1][0]
    cr.elements[1].color = _c(stops[1][1])
    for pos, col in stops[2:]:
        el = cr.elements.new(pos)
        el.color = _c(col)
    nt.links.new(sep.outputs[1], ramp.inputs[0])

    # 단면별 발광 강도(흰 선/거품만 날아가게)
    st = nt.nodes.new("ShaderNodeValToRGB")
    sr = st.color_ramp
    sr.interpolation = "CONSTANT"
    svals = [(0.000, 0.02), (0.022, 1.00), (0.092, 0.62),
             (0.140, 0.24), (0.240, 0.58), (0.340, 0.20), (0.972, 0.02)]
    sr.elements[0].position = svals[0][0]
    v0 = svals[0][1]
    sr.elements[0].color = (v0, v0, v0, 1)
    sr.elements[1].position = svals[1][0]
    v1 = svals[1][1]
    sr.elements[1].color = (v1, v1, v1, 1)
    for pos, v in svals[2:]:
        el = sr.elements.new(pos)
        el.color = (v, v, v, 1)
    nt.links.new(sep.outputs[1], st.inputs[0])

    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(st.outputs[0], mul.inputs[0])
    nt.links.new(agestep.outputs[0], mul.inputs[1])
    gain = nt.nodes.new("ShaderNodeMath")
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = strength
    nt.links.new(mul.outputs[0], gain.inputs[0])

    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ramp.outputs[0], em.inputs[0])
    nt.links.new(gain.outputs[0], em.inputs[1])

    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(vis.outputs[0], mix.inputs[0])   # 하드 온/오프
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m, nowv


def build_ribbon_bundle(name, samples, n_strands=9, seed=3,
                        inner=0.24, strand_w=0.105, gap=0.010,
                        curve_boost=2.6, wobble=0.020, radial_swing=0.10,
                        tail=0.34, strength=10.0):
    """samples=[(base,tip),...] 월드 좌표. 가닥을 인접 배치해 분리선이 생기게 한다.
    두께는 곡률에 비례(꺾이는 곳이 두껍다).
    """
    rng = random.Random(seed)
    N = len(samples)
    # 진행 방향 + 곡률
    vel, curv = [], []
    for i in range(N):
        a = samples[max(0, i - 1)][1]
        b = samples[min(N - 1, i + 1)][1]
        v = b - a
        vel.append(v.normalized() if v.length > 1e-6 else Vector((0, 0, 1)))
    for i in range(N):
        v0 = vel[max(0, i - 2)]
        v1 = vel[min(N - 1, i + 2)]
        d = max(-1.0, min(1.0, v0.dot(v1)))
        curv.append(math.acos(d))                 # 0..pi
    cmax = max(curv) if max(curv) > 1e-6 else 1.0
    thick = [1.0 + (curve_boost - 1.0) * (c / cmax) ** 0.7 for c in curv]
    # 평활화
    sm = []
    for i in range(N):
        w = [thick[j] for j in range(max(0, i - 3), min(N, i + 4))]
        sm.append(sum(w) / len(w))
    thick = sm

    objs, nows = [], []
    for k in range(n_strands):
        ph = rng.uniform(0, math.tau)
        freq = rng.uniform(1.2, 2.6)
        amp = wobble * (0.5 + rng.random())
        # 레퍼런스 핵심: 가닥끼리 앞뒤로 교차(occlusion)해야 3D 브레이드로 읽힌다.
        # 반경 자체를 시간에 따라 흔들어 이웃 가닥과 서로 넘나들게 한다.
        ph2 = rng.uniform(0, math.tau)
        freq2 = rng.uniform(0.8, 2.0)
        swing = radial_swing * (0.6 + rng.random() * 0.8)
        verts, faces, uvs = [], [], []
        for i in range(N):
            bpos, tpos = samples[i]
            axis = tpos - bpos
            L = axis.length
            if L < 1e-6:
                axis = Vector((1, 0, 0))
                L = 1.0
            adir = axis / L
            perp = adir.cross(vel[i])
            perp = perp.normalized() if perp.length > 1e-6 else adir.cross(Vector((0, 0, 1))).normalized()
            t = thick[i]
            u_ = i / max(1, N - 1)
            # 가닥 k 의 반경 구간(곡률만큼 두꺼워짐) + 반경 스윙으로 교차
            rc = inner + k * (strand_w + gap) * t
            rc += swing * math.sin(ph2 + u_ * math.tau * freq2)
            r0 = rc
            r1 = rc + strand_w * t
            off = perp * (amp * L * math.sin(ph + (i / max(1, N - 1)) * math.tau * freq))
            po = bpos + adir * (L * r1) + off      # 바깥
            pi_ = bpos + adir * (L * r0) + off     # 안쪽
            u = i / (N - 1)
            # 레퍼런스: 하이라이트가 항상 "화면 위쪽" 모서리에 붙는다(스크린스페이스 규칙).
            # 바깥 모서리가 아래를 향하면 UV.y 를 뒤집어 밝은 층이 위로 오게 한다.
            up_out = 0.0 if po.z >= pi_.z else 1.0
            verts.append(tuple(po))
            uvs.append((u, up_out))
            verts.append(tuple(pi_))
            uvs.append((u, 1.0 - up_out))
        for i in range(N - 1):
            a = i * 2
            faces.append((a, a + 2, a + 3, a + 1))
        me = bpy.data.meshes.new("%s_%d" % (name, k))
        me.from_pydata(verts, [], faces)
        me.validate()
        me.update()
        uvl = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                uvl.data[li].uv = uvs[me.loops[li].vertex_index]
        ob = bpy.data.objects.new("%s_%d" % (name, k), me)
        bpy.context.collection.objects.link(ob)
        mat, nownode = make_ribbon_material(
            "%s_mat_%d" % (name, k),
            tail=tail * rng.uniform(0.88, 1.14),
            strength=strength * rng.uniform(0.85, 1.15))
        me.materials.append(mat)
        objs.append(ob)
        nows.append(nownode)
    return objs, nows, thick


def make_foam_material(name, strength=13.0):
    """거품/물방울: 흰 채움 + 남색 아웃라인 느낌(발광)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.blend_method = "BLEND"
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = _c(C_FOAM)
    em.inputs[1].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.0
    mix.name = "FMIX"
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m, mix


def build_wave(name, samples, seed=5, inner=0.15, crest=1.25,
               curl_r=0.42, curl_turns=1.5, rise=0.30, prof_n=26,
               tail=0.34, strength=4.2, thick=None):
    """호쿠사이식 '말려 올라가는 파도' 시트.

    단면 프로파일: 안쪽은 평평하게 누워 있다가 바깥으로 갈수록 솟구치고
    마지막 40%에서 나선으로 말려 넘어간다(부서지는 파도 마루).
    UV.y = 0 이 마루(흰 포말), 1 이 바닥(진남색)이라 기존 밴딩 램프를 그대로 쓴다.
    반환 (obj, now_node, crest_points)
    """
    rng = random.Random(seed)
    N = len(samples)
    if thick is None:
        thick = [1.0] * N
    vel = []
    for i in range(N):
        a = samples[max(0, i - 1)][1]
        b = samples[min(N - 1, i + 1)][1]
        v = b - a
        vel.append(v.normalized() if v.length > 1e-6 else Vector((0, 0, 1)))

    # 단면 프로파일 (u=칼축 방향 배율, v=수직 방향 배율)
    prof = []
    for j in range(prof_n):
        t = j / (prof_n - 1)
        if t <= 0.58:
            a = t / 0.58
            u = inner + (crest - inner) * a
            v = rise * (a ** 2.2) * 0.30
        else:
            s = (t - 0.58) / 0.42
            ang = s * math.pi * curl_turns
            rad = curl_r * (1.0 - 0.42 * s)
            u = crest + rad * math.sin(ang) - rad * 0.10 * s
            v = rise * 0.30 + rad * (1.0 - math.cos(ang))
        prof.append((u, v))

    verts, faces, uvs = [], [], []
    crest_pts = []
    for i in range(N):
        bpos, tpos = samples[i]
        axis = tpos - bpos
        L = axis.length
        if L < 1e-6:
            axis = Vector((1, 0, 0))
            L = 1.0
        adir = axis / L
        up = adir.cross(vel[i])
        up = up.normalized() if up.length > 1e-6 else adir.cross(Vector((0, 0, 1))).normalized()
        if up.z < 0:                      # 파도는 위로 솟구쳐야 한다
            up = -up
        tk = thick[i]
        wob = 0.05 * math.sin(i * 0.55 + rng.random() * 0.001)
        for j, (pu, pv) in enumerate(prof):
            p = bpos + adir * (L * pu * tk * (1.0 + wob)) + up * (L * pv * tk)
            verts.append(tuple(p))
            tj = j / (prof_n - 1)
            uvs.append((i / (N - 1), (1.0 - tj) ** 0.55))   # 마루쪽 밝은 층을 넓게
        # 마루 지점(포말 배치용) = 프로파일 끝쪽
        jc = int(prof_n * 0.86)
        pu, pv = prof[jc]
        crest_pts.append(bpos + adir * (L * pu * tk) + up * (L * pv * tk))
    for i in range(N - 1):
        for j in range(prof_n - 1):
            a = i * prof_n + j
            b = (i + 1) * prof_n + j
            faces.append((a, b, b + 1, a + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    mat, nownode = make_ribbon_material(name + "_mat", tail=tail, strength=strength)
    me.materials.append(mat)
    return ob, nownode, crest_pts


def drive_now(now_node, f0, f1):
    """NOW 값을 프레임에 직접 연동(키프레임 대신 드라이버).
    Blender 4.4+ 슬롯형 액션에서 노드 소켓 keyframe_insert 가 조용히 실패하는 경우가 있어
    드라이버로 확실하게 건다. f0 에서 0, f1 에서 1.
    """
    span = max(1e-6, float(f1 - f0))
    fc = now_node.outputs[0].driver_add("default_value")
    drv = fc.driver
    drv.type = "SCRIPTED"
    drv.expression = "(frame - %f) / %f" % (float(f0), span)
    return fc
