"""Sesión vencida o cuenta bloqueada, venga de la llamada que venga
(backend/client.py: _revisar_sesion), y el motivo real al no poder entrar
(auth/func_login.py: LoginFallido)."""

import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import requests  # noqa: E402

from backend import client as cliente  # noqa: E402


def _respuesta(status, cuerpo=None, con_token=True):
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(cuerpo or {}).encode()
    pedido = requests.Request("GET", "http://x/api/sync.php",
                              headers={"Authorization": "Bearer abc"} if con_token else {})
    r.request = pedido.prepare()
    return r


def _avisos(respuesta):
    vistos = []
    cliente.al_perder_sesion = vistos.append
    try:
        cliente._revisar_sesion(respuesta)
    finally:
        cliente.al_perder_sesion = None
    return vistos


def test_un_401_con_token_es_sesion_vencida():
    assert _avisos(_respuesta(401, {"codigo": "sesion_vencida"})) == ["vencida"]


def test_un_403_de_cuenta_bloqueada_avisa_bloqueada():
    assert _avisos(_respuesta(403, {"codigo": "cuenta_bloqueada"})) == ["bloqueada"]


def test_otro_403_no_es_perder_la_sesion():
    assert _avisos(_respuesta(403, {"error": "Requiere permisos de administrador"})) == []


def test_sin_token_no_avisa():
    # El login con contraseña mala da 401 sin token: eso lo muestra el login.
    assert _avisos(_respuesta(401, con_token=False)) == []


def test_lo_que_sale_bien_no_avisa():
    assert _avisos(_respuesta(200, {"items": []})) == []


def test_el_cliente_trae_el_hook_puesto():
    c = cliente.BackendClient("http://127.0.0.1:9", "/tmp/no-existe-session.json")
    assert cliente._revisar_sesion in c._http.hooks["response"]


def test_login_fallido_es_falso_y_trae_el_motivo():
    from auth.func_login import LoginFallido
    f = LoginFallido("Tu cuenta está bloqueada. Habla con tu docente.")
    assert not f and f.mensaje.startswith("Tu cuenta está bloqueada")


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
    sys.exit(1 if fallas else 0)
