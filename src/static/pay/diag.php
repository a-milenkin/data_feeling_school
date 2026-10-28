<?php
// ВРЕМЕННО: диагностика окружения оплаты, значения ключей не выводит. Удалить после отладки.
header('Content-Type: text/plain; charset=utf-8');
$home = dirname(__DIR__, 3);
$f = $home . '/dfs_secrets.php';
echo 'home: ', $home, "\n";
echo 'open_basedir: ', ini_get('open_basedir'), "\n";
echo 'euid: ', function_exists('posix_geteuid') ? posix_geteuid() : '?', ' owner: ', @fileowner($f), "\n";
echo 'is_file: ', var_export(@is_file($f), true), ' readable: ', var_export(@is_readable($f), true), ' perms: ', substr(sprintf('%o', @fileperms($f)), -4), "\n";
echo 'home writable: ', var_export(@is_writable($home), true), "\n";
echo 'curl: ', var_export(function_exists('curl_init'), true), "\n";
try { $c = require $f; echo 'require: ', gettype($c), ' keys=', is_array($c) ? implode(',', array_keys($c)) : '-', "\n"; }
catch (Throwable $e) { echo 'require error: ', get_class($e), ' ', $e->getMessage(), "\n"; }
$t = @tempnam(sys_get_temp_dir(), 'x'); echo 'tmp: ', sys_get_temp_dir(), ' ', $t ? 'ok' : 'fail', "\n";
foreach ([dirname(__DIR__, 2), dirname(__DIR__)] as $d) {
    $probe = $d . '/.dfs_probe';
    $w = @file_put_contents($probe, 'x') !== false;
    echo $d, ': perms ', substr(sprintf('%o', fileperms($d)), -4), ' owner ', fileowner($d), ' group ', filegroup($d), ' write ', var_export($w, true);
    if ($w) { echo ' new file owner ', fileowner($probe), ' perms ', substr(sprintf('%o', fileperms($probe)), -4); @unlink($probe); }
    echo "\n";
}
echo 'egid: ', function_exists('posix_getegid') ? posix_getegid() : '?', ' secrets group: ', @filegroup($f), "\n";
