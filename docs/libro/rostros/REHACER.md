# Rostros con signos clínicos

El modelo económico (`gemini-3.1-flash-lite-image`) y el normal (`gemini-3.1-flash-image`) no dibujan signos clínicos sutiles. El 2026-10-17 se rehicieron con **`gemini-3-pro-image`** (Nano Banana Pro) y pedidos que ponen el signo como "KEY CLINICAL SIGN"; cada uno se revisó a mano:

| Clave | Signo | Resultado |
|---|---|---|
| cap17_rubeola_congenita | cataratas congénitas (pupilas blanquecinas) | se ve |
| cap36_alergica | ojeras alérgicas, pliegue nasal, punta roja | se ve |
| cap36_medicamentosa | narinas irritadas, labios secos, boca abierta | se ve |
| cap30_nino_otitis | respiradora bucal, ojeras | se ve |
| cap29_autoinmune | audífono retroauricular | se ve |
| cap29_aun_no | audífono retroauricular | se ve |
| cap35_valvula | nariz estrecha tras rinoplastia de reducción | sutil, aceptable |
| cap12_infarto_aica | parálisis facial de un lado | se ve (dos intentos) |
| cap12_glioma_tronco | esotropía | se ve (tres intentos; los dos primeros salieron con el ojo hacia afuera) |
| cap35_desviacion | nariz desviada por fractura | se ve, sutil (el primer intento salió con un marco antiguo) |
| cap36_mixta | nariz desviada | sutil |

Regla para lo que venga: rostros comunes con el modelo por defecto (Lite); si el caso necesita un signo visible, pedirlo explícito y generar con
`LIBRO_MODELO_IMAGEN=gemini-3-pro-image python3 docs/libro/herramientas/rostros.py <clave>`, y mirarlo de cerca (los lados y las direcciones se confunden: describir el lado "de la imagen").
Gemini sigue sin dibujar malformaciones (microtia del cap. 1 con gorro, Paget del cap. 4 apenas sugerido).
