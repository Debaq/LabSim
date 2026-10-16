#!/usr/bin/env python3
"""Crea los dos archivos de un capítulo a partir del índice (indice.md):

    capitulos/NN-titulo.py   el GENERADOR: pacientes y figuras (se edita y se corre)
    capitulos/NN-titulo.md   el TEXTO: bloques, recuadros y figuras relatadas

    python3 docs/libro/herramientas/nuevo_capitulo.py 11          un capítulo clínico
    python3 docs/libro/herramientas/nuevo_capitulo.py H4          una herramienta
    python3 docs/libro/herramientas/nuevo_capitulo.py todos       todos los que falten
    ... --forzar                                     pisa los que existan (¡texto del autor!)

Nunca pisa un archivo existente sin --forzar. Después:

    python3 docs/libro/capitulos/NN-titulo.py        arma casos, figuras y PDF

Capítulo clínico: cada paciente ★ del índice entra como demo(), cada cuadro
como cuadro() con la edad y la lateralidad que admite el catálogo
(CaseProfile); las figuras por defecto salen de la parte del libro. El texto
trae un hueco "✍" por bloque, los recuadros, la ficha y un :::figura por
figura para relatarla con globos, y las referencias SUGERIDAS:

  - Técnica: las ✓ del índice y la investigación (tecnica_a.md, tecnica_b.md);
  - Fisiología: investigacion/fisiologia.md;
  - Patología: BibliografiaPatologias, de los cuadros de los casos.

Herramienta (H): plantilla de 8 secciones (para qué sirve, fundamento, antes
de empezar, paso a paso, cómo se informa, errores frecuentes, en LabSim,
referencias) y un generador sin pacientes, para agregar los que ilustren.
"""
import json
import pathlib
import re
import subprocess
import sys
import unicodedata

AQUI = pathlib.Path(__file__).resolve().parent        # docs/libro/herramientas
LIBRO = AQUI.parent                                   # docs/libro
RAIZ = LIBRO.parents[1]
INDICE = LIBRO / 'indice.md'
CAPITULOS = LIBRO / 'capitulos'
INVESTIGACION = LIBRO / 'investigacion'

PHP_DATOS = r'''
foreach (["Bibliografia","BibliografiaPatologias","AbrReferences","EcochgReferences","CaseProfile"] as $c) require_once "src/$c.php";
$cita = function ($v) { foreach (["cita","ref","referencia","titulo"] as $k) if (is_array($v) && isset($v[$k]) && is_string($v[$k])) return $v[$k]; return is_string($v) ? $v : null; };
$codigos = [];
foreach (["ABR_COMPLEMENTARIAS","TAMIZAJE","ACUMETRIA","IMPEDANCIOMETRIA","NORMAS","FUENTES_TECNICAS"] as $k)
    foreach (constant("Bibliografia::$k") as $id => $v) $codigos[$id] = $cita($v);
foreach (AbrReferences::FUENTES as $id => $v) $codigos[$id] = $cita($v);
foreach (EcochgReferences::FUENTES as $id => $v) $codigos[$id] = $cita($v);
$pat = [];
foreach (BibliografiaPatologias::CITAS as $k => $lista) $pat[$k] = array_values(array_filter(array_map($cita, $lista)));
$neo = defined("CaseProfile::SCENARIO_NEONATAL") ? CaseProfile::SCENARIO_NEONATAL : [];
$esc = [];
foreach (CaseProfile::SCENARIOS as $k => $s)
    $esc[$k] = ["lateralidad" => $s["lateralidad"] ?? null, "grados" => $s["grados"] ?? [],
                "edad" => CaseProfile::SCENARIO_EDAD[$k] ?? null, "neonatal" => in_array($k, $neo, true)];
echo json_encode(["codigos" => $codigos, "patologias" => $pat, "escenarios" => $esc], JSON_UNESCAPED_UNICODE);
'''

# Figuras por defecto según la parte del libro (se cambian en el generador)
FIGURAS_POR_CAPITULO = {
    range(1, 5): 'fig.audiograma(), fig.timpanograma(), fig.reflejos()',
    range(5, 11): 'fig.audiograma(), fig.logo(), fig.teoae(), fig.dpoae()',
    range(11, 15): 'fig.audiograma(), fig.logo(), fig.reflejos(), fig.abr()',
    range(15, 16): 'fig.audiograma(), fig.timpanograma(), fig.reflejos(), fig.abr()',
    range(16, 18): 'fig.timpanograma(sonda=1000), fig.teoae(), fig.abr(niveles=(80, 60, 40, 20))',
    range(18, 20): 'fig.audiograma(), fig.logo(), fig.abr()',
    range(20, 21): 'fig.audiograma(), fig.vemp(), fig.vemp(subtipo="ovemp")',
}

SECCIONES_HERRAMIENTA = [
    ('Para qué sirve', 'la pregunta clínica que responde y cuándo se pide'),
    ('Fundamento', 'la fisiología justa para entender por qué se hace así (remite a Bases, B1-B4)'),
    ('Antes de empezar', 'equipo, calibración, ambiente y preparación del paciente'),
    ('Paso a paso', 'el procedimiento, con el porqué de cada paso'),
    ('Cómo se informa', 'criterios, valores de referencia y un ejemplo de informe'),
    ('Errores frecuentes', 'los que se ven en la práctica y en LabSim'),
    ('En LabSim', 'cómo se practica en el simulador'),
]


def datos_del_sistema():
    r = subprocess.run(['php', '-r', PHP_DATOS], cwd=RAIZ / 'labsim_backend',
                       check=True, capture_output=True, text=True)
    return json.loads(r.stdout)


def seccion_del_indice(clave):
    """'11' o 'H4' -> (título, cuerpo de la sección)."""
    texto = INDICE.read_text(encoding='utf-8')
    m = re.search(rf'^### {re.escape(clave)}\. (.+?)$\n(.*?)(?=^#{{2,3}} |\Z)', texto, re.M | re.S)
    if not m:
        sys.exit(f'No encuentro "### {clave}." en {INDICE.name}')
    titulo = re.sub(r'\s*\*\(.*?\)\*\s*$', '', m[1]).strip()
    return titulo, m[2]


def capitulo_clinico(n):
    titulo, cuerpo = seccion_del_indice(str(n))

    def bloque(nombre):
        b = re.search(rf'^- \*\*{nombre}(?: en foco\*\* \(→ [^)]*\))?:(?:\*\*)?(.*?)(?=^- \*\*|\Z)', cuerpo, re.M | re.S)
        return b[1].strip() if b else ''

    foco = re.search(r'Técnica en foco\*\* \(→ ([^)]*)\)', cuerpo)
    casos = re.search(r'^- \*\*Casos:\*\*(.*?)(?=^- \*\*|\Z)', cuerpo, re.M | re.S)
    casos = casos[1] if casos else ''
    # orden de aparición: '★39' o la clave del cuadro; cada ★ va con la clave que la sigue
    orden = [m.group(1) or m.group(2) for m in re.finditer(r'★(\d+)|\[`([a-z0-9_]+)`', casos)]
    nombres = {m[2]: re.sub(r'^★\d+\s*', '', m[1].strip(' -'))
               for m in re.finditer(r'(?:★\d+\s*)?([^·\n\[\]]+?)\s*\[`([a-z0-9_]+)`\]', casos)}
    return {'titulo': titulo, 'tecnica': bloque('Técnica'), 'fisiologia': bloque('Fisiología'),
            'foco': foco[1] if foco else '', 'orden': orden, 'nombres': nombres}


def sin_marcas(s):
    s = re.sub(r'\((?:✓|✗)[^)]*\)', '', s)
    return re.sub(r'\s+', ' ', s.replace('\n', ' ')).strip(' ;·-')


def codigos_ok(s):
    out = []
    for grupo in re.findall(r'✓ ([^)]*)\)', s):
        grupo = grupo.split(';')[0]
        for c in (c.strip() for c in grupo.split(',')):
            rango = re.fullmatch(r'([A-Z])(\d+)-\1?(\d+)', c)      # E01-E07, F01-F27
            if rango:
                ancho = len(rango[2])
                out += [f'{rango[1]}{i:0{ancho}d}' for i in range(int(rango[2]), int(rango[3]) + 1)]
            elif re.fullmatch(r'[A-Z][A-Z0-9-]*', c):
                out.append(c)
    return out


def investigacion(archivo, clave):
    """Entradas cuyo título dice (cap. N) o (caps. ... N ...)."""
    texto = (INVESTIGACION / archivo).read_text(encoding='utf-8').split('## No encontrado')[0]
    out = []
    for sec in re.split(r'^## ', texto, flags=re.M)[1:]:
        cab = sec.splitlines()[0]
        caps = re.search(r'\(caps?\.\s*([^)]*)\)', cab)
        if not caps or str(clave) not in re.findall(r'\d+', caps[1]):
            continue
        for bloque in re.split(r'\n\s*\n', sec):
            lineas = [l.strip() for l in bloque.strip().splitlines() if l.strip()]
            if len(lineas) >= 2 and lineas[1].startswith('—'):
                out.append(lineas[0])
            elif lineas and lineas[0].startswith('- ') and '—' in lineas[0]:
                out.append(lineas[0][2:].split(' — ')[0])
    return out


def investigacion_por_seccion(texto_indice):
    """Entradas de las secciones que nombra el índice: `tecnica_b.md` §3, §6-§9."""
    out = []
    for archivo, secs in re.findall(r'`((?:tecnica_[ab]|fisiologia)\.md)`\s*((?:§\d+(?:-§?\d+)?[,\s]*)+)', texto_indice):
        nums = []
        for a, b in re.findall(r'§(\d+)(?:-§?(\d+))?', secs):
            nums += list(range(int(a), int(b or a) + 1))
        texto = (INVESTIGACION / archivo).read_text(encoding='utf-8').split('## No encontrado')[0]
        for sec in re.split(r'^## ', texto, flags=re.M)[1:]:
            m = re.match(r'(\d+)\.', sec)
            if not m or int(m[1]) not in nums:
                continue
            for bloque in re.split(r'\n\s*\n', sec):
                lineas = [l.strip() for l in bloque.strip().splitlines() if l.strip()]
                if len(lineas) >= 2 and lineas[1].startswith('—'):
                    out.append(lineas[0])
                elif lineas and lineas[0].startswith('- ') and '—' in lineas[0]:
                    out.append(lineas[0][2:].split(' — ')[0])
    return out


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:40]


def figuras_por_defecto(n):
    for rango, figs in FIGURAS_POR_CAPITULO.items():
        if n in rango:
            return figs
    return 'fig.audiograma()'


# Edad por defecto de los capítulos del recién nacido y el lactante
EDAD_POR_CAPITULO = {16: 'edad_horas=24', 17: 'edad_meses=4'}


def pedidos_clinicos(cap, esc, n=None):
    """Lista de (nombre, código del caso, cuadros, nota) en el orden del índice."""
    out, vistos = [], set()
    orden = cap['orden']
    for i, tok in enumerate(orden):
        if tok.isdigit():
            clave = orden[i + 1] if i + 1 < len(orden) and not orden[i + 1].isdigit() else None
            vistos.add(clave)
            out.append((f'p{tok}', f'demo({tok}, FIGURAS)', [clave], ''))
            continue
        if tok in vistos:
            continue
        vistos.add(tok)
        e = esc.get(tok, {})
        r0, r1 = e.get('edad') or [None, None]
        # un adulto de 45, dentro del rango de edad que admite el cuadro
        edad = max(45, r0 or 0)
        if r1 is not None:
            edad = min(edad, r1)
        lados = "od='{0}', oi='{0}'".format(tok) if e.get('lateralidad') == 'bilateral' else f"od='{tok}'"
        nota = ''
        if r1 is not None and r1 < 1:          # solo existe en el recién nacido
            nota = 'recién nacido: armar_casos.sh todavía no carga la edad en horas'
        edad_txt = EDAD_POR_CAPITULO.get(n, f'edad={edad}')
        if n in EDAD_POR_CAPITULO:
            nota = ''
        out.append((tok, f"cuadro('{tok}', FIGURAS, {lados}, {edad_txt})", [tok], nota))
    return out


def generador_clinico(n, cap, pedidos, archivo_md):
    lineas = []
    for _, codigo, _, nota in pedidos:
        lineas.append(f'    # {nota}\n    # {codigo},' if nota else f'    {codigo},')
    return f'''#!/usr/bin/env python3
"""Capítulo {n} — {cap['titulo']}.

    python3 docs/libro/capitulos/{archivo_md.stem}.py              casos + figuras + PDF
    python3 docs/libro/capitulos/{archivo_md.stem}.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/{archivo_md.stem}.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
{archivo_md.name} (cada caso se nombra ahí como cap{n:02d}_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [{figuras_por_defecto(n)}]

CASOS = [
{chr(10).join(lineas)}
]

if __name__ == '__main__':
    Capitulo({n}).generar(CASOS)
'''


def referencias(clave, tecnica, fisiologia, cuadros, sistema):
    L = ['## Referencias', '', '<!-- Sugeridas: podar y ordenar. -->', '', '### Técnica', '']
    tec = [sistema['codigos'][c] for c in codigos_ok(tecnica) if sistema['codigos'].get(c)]
    tec += investigacion('tecnica_a.md', clave) + investigacion('tecnica_b.md', clave)
    L += [f'1. {r}' for r in dict.fromkeys(tec)] or ['> ✍ Sin referencias de técnica todavía']
    if fisiologia is not None:
        L += ['', '### Fisiología', '']
        fis = investigacion('fisiologia.md', clave)
        L += [f'1. {r}' for r in dict.fromkeys(fis)] or ['> ✍ Sin referencias de fisiología todavía']
    if cuadros:
        L += ['', '### Patología', '']
        pat = [c for k in cuadros for c in sistema['patologias'].get(k, [])]
        L += [f'1. {r}' for r in dict.fromkeys(pat)] or ['> ✍ Sin referencias de patología todavía']
    return L


def texto_clinico(n, cap, pedidos, figuras, sistema):
    prefijo = f'cap{n:02d}_'
    foco = f' (→ {cap["foco"]})' if cap['foco'] else ''
    cuadros = [c for p in pedidos for c in p[2] if c]
    L = [f'# {n}. {cap["titulo"]}', '',
         ':::objetivos En este capítulo', '- ✍ Objetivos del capítulo', ':::', '',
         '> ✍ Párrafo de entrada: la situación clínica que abre el capítulo', '',
         '## Técnica en foco', '',
         f'> ✍ Qué mirar de la técnica en este problema{foco}: {sin_marcas(cap["tecnica"])}', '',
         ':::ayuda Ayuda memoria', '✍', ':::', '',
         '## Fisiología', '',
         f'> ✍ {sin_marcas(cap["fisiologia"]) or "Lo justo del mecanismo"} (el detalle está en Bases, B1-B4)', '',
         '## Patología', '', '> ✍ ' + '; '.join(cap['nombres'].get(c, c) for c in cuadros), '',
         ':::sabias ¿Sabías que?', '✍', ':::', '',
         '## Razonamiento', '', '> ✍ Texto del autor', '',
         ':::pregunta Pregunta abierta', '✍', ':::', '', '## Casos', '',
         'Cada caso se trabaja en cuatro pasos, como en el aprendizaje basado en problemas: lee la entrevista, '
         'separa los datos que importan, plantea tus hipótesis y decide qué pedir **antes** de mirar los '
         'resultados. La resolución de cada caso está al final del capítulo.', '']
    for nombre, _, _, nota in pedidos:
        if nota:
            L += [f'<!-- {prefijo}{nombre}: {nota} -->', '']
            continue
        L += [f'{{{{caso {prefijo}{nombre}}}}}', '',
              ':::pregunta Paso 1 · ¿Qué datos importan?', '✍', ':::', '',
              ':::pregunta Paso 2 · Tus hipótesis', '✍', ':::', '',
              ':::pregunta Paso 3 · ¿Qué pedirías y por qué?', '✍', ':::', '',
              '#### Paso 4 · Los resultados', '']
        vistos = {}
        for tipo in figuras:
            vistos[tipo] = vistos.get(tipo, 0) + 1
            extra = f' {vistos[tipo]}' if vistos[tipo] > 1 else ''
            L += [f':::figura {prefijo}{nombre} {tipo}{extra}',
                  '- ✍ observación (con globo: "- @ANCLA | texto"; anclas como "OD 4000", "OD 80 V", "ipsi OD 1000", "OD max")',
                  ':::', '']
        L += [':::docente Guía del caso',
              '- **Datos clave:** ✍', '- **Hipótesis esperables:** ✍', '- **Qué pedir:** ✍',
              '- **Errores esperables:** ✍', '- **En LabSim:** ✍', ':::', '']
    L += ['## Resolución de los casos', '',
          'Intenta resolver cada caso con los pasos del aprendizaje basado en problemas antes de leer esta sección.', '']
    for k, (nombre, _, _, nota) in enumerate([q for q in pedidos if not q[3]], start=1):
        L += [f'### Caso {n}.{k}', '', '#### Razonamiento', '', '> ✍ Texto del autor', '',
              '#### Diagnóstico y qué sigue', '', '> ✍ Texto del autor', '']
    L += ['## Para cerrar', '', ':::pregunta Preguntas para discutir', '1. ✍', ':::', '',
          ':::ayuda Ayuda memoria del capítulo', '- ✍', ':::', '']
    L += referencias(n, cap['tecnica'], cap['fisiologia'], cuadros, sistema)
    return '\n'.join(L) + '\n'


def herramienta(clave, sistema):
    titulo, cuerpo = seccion_del_indice(clave)
    descripcion = sin_marcas(re.sub(r'Refs?:.*$', '', cuerpo.strip(), flags=re.S))
    L = [f'# {clave}. {titulo}', '',
         ':::objetivos En esta herramienta', '- ✍ Qué vas a saber hacer al terminar', ':::', '',
         f'> ✍ {descripcion}', '']
    for sec, que in SECCIONES_HERRAMIENTA:
        L += [f'## {sec}', '', f'> ✍ {que}', '']
        if sec == 'Paso a paso':
            L += [':::ayuda Ayuda memoria', '✍', ':::', '']
        if sec == 'Errores frecuentes':
            L += [':::ojo Ojo clínico', '✍', ':::', '']
    L += [':::pregunta Preguntas para practicar', '1. ✍', ':::', '']
    # Las herramientas toman las referencias que el índice les asigna (✓ y §),
    # no por número: H4 no es el capítulo 4.
    tec = [sistema['codigos'][c] for c in codigos_ok(cuerpo) if sistema['codigos'].get(c)]
    tec += investigacion_por_seccion(cuerpo)
    L += ['## Referencias', '', '<!-- Sugeridas: podar y ordenar. -->', '']
    L += [f'1. {r}' for r in dict.fromkeys(tec)] or ['> ✍ Sin referencias todavía']
    gen = f'''#!/usr/bin/env python3
"""Herramienta {clave} — {titulo}.

    python3 docs/libro/capitulos/<este archivo>.py              figuras + PDF
    python3 docs/libro/capitulos/<este archivo>.py --solo-pdf   solo el PDF

Una herramienta no necesita pacientes, pero puede ilustrar con algunos
(demo() o cuadro(), igual que un capítulo clínico; ver libro.py).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

CASOS = [
]

if __name__ == '__main__':
    Capitulo('{clave}').generar(CASOS)
'''
    return titulo, '\n'.join(L) + '\n', gen


def crear(clave, sistema, forzar):
    CAPITULOS.mkdir(exist_ok=True)
    if clave.upper().startswith('B'):
        # Bases: capítulos que escribe otra persona; solo el lugar en el libro
        clave = clave.upper()
        titulo, cuerpo = seccion_del_indice(clave)
        base = CAPITULOS / f'B{int(clave[1:]):02d}-{slug(titulo)}'
        md = f'# {clave}. {titulo}\n\n> ✍ {sin_marcas(cuerpo.strip())}\n'
        py = None
    elif clave.upper().startswith('H'):
        clave = clave.upper()
        titulo, md, py = herramienta(clave, sistema)
        base = CAPITULOS / f'H{int(clave[1:]):02d}-{slug(titulo)}'
    else:
        n = int(clave)
        cap = capitulo_clinico(n)
        base = CAPITULOS / f'{n:02d}-{slug(cap["titulo"])}'
        pedidos = pedidos_clinicos(cap, sistema['escenarios'], n)
        figuras = ['logoaudiometria' if f == 'logo' else f
                   for f in re.findall(r'fig\.(\w+)\(', figuras_por_defecto(n))]
        py = generador_clinico(n, cap, pedidos, base.with_suffix('.md'))
        md = texto_clinico(n, cap, pedidos, figuras, sistema)
    hechos = []
    for archivo, contenido in ((base.with_suffix('.py'), py), (base.with_suffix('.md'), md)):
        if contenido is None or (archivo.exists() and not forzar):
            continue
        archivo.write_text(contenido, encoding='utf-8')
        if archivo.suffix == '.py':
            archivo.chmod(0o755)
        hechos.append(archivo.name)
    print(f'{clave}: ' + (', '.join(hechos) if hechos else 'ya existía, no se tocó'))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    sistema = datos_del_sistema()
    if args == ['todos']:
        claves = re.findall(r'^### ([HB]?\d+)\. ', INDICE.read_text(encoding='utf-8'), re.M)
    else:
        claves = args
    for clave in claves:
        crear(clave, sistema, '--forzar' in sys.argv)


if __name__ == '__main__':
    main()
