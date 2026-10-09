<?php

final class Response
{
    public static function json(array $data, int $status = 200): void
    {
        http_response_code($status);
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode($data, JSON_UNESCAPED_UNICODE);
        exit;
    }

    /** @param array<string, mixed> $extra campos además de 'error' (ej. 'codigo') */
    public static function error(string $message, int $status = 400, array $extra = []): void
    {
        self::json(['error' => $message] + $extra, $status);
    }
}
