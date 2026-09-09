<?php

declare(strict_types=1);

/**
 * La revisión ficha por ficha que cierra un caso: qué pestañas tiene el
 * editor, y cuáles declaró revisadas el docente antes de guardar.
 *
 * Antes de esto la única ficha que pedía una confirmación explícita era el
 * VEMP ("Ya decidí qué pasa en el VEMP de este oído"), y era una casilla
 * escondida adentro de la propia pestaña: la única forma de saber si un
 * hallazgo normal era una decisión o una ficha que nadie abrió. El resto
 * del caso no tenía nada equivalente -- un caso generado al azar se
 * guardaba entero sin que nadie hubiera mirado una sola pestaña.
 *
 * La casilla del VEMP resolvía un caso particular de un problema general, y
 * mal: pedía la decisión en el mismo lugar donde ya estaba mirando el
 * docente, y solo cuando el editor la reclamaba. Acá la revisión es una
 * pasada única al final (la pestaña Resumen), con el estado de cada ficha a
 * la vista, y vale para las once.
 *
 * Lo que se guarda es qué se aceptó y quién lo aceptó, no un puntaje: el
 * docente es el experto y "esto está bien así" es una respuesta válida para
 * cualquier ficha, incluso para las que el editor marca en rojo.
 */
final class CaseReview
{
    /**
     * Las pestañas del editor, en orden de aparición.
     *
     * Es la fuente única: admin/case_create.php dibuja la barra de pestañas
     * desde acá y la ficha Resumen lista las revisables desde acá. Tenerlo
     * en dos lados dejaba listar en el Resumen una ficha que no existe (o
     * peor, olvidarse de listar una que sí).
     *
     * `revisable` en false son las dos que no son parte del caso: el
     * Armado rápido (herramienta, no dato) y el Resumen mismo.
     */
    public const TABS = [
        'armado' => ['grupo' => 'Empezar acá', 'label' => 'Armado rápido', 'revisable' => false],
        'paciente' => ['grupo' => 'Quién es', 'label' => 'Paciente'],
        'sala' => ['grupo' => 'Quién es', 'label' => 'Sala'],
        'perfil' => ['grupo' => 'El caso', 'label' => 'Perfil auditivo'],
        'audiometria' => ['grupo' => 'Exámenes', 'label' => 'Audiometría'],
        'otoscopia' => ['grupo' => 'Exámenes', 'label' => 'Otoscopia'],
        'timpanometria' => ['grupo' => 'Exámenes', 'label' => 'Timpanometría'],
        'abr' => ['grupo' => 'Exámenes', 'label' => 'ABR'],
        'eoas' => ['grupo' => 'Exámenes', 'label' => 'EOA'],
        'vemp' => ['grupo' => 'Exámenes', 'label' => 'VEMP'],
        'tinnitus' => ['grupo' => 'Exámenes', 'label' => 'Tinnitus'],
        'anamnesis' => ['grupo' => 'Entrevista', 'label' => 'Anamnesis'],
        'resumen' => ['grupo' => 'Cerrar', 'label' => 'Resumen', 'revisable' => false],
    ];

    /**
     * Solo las fichas que se revisan, con el número que llevan en la barra
     * ("4. Audiometría"). El número sale del orden, no está escrito al lado
     * de cada label: insertar una ficha en el medio renumeraba las nueve de
     * abajo a mano.
     *
     * @return array<string,string> tab => label numerado
     */
    public static function revisables(): array
    {
        $out = [];
        $n = 0;
        foreach (self::TABS as $tab => $meta) {
            if ($meta['revisable'] ?? true) {
                $out[$tab] = ++$n . '. ' . $meta['label'];
            }
        }
        return $out;
    }

    /** El label como se ve en la barra, numerado o no según la ficha. */
    public static function label(string $tab): string
    {
        return self::revisables()[$tab] ?? (self::TABS[$tab]['label'] ?? $tab);
    }

    /**
     * La revisión que viaja en el POST -> el shape que se guarda en
     * cases.data['Revision'].
     *
     * `at`/`by` son del guardado que trae la tilde puesta, no de un momento
     * anterior: no hay forma de saber cuándo se tildó realmente la casilla
     * (el formulario no vuelve al servidor hasta que se guarda), y una
     * fecha inventada en un registro de quién revisó qué es peor que no
     * tenerla.
     *
     * @param array $v  El $_POST crudo.
     * @param array $me El admin de la sesión.
     */
    public static function fromPost(array $v, array $me): array
    {
        $tabs = [];
        foreach (array_keys(self::revisables()) as $tab) {
            // Una casilla destildada no viaja en el POST: la ausencia ES el
            // "no revisada", no un dato que falta.
            $tabs[$tab] = !empty($v['revisado'][$tab]);
        }
        return [
            'tabs' => $tabs,
            'at' => gmdate('c'),
            'by' => (string) ($me['username'] ?? $me['id'] ?? ''),
        ];
    }

    /**
     * ¿Esta ficha quedó revisada en un caso ya guardado?
     *
     * Un caso guardado antes de que existiera la revisión no trae nada, y
     * ninguna ficha cuenta como revisada -- se revisa la primera vez que se
     * abre en el editor. La excepción es el VEMP: la casilla vieja
     * ("decidido", por oído) decía exactamente esto de esa ficha, así que
     * un caso que la traía tildada en los dos oídos ya está revisado ahí y
     * no se le vuelve a pedir.
     */
    public static function revisada(array $data, string $tab): bool
    {
        $tabs = is_array($data['Revision']['tabs'] ?? null) ? $data['Revision']['tabs'] : [];
        if (!empty($tabs[$tab])) {
            return true;
        }
        if ($tab === 'vemp') {
            $vemp = is_array($data['VEMP'] ?? null) ? $data['VEMP'] : [];
            return !empty($vemp['OD']['decidido']) && !empty($vemp['OI']['decidido']);
        }
        return false;
    }

    /**
     * Las fichas que todavía nadie declaró revisadas.
     *
     * @return array<string,string> tab => label numerado
     */
    public static function sinRevisar(array $data): array
    {
        $out = [];
        foreach (self::revisables() as $tab => $label) {
            if (!self::revisada($data, $tab)) {
                $out[$tab] = $label;
            }
        }
        return $out;
    }

    /**
     * Lo guardado -> el shape del formulario ($v['revisado']['vemp'] = '1'),
     * para que al reeditar un caso las tildes aparezcan puestas.
     */
    public static function toForm(array $data): array
    {
        $out = [];
        foreach (array_keys(self::revisables()) as $tab) {
            if (self::revisada($data, $tab)) {
                $out[$tab] = '1';
            }
        }
        return $out;
    }
}
