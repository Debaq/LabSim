"""El intercomunicador de la sala de control del PSG (nasal/intercom.py) y el ronquido.

- Cada frase tiene su audio (scripts/voces_comandos.py --psg) y su texto.
- Las biocalibraciones se ven en los canales (sueno.BIOCAL): EOG al mirar a los lados y parpadear, EMG
  al apretar los dientes, alfa con los ojos cerrados, la cánula casi plana respirando por la boca con
  el térmico normal, flujo y bandas quietos aguantando la respiración, ronquido al simularlo.
- En la ventana: la noche parte con la luz encendida y en tiempo real; despierto hace la maniobra y
  dormido no la oye; "Apagar la luz" larga la noche; pedirle una posición lo da vuelta al terminar la
  frase; las biocalibraciones quedan en el informe (también después de darse vuelta) y vuelven al
  retomar; cada frase va al registro (psg_intercom).
- El ronquido: grabaciones CC0 recortadas por sexo (resources/audio/psg/<sexo>/); cada caso usa una
  grabación de su sexo, siempre la misma; la vista ronca al empezar cada inspiración mientras el modelo
  dice que ronca, y no cuando no.
"""
import ast
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
RAIZ = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(RAIZ, 'src'))
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(RAIZ)

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from nasal import intercom  # noqa: E402
from nasal import pieza_vista as pv  # noqa: E402
from nasal import sueno as Z  # noqa: E402
import test_nasal_sueno as T  # noqa: E402


def _textos_psg():
    arbol = ast.parse(open('scripts/voces_comandos.py', encoding='utf-8').read())
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and getattr(nodo.targets[0], 'id', '') == 'COMANDOS_PSG':
            return ast.literal_eval(nodo.value)
    raise AssertionError('falta COMANDOS_PSG')


def test_cada_frase_tiene_texto_y_audio():
    textos = _textos_psg()
    assert set(textos) == set(intercom.CLAVES)
    for clave in intercom.CLAVES:
        ruta = os.path.join('resources', 'audio', 'comandos_psg', f'{clave}.mp3')
        assert os.path.getsize(ruta) > 5000, ruta
    assert set(intercom.POSICION.values()) == set(Z.POSICIONES)
    assert {c for c in intercom.CLAVES if c in Z.BIOCAL} == set(Z.BIOCAL)


def _rango(x, a, b):
    return max(x[a:b]) - min(x[a:b])


def test_biocalibraciones_en_los_canales():
    S = Z.noche({'perfil': 'moderado'}, 'psg')
    mont = [k for k, _, _ in Z.SENSORES]
    a = Z.senales(S, 0, 240, mont)
    S['bio'] = [(10, 'mire_a_los_lados'), (30, 'aguante'), (50, 'respire_boca'), (70, 'apriete_dientes'),
                (80, 'parpadee'), (90, 'ojos_cerrados'), (130, 'ronque')]
    b = Z.senales(S, 0, 240, mont)
    fs = 10
    ventana = {c: (int((t + Z.BIOCAL[c][0]) * fs), int((t + sum(Z.BIOCAL[c])) * fs)) for t, c in S['bio']}
    i, j = ventana['mire_a_los_lados']
    assert _rango(b['eog'], i, j) > 1.6 > 5 * _rango(a['eog'], i, j)
    i, j = ventana['aguante']
    assert _rango(b['canula'], i, j) < 0.2 and _rango(b['torax'], i, j) < 0.2 and _rango(a['canula'], i, j) > 1
    i, j = ventana['respire_boca']
    assert _rango(b['canula'], i, j) < 0.4 and _rango(b['termico'], i, j) > 1.5
    i, j = ventana['apriete_dientes']
    assert _rango(b['emg'], i, j) > 1.5 > 2 * _rango(a['emg'], i, j)
    i, j = ventana['parpadee']
    assert max(b['eog'][i:j]) > 0.7
    i, j = ventana['ojos_cerrados']
    assert _rango(b['eeg'], i, j) > 0.8
    i, j = ventana['ronque']
    assert _rango(b['ron'], i, j) > 2 * _rango(a['ron'], i, j)
    # Fuera de las maniobras no cambia nada.
    assert b['eog'][:100] == a['eog'][:100]


def _noche_en_vivo():
    w = T.ventana(T.caso({'perfil': 'moderado'}, edad=52, gender=0))
    w.cmb_estudio.setCurrentIndex(w.cmb_estudio.findData('psg'))
    for k in Z.sensores_del_estudio('psg'):
        w.chk_sensor[k].click()
    w._registrar()
    T.esperar(lambda: w.S is not None)
    w.timer.stop()
    return w


def test_la_sala_de_control():
    T.LOGS.eventos.clear()
    w = _noche_en_vivo()
    assert w.cmb_velocidad.currentData() == 1 and w.S['etapa'][0] == 'W'
    # Con la luz encendida el botón para apagarla está a la vista en la sala.
    w.dibujar()
    assert w.luz_encendida and not w.btn_luz.isHidden() and 'Luz encendida' in w.lbl_camara.text()
    w.t_actual = 20
    w._intercom('mire_a_los_lados')
    assert w.S['bio'] == [(20, 'mire_a_los_lados')]
    w.t_actual = 40
    w.t0 = 0
    sen = Z.senales(w.S, 0, 60, w.montaje)
    assert _rango(sen['eog'], 260, 340) > 1.6
    # Dormido no la oye.
    dormido = next(t for t in range(w.S['N']) if w.S['etapa'][t] == 'N2')
    w.t_actual = dormido
    w._intercom('apriete_dientes')
    assert len(w.S['bio']) == 1 and 'dormido' in w.lbl_mensaje.text()
    # Apagar la luz (el botón de la sala) larga la noche.
    w._apagar_luz()
    assert w.cmb_velocidad.currentData() == 0 and not w.luz_encendida and w.btn_luz.isHidden()
    assert 'Luz encendida' not in w.lbl_camara.text()
    # Dormido y roncando, la sala lo dice (y la pieza ronca).
    ronca = next(t for t in range(dormido, w.S['N']) if w.S['etapa'][t] != 'W' and w.S['ron'][t // 60]
                 and Z.respiracion_en(w.S, Z.eventos_cerca(w.S, t), t)[0] > 0.3)
    w.t_actual = ronca
    w.dibujar()
    assert 'ronca' in w.lbl_camara.text()
    # Pedirle otra posición: se da vuelta al terminar la frase y conserva las biocalibraciones.
    antes = w.S['pos'][dormido]
    otra = next(p for p in Z.POSICIONES if p != antes)
    w._pedir_posicion(otra)
    assert w.S['pos'][dormido] == antes                      # todavía oyendo la frase
    T.esperar(lambda: not w.recalculando and w.S['pos'][dormido] == otra, limite=30)
    assert w.S['bio'] == [(20, 'mire_a_los_lados')]
    assert [(t, p) for t, p in w.S['acomodos']] == [(dormido, otra)]
    # Al informe y de vuelta.
    job = w.report_job()
    assert job['data']['bio'] == [[20, 'mire_a_los_lados']]
    w2 = T.ventana(T.caso({'perfil': 'moderado'}, edad=52, gender=0), login={'permission': 444, 'name': 'a'})
    assert w2.restore_report(job['data']) and w2.S['bio'] == [(20, 'mire_a_los_lados')]
    claves = [x['clave'] for x in T.LOGS.de('psg_intercom')]
    assert {'mire_a_los_lados', 'apriete_dientes', 'apagar_luz'} <= set(claves)
    hizo = {x['clave']: x['hizo'] for x in T.LOGS.de('psg_intercom')}
    assert hizo['apriete_dientes'] is None and hizo['mire_a_los_lados'] == 'mire_a_los_lados'


def test_ronquidos_por_sexo():
    for sexo in ('hombre', 'mujer'):
        grabaciones = pv.ronquidos_de(sexo)
        assert len(grabaciones) >= 2, sexo
        for g in grabaciones:
            assert len(g) >= 3 and all(os.path.getsize(r) > 15000 for r in g)
    assert set(map(str, pv.ronquidos_de('hombre'))) .isdisjoint(map(str, pv.ronquidos_de('mujer')))
    v = pv.VistaPieza(sonido=True)
    v.paciente('mujer', 7)
    a = list(v.ronquidos)
    assert a and all('/mujer/' in r for r in a)
    v.paciente('mujer', 7)
    assert list(v.ronquidos) == a          # mismo caso, misma grabación
    v.paciente('hombre', 7)
    assert all('/hombre/' in r for r in v.ronquidos)
    assert not pv.VistaPieza(sonido=False).ronquidos
    # En la ventana: la paciente mujer ronca con voz de mujer.
    w = T.ventana(T.caso({'perfil': 'moderado'}, edad=52, gender=1))
    assert all('/mujer/' in r for r in w.camara.ronquidos) and w.camara.ronquidos


def test_ronca_al_inspirar():
    v = pv.VistaPieza(sonido=True)
    v.paciente('hombre', 3)
    assert v.ronquidos
    # Suena con QMediaPlayer (QSoundEffect no se oía en el equipo del autor): el archivo queda cargado.
    v._roncar(0.8)
    reproductor, salida = v._reproductores[0]
    assert reproductor.source().toLocalFile() == v.ronquidos[0] and abs(salida.volume() - 0.8) < 0.01
    v.callar()

    def correr(resp, segundos=12):
        v.poner('supino', False, '', resp)
        v.ronco = 0
        for _ in range(int(segundos / 0.05)):
            v._t -= 0.05
            v._tic()
        return v.ronco

    sin = {'ev': [], 'esp': [], 'ron': [False] * 3}
    con = {'ev': [], 'esp': [], 'ron': [True] * 3}
    assert correr(Z.respiracion_en(sin, [], 30)) == 0
    assert 2 <= correr(Z.respiracion_en(con, [], 30)) <= 4          # una por respiración (~4,4 s)
    # En la apnea obstructiva no ronca (no pasa aire); al terminar, ronquidos de recuperación.
    ao = {'ev': [dict(t=100, dur=20, tipo='ao', arousal=True)], 'esp': [], 'ron': [False] * 3}
    assert correr(Z.respiracion_en(ao, ao['ev'], 110)) == 0
    assert correr(Z.respiracion_en(ao, ao['ev'], 122), 6) >= 1


def test_acelerada_es_adelantar_la_grabacion():
    w = _noche_en_vivo()
    w._apagar_luz()                                     # pasa a "Noche en 15 min" (~×31)
    w.timer.stop()
    S = w.S
    t = next(t for t in range(S['N']) if S['etapa'][t] != 'W' and all(S['ron'][(t // 60) + k] for k in range(3)))
    w.t_actual = t
    w.dibujar()
    v = w.camara
    assert v.factor and v.factor > 20
    v.ronco = 0
    for _ in range(200):                                # 10 s: ni respira ni ronca
        v._t -= 0.05
        v._tic()
    assert v.ronco == 0 and v.niveles() == (1.5, 1.5) and v.boca == 0
    # En pausa o en tiempo real: en vivo, ronca.
    w._pausa()
    assert v.factor is None
    for _ in range(200):
        v._t -= 0.05
        v._tic()
    assert v.ronco >= 1
    w._pausa()
    assert v.factor
    w.cmb_velocidad.setCurrentIndex(w.cmb_velocidad.findData(1))
    assert v.factor is None and T.LOGS.de('psg_velocidad')


def test_ver_la_proxima_apnea():
    from nasal.PolisomnografiaWindow import ANTES_DE_LA_APNEA
    T.LOGS.eventos.clear()
    w = _noche_en_vivo()
    w._apagar_luz()
    w.timer.stop()
    ev = next(x for x in w.S['ev'] if x['tipo'] in Z.APNEAS)
    w._proxima_apnea()
    w.timer.stop()
    assert w.t_actual == ev['t'] - ANTES_DE_LA_APNEA and w.cmb_velocidad.currentData() == 1
    assert w.camara.factor is None and w.corriendo
    assert T.LOGS.de('psg_proxima_apnea')[0]['verdad']['t'] == ev['t']
    # Al llegar a la apnea, la pieza recibe la apnea (la obstructiva, con paradoja).
    w.t_actual = ev['t'] + ev['dur'] - 2
    w.dibujar()
    assert w.camara.resp[1] < 0.1 if ev['tipo'] == 'ac' else w.camara.resp[0] < 0.1
    # La siguiente vez va a la apnea que sigue; al final de la noche, no hay más.
    w._proxima_apnea()
    sig = next(x for x in w.S['ev'] if x['tipo'] in Z.APNEAS and x['t'] > ev['t'])
    assert w.t_actual == sig['t'] - ANTES_DE_LA_APNEA
    w.t_actual = w.S['N'] - 5
    w._proxima_apnea()
    assert 'No quedan apneas' in w.lbl_mensaje.text()


if __name__ == '__main__':
    for nombre, fn in list(globals().items()):
        if nombre.startswith('test_') and callable(fn):
            fn()
            print(f'  {nombre} OK', flush=True)
    print('TODOS LOS TESTS PASARON', flush=True)
    os._exit(0)
