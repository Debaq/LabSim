# Rostros que no muestran el signo pedido

El modelo de imágenes no dibujó el rasgo clínico que el caso necesita (revisado el 2026-10-17). La cara sirve igual para la ficha, pero no enseña el signo. Rehacer con un modelo mejor cuando se quiera:

    LIBRO_MODELO_IMAGEN=gemini-3.1-flash-image python3 docs/libro/herramientas/rostros.py <clave> [<clave> ...]

(Si tampoco alcanza, probar el modelo Pro de imagen; cuesta más.)

| Clave | Signo que falta | Hecho con |
|---|---|---|
| cap17_rubeola_congenita | cataratas congénitas (pupilas blanquecinas) | flash-lite |
| cap35_desviacion | dorso nasal desviado (fractura antigua) | flash-lite |
| cap36_mixta | dorso nasal desviado | flash-lite |
| cap35_valvula | narinas angostas tras rinoplastia de reducción | flash-lite |
| cap36_alergica | ojeras alérgicas, pliegue nasal transversal, punta de la nariz roja | flash-lite |
| cap36_medicamentosa | piel irritada alrededor de las narinas, labios secos, boca entreabierta | flash-lite |
| cap30_nino_otitis | boca entreabierta (respiradora bucal), ojeras | flash-lite |
| cap29_autoinmune | audífonos retroauriculares en ambos oídos | flash-lite |
| cap29_aun_no | audífonos retroauriculares en ambos oídos | flash-lite |
| cap12_glioma_tronco | ojo desviado hacia adentro (esotropía) | flash (no Lite) |
| cap12_infarto_aica | caída de la comisura bucal (paresia facial) | flash (no Lite) |

Ya se sabía (ESTADO.md, Rostros): Gemini no dibuja malformaciones; la microtia del cap. 1 va tapada con un gorro y el Paget del cap. 4 sale apenas sugerido.
