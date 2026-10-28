<?php
// HTTP-уведомления ЮKassa (кабинет → Интеграция → HTTP-уведомления → этот адрес).
// Телу уведомления не доверяем: статус платежа перепроверяем запросом к API.
require __DIR__ . '/lib.php';

$in = json_decode(file_get_contents('php://input'), true) ?: [];
$pid = (string) ($in['object']['id'] ?? '');
if (!preg_match('/^[A-Za-z0-9-]{10,64}$/', $pid)) { http_response_code(400); exit; }

[$code, $payment] = yk('GET', '/payments/' . $pid);
if ($code !== 200) { http_response_code(500); exit; } // ЮKassa повторит уведомление позже
sync_payment($payment);
echo 'ok';
