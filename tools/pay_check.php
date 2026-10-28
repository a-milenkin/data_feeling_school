<?php
// Проверка настройки оплаты. Запускать на сервере Beget:  php8.4 ~/dfs_src/tools/pay_check.php
// Проверяет ключи ЮKassa, находит чат с ботом (нужно заранее нажать /start) и шлёт тестовое сообщение.
define('DFS_HOME', getenv('HOME') ?: dirname(__DIR__, 2));
$_SERVER['SCRIPT_FILENAME'] = __FILE__;
require dirname(__DIR__) . '/src/static/pay/lib.php';

function line($ok, $text) { echo ($ok ? '[OK]  ' : '[!!]  ') . $text . PHP_EOL; return $ok; }

if (!line(is_file(DFS_HOME . '/dfs_secrets.php'), 'Файл ~/dfs_secrets.php')) exit(1);
foreach (['shop_id', 'secret_key', 'tg_token', 'test_code'] as $k) line((bool) cfg($k), "в нём есть $k");

[$code, $me] = yk('GET', '/me');
line($code === 200, 'ЮKassa: ключ принят' . ($code === 200
    ? ', магазин ' . ($me['account_id'] ?? '?') . ', статус ' . ($me['status'] ?? '?') . ', тестовый: ' . (!empty($me['test']) ? 'да' : 'нет')
      . ', чеки: ' . (!empty($me['fiscalization']['enabled']) ? 'включены (' . ($me['fiscalization']['provider'] ?? '') . ')' : 'выключены')
    : " (HTTP $code: " . ($me['description'] ?? 'нет ответа') . ')'));
if ($code === 200) line(!empty($me['fiscalization']['enabled']) === (bool) cfg('receipt'),
    'Чеки: в ЮKassa ' . (!empty($me['fiscalization']['enabled']) ? 'включены' : 'выключены') . ', сайт ' . (cfg('receipt') ? 'передаёт' : 'не передаёт')
    . ' данные чека' . (!empty($me['fiscalization']['enabled']) && !cfg('receipt') ? " — добавьте 'receipt'=>true в ~/dfs_secrets.php" : ''));

$tg = 'https://api.telegram.org/bot' . cfg('tg_token');
[$code, $bot] = http_json('GET', $tg . '/getMe');
line($code === 200, 'Telegram: бот ' . ($code === 200 ? '@' . $bot['result']['username'] : "не отвечает (HTTP $code: " . ($bot['description'] ?? 'нет связи с api.telegram.org') . ')'));
[, $wh] = http_json('GET', $tg . '/getWebhookInfo');
if (!empty($wh['result']['url'])) line(false, 'Telegram: у бота настроен вебхук на другой сервис, getUpdates не работает. Найдите chat_id через @userinfobot и добавьте \'tg_chat_id\' в ~/dfs_secrets.php');

if (!tg_chat_id()) {
    [$code, $upd] = http_json('GET', $tg . '/getUpdates');
    line($code === 200, 'Telegram: новых сообщений боту — ' . count($upd['result'] ?? []) . ($code === 200 ? '' : ' (' . ($upd['description'] ?? '') . ')'));
    foreach (array_reverse($upd['result'] ?? []) as $u) {
        $chat = $u['message']['chat'] ?? null;
        if ($chat && $chat['type'] === 'private') {
            orders_dir();
            file_put_contents(DFS_DATA . '/tg_chat_id', $chat['id']);
            line(true, 'Telegram: нашёл чат с @' . ($chat['username'] ?? $chat['id']) . ', сохранил в ~/dfs_data/tg_chat_id');
            break;
        }
    }
}
if (line((bool) tg_chat_id(), 'Telegram: chat_id есть')) {
    line(tg_send('✅ Бот подключён к оплатам на datafeelingschool.ru. Сюда будут приходить оплаты практикума.'),
         'Telegram: тестовое сообщение отправлено');
} else {
    line(false, 'Нажмите /start у бота и запустите проверку ещё раз');
}

echo PHP_EOL . 'Адрес для HTTP-уведомлений ЮKassa (событие payment.succeeded):' . PHP_EOL
   . SITE_URL . '/pay/webhook.php' . PHP_EOL
   . 'Тестовая оплата 1 ₽: ' . SITE_URL . '/pet-project/?pay_test=' . cfg('test_code') . '#price' . PHP_EOL;
