<?php
/**
 * LabSim - Seed: Paciente de ejemplo
 *
 * Inserta un caso clínico de demostración bloqueado (no editable, no eliminable).
 * Seguro de ejecutar múltiples veces (idempotente por ID fijo).
 *
 * Uso:  php seed-example-patient.php
 *   O:  https://tmeduca.org/labsim/backend/seed-example-patient.php
 */

$isCli = php_sapi_name() === 'cli';

function out($msg, $isCli) {
    echo $isCli ? "$msg\n" : "<p>$msg</p>";
}

if (!$isCli) {
    echo '<!DOCTYPE html><html><head><title>LabSim Seed</title>
    <style>body{font-family:monospace;max-width:700px;margin:40px auto;padding:20px;background:#1a1a2e;color:#e0e0e0}
    p{margin:4px 0}.ok{color:#4ade80}.err{color:#f87171}.warn{color:#fbbf24}h1{color:#818cf8}</style></head><body>';
    echo '<h1>LabSim - Paciente de ejemplo</h1>';
}

require_once __DIR__ . '/core/config.php';
require_once __DIR__ . '/core/db.php';

$db = Database::get();

// ─── ID fijo para idempotencia ──────────────────────
$CASE_ID = 'example-carmen-reyes-presbiacusia';

// Verificar si ya existe
$existing = $db->prepare('SELECT id FROM cases WHERE id = :id');
$existing->execute([':id' => $CASE_ID]);
if ($existing->fetch()) {
    out($isCli ? "· Paciente de ejemplo ya existe (ID: $CASE_ID). Nada que hacer." : "<span class='warn'>· Paciente de ejemplo ya existe. Nada que hacer.</span>", $isCli);
    exit(0);
}

// Buscar un usuario admin como autor (fallback: primer usuario)
$admin = $db->query("SELECT id FROM users WHERE role = 'admin' LIMIT 1")->fetch(PDO::FETCH_ASSOC);
if (!$admin) {
    $admin = $db->query("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")->fetch(PDO::FETCH_ASSOC);
}
if (!$admin) {
    out($isCli ? "✗ No hay usuarios en la BD. Ejecuta install.php primero." : "<span class='err'>✗ No hay usuarios</span>", $isCli);
    exit(1);
}

$authorId = $admin['id'];

// ─── Perfil del paciente ────────────────────────────
$profile = [
    'core' => [
        'identity' => [
            'firstName'       => 'Carmen',
            'lastName'        => 'Reyes Fuentes',
            'displayName'     => 'Sra. Carmen Reyes',
            'documentId'      => '8.245.631-2',
            'birthDate'       => '1957-08-14',
            'age'             => 68,
            'gender'          => 'femenino',
            'phone'           => '+56 9 7612 3344',
            'email'           => 'carmen.reyes@correo.cl',
            'address'         => 'Av. Los Leones 1420, depto. 304',
            'city'            => 'Providencia',
            'occupation'      => 'Profesora jubilada (Lenguaje y Comunicación)',
            'referredBy'      => 'Médico general — Dr. Patricio Soto',
            'healthInsurance' => 'FONASA tramo C',
            'notes'           => 'Vive sola. Hija la acompaña a consultas. Usa lentes de lectura.',
        ],
        'personality' => [
            'personalityType'    => 'colaborador',
            'communicationStyle' => 'detallista',
            'toneOfVoice'        => 'formal',
            'cooperationLevel'   => 'total',
        ],
        'clinicalHistory' => [
            'mainComplaint'        => 'Dificultad para entender conversaciones',
            'complaintDescription' => 'Desde hace unos dos años me cuesta entender lo que me dicen, sobre todo cuando hay varias personas hablando o cuando estoy en lugares con mucho ruido, como el supermercado o reuniones familiares. Mi hija me dice que pongo la televisión muy fuerte. A veces pido que me repitan las cosas y me da vergüenza. En ambientes tranquilos escucho mejor, pero igual noto que ya no es como antes.',
            'evolutionTime'        => '2 años',
            'severity'             => 'moderado',
            'medicalHistory'       => ['hipertensión arterial', 'dislipidemia', 'artrosis cervical'],
            'surgicalHistory'      => 'Colecistectomía (2015)',
            'familyHistory'        => 'Madre usó audífonos desde los 70 años. Padre falleció de ACV.',
            'medications'          => 'Losartán 50 mg/día, Atorvastatina 20 mg/día',
            'allergies'            => 'Sin alergias conocidas',
            'noiseExposure'        => 'No significativa. 35 años como profesora de aula.',
            'noiseYears'           => 35,
            'hearingProtection'    => false,
            'tinnitus'             => true,
            'tinnitusDescription'  => 'Zumbido agudo bilateral, más notorio por las noches. No interfiere con el sueño pero sí lo percibe al estar en silencio. Presente hace aproximadamente un año.',
            'vertigo'              => false,
            'vertigoDescription'   => '',
        ],
    ],
    'modules' => [
        // ─── Audiometría ────────────────────────────────
        // Presbiacusia bilateral: caída en agudos, sensorioneural
        'audiometry' => [
            'umbralesAereos' => [
                'oidoDerecho' => [
                    '125'  => 15,
                    '250'  => 15,
                    '500'  => 20,
                    '750'  => 20,
                    '1000' => 25,
                    '1500' => 30,
                    '2000' => 35,
                    '3000' => 45,
                    '4000' => 55,
                    '6000' => 60,
                    '8000' => 65,
                ],
                'oidoIzquierdo' => [
                    '125'  => 20,
                    '250'  => 20,
                    '500'  => 25,
                    '750'  => 25,
                    '1000' => 30,
                    '1500' => 35,
                    '2000' => 40,
                    '3000' => 50,
                    '4000' => 60,
                    '6000' => 65,
                    '8000' => 70,
                ],
            ],
            'umbralesOseos' => [
                'oidoDerecho' => [
                    '250'  => 15,
                    '500'  => 20,
                    '1000' => 25,
                    '2000' => 35,
                    '3000' => 45,
                    '4000' => 55,
                ],
                'oidoIzquierdo' => [
                    '250'  => 20,
                    '500'  => 25,
                    '1000' => 30,
                    '2000' => 40,
                    '3000' => 50,
                    '4000' => 60,
                ],
            ],
            'ldl' => [
                'oidoDerecho' => [
                    '500'  => 95,
                    '1000' => 95,
                    '2000' => 90,
                    '4000' => 85,
                ],
                'oidoIzquierdo' => [
                    '500'  => 95,
                    '1000' => 95,
                    '2000' => 90,
                    '4000' => 85,
                ],
            ],
            'tipoPerdida' => [
                'oidoDerecho'   => 'sensorioneural-coclear',
                'oidoIzquierdo' => 'sensorioneural-coclear',
            ],
            'reclutamiento' => [
                'oidoDerecho'   => false,
                'oidoIzquierdo' => false,
            ],
            'deterioroTonal' => [
                'oidoDerecho'   => false,
                'oidoIzquierdo' => false,
            ],
            'patientConfig' => [
                'falsePositiveRate'  => 0.04,
                'falseNegativeRate'  => 0.03,
                'reactionTimeMs'     => 450,
                'fatigueFactor'      => 0.15,
                'seed'               => 1957,
            ],
            'observaciones' => 'Paciente colaboradora. Respuestas consistentes. Curva audiométrica compatible con presbiacusia bilateral simétrica con caída progresiva en frecuencias agudas.',
        ],
        // ─── Acumetría (diapasones) ─────────────────────
        // Consistente con HSN bilateral
        'tuningFork' => [
            'rinne' => [
                'oidoDerecho'   => 'positivo',
                'oidoIzquierdo' => 'positivo',
            ],
            'weber' => [
                'lateralizacion' => 'derecha',
            ],
            'schwabach' => [
                'oidoDerecho'   => 'acortado',
                'oidoIzquierdo' => 'acortado',
            ],
            'observaciones' => 'Rinne positivo bilateral (VA > VO) confirma componente sensorioneural. Weber lateraliza al oído con mejor umbral (derecho). Schwabach acortado bilateral.',
        ],
    ],
];

$profileJson = json_encode($profile, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);

// ─── Insertar caso ──────────────────────────────────
$stmt = $db->prepare(
    "INSERT INTO cases (id, title, description, author_id, profile_json, schema_version, tags, difficulty, is_published, is_locked)
     VALUES (:id, :title, :desc, :author, :profile, :schema, :tags, :diff, :pub, :locked)"
);

$stmt->execute([
    ':id'      => $CASE_ID,
    ':title'   => 'Carmen Reyes — Presbiacusia bilateral',
    ':desc'    => 'Mujer de 68 años, profesora jubilada. Hipoacusia sensorioneural bilateral progresiva de predominio en frecuencias agudas, compatible con presbiacusia. Caso clásico de dificultad comprensiva en ambientes ruidosos. Incluye audiometría tonal, acumetría y anamnesis completa. Dificultad: media.',
    ':author'  => $authorId,
    ':profile' => $profileJson,
    ':schema'  => 2,
    ':tags'    => 'presbiacusia,sensorioneural,bilateral,audiometría,acumetría,ejemplo',
    ':diff'    => 'medium',
    ':pub'     => 1,
    ':locked'  => 1,
]);

out($isCli
    ? "✓ Paciente de ejemplo insertado: Carmen Reyes — Presbiacusia bilateral (ID: $CASE_ID)"
    : "<span class='ok'>✓ Paciente de ejemplo insertado: <strong>Carmen Reyes — Presbiacusia bilateral</strong></span>",
    $isCli
);
out($isCli
    ? "  → Publicado, bloqueado (no editable, no eliminable)"
    : "<span class='ok'>  → Publicado, bloqueado (no editable, no eliminable)</span>",
    $isCli
);

if (!$isCli) echo '</body></html>';
