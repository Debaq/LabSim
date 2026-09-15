<?php

declare(strict_types=1);

require_once __DIR__ . '/CaseBuilder.php';
require_once __DIR__ . '/CaseSheetPdf.php';
require_once __DIR__ . '/Sala.php';
require_once __DIR__ . '/LlmChat.php';
require_once __DIR__ . '/AnamnesisDraft.php';
require_once __DIR__ . '/Cases.php';

/**
 * Redacta como ficha clínica real la sección de anamnesis de la FICHA DE
 * ESTUDIO (ver CaseSheetPdf, `$estudio = true`).
 *
 * No es AnamnesisDraft: ese INVENTA antecedentes plausibles para que el
 * docente arme el caso. Esto no inventa nada -- toma los hechos que el
 * docente YA decidió (antecedentes marcados, quiénes acompañan, qué
 * cuenta cada uno, el acúfeno) y los redacta como prosa clínica corrida,
 * en vez de la lista de campos etiquetados que lee el docente. Por
 * construcción nunca ve un dato interno del generador (fuente() arma el
 * mismo recorte "seguro para el alumno" que ya usa CaseSheetPdf::clinica()
 * para la ficha de estudio) -- no hay que pedírselo al modelo por prompt,
 * es que ese dato nunca llega al mensaje.
 *
 * Se genera UNA VEZ por caso y se guarda en cases.data
 * (`EstudioRedaccion.<sección>.texto`); las fichas siguientes reusan el
 * texto guardado. `hash()` detecta cuándo los hechos de origen cambiaron
 * (el docente editó el caso) para regenerar sola, sin que nadie tenga que
 * acordarse de apretar un botón. Ver ensureFresh(), que es lo único que
 * necesita llamar el endpoint.
 *
 * Estructurado por SECCIONES (hoy solo 'clinica') para poder sumar más
 * partes de la ficha de estudio a este mismo tratamiento más adelante sin
 * rehacer el mecanismo de cacheo.
 */
final class EstudioRedactor
{
    public const SECCION_CLINICA = 'clinica';

    /** Tope de caracteres del texto redactado. Varios acompañantes con su versión completa ocupan bastante. */
    public const MAX_TEXTO = 3500;

    public const SYSTEM_PROMPT = <<<'TXT'
Redactás la sección de anamnesis de una ficha clínica de un paciente, para
que un alumno de audiología la lea antes de atenderlo -- como si fuera la
ficha real de un box de atención, no un formulario.

Te paso los hechos ya decididos, en bruto. Tu trabajo es SOLO redactarlos
como un relato clínico corrido, con buena prosa médica. No agregues ni un
solo hecho clínico que no esté en lo que te paso (ni antecedentes, ni
síntomas, ni fármacos, ni una palabra de lo que dice cada acompañante):
todo lo que escribas tiene que poder rastrearse a algo que te dieron.

- Español de Chile, tercera persona, registro clínico (el de una ficha de
  verdad, no una redacción escolar).
- NO menciones umbrales, dB, resultados de exámenes ni un diagnóstico: eso
  es lo que el alumno tiene que examinar y no está en lo que te paso --
  fijate que ni te lo dieron.
- Incluí TODOS los hechos que te paso, ninguno de más. Si te dan tres
  antecedentes, van los tres. Si acompañan dos personas, las dos entran
  con su versión. Si no marcaron ningún antecedente, no inventes uno para
  rellenar -- decí que no refiere antecedentes de relevancia y seguí.
- Cuando alguien acompaña al paciente, decí quién es (según la etiqueta
  que te dan) y SOLO su versión de la historia del paciente, integrada
  como relato indirecto ("La madre refiere que...", "Según cuenta la
  pareja..."), fiel a lo que dice esa persona sobre el paciente -- no la
  resumas tanto que pierda el detalle concreto, y no le cambies el
  sentido.
- De un acompañante NUNCA comentes su propio comportamiento, actitud o
  personalidad en la consulta (que se dispersa, que es conversador, que
  hay que reencauzarlo, etc.): eso es un juicio de valor sobre un
  tercero que no es el paciente, y no pertenece acá aunque te pase ese
  dato -- de un acompañante entra solo lo que dice del paciente, nada
  más. El comportamiento en consulta que SÍ podés describir, breve y
  clínico, es el del PACIENTE (si te lo dan) -- es el sujeto de la
  ficha.
- Si el paciente puede contar la historia por sí mismo, escribilo desde su
  propio relato en vez de por acompañante.
- Organizalo en 2 a 4 párrafos: antecedentes e historia primero: motivo de
  consulta y quién acompaña después.
- No repitas la misma información en dos párrafos distintos.

Respondé SOLO este JSON, sin ```:
{"texto": "primer párrafo\n\nsegundo párrafo"}
TXT;

    /**
     * Los hechos que puede usar el redactor -- el mismo recorte que ya
     * usa CaseSheetPdf::clinica()/sala() en la ficha de estudio (antecedentes
     * marcados, no mandos del generador). Es lo que se hashea (ver hash())
     * y lo que se convierte en el mensaje del LLM (ver mensaje()): las dos
     * cosas leen de acá para no desalinearse.
     *
     * @param array<string,mixed> $data cases.data
     * @return array<string,mixed>
     */
    public static function fuente(array $data): array
    {
        $anamnesis = (array) ($data['Anamnesis'] ?? []);
        $antecedentesRaw = (array) ($anamnesis['antecedentes'] ?? []);
        $marcados = [];
        foreach (CaseBuilder::HIST_CHECKBOXES as $clave) {
            if (!empty($antecedentesRaw[$clave])) {
                $marcados[] = CaseBuilder::HIST_LABELS[$clave] ?? $clave;
            }
        }

        $personas = [];
        $sala = Sala::desde($data);
        if (Sala::tieneAcompanantes($sala)) {
            foreach ($sala['personas'] as $persona) {
                $entry = [
                    'quien' => Sala::etiqueta($persona),
                    'es_paciente' => (bool) $persona['es_paciente'],
                    'edad' => (int) $persona['edad'],
                    'informante_principal' => (bool) $persona['informante'],
                    'version' => trim((string) $persona['version']),
                ];
                // El comportamiento en consulta de un ACOMPAÑANTE es dato
                // para el LLM de la sala (cómo actuar el personaje), no
                // algo que le sirva al redactor: comentarlo en la ficha
                // sería un juicio de valor sobre un tercero que no es el
                // paciente. Directamente no se le manda -- ver docblock.
                if ($entry['es_paciente']) {
                    $entry['comportamiento_en_consulta'] = trim((string) $persona['comportamiento']);
                }
                $personas[] = $entry;
            }
        }

        return [
            'edad_paciente' => (int) ($data['edad'] ?? 0),
            'sexo_paciente' => ((int) ($data['gender'] ?? 0)) === 1 ? 'femenino' : 'masculino',
            'antecedentes_marcados' => $marcados,
            'medicamentos' => trim((string) ($anamnesis['medicamentos'] ?? '')),
            'cirugias' => trim((string) ($anamnesis['cirugias'] ?? '')),
            'otros' => trim((string) ($anamnesis['otros'] ?? '')),
            'acufeno' => trim(CaseSheetPdf::acufeno((array) ($data['Tinnitus'] ?? []))),
            'comportamiento_general' => trim((string) ($data['PatientBehavior'] ?? '')),
            'quienes_acompanan' => $personas,
        ];
    }

    /**
     * Hash de los hechos de origen: si cambia, la redacción guardada quedó
     * vieja y hay que pedir una nueva. No se compara la redacción vieja
     * con la nueva, se compara el HASH de los hechos -- así no hace falta
     * guardar los hechos duplicados en cases.data, alcanza este resumen.
     */
    public static function hash(array $fuente): string
    {
        return hash('sha256', json_encode($fuente, JSON_UNESCAPED_UNICODE));
    }

    /** El mensaje de usuario: los hechos de fuente(), en JSON, sin instrucciones (esas van en SYSTEM_PROMPT). */
    public static function mensaje(array $fuente): string
    {
        return (string) json_encode($fuente, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }

    /**
     * Pide la redacción al LLM. Mismo modelo/presupuesto/reintento que
     * AnamnesisDraft (es la misma categoría de tarea -- una redacción de
     * varios párrafos, a veces con un modelo de razonamiento de por
     * medio -- así que no hace falta un campo de configuración aparte
     * todavía; si hace falta ajustarlo distinto más adelante, se separa).
     *
     * @throws Throwable si el LLM falla -- quien llama (ensureFresh) decide
     *         qué hacer, acá no se atrapa nada para no esconder el motivo.
     */
    public static function generate(array $data, int $usuarioId = 0): string
    {
        $fuente = self::fuente($data);
        $mensaje = self::mensaje($fuente);
        $presupuesto = AnamnesisDraft::maxTokens();
        $modelo = AnamnesisDraft::model();
        $opciones = [
            'model' => $modelo,
            'max_tokens' => $presupuesto,
            'timeout' => AnamnesisDraft::TIMEOUT_S,
            'campo_tokens' => 'Máximo de tokens del borrador de anamnesis',
            'tarea' => 'ficha_estudio',
            'user_id' => $usuarioId,
        ];
        try {
            $raw = LlmChat::reply(self::SYSTEM_PROMPT, [], $mensaje, $opciones);
        } catch (LlmBudgetException $e) {
            $reintento = AnamnesisDraft::retryBudget($presupuesto);
            if ($reintento <= $presupuesto) {
                throw $e;
            }
            $opciones['max_tokens'] = $reintento;
            $raw = LlmChat::reply(self::SYSTEM_PROMPT, [], $mensaje, $opciones);
        }
        $texto = self::parse($raw);
        if ($texto === null || $texto === '') {
            throw new RuntimeException('El modelo no devolvió un JSON usable para la redacción de la ficha de estudio.');
        }
        return $texto;
    }

    /** Mismo pelado de ``` que AnamnesisDraft::parse(). */
    public static function parse(string $raw): ?string
    {
        $limpio = trim($raw);
        if (substr($limpio, 0, 3) === '```') {
            $limpio = trim((string) preg_replace('/^```[a-zA-Z]*\n?|```$/', '', $limpio));
        }
        $json = json_decode($limpio, true);
        if (!is_array($json)) {
            return null;
        }
        $texto = trim((string) ($json['texto'] ?? ''));
        return $texto === '' ? null : mb_substr($texto, 0, self::MAX_TEXTO);
    }

    /**
     * Punto de entrada único para el endpoint: si la redacción guardada no
     * existe o quedó vieja (hash distinto), pide una nueva y la persiste;
     * si el LLM falla por lo que sea (sin api_key, sin red, error del
     * proveedor), NO rompe la ficha -- se queda con lo que había (o sin
     * nada, y CaseSheetPdf cae al detalle mecánico de siempre). Devuelve
     * `$data` actualizado, listo para pasarle a CaseSheetPdf::build().
     *
     * @param array<string,mixed> $data cases.data, ya decodificado
     * @return array<string,mixed> el mismo array, con EstudioRedaccion al día si se pudo
     */
    public static function ensureFresh(string $caseId, array $data, int $usuarioId = 0): array
    {
        $fuente = self::fuente($data);
        $hashActual = self::hash($fuente);
        $guardado = (array) ($data['EstudioRedaccion'][self::SECCION_CLINICA] ?? []);
        if (($guardado['hash'] ?? null) === $hashActual && trim((string) ($guardado['texto'] ?? '')) !== '') {
            return $data;
        }

        try {
            $texto = self::generate($data, $usuarioId);
        } catch (Throwable $e) {
            // Sin red, sin api_key, o el proveedor caído: la ficha de
            // estudio no se puede romper por esto. CaseSheetPdf::clinica()
            // cae al detalle mecánico si no encuentra texto guardado.
            return $data;
        }

        $data['EstudioRedaccion'][self::SECCION_CLINICA] = [
            'texto' => $texto,
            'hash' => $hashActual,
            'generado_en' => date('Y-m-d H:i:s'),
        ];
        Cases::actualizarDatos($caseId, $data);
        return $data;
    }

    /**
     * Fuerza una redacción nueva IGNORANDO el caché -- para el botón manual
     * "Regenerar" (patients.php). ensureFresh() solo regenera si los HECHOS
     * de origen cambiaron; el hash no se entera si lo que cambió fue el
     * PROMPT (una regla de redacción nueva, como la de no opinar sobre el
     * comportamiento de un acompañante) o si la primera redacción salió
     * mediocre y el docente quiere probar de nuevo con los mismos hechos.
     *
     * A diferencia de ensureFresh(), acá NO se atrapa el error del LLM:
     * quien aprieta el botón está esperando el resultado y necesita saber
     * si falló, no quedarse con la redacción vieja en silencio.
     *
     * @param array<string,mixed> $data cases.data, ya decodificado
     * @return array<string,mixed> el mismo array, con la redacción nueva
     * @throws Throwable si el LLM falla
     */
    public static function regenerate(string $caseId, array $data, int $usuarioId = 0): array
    {
        $texto = self::generate($data, $usuarioId);
        $data['EstudioRedaccion'][self::SECCION_CLINICA] = [
            'texto' => $texto,
            'hash' => self::hash(self::fuente($data)),
            'generado_en' => date('Y-m-d H:i:s'),
        ];
        Cases::actualizarDatos($caseId, $data);
        return $data;
    }
}
