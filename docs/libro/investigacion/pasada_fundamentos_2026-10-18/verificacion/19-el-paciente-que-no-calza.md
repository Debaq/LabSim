# 19-el-paciente-que-no-calza
Cambios revisados: 12 · confirmados: 11 · revertidos: 0 · ajustados: 1
## Revertidos
- ninguno. Protocolo y clases sin nada sobre simulación/no orgánica; no hay Hood ni Weber en el capítulo.
## Ajustados
- Curva plana · "casi siempre de 40 a 60 dB" -> "en su mayoría de 40 a 60 dB": Holenweg y Kompis (2010) dicen "mostly in the range of 40-60 dB" (PubMed 20204391).
## Para el autor
- Atenuación interaural 40-60 -> 40-80 dB: coherente con H4 (tabla: supraaural 40-80, BSA 2018; el habla conserva 45 dB del protocolo/LabSim). LabSim usa la curva por frecuencia (35 a 50 dB en tonos, 0 en ósea; `response.py`/H4), no un rango, así que 40-60 no era valor de práctica; se deja 40-80. Efecto: en el caso de Felipe, 75-80 dB queda dentro de lo posible y el texto ya lo dice; con el modelo de LabSim (<=50 dB) el cruce ocurriría antes, lo que refuerza que "no calza".
- Chaiklin 1959 sacado de la lista del cap. 19; en H6 sigue como `verificar` (no se tocó).
- Stenger: el capítulo lo presenta como difícil de burlar; Martin y Shipp (1982) y Bell y cols. (2025) matizan eso (ya informado por el agente).
- Criterios "5 dB / 15 dB" de repetición: práctica, no tocados.
## Dudosos
- "Stenger a comienzos del siglo XX": fecha exacta sin fuente primaria (1900 vs 1907); texto prudente.
Verificado contra PubMed: Gelfand 1994 (60 dB HL, 70,9-85,7 %, 5-7 %), Kvaerner 1996 (34 pac., 25-30 dB), Brooks y Geoghegan 1992, Holenweg 2010.
