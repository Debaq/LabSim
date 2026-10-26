"""
Los seis informes del módulo ABR que no son ABR (electrococleografía,
latencia media, CAEP, P300, MMN y ASSR) de punta a punta:

1. Se registra de verdad en la ventana, con marcas donde corresponde.
2. report_job() arma el informe con SU tipo, sus datos y sus imágenes.
3. Eso mismo (JSON + JPEG) lo lee el backend (ReportPdfBuilder, el mismo
   código que corre el hosting) y sale un PDF con lo registrado.

Sin `php` en el PATH solo se prueba hasta el punto 2.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('LABSIM_DATA_DIR', __import__('tempfile').mkdtemp(prefix='labsim_datos_'))

RAIZ = os.path.join(os.path.dirname(__file__), '..')
SRC = os.path.join(RAIZ, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(RAIZ)

try:
    import numpy as np  # noqa: F401
    from core.base import context  # noqa: F401  (crea el QApplication)
    from abr.AbrMainWindow import AbrMainWindow
    import test_assr
    import test_cortical_panel as cx
    import test_ecochg_panel as ec
    HAS_UI = True
except ImportError as exc:          # sin PySide6/pyqtgraph
    print(f"  (tests e2e salteados: {exc})")
    HAS_UI = False

# prueba -> (tipo del informe, frases ASCII que el PDF tiene que decir)
ESPERADO = {
    'ECochG': ('ELECTROCOCLEO', ['Electrococle', 'Medidas']),
    'MLR': ('PEALM', ['latencia media', 'Medidas OD']),
    'CAEP': ('CAEP', ['P1-N1-P2', 'Medidas OD']),
    'P300': ('P300', ['P300', 'Medidas OD']),
    'MMN': ('MMN', ['MMN', 'Medidas OD']),
    'ASSR': ('ASSR', ['estado estable', 'Portadoras OD', 'Portadoras OI',
                      'rechazadas por artefacto']),
}


def _registrar(prueba):
    """Una ventana con la prueba registrada y marcada, lista para informar."""
    if prueba == 'ECochG':
        w = ec._ventana()
        curva = ec._capturar(w)
        ec._marcar(w, curva)
    elif prueba == 'ASSR':
        w = test_assr._ventana()
        test_assr._registrar(w, 60)
    else:
        w = cx._ventana(prueba)
        cx._capturar(w)
        marca, canal, lat = {'MLR': ('Pa', 'Cz', 30.0), 'CAEP': ('N1', 'Cz', 100.0),
                             'P300': ('P3', 'Pz', 310.0), 'MMN': ('MMN', 'Fz', 180.0)}[prueba]
        cx._marcar(w, 0, canal, marca, lat)
    w.report.text_edit_1.setPlainText(f'Hallazgos de {prueba}.')
    w.report.text_edit_2.setPlainText(f'Conclusion de {prueba}.')
    return w


def _jobs():
    jobs = {}
    for prueba in ESPERADO:
        w = _registrar(prueba)
        job = w.report_job()
        assert job is not None, f'{prueba}: no arma informe'
        jobs[prueba] = (w, job)
    return jobs


def test_each_test_builds_its_own_report_with_data_and_images():
    if not HAS_UI:
        return
    for prueba, (w, job) in _jobs().items():
        tipo = ESPERADO[prueba][0]
        assert job['tipo'] == tipo, (prueba, job['tipo'])
        assert job['appointment_id'] in (7, 42)
        data = job['data']
        assert data['prueba'] == prueba
        assert data['conclusion'] == f'Conclusion de {prueba}.'
        assert data.get('curvas') or data.get('assr'), prueba
        json.dumps(data)                       # viaja como JSON
        imagenes = job['images']()
        assert imagenes, f'{prueba}: sin imágenes'
        assert all(os.path.getsize(r) > 500 for r in imagenes.values()), prueba
        # Cada prueba se sube como lo que es, no como un ABR.
        assert data['tecnica'], prueba


def test_the_backend_renders_a_pdf_of_each_report():
    if not HAS_UI or shutil.which('php') is None:
        return
    tmp = tempfile.mkdtemp(prefix='labsim_e2e_')
    try:
        shutil.copytree(os.path.join(RAIZ, 'labsim_backend', 'src'),
                        os.path.join(tmp, 'src'))
        reportes = os.path.join(tmp, 'data', 'reports')
        os.makedirs(reportes)
        trabajos = []
        for n, (prueba, (w, job)) in enumerate(_jobs().items(), start=1):
            for sufijo, ruta in job['images']().items():
                shutil.copy(ruta, os.path.join(reportes, f'report_{n}_{sufijo}.jpg'))
            trabajos.append({'id': n, 'prueba': prueba, 'tipo': job['tipo'],
                             'data': job['data']})
        with open(os.path.join(tmp, 'trabajos.json'), 'w') as f:
            json.dump(trabajos, f)
        with open(os.path.join(tmp, 'render.php'), 'w') as f:
            f.write(r"""<?php
require __DIR__ . '/src/ReportFile.php';
require __DIR__ . '/src/ReportPdfBuilder.php';
$paciente = ['nombre' => 'Ana', 'apellido' => 'Perez', 'rut' => '1-9', 'fecha_nac' => '2000-01-01'];
foreach (json_decode(file_get_contents(__DIR__ . '/trabajos.json'), true) as $t) {
    $pdf = ReportPdfBuilder::build($t['id'], $t['tipo'], $t['data'], $paciente, 'Alumno', '26-10-2026');
    file_put_contents(__DIR__ . "/informe_{$t['id']}.pdf", $pdf);
}
""")
        r = subprocess.run(['php', '-d', 'error_reporting=0', 'render.php'],
                           cwd=tmp, capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stdout + r.stderr
        for t in trabajos:
            with open(os.path.join(tmp, f"informe_{t['id']}.pdf"), 'rb') as f:
                pdf = f.read()
            assert pdf.startswith(b'%PDF-1.4') and pdf.rstrip().endswith(b'%%EOF'), t['tipo']
            # Las imágenes del informe están embebidas (DCTDecode = JPEG).
            assert b'DCTDecode' in pdf, f"{t['prueba']}: el PDF no trae imágenes"
            for frase in ESPERADO[t['prueba']][1]:
                assert frase.encode('latin-1') in pdf, (t['prueba'], frase)
            assert f"Hallazgos".encode() in pdf, t['prueba']
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    for prueba in pruebas:
        prueba()
        print(f"  ok  {prueba.__name__}")
    print("TODOS LOS TESTS PASARON")
