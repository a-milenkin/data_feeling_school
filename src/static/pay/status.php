<?php
// Статус заказа для страницы /pay/success/. Если уведомление ЮKassa ещё не пришло,
// спрашивает API сам — так оплата подтверждается, даже когда вебхук задерживается.
require __DIR__ . '/lib.php';

$order = order_load($_GET['order'] ?? '');
if (!$order) json_out(['status' => 'not_found'], 404);

if (!in_array($order['status'], ['succeeded', 'canceled'], true) || empty($order['notified'])) {
    [$code, $payment] = yk('GET', '/payments/' . $order['payment_id']);
    if ($code === 200) $order = sync_payment($payment) ?: $order;
}
json_out(['status' => $order['status']]);
