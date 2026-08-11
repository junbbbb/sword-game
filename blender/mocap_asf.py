# -*- coding: utf-8 -*-
"""CMU 모션캡처(ASF/AMC)를 읽어 우리 리그로 리타게팅한다.

왜 이걸 직접 짰나
  검술 모션이 필요한데, 무료 검 모캡 팩(MoCap Online / itch.io)은 전부 로그인·결제
  절차를 요구한다. CMU Graphics Lab 데이터베이스는 직접 받을 수 있고
  **subject 02 의 07/08/09 가 양손 목검 검술**이다(미리보기 영상으로 확인:
  상단세로 들었다가 내려베고, 두 손으로 자루를 잡고 있다).
  BVH 변환본은 직링크가 없어서 원본 ASF/AMC 를 파싱한다.

ASF/AMC 계산
  뼈마다 로컬 좌표계 C(= axis 값으로 만든 회전)가 있고, 프레임의 dof 값으로
  회전 R 을 만든다. 뼈의 전역 회전은
      L = C @ R @ C^-1,   G = G(부모) @ L
  뼈 끝점은  p_child = p + G @ (direction * length).

리타게팅 방식
  ★관절 회전을 그대로 복사하면 안 된다(레스트 포즈가 완전히 다르다).
  각 뼈의 **월드 방향**을 우리 뼈에 aim 으로 옮긴다(asset_anim 과 같은 원리).
  비틀림(roll)은 안 넘어오지만, 칼은 우리가 파지 계산으로 따로 잡으므로 문제없다.
"""
import math
import os
from mathutils import Vector, Matrix

MOCAP = "/Users/lbj/Documents/gameproject/mocap"


def _rot(order, deg):
    """ASF 순서(RX RY RZ 등)대로 회전 행렬을 만든다."""
    m = Matrix.Identity(3)
    for ax, d in zip(order, deg):
        r = Matrix.Rotation(math.radians(d), 3, ax)
        m = r @ m                      # 먼저 적은 축부터 적용
    return m


class Skel(object):
    def __init__(self, asf_path):
        self.dir = {}          # 뼈 방향(단위)
        self.len = {}          # 뼈 길이
        self.C = {}            # 로컬 좌표계
        self.dof = {}          # dof 축 순서 (예 "XZY")
        self.child = {}        # 부모 -> 자식 목록
        self.parent = {}
        self._parse(asf_path)

    def _parse(self, path):
        txt = open(path, errors="ignore").read().splitlines()
        sec = None
        cur = None
        for raw in txt:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith(":"):
                sec = s.split()[0][1:]
                continue
            if sec == "root":
                continue
            if sec == "bonedata":
                if s == "begin":
                    cur = {}
                elif s == "end":
                    n = cur["name"]
                    self.dir[n] = Vector(cur["direction"]).normalized()
                    self.len[n] = cur["length"]
                    ax = cur["axis"]
                    self.C[n] = _rot(ax[3], ax[:3])
                    self.dof[n] = cur.get("dof", "")
                    cur = None
                else:
                    k = s.split()[0]
                    v = s.split()[1:]
                    if k == "name":
                        cur["name"] = v[0]
                    elif k == "direction":
                        cur["direction"] = [float(x) for x in v]
                    elif k == "length":
                        cur["length"] = float(v[0])
                    elif k == "axis":
                        cur["axis"] = [float(v[0]), float(v[1]), float(v[2]), v[3]]
                    elif k == "dof":
                        cur["dof"] = "".join(x[-1].upper() for x in v)
            elif sec == "hierarchy":
                if s in ("begin", "end"):
                    continue
                p = s.split()
                self.child[p[0]] = p[1:]
                for c in p[1:]:
                    self.parent[c] = p[0]
        self.C["root"] = Matrix.Identity(3)
        self.dir["root"] = Vector((0, 0, 0))
        self.len["root"] = 0.0
        self.dof["root"] = "XYZ"

    def pose(self, frame):
        """frame = {뼈이름: [값...]}. 반환 {뼈이름: (머리 위치, 전역회전)}"""
        out = {}
        rootv = frame.get("root", [0] * 6)
        rp = Vector(rootv[0:3])
        rr = _rot("XYZ", rootv[3:6])
        out["root"] = (rp, rr)
        stack = [("root", rp, rr)]
        while stack:
            n, p, g = stack.pop()
            for c in self.child.get(n, []):
                vals = frame.get(c, [])
                d = self.dof.get(c, "")
                deg = [0.0, 0.0, 0.0]
                for i, axc in enumerate(d):
                    if i < len(vals):
                        deg["XYZ".index(axc)] = vals[i]
                R = _rot(d if d else "XYZ",
                         [deg["XYZ".index(a)] for a in (d if d else "XYZ")])
                C = self.C[c]
                gc = g @ (C @ R @ C.inverted())
                # ★ASF 의 direction 은 이미 **전역 좌표**로 적혀 있다. 여기에 로컬
                # 프레임 C 를 또 곱하면 안 된다(다리가 옆으로 벌어졌었다).
                # 그리고 자식 뼈의 끝점은 **자식의** 전역회전으로 옮긴다.
                pc = p + gc @ (self.dir[c] * self.len[c])
                out[c] = (pc, gc)
                stack.append((c, pc, gc))
        return out


def read_amc(path, limit=None):
    frames = []
    cur = None
    for raw in open(path, errors="ignore"):
        s = raw.strip()
        if not s or s.startswith("#") or s.startswith(":"):
            continue
        if s.isdigit():
            if cur is not None:
                frames.append(cur)
                if limit and len(frames) >= limit:
                    return frames
            cur = {}
            continue
        p = s.split()
        if cur is not None:
            cur[p[0]] = [float(x) for x in p[1:]]
    if cur:
        frames.append(cur)
    return frames


# CMU 는 Y 가 위. 우리는 Z 가 위이고 -Y 가 앞.
def cmu2ours(v):
    return Vector((v.x, -v.z, v.y))


# 우리 뼈 <- (CMU 시작관절, CMU 끝관절). 뼈의 **방향**만 옮긴다.
MAP = [
    # ★뼈 벡터 = 끝(그 관절) - 끝(부모 관절). 한 칸씩 밀리면 쇄골에 위팔 방향이
    # 들어가 몸이 접힌다(실제로 그랬다: 쇄골 방향이 (−0.30, −0.21, −0.93) 아래로).
    ("pelvis", "root", "lowerback"),
    ("spine", "lowerback", "thorax"),
    ("neck", "thorax", "upperneck"),
    ("head", "upperneck", "head"),
    ("l clavicle", "thorax", "lclavicle"),
    ("l upperarm", "lclavicle", "lhumerus"),
    ("l forearm", "lhumerus", "lradius"),
    ("l hand", "lradius", "lwrist"),
    ("r clavicle", "thorax", "rclavicle"),
    ("r upperarm", "rclavicle", "rhumerus"),
    ("r forearm", "rhumerus", "rradius"),
    ("r hand", "rradius", "rwrist"),
    ("l thigh", "lhipjoint", "lfemur"),
    ("l calf", "lfemur", "ltibia"),
    ("l foot", "ltibia", "lfoot"),
    ("l toe0", "lfoot", "ltoes"),
    ("r thigh", "rhipjoint", "rfemur"),
    ("r calf", "rfemur", "rtibia"),
    ("r foot", "rtibia", "rfoot"),
    ("r toe0", "rfoot", "rtoes"),
]


def joint_dir(sk, po, a, b):
    """CMU 관절 a 에서 b 로 가는 월드 방향(우리 좌표계)."""
    if a not in po:
        return None
    if b is None:
        p, g = po[a]
        v = g @ (sk.dir[a] * sk.len[a]) if sk.len.get(a) else None
        return None if v is None or v.length < 1e-6 else cmu2ours(v).normalized()
    if b not in po:
        return None
    v = po[b][0] - po[a][0]
    return None if v.length < 1e-6 else cmu2ours(v).normalized()


def apply_frame(ps, sk, frame, parts=None):
    """우리 리그를 이 프레임 포즈로. 부모부터 aim 한다."""
    po = sk.pose(frame)
    n = 0
    for name, a, b in MAP:
        if parts is not None and name not in parts:
            continue
        d = joint_dir(sk, po, a, b)
        if d is None:
            continue
        ps.aim(name, d)
        n += 1
    return n


def blade_dir(sk, frame):
    """모캡에서 **칼날 방향**을 뽑는다.

    모캡엔 칼이 안 찍혀 있지만 **양 손목이 찍혀 있다.** 양손으로 자루를 잡으면
    두 손을 잇는 선이 곧 자루 축이고 칼날은 그 연장이다. 그래서 추측할 필요가 없다.
    (검증: 모캡 두 손목 거리 0.10~0.13 H, 우리 설계 양손 간격 0.142 H)
    왼 손목 -> 오른 손목 방향이 칼끝 쪽이다(오른손이 츠바 쪽).
    """
    po = sk.pose(frame)
    if "lwrist" not in po or "rwrist" not in po:
        return None
    v = cmu2ours(po["rwrist"][0] - po["lwrist"][0])
    return None if v.length < 1e-6 else v.normalized()
