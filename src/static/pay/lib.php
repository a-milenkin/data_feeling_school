<?php
// Оплата практикума на сайте через ЮKassa + уведомление в Telegram.
// Секреты лежат на сервере в ~/testdraft.store/dfs_secrets.php (над public_html: из интернета не видно, в git не попадает),
// заказы — в ~/testdraft.store/dfs_data/orders/. Домашняя папка не подходит: PHP сайта на Beget работает
// от другого системного пользователя и видит только папку сайта. Как настроить — README, раздел «Оплата на сайте».
if (realpath(__FILE__) === realpath($_SERVER['SCRIPT_FILENAME'] ?? '')) { http_response_code(404); exit; }

if (!defined('DFS_HOME')) define('DFS_HOME', dirname(__DIR__, 2)); // ~/testdraft.store/public_html/pay → ~/testdraft.store
define('DFS_DATA', DFS_HOME . '/dfs_data');
// ошибки оплаты пишем сами в dfs_pay_errors.log рядом с секретами: путь error_log на Beget не переопределяется
function pay_log($msg) {
    @file_put_contents(DFS_HOME . '/dfs_pay_errors.log', date('c') . ' ' . $msg . PHP_EOL, FILE_APPEND);
}
set_exception_handler(function ($e) {
    pay_log(get_class($e) . ': ' . $e->getMessage() . ' @ ' . basename($e->getFile()) . ':' . $e->getLine());
    // в тестовом режиме (запрос с test_code) показываем причину, чтобы отладить без доступа к логам
    $debug = cfg('test_code') && str_contains((string) file_get_contents('php://input'), (string) cfg('test_code'));
    json_out(['error' => 'Ошибка сервера оплаты. Напишите нам в Telegram.']
        + ($debug ? ['debug' => $e->getMessage() . ' @ ' . basename($e->getFile()) . ':' . $e->getLine(),
                     'ini' => ['open_basedir' => ini_get('open_basedir'), 'home' => DFS_HOME]] : []), 500);
});

const PRODUCT_TITLE = 'Практикум «Пет-проект → микро-SaaS»';
const SITE_URL = 'https://datafeelingschool.ru';

// Потоки стартуют 1-го числа каждого месяца в 00:00 МСК; 1 ноября 2026 — поток №3.
// Цена на сайте: Stepik − 7%, а за EARLY_DAYS дней до старта — ещё −5%.
// Те же правила продублированы в assets/js/main.js (таймер и цена на странице).
const STEPIK_PRICE = 48500;
const SITE_OFF = 7;
const EARLY_OFF = 5;
const EARLY_DAYS = 5;
const FIRST_STREAM = [2026, 11, 3]; // год, месяц, номер потока

function stream_info() {
    $tz = new DateTimeZone('Europe/Moscow');
    $now = new DateTimeImmutable('now', $tz);
    $start = $now->modify('first day of next month')->setTime(0, 0);
    $months = ((int) $start->format('Y') - FIRST_STREAM[0]) * 12 + (int) $start->format('n') - FIRST_STREAM[1];
    $early = $start->getTimestamp() - $now->getTimestamp() <= EARLY_DAYS * 86400;
    $off = SITE_OFF + ($early ? EARLY_OFF : 0);
    return ['number' => FIRST_STREAM[2] + $months, 'start' => $start, 'early' => $early,
            'off' => $off, 'price' => (int) round(STEPIK_PRICE * (100 - $off) / 100)];
}

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
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE);
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
    if ($raw === false) pay_log(preg_replace('~/bot[^/]+~', '/bot***', $url) . ' ' . curl_error($ch));
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
    if (!$chat || !cfg('tg_token')) { pay_log('нет tg_token или chat_id'); return false; }
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
        . $e(PRODUCT_TITLE) . "\n"
        . 'Поток №' . $e($order['stream'] ?? '?') . ', старт ' . $e($order['stream_start'] ?? '?')
        . (isset($order['off']) ? " · скидка {$order['off']}%" : '') . "\n\n"
        . 'Имя: ' . $e($order['name']) . "\n"
        . 'Почта: ' . $e($order['email']) . "\n"
        . 'Telegram: @' . $e($order['tg']) . "\n\n"
        . 'Платёж ЮKassa: <code>' . $e($payment['id']) . '</code>';
}
