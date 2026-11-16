"""Los ronquidos del paciente del laboratorio de sueño, recortados de grabaciones CC0 de Freesound.

Por cada grabación baja la vista previa (mp3), busca las inspiraciones roncadas (tramos con energía
muy por encima del fondo, de 0,4 a 3 s), se queda con las más limpias, las recorta con entrada y salida
suaves, iguala el volumen y deja:

    resources/audio/psg/<sexo>/<id de Freesound>_<n>.wav   (mono, 22,05 kHz)
    resources/audio/psg/FUENTES.md                          (de dónde sale cada una)

LabSim (nasal/pieza_vista.py) elige una grabación por paciente (la misma para el mismo caso, según su
sexo) y toca sus ronquidos, uno por inspiración, mientras ronca.

Son grabaciones reales, no sintéticas: el ronquido sintético sonaba "como un motor, muy metálico"
(él, 2026-11-16). Todas CC0 (licencia verificada en la página de cada una al bajarlas).

    python3 scripts/psg_pieza/ronquidos.py
"""
import pathlib
import subprocess
import urllib.request
import wave

import numpy as np

RAIZ = pathlib.Path(__file__).resolve().parents[2]
SALIDA = RAIZ / 'resources' / 'audio' / 'psg'
CACHE = pathlib.Path.home() / '.cache' / 'labsim' / 'ronquidos'
SR = 22050
POR_GRABACION = 5
# sexo -> [(id, autor, título, vista previa)]
FUENTES = {
    'hombre': [
        (180148, 'justinstroud', 'snoring.wav', 'https://cdn.freesound.org/previews/180/180148_3351291-hq.mp3'),
        (432997, 'mattyharm', 'Male Snore 1.wav', 'https://cdn.freesound.org/previews/432/432997_897016-hq.mp3'),
        (432994, 'mattyharm', 'Male Snore 4.wav', 'https://cdn.freesound.org/previews/432/432994_897016-hq.mp3'),
        (389683, 'Shamewap', 'Man Snoring.wav', 'https://cdn.freesound.org/previews/389/389683_6861640-hq.mp3'),
    ],
    'mujer': [
        (595470, 'SavReese', '13-Woman snoring (voice)-210819_2208.wav',
         'https://cdn.freesound.org/previews/595/595470_12672587-hq.mp3'),
        (539215, 'Legnalegna55', 'Snoring Sound effect.mp3',
         'https://cdn.freesound.org/previews/539/539215_10485775-hq.mp3'),
    ],
}


def bajar(sid, url):
    CACHE.mkdir(parents=True, exist_ok=True)
    mp3 = CACHE / f'{sid}.mp3'
    if not mp3.exists():
        pedido = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        mp3.write_bytes(urllib.request.urlopen(pedido, timeout=120).read())
    crudo = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp3), '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                           capture_output=True, check=True).stdout
    return np.frombuffer(crudo, '<i2').astype(np.float64) / 32768


def tramos(x):
    """Inspiraciones roncadas: (inicio, fin, limpieza) en muestras."""
    paso = int(0.02 * SR)
    rms = np.sqrt(np.convolve(x ** 2, np.ones(paso) / paso, 'same')[::paso])
    rms = np.convolve(rms, np.ones(5) / 5, 'same')
    fondo = np.percentile(rms, 20) + 1e-6
    alto = np.percentile(rms, 98)
    umbral = max(fondo * 4, alto * 0.18)
    arriba = rms > umbral
    out, i, n = [], 0, len(rms)
    while i < n:
        if not arriba[i]:
            i += 1
            continue
        j = i
        while j < n and (arriba[j] or (j + 8 < n and arriba[j:j + 8].any())):   # junta pausas < 160 ms
            j += 1
        dur = (j - i) * paso / SR
        if 0.4 <= dur <= 3.0:
            out.append((i * paso, j * paso, float(rms[i:j].max() / fondo)))
        i = j
    return out


def recortar(x, a, b):
    a, b = max(0, a - int(0.08 * SR)), min(len(x), b + int(0.12 * SR))
    y = x[a:b].copy()
    f = int(0.04 * SR)
    y[:f] *= np.linspace(0, 1, f)
    y[-f:] *= np.linspace(1, 0, f)
    y -= y.mean()
    rms = np.sqrt((y ** 2).mean())
    y *= 10 ** (-18 / 20) / max(rms, 1e-6)          # todos al mismo nivel (-18 dBFS RMS)
    pico = np.abs(y).max()
    if pico > 0.95:
        y *= 0.95 / pico
    return y


def main():
    lineas = ['# Ronquidos del laboratorio de sueño', '',
              'Recortados por `scripts/psg_pieza/ronquidos.py` de grabaciones de Freesound con licencia CC0',
              '(dominio público: sin obligación de crédito; se deja igual de dónde salen).', '']
    for sexo, fuentes in FUENTES.items():
        carpeta = SALIDA / sexo
        carpeta.mkdir(parents=True, exist_ok=True)
        for viejo in carpeta.glob('*.wav'):
            viejo.unlink()
        lineas.append(f'## {sexo.capitalize()}')
        lineas.append('')
        for sid, autor, titulo, url in fuentes:
            x = bajar(sid, url)
            elegidos = sorted(tramos(x), key=lambda t: -t[2])[:POR_GRABACION]
            for k, (a, b, _) in enumerate(sorted(elegidos), 1):
                y = recortar(x, a, b)
                with wave.open(str(carpeta / f'{sid}_{k}.wav'), 'wb') as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(SR)
                    w.writeframes((y * 32767).astype('<i2').tobytes())
            print(f'{sexo} {sid}: {len(elegidos)} ronquidos')
            lineas.append(f'- `{sid}_*.wav`: "{titulo}" de {autor}, CC0, '
                          f'https://freesound.org/people/{autor}/sounds/{sid}/')
        lineas.append('')
    (SALIDA / 'FUENTES.md').write_text('\n'.join(lineas), encoding='utf-8')


if __name__ == '__main__':
    main()
