"""
Test de regresión: segfault al ingresar (login async).

Bug original (core dumps del 2026-09-07, SIGSEGV/SIGBUS en el thread
"QThread"): MainLogin conectaba `worker.finished -> worker.deleteLater`.
Ese DeferredDelete se despacha DENTRO del thread del worker, así que
Shiboken destruía ahí el wrapper Python del LoginWorker mientras el thread
de la GUI corría el post-login (load_sub_windows) y soltaba su referencia
al worker. Dos dueños liberando el mismo objeto en paralelo ->
"QObject: shared QObject was deleted directly" y crash intermitente.

El test corre el flujo real de MainLogin (QThread + LoginWorker) N veces
con LoginConnect stubeado, haciendo trabajo pesado de widgets dentro del
slot de resultado para forzar la carrera. Va en un SUBPROCESO a propósito:
la regresión no es una excepción, es un segfault, y mataría al runner.

Con el código con bug este test volvía 139 (SIGSEGV) de forma consistente.
"""

import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGINS = 25
TIMEOUT_S = 180


def _child() -> int:
    """Cuerpo real del test, corriendo en el subproceso."""
    sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

    # core.base (importado por auth.func_login) es quien crea la QApplication.
    import auth.func_login as func_login
    app = QApplication.instance()

    class FakeLoginConnect:
        """Login que tarda un poco y siempre devuelve una sesión válida."""

        def login(self, name, passw):
            import time
            time.sleep(0.15)
            return {"user": name or "alumno", "name": "Test", "permission": 777}

    func_login.LoginConnect = FakeLoginConnect
    import auth.login_worker as login_worker
    login_worker.LoginConnect = FakeLoginConnect

    from auth.login import MainLogin

    win = MainLogin()
    win.show()

    state = {"hechos": 0, "junk": []}

    def trabajo_pesado(_data):
        """Simula MainWindow.load_sub_windows: muchos widgets dentro del slot."""
        for _ in range(30):
            cont = QWidget()
            lay = QVBoxLayout(cont)
            for k in range(10):
                lay.addWidget(QLabel(f"x{k}", cont))
            state["junk"].append(cont)
        state["junk"] = state["junk"][-5:]
        app.processEvents()
        state["hechos"] += 1
        if state["hechos"] >= LOGINS:
            QTimer.singleShot(200, app.quit)
        else:
            QTimer.singleShot(10, siguiente_login)

    win.data_login_signal.connect(trabajo_pesado)

    def siguiente_login():
        win._enable_widgets()
        win.Le_name.setText("admin")
        win.Le_passw.setText("1234")
        win.get()

    QTimer.singleShot(50, siguiente_login)
    QTimer.singleShot(TIMEOUT_S * 1000, app.quit)
    app.exec()
    return 0 if state["hechos"] >= LOGINS else 1


def test_login_repetido_no_crashea():
    """N logins seguidos no deben segfaultear ni dejar el worker colgado."""
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    proc = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "--child"],
        cwd=REPO_ROOT,  # resources/ se resuelve relativo al cwd
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_S + 30,
    )
    assert proc.returncode == 0, (
        f"login repetido falló (returncode={proc.returncode}; "
        f"-11 = SIGSEGV, la regresión original)\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    assert "shared QObject was deleted directly" not in proc.stderr, (
        "Qt avisó de un QObject compartido destruido directamente:\n" + proc.stderr
    )


if __name__ == '__main__':
    if "--child" in sys.argv:
        sys.exit(_child())
    test_login_repetido_no_crashea()
    print('  test_login_repetido_no_crashea OK')
    print('TODOS LOS TESTS PASARON')
