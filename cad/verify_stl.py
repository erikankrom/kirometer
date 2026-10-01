"""Verify actual binary STL exports using only the Python standard library."""
from collections import Counter
from pathlib import Path
import struct
import json

root=Path(__file__).resolve().parents[1]
results={}
for path in sorted((root/'exports').glob('*.stl')):
    data=path.read_bytes()
    count=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*count, f'{path.name}: invalid binary STL length'
    edges=Counter(); volume=0
    for index in range(count):
        values=struct.unpack_from('<12fH',data,84+50*index)
        a,b,c=[tuple(values[i:i+3]) for i in (3,6,9)]
        for p,q in ((a,b),(b,c),(c,a)):
            assert p != q, f'{path.name}: collapsed edge'
            edges[tuple(sorted((p,q)))]+=1
        volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    bad=sum(n!=2 for n in edges.values())
    assert bad==0, f'{path.name}: {bad} non-manifold edges'
    assert volume>0, f'{path.name}: inward or zero volume'
    results[path.name]={'triangles':count,'non_manifold_edges':bad,'volume_mm3':round(volume,2)}
assert len(results)==6, 'Expected exactly six print parts'
(root/'exports/stl-validation.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
