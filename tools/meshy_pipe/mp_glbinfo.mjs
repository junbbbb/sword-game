// 받은 glb 를 열어 "정말 텍스처가 들어 있나"를 확인한다(파일 크기는 증거가 아니다).
//   node tools/meshy_pipe/mp_glbinfo.mjs <glb...>
import fs from 'fs';

for (const p of process.argv.slice(2)) {
  const buf = fs.readFileSync(p);
  const magic = buf.toString('ascii', 0, 4);
  if (magic !== 'glTF') { console.log(`${p}: ★glTF 아님(${JSON.stringify(magic)})`); continue; }
  const jsonLen = buf.readUInt32LE(12);
  const j = JSON.parse(buf.toString('utf8', 20, 20 + jsonLen));
  const tris = (j.meshes || []).flatMap(m => m.primitives).reduce((s, p2) => {
    const acc = j.accessors[p2.indices ?? -1];
    return s + (acc ? acc.count / 3 : 0);
  }, 0);
  const imgs = (j.images || []).map((im, i) => {
    const bv = j.bufferViews[im.bufferView];
    return `#${i} ${im.mimeType || '?'} ${(bv ? (bv.byteLength / 1048576).toFixed(2) + 'MB' : im.uri || '?')}`;
  });
  const mats = (j.materials || []).map(m => {
    const pbr = m.pbrMetallicRoughness || {};
    return `${m.name || '(무명)'}[base=${pbr.baseColorTexture ? 'O' : 'X'} mr=${pbr.metallicRoughnessTexture ? 'O' : 'X'} nrm=${m.normalTexture ? 'O' : 'X'}]`;
  });
  console.log(`${p}\n  ${(buf.length / 1048576).toFixed(1)}MB · 메시 ${j.meshes?.length || 0} · 삼각형 ${Math.round(tris).toLocaleString()} · 이미지 ${j.images?.length || 0}\n  재질: ${mats.join(' ')}\n  이미지: ${imgs.join(' | ')}`);
}
