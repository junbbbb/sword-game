# -*- coding: utf-8 -*-
"""3연타 콤보 포즈 정의 + 포즈 적용기 (s5_combo / s6_export_game 공용).

왜 이렇게 바꿨나 (2차 개정):
  칼이 몸을 감아 도는 문제가 계속 남았다. 근본 원인은 스윙 각도가 아니라
  **한 손 파지**였다. 한 손이면 팔이 몸 옆/뒤로 돌아가는 게 물리적으로 가능해진다.
  레퍼런스(water-breathing.mp4)를 프레임 단위로 보면 물의 호흡은 전부
  **양손으로 자루를 잡고**, 손은 몸 정중선 근처에 머물며, 크게 움직이는 건
  손이 아니라 **칼날 각도**다. 검도 카마에(中段/上段)가 그대로 들어있다.

  그래서 포즈를 "관절 각도"가 아니라 **검도 자세의 3요소**로 적는다:
    1. 오른손을 몸 기준 어디에 두는가        -> IK
    2. 칼날이 어디를 향하는가                 -> BLADE
    3. 왼손은 자루를 잡는다(항상)             -> GRIP (자동 IK)
  양손이 자루에 묶여 있으면 팔이 몸을 감을 수가 없다. 이게 핵심.

기준축 (probe_axes.py 실측):
    RIGHT = (-1, 0, 0)   캐릭터의 오른쪽
    UP    = ( 0, 0, 1)
    FWD   = ( 0,-1, 0)   캐릭터가 바라보는 쪽
(r, u, f) 좌표는 **척추 본 위치 기준**, 키 H 로 정규화. 몸 높이 참고값:
    어깨 +0.22 / 눈 +0.31 / 정수리 +0.44 / 배꼽 -0.02 / 무릎 -0.35

그 외 회전 부호 (실측):
    spine Z + -> 오른어깨가 앞으로 (상체가 왼쪽으로 비틀림)
    spine X + -> 앞으로 숙임
"""
import math
from mathutils import Vector, Matrix

RIGHT = Vector((-1, 0, 0))
UP = Vector((0, 0, 1))
FWD = Vector((0, -1, 0))

X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
AIM = "AIM"        # 본이 향할 월드 방향
BLADE = "BLADE"    # 칼날이 향할 월드 방향 (손목으로 맞춤)
IK = "IK"          # 손을 그 자리에 갖다 놓음 (2본 IK)
GRIP = "GRIP"      # 왼손을 자루에 붙임. 값 = 오른손에서 물미 쪽으로 떨어진 거리(H 단위)
FACE = "FACE"      # 본을 월드 수직축으로 돌려 **바라보는 방향**을 맞춘다.
                   # AIM 은 본 축(머리 위쪽)만 맞추므로 좌우로 돌아간 건 못 잡는다.
                   # 원본 달리기는 병사가 두리번거려서 머리가 35~58도 돌아가 있었다.
HEAD_FACE_LOCAL = Vector((-0.052, 0.996, 0.070))   # 중단세에서 실측
ARC = "ARC"        # 손을 **어깨 기준 방향+반지름**으로 놓는다. 값 = (r, u, f, R)
                   # 팔 흔들기는 어깨 중심 호를 그린다. (r,u,f) 절대좌표로 보간하면
                   # 어깨와의 거리가 변해 팔꿈치가 접혔다 펴졌다 한다(실측 ROM 96도).
ELBOW = "ELBOW"

# 칼날이 오른손 본 로컬에서 향하는 방향.
# convert_to_slayer.py 의 그립 정렬에서 유도:
#   칼 로컬 +X(칼끝) --q--> 손 본 로컬 -Y, 그 뒤 Z 축으로 KAT_TILT(기본 22도).
#   Rz(-90) @ Rz(22) @ (1,0,0) = (sin22, -cos22, 0)
# 웹에서 실측한 값 (0.512,-0.854,0.088) 과 10도 이내로 일치한다.
# 그립 정렬을 바꾸면 여기도 같이 고쳐야 한다.
_TILT = math.radians(22.0)
BLADE_LOCAL = Vector((math.sin(_TILT), -math.cos(_TILT), 0.0))


def ruf(r, u, f):
    """(오른쪽, 위, 앞) 성분 -> 월드 방향 벡터."""
    return (RIGHT * r + UP * u + FWD * f).normalized()


class Poser(object):
    """armature 하나에 대해 포즈를 적용한다. height = 캐릭터 키(월드 단위)."""

    def __init__(self, arm, height):
        self.arm = arm
        self.H = height
        self.A2W = arm.matrix_world
        self.W2A = arm.matrix_world.inverted()
        self.home = arm.location.copy()
        self.reach_log = []          # IK 가 못 닿은 기록 (검증용)
        self.palm = {}               # 손 본 로컬에서의 주먹 중심
        self.fist_r = {}             # 주먹 반지름(월드)
        self._bind_hands()

    def _bind_hands(self):
        """주먹 중심을 손 본 로컬 좌표로 재둔다.

        ★칼은 손목 관절이 아니라 **주먹 중심**에 붙어 있다
        (convert_to_slayer 의 palm_local. 손목에 붙이면 '손목에 칼이 달린' 그림이 된다).
        그런데 파지 계산을 손목으로 하면 자루 축이 손에서 0.072 H 어긋나고,
        그 어긋나는 **방향이 포즈마다 달라져서** 손과 자루가 따로 노는 그림이 된다.
        실측: 왼 주먹이 자루 축에서 주먹 1.1~2.4 개만큼 떨어져 있었다(= 아예 안 쥠).
        주먹은 손 본에 강체로 묶여 있어(모든 포즈에서 손목→주먹 0.1739 로 일정)
        이 로컬 좌표는 상수다."""
        import bpy
        mesh = None
        for o in bpy.data.objects:
            if o.type != "MESH":
                continue
            for m in o.modifiers:
                if m.type == "ARMATURE" and m.object is self.arm:
                    if mesh is None or len(o.data.vertices) > len(mesh.data.vertices):
                        mesh = o
        if mesh is None:
            return
        vgn = {g.index: g.name for g in mesh.vertex_groups}
        idx = {"r": [], "l": []}
        for v in mesh.data.vertices:
            best, bw = None, -1.0
            for g in v.groups:
                if g.weight > bw:
                    bw, best = g.weight, vgn.get(g.group, "")
            if not best:
                continue
            nm = best.lower()
            if "r hand" in nm:
                idx["r"].append(v.index)
            elif "l hand" in nm:
                idx["l"].append(v.index)
        for s, ids in idx.items():
            bone = self.pb("%s hand" % s)
            if not ids or bone is None:
                continue
            # 레스트 본 행렬 기준이라 현재 포즈와 무관하다.
            rest = self.A2W @ self.arm.data.bones[bone.name].matrix_local
            inv = rest.inverted()
            pts = [inv @ (mesh.matrix_world @ mesh.data.vertices[i].co) for i in ids]
            c = sum(pts, Vector((0, 0, 0))) / len(pts)
            self.palm[s] = c
            sc = rest.to_scale()
            self.fist_r[s] = max((p - c).length for p in pts) * abs(sc.x)

    def palm_world(self, side):
        """주먹 중심의 월드 좌표. 자루는 여기를 통과해야 한다."""
        p = self.palm.get(side)
        b = self.pb("%s hand" % side)
        if p is None or b is None:
            return None
        return (self.A2W @ b.matrix) @ p

    # ---- 유틸 ----
    def pb(self, key):
        for b in self.arm.pose.bones:
            if key.lower() in b.name.lower():
                return b
        return None

    def _update(self):
        import bpy
        bpy.context.view_layer.update()

    def wpos(self, key):
        b = self.pb(key)
        return (self.A2W @ b.matrix).translation.copy() if b else None

    def origin(self):
        """포즈 좌표의 기준점. 척추 본 head 는 spine 회전의 피벗이라 안 움직이고,
        루트 이동(스텝)은 따라간다."""
        return self.wpos("spine")

    def _rotate(self, b, axis_world, rad):
        if abs(rad) < 1e-7:
            return
        ax = (self.W2A.to_3x3() @ Vector(axis_world)).normalized()
        head = b.matrix.translation.copy()
        b.matrix = (Matrix.Translation(head) @ Matrix.Rotation(rad, 4, ax)
                    @ Matrix.Translation(-head) @ b.matrix)
        self._update()

    # ★골반·척추는 자식이 여럿이다(골반 -> 척추 + 양 허벅지).
    # children[0] 을 쓰면 허벅지 쪽을 뼈 방향으로 잡아 몸이 접힌다(모캡 리타게팅에서 발견).
    CHILD_HINT = {"pelvis": "spine", "spine": "neck", "neck": "head"}

    def bone_dir(self, key):
        b = self.pb(key)
        if b is None or not b.children:
            return None
        ch = b.children[0]
        hint = None
        for k, v in self.CHILD_HINT.items():
            if k in b.name.lower():
                hint = v
                break
        if hint:
            for c in b.children:
                if hint in c.name.lower():
                    ch = c
                    break
        a = (self.A2W @ b.matrix).translation
        c = (self.A2W @ ch.matrix).translation
        d = c - a
        return d.normalized() if d.length > 1e-6 else None

    def elbow_axis(self, side):
        d = self.bone_dir("%s upperarm" % side)
        if d is None:
            return (1, 0, 0)
        h = d.cross(FWD)
        if h.length < 1e-4:
            h = d.cross(UP)
        return tuple(h.normalized())

    def blade_dir(self):
        """칼날이 향하는 현재 월드 방향. 칼 오브젝트 없이 손 본만으로 구한다
        (s6 는 칼을 메시에 병합해버려서 오브젝트가 남지 않는다)."""
        b = self.pb("r hand")
        if b is None:
            return None
        return ((self.A2W @ b.matrix).to_3x3() @ BLADE_LOCAL).normalized()

    # ---- 오퍼레이션 ----
    def aim(self, key, target):
        b = self.pb(key)
        d0 = self.bone_dir(key)
        if b is None or d0 is None:
            return
        t = Vector(target)
        if t.length < 1e-9:
            return
        q = d0.rotation_difference(t.normalized())
        ax, ang = q.to_axis_angle()
        self._rotate(b, ax, ang)

    def wrist_bend(self, side="r"):
        """팔뚝 방향과 손 방향의 각도. 0 이면 곧게 편 손목."""
        fa, hd = self.wpos("%s forearm" % side), self.wpos("%s hand" % side)
        pw = self.palm_world(side)
        if fa is None or hd is None or pw is None:
            return 0.0
        a = (hd - fa)
        b = (pw - hd)
        if a.length < 1e-9 or b.length < 1e-9:
            return 0.0
        return math.degrees(a.angle(b))

    # ★손목 꺾임 기본 한계. 사람 손목은 굴곡 80 / 신전 70 도가 끝인데,
    # 칼날 방향을 무제한으로 맞추면 121~153 도까지 꺾인다(관절 감사에서 발견).
    #
    # ★★이 제한은 **조용히 칼날 방향을 바꾼다.** 그게 사고의 원인이었다.
    # 포즈에 적은 BLADE 방향이 손목 한계를 넘으면 여기서 되돌려지는데, 로그가 안 남아서
    # "적은 대로 나오고 있다"고 착각하게 된다. 실제로 벌어진 일(probe_swing 실측):
    #   · 3연타 1타 S1/E1 이 손목 126/151 도를 요구 -> 제한이 물어서 대각선이 옆으로 쓸림
    #   · 수면참 HS/HE1/HE2 가 152/114/146 도를 요구 -> 내리베기가 가로베기가 됨
    # 제한을 풀면 성격은 살아나지만 손목이 150 도 꺾인 그림이 된다(둘 다 틀렸다).
    # **답은 손 위치다.** 팔뚝이 먼저 벨 방향을 가리키게 손을 놓으면 손목은 20~50 도로
    # 끝나고 적은 칼날 방향이 그대로 나온다. 새 베기 포즈를 만들 때는
    # probe_swing.py 의 "키포즈별 오른손목" 표에서 * 표시가 없는지 반드시 확인할 것.
    WRIST_MAX = 78.0

    def aim_blade(self, target, max_wrist="default"):
        """칼날을 그 방향으로. max_wrist 를 주면 손목이 그 이상 꺾이지 않게 되돌린다.
        ★칼날 방향을 무조건 맞추면 손목이 77 도까지 꺾인다(달리기에서 실측).
        사람 손목은 굽힘 80 / 폄 70 도가 한계이고, 칼을 들고 달릴 땐 거의 곧게 편다."""
        b = self.pb("r hand")
        d0 = self.blade_dir()
        if b is None or d0 is None:
            return
        q = d0.rotation_difference(Vector(target).normalized())
        ax, ang = q.to_axis_angle()
        self._rotate(b, ax, ang)
        if max_wrist == "default":
            max_wrist = self.WRIST_MAX
        if max_wrist is None:
            return
        for _ in range(14):
            w = self.wrist_bend("r")
            if w <= max_wrist + 0.5:
                break
            self._rotate(b, ax, -math.radians(min(8.0, w - max_wrist)))

    def ik(self, side, target_world, label="", lat_mul=1.0, pole_ruf=None):
        """2본 IK: 어깨-팔꿈치-손목. 팔꿈치는 pole 방향으로 밀어낸다.
        pole 을 옆+아래로 고정하면 상단세(머리 위)에서 팔꿈치가 아래로 꺾여
        어색하므로, 손이 어깨보다 높아질수록 팔꿈치도 위로 뜨게 한다."""
        ua, fa, hd = (self.pb("%s upperarm" % side), self.pb("%s forearm" % side),
                      self.pb("%s hand" % side))
        if not (ua and fa and hd):
            return
        A = (self.A2W @ ua.matrix).translation.copy()
        B = (self.A2W @ fa.matrix).translation.copy()
        C = (self.A2W @ hd.matrix).translation.copy()
        L1, L2 = (B - A).length, (C - B).length
        T = Vector(target_world)
        v = T - A
        d = v.length
        if d < 1e-6:
            return
        n = v / d
        reach = L1 + L2
        if d > reach * 0.999:
            self.reach_log.append((label or side, round(d / reach, 3)))
            d = reach * 0.999
        # 코사인법칙으로 어깨각
        c = max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)))
        ang = math.acos(c)
        lat = RIGHT * (1.0 if side == "r" else -1.0)
        rel_u = (T - A).dot(UP) / self.H
        up_bias = -1.15 + 1.75 * max(0.0, min(1.0, (rel_u + 0.05) / 0.28))
        if pole_ruf is not None:
            pr, pu, pf = pole_ruf
            pole = (lat * pr + UP * pu + FWD * pf)
        else:
            pole = (lat * (0.34 * lat_mul) + UP * up_bias + FWD * 0.30)
        perp = pole - n * pole.dot(n)
        if perp.length < 1e-5:
            perp = n.cross(UP)
        perp.normalize()
        elbow = A + n * (L1 * math.cos(ang)) + perp * (L1 * math.sin(ang))
        self.aim("%s upperarm" % side, elbow - A)
        B2 = (self.A2W @ fa.matrix).translation
        self.aim("%s forearm" % side, (A + n * d) - B2)

    def hand_rot(self, side):
        """손 본의 월드 회전(스케일 제거)."""
        b = self.pb("%s hand" % side)
        return None if b is None else (self.A2W @ b.matrix).decompose()[1]

    def align_hand(self, side, target_q):
        """손 본의 월드 회전을 target 으로 맞춘다.
        ★pb.matrix 에 행렬을 직접 대입하면 아마추어 스케일(0.0254)이 날아가
        손이 39 배로 부푼다. head 를 피벗으로 **회전만** 건다."""
        b = self.pb("%s hand" % side)
        cur = self.hand_rot(side)
        if b is None or cur is None:
            return
        ax, ang = (target_q @ cur.inverted()).to_axis_angle()
        self._rotate(b, ax, ang)

    def grip(self, back):
        """왼 **주먹 중심**을 자루 축 위에 올린다. back = 오른 주먹에서 물미 쪽으로
        떨어진 거리(H 단위). 양손이 자루에 묶이면 팔이 몸을 감아 돌 수가 없다.

        IK 는 '손목'을 목표점에 놓기 때문에, 주먹이 원하는 자리에 오게 하려면
        오차를 되먹여 몇 번 반복해야 한다(손목→주먹 오프셋의 방향이 팔 자세에
        따라 달라져서 한 번에 못 맞춘다)."""
        bd = self.blade_dir()
        if bd is None:
            return
        axis_pt = self.palm_world("r")
        if axis_pt is None:                      # 주먹 정보가 없으면 옛 방식
            axis_pt = self.wpos("r hand")
        if axis_pt is None:
            return
        want = axis_pt - bd * (back * self.H)    # 왼 주먹 중심이 있어야 할 곳
        # ★왼 팔꿈치를 **뒤-아래**로 보낸다. 옆으로 두면 팔뚝이 배 앞을
        # 거의 수평(14도)으로 가로질러 팔이 교차한 것처럼 보인다(실측).
        # 검도에서도 왼 팔꿈치는 몸통 옆 아래, 살짝 뒤다.
        pole = (0.18, -1.00, -0.85)
        # ★손 **회전**. IK 는 위치만 맞추고 손 본의 자체 회전은 방치돼 있었다.
        # 그래서 왼 주먹이 자루 위에 얹혀만 있고 "전혀 다른 방향의 칼을 쥔 손"
        # 모양이었다(실측: 자루 통과축이 평균 64.7 도, 최대 130 도 어긋남.
        # 오른손은 칼이 강체로 붙어 있어 항상 0 도). 주먹 메시가 본 로컬 Z 로
        # 정확히 대칭이라 정답은 한 줄이다: **왼손 월드 회전 = 오른손 월드 회전.**
        tq = self.hand_rot("r")
        n0 = len(self.reach_log)
        tgt = want.copy()
        best, best_d = tgt.copy(), 1e9
        for _ in range(8):
            del self.reach_log[n0:]              # 반복 흔적이 쌓이지 않게
            self.ik("l", tgt, label="l grip", pole_ruf=pole)
            if tq is not None:
                self.align_hand("l", tq)         # 손을 돌리면 주먹이 밀리므로 되먹임 안에서
            got = self.palm_world("l")
            if got is None:
                return
            err = want - got
            if err.length < best_d:
                best_d, best = err.length, tgt.copy()
            if err.length < self.H * 0.002:
                return
            tgt = tgt + err
        if (want - self.palm_world("l")).length > best_d + 1e-9:
            del self.reach_log[n0:]
            self.ik("l", best, label="l grip", pole_ruf=pole)
            if tq is not None:
                self.align_hand("l", tq)

    def swing(self, key, axis, deg):
        b = self.pb(key)
        if b is None:
            print("!bone", key)
            return
        if axis == ELBOW:
            axis = self.elbow_axis("l" if key.lower().startswith("l") else "r")
        self._rotate(b, axis, math.radians(deg))

    def reset(self):
        for b in self.arm.pose.bones:
            b.rotation_mode = "QUATERNION"
            b.matrix_basis = Matrix()
        self._update()

    def apply(self, pose, reset=True):
        """리스트 순서대로 적용. spine -> 오른팔 IK -> BLADE -> 왼손 GRIP 순서를 지킬 것.
        GRIP 은 칼날 방향이 정해진 뒤라야 자루 위치를 알 수 있다.
        reset=False 면 지금 포즈 위에 덧씌운다(원본 에셋 하체 + 우리 팔 조합용)."""
        if reset:
            self.reset()
            self.arm.location = self.home + Vector(pose.get("r", (0, 0, 0))) * self.H
            self._update()
        for key, op, val in pose["b"]:
            if op == AIM:
                self.aim(key, ruf(*val))
            elif op == BLADE:
                if isinstance(val, (list, tuple)) and len(val) == 4:
                    self.aim_blade(ruf(*val[:3]), max_wrist=val[3])
                else:
                    self.aim_blade(ruf(*val))
            elif op == IK:
                # 기준점은 매번 다시 잡는다. 골반을 돌리면 척추 head 가 움직인다.
                org = self.origin()
                self.ik(key, org + (RIGHT * val[0] + UP * val[1] + FWD * val[2]) * self.H,
                        label=key)
            elif op == FACE:
                b = self.pb(key)
                if b is not None:
                    m = (self.A2W @ b.matrix).to_3x3()
                    fd = (m @ HEAD_FACE_LOCAL).normalized()
                    td = ruf(*val)
                    a0 = math.atan2(fd.dot(RIGHT), fd.dot(FWD))
                    a1 = math.atan2(td.dot(RIGHT), td.dot(FWD))
                    self._rotate(b, tuple(UP), a0 - a1)
            elif op == ARC:
                sh = self.wpos("%s upperarm" % key)
                if sh is not None:
                    self.ik(key, sh + ruf(*val[:3]) * (val[3] * self.H), label=key)
            elif op == GRIP:
                self.grip(val)
            else:
                self.swing(key, op, val)


def grip_of(spec):
    """포즈에서 GRIP 값(양손 간격)을 뽑는다. 없으면 None."""
    bl = spec["b"] if isinstance(spec, dict) else spec
    for k, op, v in bl:
        if op == GRIP:
            return v
    return None


def relock_grip(ps, frames, bones=("l upperarm", "l forearm", "l hand")):
    """★키프레임 **사이** 프레임에서 왼 주먹을 자루에 다시 붙인다.

    키포즈는 전부 자루를 정확히 쥐게 만들어도, 본은 쿼터니언으로 보간되는데
    IK 해는 비선형이라 중간 프레임에서 손이 자루를 놓친다.
    실측(수면참): 키는 이탈 0.00 인데 사이 프레임 최대 0.16 H = 주먹 2.3 개.
    이게 "휘두를 때 손이랑 손잡이가 따로 노는" 그림의 정체였다.
    그래서 매 프레임 왼팔만 다시 풀고 그 프레임에 키를 박는다.

    frames = [(프레임, 포즈), ...] (액션을 만들 때 쓴 그대로)
    한손 포즈가 낀 구간은 건드리지 않는다(일부러 자루를 놓는 동작이므로)."""
    import bpy
    ks = []
    for f, spec in frames:
        d = spec if isinstance(spec, dict) else {"b": spec}
        ks.append((f, grip_of(spec), bool(d.get("1h"))))
    ks.sort(key=lambda t: t[0])
    if len(ks) < 2:
        return 0
    pbs = [ps.pb(n) for n in bones]
    pbs = [b for b in pbs if b is not None]
    n = 0
    for i in range(len(ks) - 1):
        (fa, ga, ha), (fb, gb, hb) = ks[i], ks[i + 1]
        if ga is None or gb is None or ha or hb:
            continue                      # 한손 구간·파지 없는 구간은 그대로 둔다
        for f in range(int(fa) + 1, int(fb)):
            bpy.context.scene.frame_set(f)
            t = (f - fa) / float(fb - fa)
            ps.grip(ga + (gb - ga) * t)
            for b in pbs:
                b.keyframe_insert("rotation_quaternion", frame=f)
            n += 1
    # 새로 박은 키는 선형으로. 매 프레임 키가 있으니 베지어 오버슈트만 손해다.
    act = ps.arm.animation_data.action if ps.arm.animation_data else None
    if act:
        names = set(b.name for b in pbs)
        try:
            for lay in act.layers:
                for st in lay.strips:
                    for cb in st.channelbags:
                        for fc in cb.fcurves:
                            if any(('"%s"' % nm) in fc.data_path for nm in names):
                                for kp in fc.keyframe_points:
                                    kp.interpolation = "LINEAR"
        except Exception:
            pass
    return n


def P(bones, root=(0, 0, 0), onehand=False, wind=False):
    """onehand=True  왼손이 자루를 놓는다(최대 신전). 검증기가 파지 검사를 건너뛴다.
    wind=True     되감기 구간. 칼이 몸 뒤로 가도 된다(모으는 동작이므로)."""
    return {"b": bones, "r": root, "1h": onehand, "wind": wind}


# ---------------------------------------------------------------- 호(弧) 만들기
# ★왜 필요한가 (v74 개정의 핵심). 키를 드문드문 찍으면 **칼이 호를 안 그린다.**
# 실측(옛 3연타 1타) 칼끝 높이: f9 1.38 -> f10 1.41 -> f11 2.42 -> f12 1.51.
# 칼이 호를 도는 게 아니라 손 안에서 프로펠러처럼 돌았다. 궤적 길이 6.28 m 인데
# 양 끝 사이 거리는 2.24 m — 절반 넘게 제자리에서 되짚은 것이다.
# 원인 두 가지가 겹쳤다.
#   1) 팔(부모)과 손(자식) 회전이 **따로** 보간된다. 두 슬러프의 합성은
#      합성의 슬러프가 아니라서 중간 프레임에 칼날 방향이 크게 튄다.
#   2) 슬러프는 **최단 경로**로 간다. 袈裟(오른위->왼아래)처럼 칼날이 160도 넘게
#      도는 동작은 최단 경로가 "머리 위로 넘어가는" 반대쪽 길이다. 작가가 적은
#      호와 정반대 길로 가는 것이다.
# 답: 타격 구간은 작가가 **통과점**을 찍고 그 사이를 **매 프레임** 채운다.
# 보간이 개입할 틈이 없어지고, 속도 곡선도 프레임별 u 값으로 우리가 정한다.
# 통과점 사이 칼날 회전은 60도를 넘기지 않게 잡는다(그 이상이면 다시 튄다).

_ORD = {AIM: 1, FACE: 1, IK: 2, ARC: 2, BLADE: 3, GRIP: 4}


def _slerp(a, b, t):
    va, vb = Vector(a).normalized(), Vector(b).normalized()
    if va.dot(vb) < -0.9995:            # 정반대면 회전축이 안 정해진다
        return tuple(va)
    return tuple(va.slerp(vb, t))


def _mix(op, a, b, t):
    """항목 하나를 섞는다. 방향은 구면, 좌표·각도는 직선."""
    if op in (AIM, FACE):
        return _slerp(a, b, t)
    if op == BLADE:
        da = tuple(a[:3])
        db = tuple(b[:3])
        d = _slerp(da, db, t)
        wa = a[3] if len(a) == 4 else None
        wb = b[3] if len(b) == 4 else None
        if wa is None and wb is None:
            return d
        wa = wb if wa is None else wa
        wb = wa if wb is None else wb
        return (d[0], d[1], d[2], wa + (wb - wa) * t)
    if op in (IK, ARC):
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * t          # GRIP 과 축 회전 각도
    return a if t < 0.5 else b


def blend(pa, pb, t):
    """두 포즈 사이 t(0~1) 지점. 한쪽에만 있는 항목은
       · 각도면 0 에서 풀거나 0 으로 접고
       · 위치·방향·파지면 그 쪽이 우세할 때만 쓴다(양손<->한손 전환이 여기서 갈린다).
    적용 순서는 회전 -> 팔 IK -> 칼날 -> 파지 로 다시 세운다(apply 주석 참고)."""
    ba = pa["b"] if isinstance(pa, dict) else pa
    bb = pb["b"] if isinstance(pb, dict) else pb
    mb = {(k, o): v for k, o, v in bb}
    out, seen = [], set()
    for k, o, v in ba:
        seen.add((k, o))
        if (k, o) in mb:
            out.append((k, o, _mix(o, v, mb[(k, o)], t)))
        elif isinstance(v, (int, float)):
            out.append((k, o, v * (1.0 - t)))
        elif t < 0.5:
            out.append((k, o, v))
    for k, o, v in bb:
        if (k, o) in seen:
            continue
        if isinstance(v, (int, float)):
            out.append((k, o, v * t))
        elif t >= 0.5:
            out.append((k, o, v))
    out.sort(key=lambda e: _ORD.get(e[1], 0))    # 안정 정렬: 같은 등급은 원래 순서
    da = pa if isinstance(pa, dict) else {}
    db = pb if isinstance(pb, dict) else {}
    ra, rb = da.get("r", (0, 0, 0)), db.get("r", (0, 0, 0))
    near = db if t >= 0.5 else da
    return P(out, root=tuple(ra[i] + (rb[i] - ra[i]) * t for i in range(3)),
             onehand=bool(near.get("1h")), wind=bool(near.get("wind")))


def tip_of(pose):
    """이 포즈에서 칼끝이 놓이는 자리(r,u,f 근사). 통과점 사이 간격 재는 용도다.
    실측 대조: 칼끝 = 오른 주먹 + 0.55 H x 칼날 방향. 칼이 휘어 있어 8~10도
    어긋나지만, 구간 길이 비율만 쓰므로 그 정도면 충분하다."""
    hand = blade = None
    for k, o, v in (pose["b"] if isinstance(pose, dict) else pose):
        if o == IK and k == "r":
            hand = v
        elif o == BLADE and "hand" in k:
            blade = v
    if hand is None or blade is None:
        return None
    return Vector(hand) + Vector(blade[:3]).normalized() * 0.55


def arc_marks(way):
    """통과점들이 호 위 어디쯤(0~1)에 놓이는지. 스케줄 짤 때 임팩트 통과점의
    u 값을 알아야 최고속을 거기에 맞출 수 있다."""
    ts = [tip_of(p) for p in way]
    seg = [(1.0 if (ts[i] is None or ts[i + 1] is None)
            else max(1e-4, (ts[i + 1] - ts[i]).length)) for i in range(len(way) - 1)]
    tot = sum(seg)
    cum = [0.0]
    for s in seg:
        cum.append(cum[-1] + s / tot)
    return cum, tot


def stroke(way, sched):
    """way = 호를 지나는 통과점 포즈들. sched = [(프레임, u)], u 0~1.
    반환 [(프레임, 포즈)]. 매 프레임 키라서 본 보간이 끼어들지 않는다.

    ★u 는 **칼끝이 지나간 거리**의 비율이다(균등 매개변수가 아니다).
    통과점을 균등 매개변수로 나눴더니 짧은 구간에서 칼이 느려지고 긴 구간에서
    빨라져 속도에 계단이 생겼다(실측: 설계 1.02 자리에 0.72 가 찍혔다).
    거리로 나누면 **Δu x 전체 궤적길이 = 그 프레임의 칼끝 속도**가 되어
    '느리게 들어가 - 타격에서 최고속 - 팔로스루로 감속'을 u 표만 보고 설계할 수 있다."""
    cum, _ = arc_marks(way)
    n = len(way) - 1
    out = []
    for f, u in sched:
        u = max(0.0, min(1.0, u))
        i = 0
        while i < n - 1 and u > cum[i + 1]:
            i += 1
        span = cum[i + 1] - cum[i]
        out.append((f, blend(way[i], way[i + 1], (u - cum[i]) / span if span else 0.0)))
    return out


# ---------------------------------------------------------------- 포즈 정의
# 검도 카마에 기반. 손은 정중선 근처에서 작게 움직이고 칼날이 크게 돈다.
# 오른손 r 은 -0.15 ~ +0.22, f 는 항상 +0.12 이상(= 몸 앞)을 지킨다.
# 양손 간격(H 단위). ★주먹 반지름이 0.072 H 라 **0.144 보다 좁으면 두 주먹이 겹친다.**
# 0.070 으로 뒀더니 왼손이 자루가 아니라 오른 팔뚝 위에 얹혀 팔이 교차해 보였다(오너 지적).
# 손목 기준으로는 왼손이 배보다 뒤여도, 주먹 앞면(+0.072)은 배(0.154) 밖으로 나온다.
# ★손 회전을 오른손과 같게 잠근 뒤(align_hand) 두 주먹이 **한 덩어리로 뭉쳐** 보였다.
# 주먹의 자루축 방향 길이가 0.2765(월드)라 반이 0.138. GB 0.112 H = 0.270 은
# 0.276 과 거의 같아서 두 주먹이 딱 맞닿는다. 방향이 다를 땐 두 덩어리로 읽혔는데
# 같아지니 하나의 살덩이가 됐다(손가락·너클이 없는 메시라 구분할 단서가 없다).
# 사이에 자루가 보이게 0.074 월드쯤 띄운다.
GB = 0.142

# 中段の構え — 양손 배꼽 앞, 칼끝은 상대 목을 겨눈다. 검도의 기본 자세
# 中段の構え. 실측 기준(척추 높이에서 몸통 앞면 = +0.154 H):
#   1차 시안은 오른손 f 0.13 → **왼손이 +0.056 = 몸 안으로 0.10 H 파묻혔다.**
#   ("배꼽에 손 올려놓은 듯" - 오너). 검도는 왼손이 배꼽에서 주먹 하나 앞이다.
#   팔 길이 한계(오른손 f 0.21 에서 IK 비율 1.00) 안까지 밀고, 자루 잡는 간격도
#   GB 0.078 → 0.070 으로 줄여 왼손을 앞으로 당겼다.
# 팔만 따로 뺀다. 원본 에셋 달리기처럼 **하체는 남의 모션**을 쓰고
# 팔만 우리 중단세로 덮어야 할 때가 있다.
GUARD_ARMS = [
    ("r clavicle", Z, 4),                        # 어깨를 살짝 앞으로 내밀어 여유 확보
    ("r", IK, (0.02,  0.07, 0.21)),
    # ★칼날 방향이 곧 왼손 위치를 정한다. 왼손 = 오른 주먹에서 칼날 반대쪽으로 GB.
    # 앞 성분이 크면(0.87) 왼손이 그만큼 뒤로 끌려가 **배(코트) 안에 박힌다.**
    # 실측: 왼 주먹 f 0.131 인데 그 높이의 코트 앞면이 0.154 → 0.33 주먹만큼 파묻힘.
    # 칼을 세워(39도) 앞 성분을 0.76 으로 줄이면 왼 주먹이 코트 밖으로 나온다.
    # 이보다 더 세우면 팔이 안 닿는다(IK 클램프). 실측 스윕으로 고른 값.
    ("r hand", BLADE, (0.20, 0.62, 0.76)),
    ("l", GRIP, GB),
]

# spine X 5 는 상체를 앞으로 숙여 배를 손 쪽으로 밀었다. 2 로 줄여 여유를 만든다.
# ★달릴 때는 중단세가 **물리적으로 불가능**하다. 달리기는 상체를 크게 숙이는데
# 중단세는 손을 배 앞 정중선에 두므로, 팔을 최대로 뻗어도(f 0.34, IK 한계 초과)
# 왼 주먹이 코트 안으로 0.66 주먹 파묻힌다(실측). 레퍼런스에서도 이동 중에는
# 칼을 몸 옆·뒤로 내려 **한 손으로** 든다. 왼팔은 원본 달리기의 팔 흔들기를 그대로 쓴다.
def run_arms(sw):
    """달리기 팔. sw = -1(오른 다리 뒤) ~ +1(오른 다리 앞).
    팔은 **같은 쪽 다리와 반대로** 흔든다. 이게 없으면 칼이 골반에 붙은 판자로 보인다.
    원본 달리기의 왼팔을 그대로 쓰면 안 된다 - 소총을 든 전투 달리기라
    빈손이 얼굴 앞까지 올라온다(렌더로 확인).
    칼은 크고 무거우므로 오른팔 진폭은 왼팔의 절반만."""
    # 실측 대조로 잡은 값 (연구: 몸통 5~10도 앞기울기 / 팔꿈치 약 90도 유지 ROM 30~56도 /
    # 손은 엉덩이에서 가슴까지 / 팔은 몸을 가로지르지 않고 앞뒤로).
    # 고친 이력:
    #   · 뒤로 젖힌 목표가 어깨에서 0.31 H = **팔 길이 그대로**라 팔꿈치가 162 도까지
    #     펴졌다(막대기 팔). 손도 배꼽 높이에서만 움직여 가슴까지 안 올라왔다.
    #   · 그다음 (r,u,f) 를 직선 보간했더니 어깨와의 거리가 크게 변해 팔꿈치가
    #     46~142 도로 벌어졌다(접혔다 펴졌다).
    # ★실제 팔 흔들기는 어깨를 중심으로 한 **호**를 그리며 팔꿈치 각을 유지한다.
    #   그래서 어깨에서 반지름 R 인 구면 위에 목표를 놓는다. R 이 팔꿈치 각을 정한다.
    def swing_dir(d_back, d_fwd, t):
        u = (t + 1.0) * 0.5
        return tuple(Vector(d_back).normalized()
                     .lerp(Vector(d_fwd).normalized(), u).normalized())

    LD = swing_dir((-0.16, -0.86, -0.48), (0.30, -0.46, 0.83), sw)
    RD = swing_dir((0.14, -0.92, -0.37), (0.26, -0.66, 0.70), -sw)
    return [
        # 어깨는 골반과 **반대로** 돈다. 원본에도 15.8도 들어있지만 더 실어야 산다.
        # 달리기는 몸통을 5~10 도 앞으로 기울인다(연구 실측). 우리는 오히려
        # 7.2 도 **뒤로** 젖혀져 있었다 - 그게 "허리가 뻣뻣하다"의 정체.
        ("spine", X, 9),
        ("spine", Z, -6.0 * sw),
        # ★목은 원본 움직임(앞뒤 0.219 / 좌우 0.106)을 그대로 쓰고 **상수 기울기만** 뺀다.
        # 절대 방향으로 못 박으면 상체가 통째로 굳는다(오너 지적).
        # 실측: 보정 없으면 좌우 +0.39~0.49, -26도 걸면 -0.01~+0.08 로 선다.
        ("neck", (0, -1, 0), -26),
        # 머리는 원본에서 앞뒤 폭이 **0.000** 이라 가져와도 안 움직인다. 직접 흔든다.
        # 달리는 사람은 시선을 안정시키므로 머리는 거의 수평을 유지하며 살짝만 끄덕인다.
        ("head", AIM, (0.02 * sw, 1.0, -0.03 + 0.06 * sw)),
        ("head", FACE, (0.03 * sw, 0.0, 1.0)),   # 달릴 땐 정면을 본다

        ("r clavicle", Z, -5),
        ("r", ARC, (RD[0], RD[1], RD[2], 0.245 + 0.020 * sw)),  # 칼이 무거워 진폭 작게
        # ★칼끝은 **앞·아래**. 뒤로 끌면 판자처럼 보이고, 옆으로 기울면 정면에서
        # 비스듬해 보인다. 좌우 성분 0 으로 두어 몸 정면과 나란히 든다.
        # 손목 꺾임 22도 한계. 방향을 무조건 맞추면 77도까지 꺾인다.
        ("r hand", BLADE, (0.0, -0.38, 0.925, 22.0)),
        ("l clavicle", Z, 5),
        # 반지름을 살짝 흔들어 팔꿈치가 **앞에서 더 접히고 뒤에서 펴지게** 한다.
        # 완전히 일정하면 기계처럼 보인다(실측 ROM 0도였다).
        ("l", ARC, (LD[0], LD[1], LD[2], 0.235 - 0.030 * sw)),
    ]


RUN_ARMS = run_arms(0.0)

GUARD = P([("spine", X, 2), ("spine", Z, -4)] + GUARD_ARMS + [
    ("l thigh", Z, -8), ("r thigh", Z, -8),
    ("l thigh", X, 8), ("r thigh", X, -10),      # 오른발 뒤 (검도 앞뒤 발)
])

# ================================================================ 공통 부품
# 포즈를 "몸 한 벌 + 팔 한 벌"로 적는다. 통과점이 20개를 넘어가면 좌표를 통째로
# 적어서는 어디를 고쳐야 할지 안 보인다.
# ★순서가 곧 적용 순서다. 몸통(회전)이 먼저, 팔 IK 가 나중이어야 한다.
#   반대로 적었더니 안 돌아간 몸통 기준으로 IK 를 풀고 나서 몸통이 돌아버려
#   팔이 통째로 끌려갔다(팔 사거리가 1.6 배까지 늘어났다).


def _arm(hand, blade, gb=GB, cz=4.0, cy=0.0):
    """오른팔 한 벌. hand=(r,u,f) 주먹 자리 / blade=(r,u,f) 칼날이 향할 곳.
    ★팔 사거리는 어깨에서 0.309 H 다(tune_swing 실측). 낮고 왼쪽인 자리는 금방
    사거리 밖으로 나간다. 칼끝을 더 보내고 싶으면 손이 아니라 **칼날을 눕힌다.**"""
    return [("r clavicle", Z, cz), ("r clavicle", Y, cy),
            ("r", IK, hand), ("r hand", BLADE, blade), ("l", GRIP, gb)]


def _arm1(hand, blade, lhand, cz=4.0, cy=0.0):
    """자루를 놓은 한손 자세. 왼손도 IK(위치)로 적는다.
    ★AIM(방향)으로 적으면 파지->한손 전환 프레임에서 왼팔이 100도 넘게 순간이동한다.
      위치로 적고, 놓는 순간 좌표를 파지가 만들어 준 자리에 맞춰 두면 이어진다."""
    return [("r clavicle", Z, cz), ("r clavicle", Y, cy),
            ("r", IK, hand), ("r hand", BLADE, blade), ("l", IK, lhand)]


def _body(pz, sz, sx, lt, rt, lc=0.0, rc=0.0, hx=0.0, tz=-8.0):
    """몸통 한 벌.
      pz 골반 비틀기 / sz 척추 비틀기 / sx 앞숙임 / lt,rt 허벅지 앞뒤(+ 가 앞)
      lc,rc 무릎 굽힘 / hx 고개 끄덕임 / tz 다리 벌림
    ★팔만 휘두르면 장난감이다. 골반이 먼저 돌고 척추가 따라가고 팔이 끌려간다.
    ★체중 이동은 **무릎**으로 적는다. 3연타는 루트 이동을 안 쓰는데(게임이 캐릭터를
      직접 옮긴다) 게임은 매 프레임 가장 낮은 발을 바닥에 붙이므로, 무릎을 깊게
      굽히면 엉덩이가 알아서 내려앉는다. 렌더 검증도 그 보정을 흉내내야 맞다.
    ★머리 좌우는 자동. 몸통이 돈 만큼 **반대로 0.42** 를 걸어 표적에서 눈을 안 뗀다
      (spine Z + = 오른어깨가 앞 = 상체가 왼쪽으로 돌아간다. 그대로 두면 시선이
       몸통과 같이 돌아 상대를 놓친다 - 횡일섬에서 이미 겪은 사고).
    ★골반을 돌리면 허벅지도 끌려간다. 절반쯤 되돌려 발이 덜 휩쓸리게 한다."""
    return [("pelvis", Z, pz), ("spine", Z, sz), ("spine", X, sx),
            ("head", Z, -0.42 * (pz + sz)), ("head", X, hx),
            ("l thigh", Z, tz - 0.45 * pz), ("r thigh", Z, tz - 0.45 * pz),
            ("l thigh", X, lt), ("r thigh", X, rt),
            ("l calf", X, lc), ("r calf", X, rc)]


# ================================================================ 3연타
# 성격(유지): 1타 袈裟(오른위->왼아래) / 2타 逆袈裟(왼아래->오른위) / 3타 上段 내리베기.
# v74 에서 바꾼 것은 성격이 아니라 **질**이다.
#   · 통과점을 넣어 칼이 진짜 호를 그린다(옛 궤적은 오르내리는 프로펠러였다.
#     궤적 길이 6.28 m 인데 양 끝 거리는 2.24 m — 절반 넘게 되짚었다)
#   · 몸통이 한 타마다 100도 넘게 돌아간다. 골반 -> 척추 -> 팔 순서로.
#     옛 포즈는 몸이 서 있고 손목만 돌아서 "칼만 도는 마네킹"이었다.
#   · 체중이 뒷발에서 앞발로 넘어간다. 무릎 굽힘 차이로 적는다.
#   · 1타 팔로스루가 그대로 2타 시작이다 -> 중간 정지가 없다
#     (옛 f14~f18 5프레임은 칼끝 이동 0.03~0.06 = 사실상 정지였다)
#   · 칼이 낮게 내려온다. 옛 궤적은 칼끝 최저 1.15 m 라 키 1.30 짜리 요괴의
#     머리 위를 스쳤다.

# ---- 1타 袈裟斬り: 오른 어깨 위 -> 왼 아래 ----
# 감아쥠(W1)은 **몸으로** 한다. 칼끝을 뒤로 멀리 보내면 감는 동안 칼이 타격만큼
# 빨라져서(실측 dv 0.95) 예비동작으로 안 읽힌다. 골반·어깨를 깊게 꼬고
# 칼은 오른 관자놀이 옆에 세우기만 한다.
W1 = P(_body(-20, -28, -4, 2, -24, -4, 34, tz=-14)
       + _arm((0.17, 0.33, 0.06), (0.42, 0.76, -0.28), cz=10, cy=-14),
       root=(0, 0.06, -0.02))
A1A = P(_body(-14, -18, 2, 10, -26, -10, 34, tz=-12)
        + _arm((0.19, 0.33, 0.11), (0.44, 0.72, 0.30), cz=8, cy=-10),
        root=(0, 0.03, -0.03))
A1B = P(_body(-2, 0, 12, 22, -30, -18, 30, tz=-10)
        + _arm((0.13, 0.30, 0.19), (0.10, 0.44, 0.89), cz=4, cy=-2),
        root=(0, -0.04, -0.04))
S1 = P(_body(14, 22, 24, 36, -38, -30, 26, tz=-4)
       + _arm((0.01, 0.19, 0.23), (-0.42, -0.34, 0.84), gb=0.128, cz=-2, cy=4),
       root=(0, -0.13, -0.05))
E1 = P(_body(20, 30, 22, 42, -42, -36, 24, tz=0)
       + _arm((-0.10, 0.07, 0.20), (-0.78, -0.55, 0.30), gb=0.116, cz=-8, cy=6),
       root=(0, -0.15, -0.05))
E1B = P(_body(22, 32, 19, 40, -40, -34, 23, tz=2)
        + _arm((-0.07, 0.03, 0.16), (-0.80, -0.58, 0.14), gb=0.110, cz=-11, cy=6),
        root=(0, -0.14, -0.05), wind=True)
# 2타는 따로 감지 않으므로 옛 이름 W2 는 이 자세를 가리킨다(검증 스크립트 호환).
W2 = E1B

# ---- 2타 逆袈裟: 왼 아래 -> 오른 위 ----
# ★따로 감지 않는다. 1타 팔로스루의 끝(E1B)이 그대로 2타의 시작이다.
#   여기서 골반이 먼저 반대로 돌기 시작하는 게 예비동작이다.
A2A = P(_body(16, 24, 18, 37, -38, -31, 22, tz=0)
        + _arm((-0.07, 0.06, 0.20), (-0.86, -0.30, 0.42), gb=0.118, cz=-8, cy=2),
        root=(0, -0.13, -0.05))
A2B = P(_body(6, 8, 12, 30, -32, -25, 20, tz=-2)
        + _arm((-0.04, 0.13, 0.25), (-0.42, 0.06, 0.90), gb=0.130, cz=-2, cy=0),
        root=(0, -0.09, -0.05))
S2 = P(_body(-6, -8, 6, 22, -24, -18, 16, tz=-6)
       + _arm((0.07, 0.18, 0.23), (0.05, 0.30, 0.95), cz=2, cy=-2),
       root=(0, -0.05, -0.05))
A2C = P(_body(-14, -18, 0, 16, -18, -12, 12, tz=-8)
        + _arm((0.13, 0.25, 0.20), (0.35, 0.58, 0.73), cz=6, cy=-6),
        root=(0, -0.03, -0.05))
E2 = P(_body(-19, -26, -6, 11, -14, -8, 9, tz=-10)
       + _arm((0.17, 0.30, 0.12), (0.58, 0.72, 0.38), cz=9, cy=-10),
       root=(0, -0.02, -0.04))
E2B = P(_body(-22, -30, -9, 8, -12, -6, 8, tz=-12)
        + _arm((0.20, 0.35, 0.04), (0.74, 0.66, 0.10), cz=11, cy=-13),
        root=(0, 0.00, -0.03))

# ---- 3타 上段からの面: 활처럼 젖혔다가 정중선을 곧게 내려벤다(마무리) ----
# 3연타에서 제일 긴 예비동작(f19~f27). 여기서 속도를 죽여야 3타가 커 보인다.
W3 = P(_body(-8, -6, -20, 8, -18, -6, 16, hx=-10, tz=-10)
       + _arm((0.06, 0.38, 0.00), (0.08, 0.58, -0.81), cz=6, cy=-6),
       root=(0, 0.07, 0.03))
A3A = P(_body(-4, -3, -12, 12, -22, -10, 20, hx=-8, tz=-9)
        + _arm((0.06, 0.37, 0.06), (0.05, 0.97, -0.24), cz=5, cy=-4),
        root=(0, 0.05, 0.01))
A3B = P(_body(0, 0, 2, 20, -28, -16, 24, hx=-4, tz=-8)
        + _arm((0.05, 0.33, 0.14), (0.02, 0.80, 0.60), cz=4, cy=-2),
        root=(0, -0.02, -0.02))
A3C = P(_body(3, 3, 16, 32, -36, -26, 28, tz=-6)
        + _arm((0.03, 0.27, 0.20), (0.00, 0.36, 0.93), cz=2, cy=0),
        root=(0, -0.12, -0.06))
S3 = P(_body(5, 5, 28, 46, -46, -40, 32, hx=6, tz=-4)
       + _arm((0.02, 0.19, 0.24), (-0.02, -0.26, 0.965), cz=0, cy=2),
       root=(0, -0.24, -0.10))
E3 = P(_body(5, 4, 33, 50, -50, -44, 34, hx=10, tz=-2)
       + _arm((0.01, 0.08, 0.24), (-0.03, -0.80, 0.60), gb=0.130, cz=-4, cy=4),
       root=(0, -0.28, -0.12))
E3B = P(_body(4, 3, 31, 47, -47, -41, 32, hx=11, tz=-2)
        + _arm((0.01, 0.03, 0.21), (-0.04, -0.92, 0.39), gb=0.126, cz=-6, cy=4),
        root=(0, -0.27, -0.12))

REC = P(_body(0, -2, 12, 20, -22, -12, 16, tz=-8)
        + _arm((0.03, 0.17, 0.26), (0.02, 0.10, 0.99)),
        root=(0, -0.12, -0.05))

# 타이밍 표. u 는 그 호 위의 진행도(0~1)이고 **프레임별 증분이 곧 칼끝 속도**다.
# 산 모양이 되게 짰다: 두세 프레임 느리게 들어가고 타격 통과점에서 최고,
# 서너 프레임에 걸쳐 감속. 옛 모션은 한 프레임에 2.33 이 튀고 다음에 0.05 로
# 죽는 '계단'이었다.
_A0 = [(1, GUARD), (2, blend(GUARD, W1, 0.12)), (3, blend(GUARD, W1, 0.38)),
       (4, blend(GUARD, W1, 0.72))]           # 감아쥠: 느리게 들어가 끝에서 빨라진다
# u 표. 임팩트 통과점 위치는 arc_marks 로 잰다(1타 S1@0.68 / 2타 S2@0.55 /
# 3타 S3@0.74). 최고속 구간이 그 u 를 지나가게 맞춘다.
# ★2·3타 프레임 자리는 게임 쪽 제약도 받는다. main.js 는 클립 진행도로 궤적 크기와
#   타격 이펙트를 켠다(u>0.30 에서 커지고 u>0.58 에서 터진다). 2타의 빠른 구간은
#   f16 이후, 3타는 f29 이후여야 그 게이트를 통과한다.
_A1 = stroke([W1, A1A, A1B, S1, E1, E1B],
             [(5, 0.00), (6, 0.04), (7, 0.16), (8, 0.50),
              (9, 0.84), (10, 0.95), (11, 1.00)])
_A2 = stroke([E1B, A2A, A2B, S2, A2C, E2, E2B],
             [(12, 0.03), (13, 0.09), (14, 0.20), (15, 0.44),
              (16, 0.78), (17, 0.94), (18, 1.00)])
_A3 = stroke([W3, A3A, A3B, A3C, S3, E3, E3B],
             [(27, 0.00), (28, 0.03), (29, 0.12), (30, 0.32),
              (31, 0.68), (32, 0.90), (33, 0.97), (34, 1.00)])

SEQ = (_A0 + _A1 + _A2
       + [(21, blend(E2B, W3, 0.22)), (24, blend(E2B, W3, 0.60))]
       + _A3
       + [(37, blend(E3B, REC, 0.45)), (41, REC),
          (45, blend(REC, GUARD, 0.55)), (48, GUARD)])
LAST = 48
# 이제 타이밍은 통과점 u 표가 만든다. 여기서 이징을 또 걸면 이중으로 먹는다.
WINDUP_F = set()
STRIKE_F = set()
# 매 프레임 키를 박은 구간. 사이를 베지어로 부풀리면 오히려 오버슛이 생긴다.
ATTACK_LINEAR = set(f for f, _ in _A1 + _A2 + _A3)
TRAILS = [(5, 11), (11, 18), (27, 34)]
IMPACTS = [8, 16, 31]


# ================================================================ 일격기(수면참)
# 성격(유지): **대각선 내리베기**(오른 위 -> 왼 아래). 옆베기는 횡일섬이 맡는다.
# 3연타와 반대로 "느리게 모아서 한 방". 타점이 하나뿐이라 예비동작이 길다.
# v74 에서 고친 것:
#   · 옛 타격은 **한 프레임에 2.33 m** 를 건너뛰었다(= 순간이동). 눈으로 못 읽는다.
#     통과점 6개로 나눠 7프레임에 걸쳐 베고, 최고속을 타격 통과점에 맞췄다.
#   · 벤 뒤 17프레임이 완전 정지(dv 0.01~0.07)였다. 잔심은 '멈춤'이 아니라
#     '아주 느린 지속'이다. 팔로스루로 계속 흘리다가 서서히 선다.
#   · 벤 끝을 낮췄다. 칼끝이 1.16 m 에서 멈추면 요괴 위를 스친다.

HG1 = P(_body(0, -6, 9, 10, -20, -8, 26, tz=-9)
        + _arm((0.03, 0.18, 0.25), (0.04, 0.36, 0.93), cz=5),
        root=(0, 0.02, -0.03))
HG2 = P(_body(-12, -26, 2, 6, -26, -6, 36, tz=-16)
        + _arm((0.13, 0.27, 0.13), (0.34, 0.84, -0.36), cz=8, cy=-14),
        root=(0, 0.06, -0.05))
HG3 = P(_body(-20, -36, -8, 2, -30, -4, 44, hx=-6, tz=-22)
        + _arm((0.20, 0.35, 0.01), (0.50, 0.70, -0.51), cz=12, cy=-20),
        root=(0, 0.10, -0.04))
HM1 = P(_body(-13, -25, 0, 10, -30, -10, 42, tz=-20)
        + _arm((0.19, 0.35, 0.09), (0.42, 0.83, 0.36), cz=10, cy=-16),
        root=(0, 0.05, -0.07))
HM2 = P(_body(-4, -9, 10, 22, -34, -20, 34, tz=-14)
        + _arm((0.13, 0.32, 0.18), (0.16, 0.66, 0.73), cz=6, cy=-10),
        root=(0, -0.04, -0.10))
HM3 = P(_body(6, 10, 20, 36, -42, -32, 28, tz=-6)
        + _arm((0.05, 0.25, 0.23), (-0.10, 0.20, 0.975), cz=2, cy=-2),
        root=(0, -0.15, -0.13))
HS = P(_body(16, 28, 28, 48, -50, -42, 30, hx=6, tz=6)
       + _arm((-0.04, 0.13, 0.24), (-0.50, -0.48, 0.72), gb=0.124, cz=-8, cy=6),
       root=(0, -0.28, -0.16))
HE1 = P(_body(21, 34, 27, 52, -52, -46, 32, hx=5, tz=10)
        + _arm((-0.11, 0.04, 0.18), (-0.72, -0.62, 0.31), gb=0.112, cz=-14, cy=8),
        root=(0, -0.31, -0.17))
HE1B = P(_body(24, 37, 25, 50, -50, -44, 31, hx=4, tz=12)
         + _arm((-0.09, -0.01, 0.14), (-0.62, -0.76, 0.20), gb=0.108, cz=-16, cy=8),
         root=(0, -0.32, -0.17))
# 잔심: 멈추는 게 아니라 아주 느리게 계속 흐른다. 칼끝이 조금 더 가라앉고
# 몸이 아주 천천히 풀린다.
HE1C = P(_body(20, 31, 22, 44, -44, -38, 28, hx=2, tz=10)
         + _arm((-0.06, 0.05, 0.19), (-0.52, -0.80, 0.30), gb=0.116, cz=-12, cy=6),
         root=(0, -0.30, -0.16))
HE2 = P(_body(14, 24, 21, 34, -36, -28, 24, tz=8)
        + _arm((-0.03, 0.22, 0.23), (-0.52, -0.28, 0.81), gb=0.128, cz=-6, cy=4),
        root=(0, -0.27, -0.14))
HR = P(_body(4, 9, 12, 20, -24, -14, 18, tz=2)
       + _arm((0.00, 0.20, 0.29), (-0.28, 0.16, 0.95), cz=0),
       root=(0, -0.14, -0.07))

# ★f27 은 _H1 의 첫 키(u=0 = HG3)와 같다. 같은 프레임을 두 번 적으면
#   probe 의 정렬이 dict 끼리 비교하다 죽는다.
_H1 = stroke([HG3, HM1, HM2, HM3, HS, HE1, HE1B],
             [(27, 0.00), (28, 0.03), (29, 0.11), (30, 0.30),
              (31, 0.66), (32, 0.89), (33, 0.97), (34, 1.00)])
HEAVY_SEQ = ([(1, GUARD), (8, HG1), (14, blend(HG1, HG2, 0.55)), (18, HG2),
              (23, blend(HG2, HG3, 0.6))]
             + _H1
             + [(37, blend(HE1B, HE1C, 0.5)), (41, HE1C),
                (47, HE2), (55, HR), (62, GUARD)])
HEAVY_LAST = 62
HEAVY_WINDUP_F = set()
HEAVY_STRIKE_F = set()
HEAVY_LINEAR = set(f for f, _ in _H1)
HEAVY_TRAILS = [(27, 34)]
HEAVY_IMPACTS = [31]


# ================================================================ 횡일섬(넓은 가로베기)
# 성격(유지): 옆베기. 오너 지시대로 **왼쪽 아래에서 오른쪽 위로** 올려 벤다(逆袈裟).
# v74 에서 고친 것:
#   · 사거리. 옛 궤적은 양 끝 1.85 m 밖에 안 됐다. 감는 쪽을 몸 뒤 왼쪽 아래까지
#     내리고 뻗는 쪽을 오른쪽 위로 더 보내 3 m 급으로 키웠다.
#   · 높이. 옛 궤적은 칼끝 최저 1.31 m 라 요괴(키 1.30)를 거의 못 건드렸다.
#     감는 자리를 0.85 m 까지 내리고 **몸통을 지나가며** 올려 벤다.
#   · 무릎. 감을 때 깊게 앉았다가 벨 때 일어선다. "올려 벤다"는 다리가 만든다.
#   · 자루를 놓는 순간. AIM 으로 적힌 왼팔이 한 프레임에 100도 넘게 튀었다.
#     놓는 자리를 파지 위치와 같은 좌표로 잡고 IK 로 적어 이어지게 했다.

XG1 = P(_body(8, 12, 12, 22, -24, -16, 24, tz=6)
        + _arm((0.01, 0.16, 0.30), (-0.44, -0.24, 0.87), cz=0, cy=2),
        root=(0, 0.02, -0.05))
XG1B = P(_body(20, 22, 12, 34, -34, -28, 32, tz=2)
         + _arm((-0.05, 0.12, 0.21), (-0.66, -0.40, 0.63), gb=0.130, cz=-6, cy=4),
         root=(0, 0.04, -0.09))
XG2 = P(_body(30, 32, 10, 46, -46, -42, 38, hx=2, tz=-2)
        + _arm((-0.11, 0.09, 0.11), (-0.72, -0.62, -0.31), gb=0.116, cz=-14, cy=6),
        root=(0, 0.05, -0.13), wind=True)
XM1 = P(_body(23, 26, 12, 42, -42, -38, 36, tz=0)
        + _arm((-0.07, 0.09, 0.19), (-0.80, -0.56, 0.24), gb=0.120, cz=-10, cy=4),
        root=(0, 0.01, -0.11))
XM2 = P(_body(9, 11, 14, 34, -34, -28, 30, tz=2)
        + _arm((0.01, 0.11, 0.25), (-0.56, -0.56, 0.61), gb=0.132, cz=-4, cy=0),
        root=(0, -0.06, -0.08))
XS0 = P(_body(-6, -6, 15, 26, -28, -20, 24, tz=4)
        + _arm((0.12, 0.11, 0.26), (-0.10, -0.44, 0.89), gb=0.126, cz=4, cy=-4),
        root=(0, -0.13, -0.05))
# 여기서 왼손이 자루를 놓는다. 놓는 좌표는 바로 앞 프레임에서 파지가 만들어 준
# 왼 주먹 자리에 최대한 붙였다(왼팔 사거리 안에서 제일 가까운 점).
XS = P(_body(-18, -20, 12, 16, -20, -12, 16, hx=-8, tz=4)
       + _arm1((0.31, 0.16, 0.16), (0.62, 0.16, 0.77), (0.14, 0.17, 0.05),
               cz=18, cy=-8),
       root=(0, -0.17, -0.02), onehand=True)
XE1 = P(_body(-28, -28, 9, 10, -14, -6, 10, hx=-14, tz=4)
        + _arm1((0.33, 0.20, 0.09), (0.88, 0.34, 0.33), (0.00, 0.10, -0.02),
                cz=20, cy=-12),
        root=(0, -0.18, 0.00), onehand=True)
XE1B = P(_body(-33, -31, 7, 8, -12, -4, 8, hx=-16, tz=4)
         + _arm1((0.31, 0.24, 0.04), (0.92, 0.30, 0.25), (-0.14, 0.06, -0.06),
                 cz=19, cy=-16),
         root=(0, -0.18, 0.01), onehand=True)
XE2 = P(_body(-21, -19, 9, 18, -22, -12, 18, hx=-8, tz=2)
        + _arm((0.13, 0.23, 0.22), (0.62, 0.36, 0.70), cz=8, cy=-6),
        root=(0, -0.12, -0.04))
XR = P(_body(-6, -4, 10, 12, -15, -5, 10, tz=-2)
       + _arm((0.04, 0.18, 0.26), (0.24, 0.14, 0.96), cz=2),
       root=(0, -0.06, -0.05))

_X1 = stroke([XG2, XM1, XM2, XS0, XS, XE1, XE1B],
             [(18, 0.00), (19, 0.04), (20, 0.12), (21, 0.32),
              (22, 0.66), (23, 0.89), (24, 0.97), (25, 1.00)])
WIDE_SEQ = ([(1, GUARD), (6, XG1), (12, XG1B)]      # f18 = _X1 첫 키(XG2)
            + _X1
            + [(29, blend(XE1B, XE2, 0.45)), (36, XE2), (45, XR), (54, GUARD)])
WIDE_LAST = 54
WIDE_WINDUP_F = set()
WIDE_STRIKE_F = set()
WIDE_LINEAR = set(f for f, _ in _X1)
WIDE_TRAILS = [(18, 25)]
WIDE_IMPACTS = [22]



# ================================================================ 점프
# 수직 이동은 코드가 root 를 띄워서 만든다(중력·체공시간을 게임이 제어해야 하므로).
# 여기서는 **다리 모양만** 만든다. 루트 이동을 넣으면 코드와 이중으로 더해진다.
#
# ★1차 시안은 "웅크림 → 폄 → 무릎당김" 3단이라 **다리를 두 번 굽히는** 것처럼 보였다.
#   원인: 키를 누른 순간 vy 가 바로 붙어 몸이 떠오르는데, 클립은 그때부터 웅크림을
#   시작한다. 공중에서 웅크렸다 폈다 다시 당기니 두 번이 된다.
#   예비동작(anticipation)을 쓰려면 도약을 몇 프레임 미뤄야 하는데, 조작감이 무뎌진다.
#   → **예비 웅크림을 빼고 폄에서 시작한다.** 굽힘은 공중 1회 + 착지 1회뿐이다.

JP_LAUNCH = P([                             # 도약 순간: 이미 발끝까지 펴져 있다
    # ★-12(뒤로 젖힘)였다가 무게중심이 뒤로 쏠렸다. 뛰어오를 땐 몸이 앞으로 간다.
    ("spine", X, 7),
    ("r", IK, (0.05, 0.20, 0.26)),
    ("r hand", BLADE, (0.06, 0.34, 0.94)),
    ("l", GRIP, GB),
    ("head", X, -4),
    ("l thigh", X, 10), ("r thigh", X, 6),
    ("l calf", X, -4), ("r calf", X, -2),
])

JP_TUCK = P([                               # 상승: 무릎을 가슴 쪽으로 당긴다 (굽힘 1회)
    ("spine", X, 16),
    ("r", IK, (0.05, 0.19, 0.28)),
    ("r hand", BLADE, (0.05, 0.26, 0.96)),
    ("l", GRIP, GB),
    ("l thigh", X, -56), ("r thigh", X, -32),
    ("l calf", X, 78), ("r calf", X, 52),
])

JP_FALL = P([                               # 하강: 발을 내려 착지를 더듬는다
    ("spine", X, 6),
    ("r", IK, (0.05, 0.18, 0.25)),
    ("r hand", BLADE, (0.05, 0.20, 0.98)),
    ("l", GRIP, GB),
    ("l thigh", X, -14), ("r thigh", X, -20),
    ("l calf", X, 18), ("r calf", X, 24),
])

JP_LAND = P([                               # 착지: 깊게 굽혀 충격을 먹는다 (굽힘 2회)
    # ★86도로 굽혔더니 공중 당김(70도)보다 깊어 "끝에서 한 번 더 굽힌다"로 읽혔다.
    # 착지는 충격 흡수라 얕고 짧아야 한다.
    ("spine", X, 17), ("spine", Z, -3),
    ("r", IK, (0.04, 0.19, 0.30)),
    ("r hand", BLADE, (0.06, 0.18, 0.98)),
    ("l", GRIP, GB),
    ("head", X, 6),
    ("l thigh", X, -28), ("r thigh", X, -30),
    ("l calf", X, 46), ("r calf", X, 48),
])

JUMP_SEQ = [(1, JP_LAUNCH), (7, JP_TUCK), (13, JP_FALL),
            (16, JP_LAND), (23, GUARD)]
JUMP_LAST = 23
JUMP_RISE_F = 7          # 올라가는 동안 여기서 버틴다
JUMP_FALL_F = 13         # 내려오는 동안 여기서 버틴다
JUMP_LAND_F = 16         # 착지 순간 여기로 건너뛴다

# ---------------------------------------------------------------- 검도 기준 팔
# 모캡(CMU subject02 검술)에는 **칼이 안 찍혀 있다**. 몸만 찍혔으므로 손 비틀림이
# 안 넘어온다. 그래서 하체·척추·체중이동은 모캡에서 가져오고 팔과 칼날은 여기서 덮는다.
#
# 검도 교본 수치 (조사)
#   中段: 왼 주먹은 배꼽에서 주먹 하나 앞, 오른손은 츠바 바로 아래, 칼끝은 상대 목
#   面打ち 마무리: **오른 주먹은 어깨 바로 아래에서 바닥과 거의 평행,
#                 왼 주먹은 가슴 바로 아래, 칼끝은 자기 머리 높이**에서 멈춤
#   (우리 기준 높이: 어깨 +0.22H, 가슴 +0.10H, 배꼽 -0.02H, 정수리 +0.44H)
#
# 지금 손으로 만든 베기는 오른손이 u +0.03(배꼽 높이)이라 손이 배에 파묻혔다.
# 자세 자체가 틀렸던 것이지 미세조정 문제가 아니었다.
# ★목·머리는 모캡에서 안 가져온다. 모캡 피험자는 칼을 올려다봤다가 표적을
# 내려다봐서 머리가 +25도 -> -26도, **51도**나 흔들린다(실측). 검사는 표적에서
# 눈을 떼지 않는다. 여기서 자세마다 작은 끄덕임만 준다.
KENDO = {
    # 이름:  (오른손 r,u,f), (칼날 r,u,f), 목 앞기울기, 머리 앞기울기
    "chudan":   ((0.02, 0.07, 0.21), (0.20, 0.62, 0.76), 0.22, -0.05),
    "raise":    ((0.06, 0.24, 0.17), (0.24, 0.88, 0.22), 0.19, -0.09),
    "jodan":    ((0.03, 0.38, 0.09), (0.10, 0.72, -0.68), 0.17, -0.11),
    "strike":   ((0.02, 0.19, 0.27), (0.00, 0.25, 0.97), 0.30, 0.10),
    "settle":   ((0.02, 0.13, 0.24), (0.06, 0.36, 0.93), 0.26, 0.03),
}


def kendo_arms(a, b, t, gb=None):
    """검도 자세 a 에서 b 로 t(0~1) 만큼 간 팔 포즈."""
    ra, ba, na, ha = KENDO[a]
    rb, bb, nb, hb = KENDO[b]
    r = tuple(ra[i] + (rb[i] - ra[i]) * t for i in range(3))
    bd = (Vector(ba).normalized().lerp(Vector(bb).normalized(), t)).normalized()
    nf = na + (nb - na) * t
    hf = ha + (hb - ha) * t
    return [
        ("neck", AIM, (0.0, 1.0, nf)),
        ("head", AIM, (0.0, 1.0, hf)),
        ("head", FACE, (0.0, 0.0, 1.0)),      # 표적에서 눈을 떼지 않는다
        ("r clavicle", Z, 4),
        ("r", IK, r),
        ("r hand", BLADE, (bd.x, bd.y, bd.z, 55.0)),   # 손목 55도 한계
        ("l", GRIP, GB if gb is None else gb),
    ]
