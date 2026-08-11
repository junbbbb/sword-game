# -*- coding: utf-8 -*-
"""원본 에셋(ToonSoldiers WW2)의 애니메이션 FBX 를 우리 리그로 리타게팅한다.

왜 필요한가
  손으로 만든 달리기는 허벅지·종아리의 X 회전 4 포즈가 전부였다. 발목·발가락·
  골반 상하가 없어서 "너무 이상하게 뛴다"(오너). 원본 팩에 제대로 만든 달리기가
  들어 있다: infantry_combat_run, 26 프레임, 보폭 1.42, 골반 상하 진동 0.236,
  **골반 전진 0.000(이미 제자리 루프)**, f26 == f1(깔끔한 루프).
  본 이름은 20/20 우리 리그와 일치한다.

★함정
  애니메이션 FBX 는 저마다 **자기 rest 포즈**를 들고 온다. 우리 리그(T 포즈)와
  최대 269 도 차이가 난다. 그래서 로컬 회전(matrix_basis)이나 쿼터니언 커브를
  복사하면 완전히 다른 포즈가 나온다.
  → **armature 공간의 최종 행렬(pose_bone.matrix)** 을 부모부터 차례로 복사해야 한다.
  본 길이는 리프(Head/Toe0, 길이가 표시용이라 무의미) 빼고 전부 0.0% 일치라
  그대로 옮겨도 몸이 늘어나지 않는다(실측).
"""
import os

PACK = "/Users/lbj/Documents/gameproject/refpack/Assets/ToonSoldiers_WW2_demo"

# 가져올 부위. 팔(clavicle/upperarm/forearm/hand)은 소총 자세라 안 가져온다.
# 우리는 양손으로 자루를 잡아야 하므로 팔은 GUARD_ARMS 로 덮는다.
LOWER = ("Pelvis", "Spine", "Neck", "Head",
         "L Thigh", "L Calf", "L Foot", "L Toe0",
         "R Thigh", "R Calf", "R Foot", "R Toe0")

# 목·머리는 가져오지 않는다. 원본은 소총을 든 병사라 **목이 오른쪽으로 크게 기울어**
# 있다(실측: 목 방향 r +0.39~0.49, 중단세는 +0.02). 그대로 쓰면 고개를 숙이고
# 갸웃한 채 달리는 그림이 된다. 달릴 때는 정면을 본다.
# 목은 **가져온다**(앞뒤 0.219, 좌우 0.106 만큼 움직인다. 이걸 버리면 상체가 굳는다).
# 대신 상수 기울기만 빼준다. 머리는 원본에서 앞뒤 폭이 **0.000** 이라
# 가져와봐야 아무 움직임이 없다 -> 우리가 직접 흔든다.
LOWER_NOHEAD = tuple(x for x in LOWER if x != "Head")


def load(name, keep_arm=None):
    """애니메이션 FBX 를 현재 blend 에 불러온다.
    반환 (소스 armature, 시작 프레임, 끝 프레임, 새로 생긴 오브젝트 목록)."""
    import bpy
    path = os.path.join(PACK, "animation/%s.FBX" % name)
    before = set(o.name for o in bpy.context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.context.scene.objects if o.name not in before]
    src = None
    for o in new:
        if o.type == "ARMATURE" and o.animation_data and o.animation_data.action:
            src = o
            break
    if src is None:
        raise RuntimeError("애니메이션 없는 FBX: %s" % path)
    act = src.animation_data.action
    # Blender 4.4+ 슬롯형 액션: 슬롯을 지정하지 않으면 아무것도 적용되지 않는다
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            src.animation_data.action_slot = slots[0]
    except Exception:
        pass
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    return src, f0, f1, new


def copy_pose(src, dst, parts=LOWER):
    """소스 리그의 현재 포즈에서 하체·척추를 우리 리그로 옮긴다.
    rest 가 달라도 되게 armature 공간 최종 행렬을 **부모부터** 복사한다."""
    import bpy
    smap = {b.name: b for b in src.pose.bones}
    todo = []
    for b in dst.pose.bones:
        if b.name not in smap:
            continue
        if not any(b.name.endswith(p) for p in parts):
            continue
        d, x = 0, b
        while x.parent:
            d += 1
            x = x.parent
        todo.append((d, b))
    todo.sort(key=lambda t: t[0])
    for _, b in todo:
        b.matrix = smap[b.name].matrix.copy()
        bpy.context.view_layer.update()
    return len(todo)


def drop(objs):
    """리타게팅이 끝난 뒤 소스 리그를 지운다. 남겨두면 glb 에 같이 나간다."""
    import bpy
    for o in objs:
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass
