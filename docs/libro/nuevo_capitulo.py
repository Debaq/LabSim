#!/usr/bin/env python3
"""Arma el esqueleto de un capítulo a partir del índice.

    python3 docs/libro/nuevo_capitulo.py 11            -> capitulos/11-<título>.md
    python3 docs/libro/nuevo_capitulo.py 11 --forzar   (pisa uno existente)

Del índice (indice.md) toma el título, los temas de Técnica y Fisiología y
los casos. Deja un hueco "✍" por bloque para el texto, los recuadros
(:::objetivos, :::ayuda, :::sabias, :::pregunta...), y por cada caso que ya
tenga pedido en casos/: la ficha {{caso ...}}, la pregunta "¿Qué pedirías?" y
un :::figura por figura, para relatarla con globos. También las referencias
SUGERIDAS, sacadas de:

  - Técnica: las ✓ del índice (Bibliografia, AbrReferences, EcochgReferences)
    y la investigación (investigacion/tecnica_a.md, tecnica_b.md);
  - Fisiología: investigacion/fisiologia.md;
  - Patología: BibliografiaPatologias, de los cuadros de los casos.

Las referencias se escriben una vez: el autor las poda y ordena en el .md.
"""
import json
import pathlib
import re
import subprocess
import sys
import unicodedata

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
INDICE = AQUI / 'indice.md'
CASOS = AQUI / 'casos'
CAPITULOS = AQUI / 'capitulos'
INVESTIGACION = AQUI / 'investigacion'

PHP_REFS = r'''
foreach (["Bibliografia","BibliografiaPatologias","AbrReferences","EcochgReferences"] as $c) require_once "src/$c.php";
$cita = function ($v) { foreach (["cita","ref","referencia","titulo"] as $k) if (is_array($v) && isset($v[$k]) && is_string($v[$k])) return $v[$k]; return is_string($v) ? $v : null; };
$codigos = [];
foreach (["ABR_COMPLEMENTARIAS","TAMIZAJE","ACUMETRIA","IMPEDANCIOMETRIA","NORMAS","FUENTES_TECNICAS"] as $k)
    foreach (constant("Bibliografia::$k") as $id => $v) $codigos[$id] = $cita($v);
foreach (AbrReferences::FUENTES as $id => $v) $codigos[$id] = $cita($v);
foreach (EcochgReferences::FUENTES as $id => $v) $codigos[$id] = $cita($v);
$pat = [];
foreach (BibliografiaPatologias::CITAS as $k => $lista) $pat[$k] = array_values(array_filter(array_map($cita, $lista)));
echo json_encode(["codigos" => $codigos, "patologias" => $pat], JSON_UNESCAPED_UNICODE);
'''


def referencias_del_sistema():
    r = subprocess.run(['php', '-r', PHP_REFS], cwd=RAIZ / 'labsim_backend',
                       check=True, capture_output=True, text=True)
    return json.loads(r.stdout)


def capitulo_del_indice(n):
    texto = INDICE.read_text(encoding='utf-8')
    m = re.search(rf'^### {n}\. (.+?)$\n(.*?)(?=^#{{2,3}} |\Z)', texto, re.M | re.S)
    if not m:
        sys.exit(f'No encuentro el capítulo {n} en {INDICE.name}')
    titulo, cuerpo = m[1].strip(), m[2]

    def bloque(nombre):
        b = re.search(rf'^- \*\*{nombre}:\*\*(.*?)(?=^- \*\*|\Z)', cuerpo, re.M | re.S)
        return b[1].strip() if b else ''

    casos = re.search(r'^- \*\*Casos:\*\*(.*?)(?=^- \*\*|\Z)', cuerpo, re.M | re.S)
    casos = casos[1] if casos else ''
    # orden de aparición en el índice: '★39' o la clave del cuadro
    orden = [m.group(1) or m.group(2) for m in re.finditer(r'★(\d+)|\[`([a-z0-9_]+)`', casos)]
    nombres = [re.sub(r'^★\d+\s*', '', m[1].strip(' -')) for m in re.finditer(r'(?:★\d+\s*)?([^·\n\[\]]+?)\s*\[`[a-z0-9_]+`\]', casos)]
    return {
        'n': n, 'titulo': titulo, 'orden': orden, 'nombres': [x for x in nombres if x],
        'tecnica': bloque('Técnica'), 'fisiologia': bloque('Fisiología'),
        'cuadros': list(dict.fromkeys(re.findall(r'\[`([a-z0-9_]+)`', casos))),
        'estrellas': re.findall(r'★(\d+)', casos),
    }


def sin_marcas(s):
    """El tema tal como lo escribe el índice, sin las marcas ✓/✗ ni códigos."""
    s = re.sub(r'\((?:✓|✗)[^)]*\)', '', s)
    s = re.sub(r'\s+', ' ', s.replace('\n', ' ')).strip(' ;·-')
    return s


def codigos_ok(s):
    out = []
    for grupo in re.findall(r'✓ ([^)]*)\)', s):
        grupo = grupo.split(';')[0]
        out += [c.strip() for c in grupo.split(',') if re.fullmatch(r'[A-Z][A-Z0-9-]*', c.strip())]
    return out


def investigacion(archivo, n):
    """Entradas de la investigación cuyo título dice (cap. n) o (caps. ... n ...)."""
    texto = (INVESTIGACION / archivo).read_text(encoding='utf-8')
    texto = texto.split('## No encontrado')[0]
    out = []
    for sec in re.split(r'^## ', texto, flags=re.M)[1:]:
        cab = sec.splitlines()[0]
        caps = re.search(r'\(caps?\.\s*([^)]*)\)', cab)
        if not caps or str(n) not in re.findall(r'\d+', caps[1]):
            continue
        for bloque in re.split(r'\n\s*\n', sec):
            lineas = [l.strip() for l in bloque.strip().splitlines() if l.strip()]
            if len(lineas) >= 2 and lineas[1].startswith('—'):
                sirve = next((l for l in lineas if l.lower().startswith('sirve para')), '')
                out.append((lineas[0], sirve))
    return out


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:40]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    n = int(args[0])
    cap = capitulo_del_indice(n)
    CAPITULOS.mkdir(exist_ok=True)
    destino = CAPITULOS / f'{n:02d}-{slug(cap["titulo"])}.md'
    if destino.exists() and '--forzar' not in sys.argv:
        sys.exit(f'{destino.name} ya existe (tiene texto del autor). Usar --forzar para pisarlo.')

    sistema = referencias_del_sistema()
    pedidos = sorted(p.stem for p in CASOS.glob(f'cap{n:02d}_*.json')) + \
        [f'paciente_{e}' for e in cap['estrellas'] if (CASOS / f'paciente_{e}.json').exists()]
    cubiertos, posicion = set(), {}
    for p in pedidos:
        spec = json.loads((CASOS / f'{p}.json').read_text(encoding='utf-8'))
        if isinstance(spec['caso'], dict):
            claves = list(spec['caso'].get('cuadro', {}).values())
        else:
            # paciente ★: su cuadro es la clave que sigue a la ★ en el índice
            num = p.split('_')[-1]
            i = cap['orden'].index(num) if num in cap['orden'] else -1
            claves = [num] + ([cap['orden'][i + 1]] if 0 <= i < len(cap['orden']) - 1 else [])
        cubiertos |= set(claves)
        posicion[p] = min((cap['orden'].index(k) for k in claves if k in cap['orden']), default=999)
    pedidos.sort(key=lambda p: posicion[p])
    sin_pedido = [c for c in cap['cuadros'] if c not in cubiertos]

    L = [f'# {n}. {cap["titulo"]}', '',
         ':::objetivos En este capítulo', '- ✍ Objetivos del capítulo', ':::', '',
         '> ✍ Párrafo de entrada: la situación clínica que abre el capítulo', '']
    for bloque, tema in (('Técnica', cap['tecnica']), ('Fisiología', cap['fisiologia'])):
        L += [f'## {bloque}', '', f'> ✍ {sin_marcas(tema) or "Texto del autor"}', '',
              ':::ayuda Ayuda memoria', '✍', ':::', '']
    L += ['## Patología', '', '> ✍ ' + '; '.join(cap['nombres']), '',
          ':::sabias ¿Sabías que?', '✍', ':::', '',
          '## Razonamiento', '', '> ✍ Texto del autor', '',
          ':::pregunta Pregunta abierta', '✍', ':::', '', '## Casos', '']
    for p in pedidos:
        spec = json.loads((CASOS / f'{p}.json').read_text(encoding='utf-8'))
        L += [f'{{{{caso {p}}}}}', '', ':::pregunta ¿Qué pedirías?', '✍', ':::', '']
        vistos = {}
        for f in spec.get('figuras', []):
            vistos[f['tipo']] = vistos.get(f['tipo'], 0) + 1
            extra = f" {vistos[f['tipo']]}" if vistos[f['tipo']] > 1 else ''
            L += [f":::figura {p} {f['tipo']}{extra}",
                  '- ✍ observación (con globo: "- @ANCLA | texto"; anclas como "OD 4000", "OD 80 V", "ipsi OD 1000", "OD max")',
                  ':::', '']
        L += ['#### Razonamiento', '', '> ✍ Texto del autor', '',
              '#### Diagnóstico y qué sigue', '', '> ✍ Texto del autor', '']
    if sin_pedido:
        L += [f'<!-- Cuadros del índice sin pedido en casos/: {", ".join(sin_pedido)} -->', '']

    L += ['## Para cerrar', '', ':::pregunta Preguntas para discutir', '1. ✍', ':::', '',
          ':::ayuda Ayuda memoria del capítulo', '- ✍', ':::', '']
    L += ['## Referencias', '', '<!-- Sugeridas: podar y ordenar. -->', '', '### Técnica', '']
    tec = [sistema['codigos'][c] for c in codigos_ok(cap['tecnica']) if sistema['codigos'].get(c)]
    tec += [r for r, _ in investigacion('tecnica_a.md', n) + investigacion('tecnica_b.md', n)]
    L += [f'1. {r}' for r in dict.fromkeys(tec)] or ['> ✍ Sin referencias de técnica todavía']
    L += ['', '### Fisiología', '']
    fis = [sistema['codigos'][c] for c in codigos_ok(cap['fisiologia']) if sistema['codigos'].get(c)]
    fis += [r for r, _ in investigacion('fisiologia.md', n)]
    L += [f'1. {r}' for r in dict.fromkeys(fis)] or ['> ✍ Sin referencias de fisiología todavía']
    L += ['', '### Patología', '']
    pat = [c for k in cap['cuadros'] for c in sistema['patologias'].get(k, [])]
    L += [f'1. {r}' for r in dict.fromkeys(pat)] or ['> ✍ Sin referencias de patología todavía']
    destino.write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(destino)
    if sin_pedido:
        print('Cuadros sin pedido de caso:', ', '.join(sin_pedido))


if __name__ == '__main__':
    main()
