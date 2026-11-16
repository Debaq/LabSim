"""La pieza del laboratorio de sueño (nasal/pieza_vista.py, resources/psg_pieza).

- El paquete trae, para cada punto de vista de la ventanilla y para la cámara del techo, un recorte por
  cada pose y estado (dormido: grilla tórax × abdomen; despierto y roncando: en fase), y todos se leen.
- Cada pose se ve distinta (el recorte de la cama cambia); la respiración, la paradoja y la boca abierta
  mueven algo.
- Respira como las bandas: en la apnea obstructiva el abdomen va al revés del tórax, en la central se
  queda quieto, después del evento ronca con la boca abierta; despierto no hay paradoja.
- La vista: dibuja la pieza; el mouse cambia el punto de vista; clic en la cámara chica intercambia las
  vistas; doble clic en la grande pide ampliarla; sin paquete no se cae.
- En la ventana del PSG la vista sigue a la noche (pose, vigilia y respiración del segundo en curso) y
  hay velocidad de tiempo real.
"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
RAIZ = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(RAIZ, 'src'))
os.chdir(RAIZ)

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtGui import QImage  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from nasal import pieza_vista as pv  # noqa: E402

POSES = ('supino', 'izquierda', 'derecha')


def _paquete():
    P = pv.Paquete.cargar()
    assert P is not None, 'falta resources/psg_pieza (scripts/psg_pieza/LEEME.md)'
    return P


def _claves(P):
    n = range(P.respira)
    return ({f'{p}_0_{i}_{j}' for p in POSES for i in n for j in n}
            | {f'{p}_{e}_{r}_{r}' for p in POSES for e in (1, 2) for r in n})


def test_el_paquete_trae_todo():
    P = _paquete()
    assert len(P.vistas) == 5 and P.respira >= 3
    for g in [*P.vistas, P.techo]:
        assert set(g['cuadros']) == _claves(P)
        base = P.imagen(g['base'])
        assert not base.isNull()
        x, y, w, h = g['rect']
        assert 0 <= x and 0 <= y and x + w <= base.width() and y + h <= base.height()
        for ref in g['cuadros'].values():
            im = P.imagen(ref)
            assert (im.width(), im.height()) == (w, h)
    for g in P.vistas:
        assert len(g['vano']) == 4


def _distintas(a, b, umbral=1500):
    """Cuántos píxeles (muestreados) cambian entre dos imágenes del mismo tamaño."""
    n = 0
    for y in range(0, a.height(), 3):
        for x in range(0, a.width(), 3):
            ca, cb = a.pixelColor(x, y), b.pixelColor(x, y)
            if abs(ca.red() - cb.red()) + abs(ca.green() - cb.green()) + abs(ca.blue() - cb.blue()) > 30:
                n += 1
    return n > umbral / 9


def test_cada_pose_se_ve_distinta_y_respira():
    P = _paquete()
    g = P.vistas[2]
    n = P.respira - 1
    im = {p: P.imagen(g['cuadros'][f'{p}_0_0_0']) for p in POSES}
    assert _distintas(im['supino'], im['izquierda']) and _distintas(im['izquierda'], im['derecha'])
    hondo = P.imagen(g['cuadros'][f'supino_0_{n}_{n}'])
    assert _distintas(im['supino'], hondo, umbral=60)
    paradoja = P.imagen(g['cuadros'][f'supino_0_{n}_0'])     # tórax arriba, abdomen abajo
    assert _distintas(paradoja, hondo, umbral=30) and _distintas(paradoja, im['supino'], umbral=30)
    # La boca abierta se ve en el primer plano de la cámara (techo), aunque sea poco.
    t = P.techo
    assert _distintas(P.imagen(t['cuadros'][f'supino_0_{n}_{n}']), P.imagen(t['cuadros'][f'supino_2_{n}_{n}']),
                      umbral=3)


def _recorrido(v, resp, despierto=False):
    """(tórax, abdomen) a lo largo de un ciclo, con la respiración `resp`, ya asentada."""
    v.poner('supino', despierto, '', resp)
    v.esfuerzo, v.paradoja = resp[1], resp[2]
    out = []
    for k in range(20):
        v.fase = k / 20
        out.append(v.niveles())
    return out


def test_respira_como_las_bandas():
    from nasal import sueno as Z
    v = pv.VistaPieza()
    ev = [dict(t=100, dur=20, tipo='ao', arousal=True), dict(t=200, dur=20, tipo='ac', arousal=False),
          dict(t=300, dur=20, tipo='am', arousal=False)]
    S = {'ev': ev, 'esp': [], 'ron': [False] * 10}
    # Normal: tórax y abdomen juntos, todo el rango.
    normal = _recorrido(v, Z.respiracion_en(S, ev, 50))
    assert max(t for t, _ in normal) > 2.8 and min(t for t, _ in normal) < 0.2
    assert all(abs(t - a) < 0.5 for t, a in normal)
    # Final de la obstructiva: el abdomen sube cuando el tórax baja.
    ao = _recorrido(v, Z.respiracion_en(S, Z.eventos_cerca(S, 118), 118))
    assert all((t - 1.5) * (a - 1.5) <= 0.05 for t, a in ao) and max(abs(t - a) for t, a in ao) > 2
    # Central: quieto. Mixta: empieza quieta y termina paradójica.
    ac = _recorrido(v, Z.respiracion_en(S, Z.eventos_cerca(S, 210), 210))
    assert max(t for t, _ in ac) - min(t for t, _ in ac) < 0.2
    am0 = _recorrido(v, Z.respiracion_en(S, Z.eventos_cerca(S, 303), 303))
    am1 = _recorrido(v, Z.respiracion_en(S, Z.eventos_cerca(S, 318), 318))
    assert max(t for t, _ in am0) - min(t for t, _ in am0) < 0.2
    assert max(abs(t - a) for t, a in am1) > 1.5
    # Después de la obstructiva: respiraciones hondas y ronca (boca abierta).
    rec = Z.respiracion_en(S, Z.eventos_cerca(S, 122), 122)
    v.poner('supino', False, '', rec)
    for _ in range(40):
        v._t -= 0.05
        v._tic()
    assert v.boca > 0.8 and v.esfuerzo > 1.2
    # Sin ronquido ni evento la boca se cierra.
    v.poner('supino', False, '', Z.respiracion_en(S, ev, 50))
    for _ in range(40):
        v._t -= 0.05
        v._tic()
    assert v.boca < 0.1


def _foto(v):
    return v.grab().toImage().convertToFormat(QImage.Format.Format_RGB32)


def test_la_vista():
    v = pv.VistaPieza()
    v.resize(480, 300)
    v.show()
    v.poner('supino', False, '02:14')
    QTest.qWait(80)
    a = _foto(v)
    centro = a.pixelColor(240, 150)
    assert centro.red() + centro.green() + centro.blue() > 60      # se ve la pieza, no el fondo
    v.poner('izquierda', False, '02:15')
    assert _distintas(a, _foto(v), umbral=300)
    # El mouse a la izquierda: el punto de vista se corre y la imagen cambia.
    QTest.mouseMove(v, QPoint(10, 150))
    assert v.u_meta < 0.5
    v.u = v.u_meta
    b = _foto(v)
    QTest.mouseMove(v, QPoint(470, 150))
    v.u = v.u_meta
    assert v.u > 3.5 and _distintas(b, _foto(v), umbral=300)
    # Clic en la cámara chica: pasa a ser la grande (y vuelve).
    chica = v._rect_chica(v._area()).center().toPoint()
    QTest.mouseClick(v, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, chica)
    assert v.principal == 'techo'
    QTest.mouseClick(v, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                     v._rect_chica(v._area()).center().toPoint())
    assert v.principal == 'ventanilla'
    pedidos = []
    v.ampliar.connect(lambda: pedidos.append(1))
    QTest.mouseDClick(v, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(400, 200))
    assert pedidos
    # Respira: la fase avanza con el reloj.
    f0 = v.fase
    QTest.qWait(300)
    assert v.fase != f0
    v.hide()


def test_sin_paquete_no_se_cae():
    guardado = pv.Paquete._uno
    try:
        falso = pv.Paquete.__new__(pv.Paquete)
        falso.ok = False
        pv.Paquete._uno = falso
        v = pv.VistaPieza()
        v.resize(320, 200)
        v.poner('supino', True, '03:00')
        v.grab()
        QTest.mouseMove(v, QPoint(20, 20))
    finally:
        pv.Paquete._uno = guardado


def test_en_la_ventana_del_psg():
    from nasal import sueno as Z
    from nasal.PolisomnografiaWindow import PolisomnografiaWindow
    import test_nasal_sueno as T
    w = T.ventana(T.caso({'perfil': 'moderado'}, edad=52, gender=0))
    w.cmb_estudio.setCurrentIndex(w.cmb_estudio.findData('psg'))
    for k in Z.sensores_del_estudio('psg'):
        w.chk_sensor[k].click()
    w._registrar()
    T.esperar(lambda: w.S is not None)
    w.timer.stop()
    assert isinstance(w, PolisomnografiaWindow) and w._en_vivo()
    t = int(w.t_actual)
    assert w.camara.pos == w.S['pos'][t]
    assert w.camara.despierto == (w.S['etapa'][t] == 'W')
    assert w.camara.resp == Z.respiracion_en(w.S, Z.eventos_cerca(w.S, w.t_actual), w.t_actual)
    # En una apnea obstructiva la pieza recibe la paradoja de las bandas.
    ao = next(x for x in w.S['ev'] if x['tipo'] == 'ao')
    w.t_actual = ao['t'] + ao['dur'] - 2
    w.dibujar()
    assert w.camara.resp[2] > 0.9 and w.camara.pos == w.S['pos'][int(w.t_actual)]
    w.cmb_velocidad.setCurrentIndex(w.cmb_velocidad.findData(1))
    assert w._velocidad() == 1
    w._ampliar_pieza()
    assert w.pieza_grande.isVisible() and w.pieza_grande.pos == w.camara.pos
    w._manana()
    assert not w.pieza_grande.isVisible()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(__file__))
    for nombre, fn in list(globals().items()):
        if nombre.startswith('test_') and callable(fn):
            fn()
            print(f'  {nombre} OK', flush=True)
    print('TODOS LOS TESTS PASARON', flush=True)
    os._exit(0)
