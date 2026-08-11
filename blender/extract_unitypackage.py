#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""unitypackage 추출기.

.unitypackage 는 gzip tar 이고, 내부는 GUID 디렉토리마다
  asset      = 실제 파일 바이트
  pathname   = 원래 프로젝트 상대 경로
구조다. Unity 없이 원본 경로 그대로 풀어낸다.

사용: python3 extract_unitypackage.py <파일.unitypackage> <출력디렉토리>
"""
import os
import sys
import tarfile


def extract(pkg_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    count = 0
    skipped = 0
    with tarfile.open(pkg_path, "r:gz") as tar:
        members = tar.getmembers()
        # guid -> {asset: member, pathname: member}
        guids = {}
        for m in members:
            parts = m.name.split("/")
            if len(parts) < 2:
                continue
            guid, leaf = parts[0], parts[-1]
            if leaf in ("asset", "pathname"):
                guids.setdefault(guid, {})[leaf] = m
        for guid, entry in sorted(guids.items()):
            if "pathname" not in entry or "asset" not in entry:
                skipped += 1
                continue
            f = tar.extractfile(entry["pathname"])
            if f is None:
                skipped += 1
                continue
            rel = f.read().decode("utf-8").splitlines()[0].strip()
            rel = rel.lstrip("/")
            if not rel or ".." in rel.split("/"):
                skipped += 1
                continue
            dst = os.path.join(out_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            src = tar.extractfile(entry["asset"])
            if src is None:
                skipped += 1
                continue
            with open(dst, "wb") as w:
                w.write(src.read())
            count += 1
            print("  %s" % rel)
    print("\n추출 %d개, 건너뜀 %d개 -> %s" % (count, skipped, out_dir))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    extract(sys.argv[1], sys.argv[2])
