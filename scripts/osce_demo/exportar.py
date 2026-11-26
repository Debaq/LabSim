import sqlite3, sys
db = sqlite3.connect(sys.argv[1])
out = []
for t in ['osce', 'osce_estacion', 'osce_item', 'osce_pregunta', 'osce_participante']:
    cur = db.execute(f'SELECT * FROM {t} ORDER BY id')
    cols = [c[0] for c in cur.description]
    for row in cur:
        vals = []
        for v in row:
            if v is None: vals.append('NULL')
            elif isinstance(v, (int, float)): vals.append(repr(v))
            else: vals.append("'" + str(v).replace("'", "''") + "'")
        out.append(f"INSERT INTO {t} ({', '.join(cols)}) VALUES ({', '.join(vals)});")
open(sys.argv[2], 'w').write('\n'.join(out) + '\n')
print(len(out), 'filas')
