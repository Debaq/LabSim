<?php
/**
 * LabSim Backend - Validación de inputs
 */

/**
 * Valida campos requeridos en un array
 * @return array errores encontrados (vacío si todo ok)
 */
function validate_required(array $data, array $fields): array {
    $errors = [];
    foreach ($fields as $field) {
        if (!isset($data[$field]) || (is_string($data[$field]) && trim($data[$field]) === '')) {
            $errors[] = "El campo '$field' es requerido";
        }
    }
    return $errors;
}

/**
 * Valida que un valor esté en una lista permitida
 */
function validate_enum($value, array $allowed, string $fieldName): ?string {
    if ($value !== null && !in_array($value, $allowed, true)) {
        return "Valor inválido para '$fieldName'. Permitidos: " . implode(', ', $allowed);
    }
    return null;
}

/**
 * Valida formato de email
 */
function validate_email(?string $email): ?string {
    if ($email !== null && $email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        return 'Email inválido';
    }
    return null;
}

/**
 * Valida longitud de string
 */
function validate_length(string $value, string $field, int $min = 1, int $max = 255): ?string {
    $len = mb_strlen($value);
    if ($len < $min) {
        return "'$field' debe tener al menos $min caracteres";
    }
    if ($len > $max) {
        return "'$field' no puede exceder $max caracteres";
    }
    return null;
}

/**
 * Valida formato de fecha YYYY-MM-DD
 */
function validate_date(?string $date): ?string {
    if ($date === null || $date === '') return null;
    $d = DateTime::createFromFormat('Y-m-d', $date);
    if (!$d || $d->format('Y-m-d') !== $date) {
        return 'Formato de fecha inválido (esperado YYYY-MM-DD)';
    }
    return null;
}

/**
 * Valida formato de hora HH:MM
 */
function validate_time(?string $time): ?string {
    if ($time === null || $time === '') return null;
    if (!preg_match('/^\d{2}:\d{2}$/', $time)) {
        return 'Formato de hora inválido (esperado HH:MM)';
    }
    return null;
}

/**
 * Sanitiza un string para uso seguro
 */
function sanitize_string(?string $value): ?string {
    if ($value === null) return null;
    return trim(htmlspecialchars($value, ENT_QUOTES, 'UTF-8'));
}

/**
 * Valida y recopila errores, lanza error si hay alguno
 */
function validate_or_fail(array $errors): void {
    $errors = array_filter($errors);
    if (!empty($errors)) {
        error_response('Errores de validación', 422, array_values($errors));
    }
}

/**
 * Valida username: alfanumérico, guiones, puntos, 3-50 chars
 */
function validate_username(string $username): ?string {
    if (!preg_match('/^[a-zA-Z0-9._-]{3,50}$/', $username)) {
        return 'Username debe ser alfanumérico (3-50 caracteres, permite . _ -)';
    }
    return null;
}

/**
 * Valida password: mínimo 6 caracteres
 */
function validate_password(string $password): ?string {
    if (mb_strlen($password) < 6) {
        return 'La contraseña debe tener al menos 6 caracteres';
    }
    return null;
}
