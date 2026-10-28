<?php
// Оплата практикума на сайте через ЮKassa + уведомление в Telegram.
// Секреты лежат на сервере в ~/dfs_secrets.php (вне папки сайта, в git не попадают),
// заказы — в ~/dfs_data/orders/. Как настроить — README, раздел «Оплата на сайте».
if (realpath(__FILE__) === realpath($_SERVER['SCRIPT_FILENAME'] ?? '')) { http_response_code(404); exit; }

if (!defined('DFS_HOME')) define('DFS_HOME', dirname(__DIR__, 3)); // ~/testdraft.store/public_html/pay → ~
define('DFS_DATA', DFS_HOME . '/dfs_data');

const PRODUCT_TITLE = 'Практикум «Пет-проект → микро-SaaS»';
const PRODUCT_PRICE = 45105; // 48 500 ₽ на Stepik − 7%
const SITE_URL = 'https://datafeelingschool.ru';

function cfg($key) {
    static $c;
    if ($c === null) {
        $f = DFS_HOME . '/dfs_secrets.php';
        $c = is_file($f) ? (require $f) : [];
    }
    return $c[$key] ?? null;
}

function json_out($data, $code = 200) {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function http_json($method, $url, $body = null, $headers = [], $userpwd = null) {
    $ch = curl_init($url);
    $headers[] = 'Content-Type: application/json';
    curl_setopt_array($ch, [
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 20,
        CURLOPT_HTTPHEADER => $headers,
    ]);
    if ($userpwd) curl_setopt($ch, CURLOPT_USERPWD, $userpwd);
    if ($body !== null) curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body, JSON_UNESCAPED_UNICODE));
    $raw = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    if ($raw === false) error_log('dfs pay: ' . $url . ' ' . curl_error($ch));
    curl_close($ch);
    return [$code, json_decode((string) $raw, true) ?: []];
}

function yk($method, $path, $body = null, $idempotence_key = null) {
    $headers = $idempotence_key ? ['Idempotence-Key: ' . $idempotence_key] : [];
    return http_json($method, 'https://api.yookassa.ru/v3' . $path, $body, $headers,
                     cfg('shop_id') . ':' . cfg('secret_key'));
}

function tg_chat_id() {
    if (cfg('tg_chat_id')) return cfg('tg_chat_id');
    $f = DFS_DATA . '/tg_chat_id';
    return is_file($f) ? trim(file_get_contents($f)) : null;
}

function tg_send($text) {
    $chat = tg_chat_id();
    if (!$chat || !cfg('tg_token')) { error_log('dfs pay: нет tg_token или chat_id'); return false; }
    [$code] = http_json('POST', 'https://api.telegram.org/bot' . cfg('tg_token') . '/sendMessage',
        ['chat_id' => $chat, 'text' => $text, 'parse_mode' => 'HTML', 'disable_web_page_preview' => true]);
    return $code === 200;
}

function order_file($id) {
    return DFS_DATA . '/orders/' . $id . '.json';
}

function valid_order_id($id) {
    return is_string($id) && preg_match('/^[a-f0-9]{16}$/', $id);
}

function order_load($id) {
    $f = order_file($id);
    return valid_order_id($id) && is_file($f) ? json_decode(file_get_contents($f), true) : null;
}

function orders_dir() {
    if (!is_dir(DFS_DATA . '/orders')) mkdir(DFS_DATA . '/orders', 0700, true);
    return DFS_DATA . '/orders';
}

function order_save($order) {
    orders_dir();
    file_put_contents(order_file($order['id']), json_encode($order, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
}

// Обновляет заказ по данным платежа из API и один раз шлёт уведомление об оплате.
// Зовётся из webhook.php и status.php: кто первым увидит оплату, тот и уведомит.
function sync_payment($payment) {
    $id = $payment['metadata']['order_id'] ?? '';
    $lock = fopen(orders_dir() . '/.lock', 'c');
    flock($lock, LOCK_EX);
    $order = order_load($id);
    if ($order && ($order['payment_id'] ?? '') === ($payment['id'] ?? '')) {
        $order['status'] = $payment['status'];
        if ($payment['status'] === 'succeeded' && empty($order['notified'])) {
            $order['paid_at'] = date('c');
            $order['notified'] = tg_send(paid_message($order, $payment));
        }
        order_save($order);
    }
    flock($lock, LOCK_UN);
    fclose($lock);
    return $order;
}

function paid_message($order, $payment) {
    $e = fn($s) => htmlspecialchars((string) $s, ENT_QUOTES);
    $sum = number_format((float) $payment['amount']['value'], 0, ',', ' ');
    return "💰 <b>Оплата на сайте: {$sum} ₽</b>" . (!empty($order['test']) ? ' (тест)' : '') . "\n"
        . $e(PRODUCT_TITLE) . "\n\n"
        . 'Имя: ' . $e($order['name']) . "\n"
        . 'Почта: ' . $e($order['email']) . "\n"
        . 'Telegram: @' . $e($order['tg']) . "\n\n"
        . 'Платёж ЮKassa: <code>' . $e($payment['id']) . '</code>';
}
