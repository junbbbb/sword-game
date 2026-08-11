# -*- coding: utf-8 -*-
"""방패 든 왼팔을 "캐리 자세"로 끌어당긴다. Walk/Run 처럼 맨손 기준으로 만들어진
애니에서 왼팔이 크게 흔들려 방패가 머리 위로 들리는 문제를 잡는 모듈.

왜 이렇게 하나
  Meshy 원본 달리기는 맨손 기준이라 양팔을 크게 휘두른다. 방패는 왼손 뼈에 웨이트
  1.0 강체로 붙으므로 그 스윙을 그대로 받는다(실측: Run f09 에서 방패 최고점이
  어깨보다 37.9cm 위). 현실에서 방패 든 팔은 몸 앞에 고정하고 반대팔만 흔든다.
  그래서 **왼팔 3뼈만** Idle 의 캐리 자세 쪽으로 slerp 로 끌어당긴다.
  오른팔·다리·척추는 손대지 않는다(뛰는 느낌은 그쪽이 만든다).

★함정 1: 쿼터니언 커브를 그대로 복사·보간하면 안 된다
  뼈마다 레스트가 달라 로컬 회전(matrix_basis)은 같은 값이라도 다른 방향을 뜻한다
  (이 프로젝트에서 최대 269도 어긋난 전례). 그래서 **아마추어 공간 pb.matrix** 의
  회전만 다루고, 부모 -> 자식 순서로 처리한다.

★함정 2: pb.matrix 에 함부로 쓰면 스케일이 날아간다(과거 손이 39배)
  이 리그는 arm.matrix_world 스케일이 **0.01** 이다(뼈 길이가 2101 단위).
  월드 행렬(A2W @ pb.matrix)을 pb.matrix 에 되쓰면 100배가 섞여 폭발한다.
  → 이 모듈은 A2W 를 **아예 쓰지 않는다**. 전부 아마추어 공간.
  → 게다가 현재 행렬을 decompose 해서 **위치와 스케일은 원본 그대로 두고 회전만**
    갈아끼운다(asset_anim.copy_pose 는 리그가 동일해 통째로 대입해도 됐지만,
    여기는 같은 리그 안에서 회전만 바꾸는 것이라 이 방식이 안전하다).

★함정 3: 위치를 "읽는 시점"
  부모(위팔)를 돌린 **뒤에** 자식(팔뚝)의 현재 위치를 읽어야 팔이 안 끊어진다.
  뼈가 use_connect=False 라 위치를 잘못 주면 팔이 공중에서 분리된다.
  자식 위치를 그대로 보존하면 로컬 location 채널이 안 변하므로
  **rotation_quaternion 만 키를 찍으면 된다**(위치·스케일 키는 손 안 댐).

★함정 4: Blender 4.4+ 슬롯형 액션
  animation_data.action_slot 을 지정하지 않으면 액션이 조용히 아무 일도 안 한다.
"""
import bpy
from mathutils import Matrix, Quaternion

# 왼팔 체인(부모 -> 자식 순서. 이 순서가 곧 처리 순서다)
L_CHAIN = ("Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand")


def use_action(arm, act):
    """액션을 붙이고 슬롯까지 지정한다(★함정 4)."""
    if isinstance(act, str):
        act = bpy.data.actions[act]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception as ex:
        print("  action_slot 지정 실패(구버전이면 무시):", ex)
    return act


def read_reference(arm, action="Idle", frame=17, bones=L_CHAIN):
    """기준 자세를 아마추어 공간 **회전**으로 읽는다.
    위치는 안 읽는다. 클립마다 어깨 위치가 다르므로 위치까지 고정하면 팔이 끊어진다."""
    use_action(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    ref = {}
    for nm in bones:
        ref[nm] = arm.pose.bones[nm].matrix.to_quaternion().normalized()
    return ref


def capture(arm, act, bones=L_CHAIN):
    """원본 애니의 프레임별 아마추어 공간 회전을 먼저 통째로 읽어 둔다.
    ★굽는 도중에 읽으면 이미 내가 바꾼 값을 다시 읽게 된다(누적 오염)."""
    act = use_action(arm, act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    src = {}
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        src[f] = {nm: arm.pose.bones[nm].matrix.to_quaternion().normalized()
                  for nm in bones}
    return f0, f1, src


def blend(q_src, q_ref, w):
    """부호를 맞춘 뒤 최단호 slerp. 부호가 반대면 먼 길로 돌아간다."""
    q = q_ref.copy()
    if q_src.dot(q) < 0.0:
        q.negate()
    return q_src.slerp(q, w).normalized()


def apply_frame(arm, src_at_frame, ref, w, bones=L_CHAIN):
    """현재 프레임의 왼팔을 기준 자세 쪽으로 w 만큼 끌어당긴다(키는 안 찍음)."""
    for nm in bones:
        pb = arm.pose.bones[nm]
        cur = pb.matrix                     # ★부모를 고친 뒤 읽어야 한다(함정 3)
        t, _, s = cur.decompose()           # 위치·스케일은 원본 유지(함정 2)
        q = blend(src_at_frame[nm], ref[nm], w)
        pb.matrix = Matrix.LocRotScale(t, q, s)
        bpy.context.view_layer.update()     # 자식이 새 부모를 보게 한다


def bake(arm, act, ref, w, bones=L_CHAIN, log=True):
    """액션의 모든 정수 프레임에 캐리 자세를 굽고 rotation_quaternion 키를 찍는다."""
    act = use_action(arm, act)
    f0, f1, src = capture(arm, act, bones)
    for nm in bones:
        pb = arm.pose.bones[nm]
        if pb.rotation_mode != "QUATERNION":
            pb.rotation_mode = "QUATERNION"   # 쿼터니언 커브에 키를 찍으려면 필수
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        apply_frame(arm, src[f], ref, w, bones)
        for nm in bones:
            arm.pose.bones[nm].keyframe_insert("rotation_quaternion", frame=f)
    if log:
        print("  [carry] %-6s f%d~%d, 가중치 %.2f, 뼈 %d개에 키 %d프레임"
              % (act.name, f0, f1, w, len(bones), f1 - f0 + 1))
    return f0, f1


def shield_sampler(arm, shield, hand=L_CHAIN[-1]):
    """방패 최고점 z 를 재는 함수를 만든다.

    방패는 손 뼈에 웨이트 1.0 강체라 메시를 굽지 않아도 정확히 계산된다.
      v_world' = (A2W @ M_pose) @ (A2W @ M_rest)^-1 @ v_world
    프레임마다 7MB 몸통 메시를 평가하지 않으므로 훨씬 빠르다."""
    A2W = arm.matrix_world
    keep = arm.data.pose_position
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    rest_inv = (A2W @ arm.pose.bones[hand].matrix).inverted()
    local = [rest_inv @ (shield.matrix_world @ v.co) for v in shield.data.vertices]
    arm.data.pose_position = keep
    bpy.context.view_layer.update()

    def top():
        m = A2W @ arm.pose.bones[hand].matrix
        return max((m @ p).z for p in local)
    return top


def shoulder_z(arm):
    """양 어깨(위팔 뿌리) 월드 z 평균. 방패 높이를 비교할 기준선."""
    A2W = arm.matrix_world
    a = (A2W @ arm.pose.bones["Bip001 L UpperArm"].matrix).translation
    b = (A2W @ arm.pose.bones["Bip001 R UpperArm"].matrix).translation
    return (a.z + b.z) / 2
