"""Nil Kervancisi v33 - shrink the exported GLB (KHR_mesh_quantization) and wrap it for the game.
  normals -> BYTE normalized, colours/weights -> UNSIGNED_BYTE normalized, masks -> one _MASK VEC4 u8,
  morph targets -> SHORT normalized (metres), animations -> rotation only (+ the hips translation), SHORT quaternions.
usage: python3 pack33.py IN.glb OUT.glb [recipes.json] [OUT_module.txt]"""
import json, struct, sys, base64, numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def read(path):
    b = open(path, 'rb').read()
    jl = struct.unpack('<I', b[12:16])[0]; J = json.loads(b[20:20 + jl]); o = 20 + jl
    bl = struct.unpack('<I', b[o:o + 4])[0]; BIN = b[o + 8:o + 8 + bl]
    return J, BIN

def get(J, BIN, i):
    a = J['accessors'][i]; dt = CT[a['componentType']]; n = NC[a['type']]
    if 'bufferView' not in a:
        out = np.zeros((a['count'], n))
        sp = a.get('sparse')
        if sp:
            iv = J['bufferViews'][sp['indices']['bufferView']]; vv = J['bufferViews'][sp['values']['bufferView']]
            idx = np.frombuffer(BIN, CT[sp['indices']['componentType']], count=sp['count'], offset=iv.get('byteOffset', 0) + sp['indices'].get('byteOffset', 0))
            val = np.frombuffer(BIN, dt, count=sp['count'] * n, offset=vv.get('byteOffset', 0) + sp['values'].get('byteOffset', 0)).reshape(-1, n)
            out[idx.astype(int)] = val
        return out
    v = J['bufferViews'][a['bufferView']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', 0)
    isz = np.dtype(dt).itemsize
    if stride and stride != isz * n:
        raw = np.frombuffer(BIN, np.uint8, count=stride * a['count'], offset=off).reshape(a['count'], stride)[:, :isz * n]
        arr = np.frombuffer(raw.tobytes(), dt).reshape(a['count'], n)
    else:
        arr = np.frombuffer(BIN, dt, count=a['count'] * n, offset=off).reshape(a['count'], n)
    if a.get('normalized'):
        if dt == np.uint8: arr = arr / 255.0
        elif dt == np.uint16: arr = arr / 65535.0
        elif dt == np.int8: arr = np.maximum(arr / 127.0, -1)
        elif dt == np.int16: arr = np.maximum(arr / 32767.0, -1)
    return np.asarray(arr, np.float64 if dt == np.float32 or a.get('normalized') else arr.dtype)

class Out:
    def __init__(self): self.bin = bytearray(); self.views = []; self.acc = []
    def view(self, data, target=None, stride=None):
        while len(self.bin) % 4: self.bin.append(0)
        v = {'buffer': 0, 'byteOffset': len(self.bin), 'byteLength': len(data)}
        if target: v['target'] = target
        if stride: v['byteStride'] = stride
        self.bin += data; self.views.append(v); return len(self.views) - 1
    def accessor(self, arr, ctype, typ, normalized=False, target=None, minmax=False, pad4=False):
        arr = np.asarray(arr); n = NC[typ]; cnt = len(arr)
        dt = CT[ctype]; a2 = arr.reshape(cnt, n).astype(dt)
        stride = None
        if pad4 and (np.dtype(dt).itemsize * n) % 4:
            w = ((np.dtype(dt).itemsize * n + 3) // 4) * 4 // np.dtype(dt).itemsize
            p = np.zeros((cnt, w), dt); p[:, :n] = a2; data = p.tobytes(); stride = w * np.dtype(dt).itemsize
        else: data = a2.tobytes()
        vi = self.view(data, target, stride)
        a = {'bufferView': vi, 'componentType': ctype, 'count': cnt, 'type': typ}
        if normalized: a['normalized'] = True
        if minmax: a['min'] = arr.reshape(cnt, n).min(0).tolist(); a['max'] = arr.reshape(cnt, n).max(0).tolist()
        self.acc.append(a); return len(self.acc) - 1

def _sparse(self, dq, count):
    nz = np.nonzero(np.abs(dq).max(1) > 1)[0]
    if not len(nz): nz = np.array([0])
    iv = self.view(nz.astype(np.uint16 if count < 65535 else np.uint32).tobytes())
    vv = self.view(dq[nz].astype(np.int16).tobytes())
    a = {'componentType': 5122, 'count': count, 'type': 'VEC3', 'normalized': True, 'min': dq.min(0).astype(int).tolist(), 'max': dq.max(0).astype(int).tolist(),
         'sparse': {'count': int(len(nz)), 'indices': {'bufferView': iv, 'componentType': 5123 if count < 65535 else 5125}, 'values': {'bufferView': vv}}}
    self.acc.append(a); return len(self.acc) - 1
Out.sparse = _sparse

def q8(x): return np.round(np.clip(x, -1, 1) * 127)
def q16(x): return np.round(np.clip(x, -1, 1) * 32767)
def u8(x): return np.round(np.clip(x, 0, 1) * 255)

def pack(src, dst):
    J, BIN = read(src); O = Out(); AV = 34962; IV = 34963
    for m in J['meshes']:
        for p in m['primitives']:
            A = p['attributes']; NA = {}
            pos = get(J, BIN, A['POSITION']); NA['POSITION'] = O.accessor(pos, 5126, 'VEC3', target=AV, minmax=True)
            if 'NORMAL' in A:
                nr = get(J, BIN, A['NORMAL']); NA['NORMAL'] = O.accessor(q8(nr), 5120, 'VEC3', True, AV, pad4=True)
            if 'COLOR_0' in A:
                c = get(J, BIN, A['COLOR_0']); NA['COLOR_0'] = O.accessor(u8(c), 5121, 'VEC4', True, AV)
            j = get(J, BIN, A['JOINTS_0']); NA['JOINTS_0'] = O.accessor(j, 5121, 'VEC4', target=AV)
            w = get(J, BIN, A['WEIGHTS_0']); w = w / np.maximum(w.sum(1, keepdims=True), 1e-9)
            wq = u8(w); d = 255 - wq.sum(1); wq[np.arange(len(wq)), wq.argmax(1)] += d          # exact sum after rounding
            NA['WEIGHTS_0'] = O.accessor(wq, 5121, 'VEC4', True, AV)
            mk = [k for k in A if k.startswith('_')]
            if mk:
                M4 = np.zeros((len(pos), 4))
                for i, k in enumerate(sorted(mk)[:4]): M4[:, i] = get(J, BIN, A[k])[:, 0]
                NA['_MASK'] = O.accessor(u8(M4), 5121, 'VEC4', True, AV)
            idx = get(J, BIN, p['indices']).ravel()
            p['indices'] = O.accessor(idx, 5123 if idx.max() < 65535 else 5125, 'SCALAR', target=IV)
            if 'targets' in p:
                T2 = []
                for t in p['targets']:
                    d = get(J, BIN, t['POSITION'])
                    T2.append({'POSITION': O.sparse(q16(d), len(pos))})
                p['targets'] = T2
            p['attributes'] = NA
            p.pop('material', None)
    # skins
    for s in J.get('skins', []):
        ibm = get(J, BIN, s['inverseBindMatrices']); s['inverseBindMatrices'] = O.accessor(ibm, 5126, 'MAT4')
    # animations: rotations (all bones) + translation of the hips only
    names = {i: n.get('name', '') for i, n in enumerate(J['nodes'])}
    for an in J.get('animations', []):
        ch2 = []; smp2 = []; inputs = {}
        for c in an['channels']:
            s = an['samplers'][c['sampler']]; node = names[c['target']['node']]; path = c['target']['path']
            if path == 'scale' or (path == 'translation' and node != 'hips'): continue
            tin = get(J, BIN, s['input']).ravel()
            out = get(J, BIN, s['output'])
            tin_k = tin
            if np.abs(out - out[:1]).max() < 1e-4:                           # constant channel
                rest = J['nodes'][c['target']['node']].get(path)
                if path == 'rotation' and rest is not None and np.abs(np.abs((out[0] * np.array(rest)).sum()) - 1) < 1e-5: continue
                out = out[:1]; tin_k = tin[:1]
            elif len(tin) > 30 and tin[-1] >= 1.9:                         # long clips: 12 fps is plenty
                sel = np.arange(0, len(tin), 2)
                if sel[-1] != len(tin) - 1: sel = np.append(sel, len(tin) - 1)
                out = out[sel]; tin_k = tin[sel]
            key = tin_k.tobytes()
            if key not in inputs: inputs[key] = O.accessor(tin_k, 5126, 'SCALAR', minmax=True)
            if path == 'rotation':
                # keep hemispheres continuous
                for i in range(1, len(out)):
                    if (out[i] * out[i - 1]).sum() < 0: out[i] = -out[i]
                oa = O.accessor(q16(out), 5122, 'VEC4', True)
            else:
                oa = O.accessor(out, 5126, 'VEC3')
            smp2.append({'input': inputs[key], 'output': oa, 'interpolation': 'LINEAR'})
            ch2.append({'sampler': len(smp2) - 1, 'target': c['target']})
        an['channels'] = ch2; an['samplers'] = smp2
    J['accessors'] = O.acc; J['bufferViews'] = O.views; J['buffers'] = [{'byteLength': len(O.bin)}]
    J.pop('materials', None)
    J['extensionsUsed'] = sorted(set(J.get('extensionsUsed', []) + ['KHR_mesh_quantization']))
    J['extensionsRequired'] = sorted(set(J.get('extensionsRequired', []) + ['KHR_mesh_quantization']))
    js = json.dumps(J, separators=(',', ':')).encode()
    while len(js) % 4: js += b' '
    while len(O.bin) % 4: O.bin.append(0)
    total = 12 + 8 + len(js) + 8 + len(O.bin)
    out = struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(O.bin), 0x004E4942) + bytes(O.bin)
    open(dst, 'wb').write(out)
    return len(out)

def module(glb, recipes, dst):
    """the inert container: base64 GLB + JSON recipes in <script type=application/octet-stream> blocks (parsed lazily)"""
    import gzip
    b64 = base64.b64encode(gzip.compress(open(glb, 'rb').read(), 9)).decode()
    rj = open(recipes).read() if recipes else '{}'
    s = '<script type="application/octet-stream" id="c33glb">' + b64 + '</script>\n<script type="application/json" id="c33rec">' + rj.replace('</', '<\\/') + '</script>\n'
    open(dst, 'w').write(s)
    return len(s)

if __name__ == '__main__':
    n = pack(sys.argv[1], sys.argv[2]); print('packed', n)
    if len(sys.argv) > 4: print('module', module(sys.argv[2], sys.argv[3], sys.argv[4]))
