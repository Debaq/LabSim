<?php
/**
 * LabSim 3.0 - API de Pacientes
 * Backend para gestión de perfiles de pacientes
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Manejar preflight OPTIONS
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Configuración
define('PATIENTS_DIR', __DIR__ . '/patients/');
define('API_PASSWORD', 'labsim2024');
define('MAX_FILE_SIZE', 5 * 1024 * 1024); // 5MB

// Crear directorio si no existe
if (!file_exists(PATIENTS_DIR)) {
    mkdir(PATIENTS_DIR, 0755, true);
}

/**
 * Procesar solicitud
 */
try {
    $action = $_GET['action'] ?? $_POST['action'] ?? '';
    
    switch ($action) {
        case 'list':
            handleListPatients();
            break;
            
        case 'get':
            handleGetPatient();
            break;
            
        case 'upload':
            handleUploadPatient();
            break;
            
        case 'delete':
            handleDeletePatient();
            break;
            
        default:
            sendError('Acción no válida', 400);
    }
    
} catch (Exception $e) {
    sendError('Error interno del servidor: ' . $e->getMessage(), 500);
}

/**
 * Listar pacientes
 */
function handleListPatients() {
    $patients = [];
    $files = glob(PATIENTS_DIR . '*.json');
    
    foreach ($files as $file) {
        try {
            $data = json_decode(file_get_contents($file), true);
            if ($data && isset($data['patient_info'])) {
                $patients[] = [
                    'id' => basename($file, '.json'),
                    'name' => extractPatientName($data),
                    'age' => extractPatientAge($data),
                    'gender' => extractPatientGender($data),
                    'diagnosis' => extractPatientDiagnosis($data),
                    'created' => extractCreatedDate($data),
                    'file_size' => filesize($file),
                    'last_modified' => date('Y-m-d H:i:s', filemtime($file))
                ];
            }
        } catch (Exception $e) {
            // Ignorar archivos corruptos
            continue;
        }
    }
    
    // Ordenar por fecha de modificación (más recientes primero)
    usort($patients, function($a, $b) {
        return strtotime($b['last_modified']) - strtotime($a['last_modified']);
    });
    
    sendSuccess($patients);
}

/**
 * Obtener paciente específico
 */
function handleGetPatient() {
    $id = $_GET['id'] ?? '';
    
    if (empty($id)) {
        sendError('ID de paciente requerido', 400);
    }
    
    $filename = sanitizeFilename($id) . '.json';
    $filepath = PATIENTS_DIR . $filename;
    
    if (!file_exists($filepath)) {
        sendError('Paciente no encontrado', 404);
    }
    
    try {
        $data = json_decode(file_get_contents($filepath), true);
        if (!$data) {
            sendError('Error leyendo datos del paciente', 500);
        }
        
        sendSuccess($data);
        
    } catch (Exception $e) {
        sendError('Error cargando paciente: ' . $e->getMessage(), 500);
    }
}

/**
 * Subir/actualizar paciente
 */
function handleUploadPatient() {
    // Verificar método POST
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        sendError('Método no permitido', 405);
    }
    
    // Verificar contraseña
    $password = $_POST['password'] ?? '';
    if ($password !== API_PASSWORD) {
        sendError('Contraseña incorrecta', 401);
    }
    
    // Obtener datos
    $jsonData = $_POST['data'] ?? '';
    if (empty($jsonData)) {
        sendError('Datos de paciente requeridos', 400);
    }
    
    // Verificar tamaño
    if (strlen($jsonData) > MAX_FILE_SIZE) {
        sendError('Archivo demasiado grande', 413);
    }
    
    try {
        // Validar JSON
        $data = json_decode($jsonData, true);
        if (!$data) {
            sendError('JSON inválido', 400);
        }
        
        // Validar estructura básica
        if (!isset($data['patient_info'])) {
            sendError('Datos de paciente incompletos (falta patient_info)', 400);
        }
        
        // Generar ID único
        $patientId = generatePatientId($data);
        $filename = $patientId . '.json';
        $filepath = PATIENTS_DIR . $filename;
        
        // Agregar metadatos
        if (!isset($data['metadata'])) {
            $data['metadata'] = [];
        }
        $data['metadata']['patient_id'] = $patientId;
        $data['metadata']['uploaded_date'] = date('c');
        $data['metadata']['server_version'] = '1.0';
        
        // Guardar archivo
        if (file_put_contents($filepath, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE))) {
            sendSuccess([
                'message' => 'Paciente guardado correctamente',
                'patient_id' => $patientId,
                'filename' => $filename,
                'size' => filesize($filepath)
            ]);
        } else {
            sendError('Error guardando archivo', 500);
        }
        
    } catch (Exception $e) {
        sendError('Error procesando datos: ' . $e->getMessage(), 500);
    }
}

/**
 * Eliminar paciente
 */
function handleDeletePatient() {
    // Verificar contraseña
    $password = $_POST['password'] ?? $_GET['password'] ?? '';
    if ($password !== API_PASSWORD) {
        sendError('Contraseña incorrecta', 401);
    }
    
    $id = $_POST['id'] ?? $_GET['id'] ?? '';
    if (empty($id)) {
        sendError('ID de paciente requerido', 400);
    }
    
    $filename = sanitizeFilename($id) . '.json';
    $filepath = PATIENTS_DIR . $filename;
    
    if (!file_exists($filepath)) {
        sendError('Paciente no encontrado', 404);
    }
    
    if (unlink($filepath)) {
        sendSuccess(['message' => 'Paciente eliminado correctamente']);
    } else {
        sendError('Error eliminando paciente', 500);
    }
}

/**
 * Generar ID único para paciente
 */
function generatePatientId($data) {
    $patientInfo = $data['patient_info'] ?? [];
    $name = $patientInfo['nombre'] ?? 'paciente';
    $age = $patientInfo['edad'] ?? '';
    
    // Crear base del ID
    $baseId = strtolower(trim($name));
    $baseId = preg_replace('/[^a-z0-9]/', '', $baseId);
    $baseId = substr($baseId, 0, 10);
    
    // Agregar edad y timestamp
    $timestamp = time();
    $id = $baseId . '_' . $age . '_' . $timestamp;
    
    // Asegurar unicidad
    $counter = 1;
    $originalId = $id;
    while (file_exists(PATIENTS_DIR . $id . '.json')) {
        $id = $originalId . '_' . $counter;
        $counter++;
    }
    
    return $id;
}

/**
 * Extraer nombre del paciente
 */
function extractPatientName($data) {
    return $data['patient_info']['nombre'] ?? 'Sin nombre';
}

/**
 * Extraer edad del paciente
 */
function extractPatientAge($data) {
    return $data['patient_info']['edad'] ?? null;
}

/**
 * Extraer género del paciente
 */
function extractPatientGender($data) {
    return $data['patient_info']['genero'] ?? null;
}

/**
 * Extraer diagnóstico
 */
function extractPatientDiagnosis($data) {
    // Buscar en varios lugares posibles
    if (isset($data['patient_info']['patologia'])) {
        return $data['patient_info']['patologia'];
    }
    
    if (isset($data['anamnesis']['diagnostico'])) {
        return $data['anamnesis']['diagnostico'];
    }
    
    return 'Sin diagnóstico';
}

/**
 * Extraer fecha de creación
 */
function extractCreatedDate($data) {
    if (isset($data['metadata']['created_date'])) {
        return $data['metadata']['created_date'];
    }
    
    if (isset($data['metadata']['uploaded_date'])) {
        return substr($data['metadata']['uploaded_date'], 0, 10);
    }
    
    return date('Y-m-d');
}

/**
 * Sanitizar nombre de archivo
 */
function sanitizeFilename($filename) {
    return preg_replace('/[^a-zA-Z0-9_-]/', '', $filename);
}

/**
 * Enviar respuesta exitosa
 */
function sendSuccess($data, $message = 'OK') {
    http_response_code(200);
    echo json_encode([
        'success' => true,
        'message' => $message,
        'data' => $data,
        'timestamp' => date('c')
    ], JSON_UNESCAPED_UNICODE);
    exit();
}

/**
 * Enviar error
 */
function sendError($message, $code = 400) {
    http_response_code($code);
    echo json_encode([
        'success' => false,
        'error' => $message,
        'timestamp' => date('c')
    ], JSON_UNESCAPED_UNICODE);
    exit();
}

/**
 * Log de debug (opcional)
 */
function debugLog($message) {
    $logFile = __DIR__ . '/debug.log';
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($logFile, "[$timestamp] $message\n", FILE_APPEND);
}
?>