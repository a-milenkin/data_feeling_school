<?php
// Создаёт платёж в ЮKassa и возвращает ссылку на страницу оплаты.
require __DIR__ . '/lib.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') json_out(['error' => 'Только POST'], 405);
if (!cfg('shop_id') || !cfg('secret_key')) json_out(['error' => 'Оплата временно недоступна. Напишите нам в Telegram.'], 503);

$in = json_decode(file_get_contents('php://input'), true) ?: [];
if (!empty($in['website'])) json_out(['error' => 'Ошибка формы'], 400); // ловушка для ботов

$name = trim(mb_substr((string) ($in['name'] ?? ''), 0, 100));
$email = trim((string) ($in['email'] ?? ''));
$tg = preg_replace('~^(https?://)?(t\.me/|telegram\.me/)|^@~i', '', trim((string) ($in['tg'] ?? '')));

if ($name === '') json_out(['error' => 'Укажите имя'], 400);
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) json_out(['error' => 'Проверьте почту'], 400);
if (!preg_match('/^[A-Za-z0-9_]{4,32}$/', $tg)) json_out(['error' => 'Укажите ник в Telegram, например @nickname'], 400);
if (empty($in['consent'])) json_out(['error' => 'Нужно согласие с офертой и политикой'], 400);

// тестовый режим: секретный код из ~/testdraft.store/dfs_secrets.php → цена 1 ₽
$test = cfg('test_code') && hash_equals((string) cfg('test_code'), (string) ($in['test'] ?? ''));
$stream = stream_info();
$amount = ['value' => number_format($test ? 1 : $stream['price'], 2, '.', ''), 'currency' => 'RUB'];

$id = bin2hex(random_bytes(8));
[$code, $p] = yk('POST', '/payments', [
    'amount' => $amount,
    'capture' => true,
    'confirmation' => ['type' => 'redirect', 'return_url' => SITE_URL . '/pay/success/?order=' . $id],
    'description' => PRODUCT_TITLE,
    'metadata' => ['order_id' => $id, 'tg' => $tg, 'stream' => $stream['number']],
] + (cfg('receipt') ? [ // чек 54-ФЗ — только если в ЮKassa включены чеки ('receipt' => true в ~/testdraft.store/dfs_secrets.php)
    'receipt' => [
        'customer' => ['email' => $email, 'full_name' => $name],
        'items' => [[
            'description' => PRODUCT_TITLE,
            'quantity' => '1.00',
            'amount' => $amount,
            'vat_code' => (int) (cfg('vat_code') ?: 1),
            'payment_mode' => 'full_payment',
            'payment_subject' => 'service',
        ]],
    ],
] : []), $id);

if ($code !== 200 || empty($p['confirmation']['confirmation_url'])) {
    pay_log('create ' . $code . ' ' . json_encode($p, JSON_UNESCAPED_UNICODE));
    json_out(['error' => 'Не получилось создать платёж. Попробуйте ещё раз или напишите нам в Telegram.'], 502);
}

order_save([
    'id' => $id, 'payment_id' => $p['id'], 'status' => $p['status'], 'test' => $test,
    'amount' => $amount['value'], 'off' => $stream['off'],
    'stream' => $stream['number'], 'stream_start' => $stream['start']->format('d.m.Y'), 'name' => $name, 'email' => $email, 'tg' => $tg, 'created_at' => date('c'),
]);
json_out(['url' => $p['confirmation']['confirmation_url']]);
