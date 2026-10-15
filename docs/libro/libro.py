"""Lo común a los generadores de capítulo (capitulos/NN-*.py).

Cada capítulo tiene dos archivos que se editan a mano:

  capitulos/NN-titulo.md   el texto (bloques, recuadros, globos)
  capitulos/NN-titulo.py   el generador: qué pacientes y qué figuras lleva

y se rehace entero con:

  python3 docs/libro/capitulos/NN-titulo.py              casos + figuras + PDF
  python3 docs/libro/capitulos/NN-titulo.py --solo-pdf   solo el PDF (texto cambiado)
  python3 docs/libro/capitulos/NN-titulo.py --rearmar    vuelve a armar los casos por cuadro

El generador declara los casos con `demo()` (un paciente de práctica) o
`cuadro()` (un caso nuevo que arma el editor real, ver figuras/armar_casos.sh)
y las figuras con `fig.*`. Un caso por cuadro se rearma solo si cambió su
pedido; si no, se reutiliza el de casos/generados/.
"""
import json
import os
import pathlib
import subprocess
import sys

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
CASOS = AQUI / 'casos'
GENERADOS = CASOS / 'generados'


class fig:
    """Las figuras que sabe hacer el motor (figuras/motor/), con sus opciones."""

    @staticmethod
    def audiograma(estudio=True, ldl=True, sin_enmascarar=False):
        """estudio: ósea solo donde la aérea es anormal; sin_enmascarar: la curva sombra."""
        return {'tipo': 'audiograma', 'estudio': estudio, 'ldl': ldl, 'sin_enmascarar': sin_enmascarar}

    @staticmethod
    def acumetria():
        return {'tipo': 'acumetria'}

    @staticmethod
    def logo(enmascarado=True):
        return {'tipo': 'logoaudiometria', 'enmascarado': enmascarado}

    @staticmethod
    def timpanograma(sonda=226):
        return {'tipo': 'timpanograma', 'sonda': sonda}

    @staticmethod
    def reflejos():
        return {'tipo': 'reflejos'}

    @staticmethod
    def teoae():
        return {'tipo': 'teoae'}

    @staticmethod
    def dpoae():
        return {'tipo': 'dpoae'}

    @staticmethod
    def abr(niveles=(80, 60, 40), estimulo=None, marcar=('I', 'III', 'V')):
        f = {'tipo': 'abr', 'niveles': list(niveles), 'marcar': list(marcar)}
        if estimulo:
            f['estimulo'] = estimulo
        return f

    @staticmethod
    def ecochg(nivel=90):
        return {'tipo': 'ecochg', 'nivel': nivel}

    @staticmethod
    def vemp(subtipo='cvemp'):
        return {'tipo': 'vemp', 'subtipo': subtipo}


def demo(numero, figuras, nombre=None):
    """Un paciente de práctica (docs/manual/capturas/casos_demo.json)."""
    return {'nombre': nombre or f'p{numero}', 'caso': f'demo:{numero}', 'figuras': list(figuras)}


def cuadro(nombre, figuras, od='normal', oi='normal', grado_od=None, grado_oi=None,
           edad=40, sexo='hombre', semilla=None, edad_horas=None, edad_meses=None,
           anamnesis=None, historia=None, antecedentes=(), medicamentos='', cirugias=''):
    """Un caso nuevo por cuadro (claves de CaseProfile::SCENARIOS) y grado.

    Un recién nacido o lactante va con edad_horas= o edad_meses= (la edad en
    años queda en 0, como lo carga el editor)."""
    pedido = {'cuadro': {'OD': od, 'OI': oi}, 'edad': edad, 'sexo': sexo}
    if edad_horas is not None or edad_meses is not None:
        pedido['edad'] = 0
        pedido['edad_valor'] = edad_horas if edad_horas is not None else edad_meses
        pedido['edad_unidad'] = 'horas' if edad_horas is not None else 'meses'
    grado = {k: v for k, v in (('OD', grado_od), ('OI', grado_oi)) if v}
    if grado:
        pedido['grado'] = grado
    if semilla is not None:
        pedido['semilla'] = semilla
    # La anamnesis va AL CASO (no solo al libro): queda en la ficha y en el
    # paciente de LabSim, que responde en el chat con esa misma historia.
    # historia: lista de (días hacia atrás, texto) -> líneas '{{-N}} texto'.
    if anamnesis or historia or antecedentes or medicamentos or cirugias:
        pedido['anamnesis'] = {
            'otros': ' '.join((anamnesis or '').split()),
            'historia': '\n'.join(f'{{{{-{d}}}}} {txt}' for d, txt in (historia or [])),
            'hist': list(antecedentes), 'medicamentos': medicamentos, 'cirugias': cirugias,
        }
    return {'nombre': nombre, 'caso': pedido, 'figuras': list(figuras)}


class Capitulo:
    def __init__(self, numero):
        self.numero = numero
        self.prefijo = f'cap{numero:02d}_' if isinstance(numero, int) else f'{str(numero).lower()}_'

    def nombre(self, c):
        return self.prefijo + c['nombre']

    def generar(self, casos, argv=None):
        argv = sys.argv[1:] if argv is None else argv
        nombres = []
        rearmar = []
        for c in casos:
            n = self.nombre(c)
            nombres.append(n)
            spec = {'caso': c['caso'], 'figuras': c['figuras']}
            (CASOS / f'{n}.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            if isinstance(c['caso'], dict):
                gen = GENERADOS / f'{n}.json'
                previo = json.loads(gen.read_text(encoding='utf-8')).get('pedido') if gen.exists() else None
                if '--rearmar' in argv or previo != c['caso']:
                    rearmar.append(n)
        if '--solo-pdf' not in argv:
            if rearmar:
                print('Armando casos:', ', '.join(rearmar))
                subprocess.run([str(AQUI / 'figuras' / 'armar_casos.sh'), *rearmar], check=True, cwd=RAIZ)
            if '--sin-figuras' not in argv:
                print('Figuras:', ', '.join(nombres))
                subprocess.run(['micromamba', 'run', '-n', 'labsim', 'python', str(AQUI / 'figuras' / 'hacer_figuras.py'),
                                *nombres], check=True, cwd=RAIZ, env=dict(os.environ, QT_QPA_PLATFORM='offscreen'))
        extra = ['--docente'] if '--docente' in argv else []
        subprocess.run([sys.executable, str(AQUI / 'hacer_libro.py'), str(self.numero), *extra], check=True, cwd=RAIZ)
