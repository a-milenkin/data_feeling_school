(function () {
  var burger = document.querySelector('.burger');
  var nav = document.querySelector('.nav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      burger.setAttribute('aria-expanded', open);
    });
  }

  // подсветка текущего раздела
  var path = location.pathname;
  document.querySelectorAll('.nav a[data-section]').forEach(function (a) {
    var s = a.getAttribute('data-section');
    if (s === '/' ? path === '/' : path.indexOf(s) === 0) a.classList.add('active');
  });

  // плавное появление блоков
  var items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('in'); });
  }

  // фильтр статей в блоге (поддерживает ?course=n8n)
  var chips = document.querySelectorAll('[data-filter]');
  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      chips.forEach(function (x) { x.classList.remove('on'); });
      c.classList.add('on');
      var f = c.getAttribute('data-filter');
      document.querySelectorAll('.post-card').forEach(function (p) {
        p.style.display = (f === 'all' || p.getAttribute('data-course') === f) ? '' : 'none';
      });
    });
  });
  var want = new URLSearchParams(location.search).get('course');
  if (want) { chips.forEach(function (c) { if (c.getAttribute('data-filter') === want) c.click(); }); }

  // потоки практикума: старт 1-го числа каждого месяца в 00:00 МСК, 1 ноября 2026 — поток №3.
  // Первые три недели месяца к оплате на сайте добавляется ещё −5%; бонус сгорает,
  // когда до старта следующего потока остаётся BONUS_CLOSE_DAYS дней или меньше.
  // Те же правила на сервере: src/static/pay/lib.php (цену в итоге считает он).
  var STREAM = { year: 2026, month: 10, number: 3 }; // month с нуля: 10 = ноябрь
  var STEPIK_PRICE = 48500, SITE_OFF = 7, BONUS_OFF = 5, BONUS_CLOSE_DAYS = 7;
  var MSK = 3 * 3600 * 1000;
  var MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
  var plural = function (n, forms) {
    var a = n % 100, b = n % 10;
    return forms[a > 10 && a < 20 ? 2 : b === 1 ? 0 : b > 1 && b < 5 ? 1 : 2];
  };
  var rub = function (n) { return String(n).replace(/\B(?=(\d{3})+$)/g, ' ') + ' ₽'; };
  var streamAt = function (y, m) { // поток, стартующий 1-го числа месяца m года y
    var months = (y - STREAM.year) * 12 + m - STREAM.month;
    return { number: STREAM.number + months, start: Date.UTC(y, m, 1) - MSK, day: '1 ' + MONTHS[m], year: y };
  };
  var nextStream = function () {
    var msk = new Date(Date.now() + MSK);
    return streamAt(msk.getUTCFullYear() + (msk.getUTCMonth() === 11 ? 1 : 0), (msk.getUTCMonth() + 1) % 12);
  };
  var timers = document.querySelectorAll('[data-stream-timer]');
  if (timers.length) {
    var st = nextStream();
    var bonusEnd = st.start - BONUS_CLOSE_DAYS * 86400000;
    var bonus = Date.now() < bonusEnd;
    var off = SITE_OFF + (bonus ? BONUS_OFF : 0);
    var setAll = function (sel, fn) { document.querySelectorAll(sel).forEach(fn); };
    setAll('[data-stream-tag]', function (el) { el.textContent = 'Поток №' + st.number + ' · старт ' + st.day; });
    setAll('[data-stream-name]', function (el) { el.textContent = 'потока №' + st.number; });
    setAll('[data-stream-date]', function (el) { el.textContent = st.day; });
    setAll('[data-site-price]', function (el) { el.textContent = rub(Math.round(STEPIK_PRICE * (100 - off) / 100)); });
    setAll('[data-site-off]', function (el) { el.textContent = '−' + off + '%'; });
    setAll('[data-bonus-date]', function (el) { // последний день бонуса по Москве
      var d = new Date(bonusEnd - 1 + MSK);
      el.textContent = d.getUTCDate() + ' ' + MONTHS[d.getUTCMonth()];
    });
    setAll('[data-bonus-deal]', function (el) {
      var pay = document.querySelector('[data-pay]'); // скидка видна, только когда видна кнопка оплаты на сайте
      el.hidden = !(bonus && pay && (!pay.hidden || new URLSearchParams(location.search).get('pay_test')));
    });
    setAll('[data-stream-schedule]', function (ol) {
      var html = '';
      for (var i = 0; i < 12; i++) {
        var m = (new Date(st.start + MSK).getUTCMonth() + i) % 12;
        var y = st.year + Math.floor((new Date(st.start + MSK).getUTCMonth() + i) / 12);
        var s = streamAt(y, m);
        html += '<li><b>Поток №' + s.number + '</b><span>' + s.day + ' ' + s.year + '</span></li>';
      }
      ol.innerHTML = html;
    });
    var LABELS = { d: ['день', 'дня', 'дней'], h: ['час', 'часа', 'часов'], m: ['минута', 'минуты', 'минут'], s: ['секунда', 'секунды', 'секунд'] };
    var tick = function () {
      var left = Math.max(0, st.start - Date.now());
      if (!left) { location.reload(); return; } // поток стартовал — пересчитываем следующий
      var v = { d: Math.floor(left / 86400000), h: Math.floor(left / 3600000) % 24, m: Math.floor(left / 60000) % 60, s: Math.floor(left / 1000) % 60 };
      timers.forEach(function (t) {
        Object.keys(v).forEach(function (k) {
          t.querySelector('[data-t="' + k + '"]').textContent = (v[k] < 10 ? '0' : '') + v[k];
          t.querySelector('[data-l="' + k + '"]').textContent = plural(v[k], LABELS[k]);
        });
      });
    };
    tick();
    setInterval(tick, 1000);
  }

  // оплата на сайте (ЮKassa): форма → /pay/create.php → страница оплаты
  // ?pay_test=<код> показывает скрытую кнопку и включает тестовую цену 1 ₽
  var modal = document.getElementById('pay-modal');
  if (modal) {
    var test = new URLSearchParams(location.search).get('pay_test');
    var form = modal.querySelector('form');
    var err = modal.querySelector('.pay-error');
    var submit = modal.querySelector('[data-pay-submit]');
    if (test) modal.querySelector('[data-pay-price]').textContent = 'ТЕСТ · 1 ₽';
    document.querySelectorAll('[data-pay]').forEach(function (b) {
      if (test) b.hidden = false;
      b.addEventListener('click', function () { modal.showModal(); });
    });
    modal.querySelector('[data-pay-close]').addEventListener('click', function () { modal.close(); });
    modal.addEventListener('click', function (e) { if (e.target === modal) modal.close(); });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = function (n) { return form.elements.namedItem(n); }; // form.name занят именем самой формы
      var d = {
        name: f('name').value, email: f('email').value, tg: f('tg').value,
        website: f('website').value, consent: f('consent').checked, test: test || ''
      };
      var miss = !d.name.trim() ? 'Укажите имя' : !f('email').checkValidity() || !d.email ? 'Проверьте почту'
        : !d.tg.trim() ? 'Укажите ник в Telegram' : !d.consent ? 'Нужно согласие с офертой и политикой' : '';
      if (miss) { err.textContent = miss; err.hidden = false; return; }
      err.hidden = true;
      submit.disabled = true;
      submit.textContent = 'Создаём платёж…';
      fetch('/pay/create.php', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(d) })
        .then(function (r) { return r.json(); })
        .then(function (r) {
          if (r.url) { location.href = r.url; return; }
          throw new Error(r.error);
        })
        .catch(function (x) {
          err.textContent = (x && x.message) || 'Не получилось создать платёж. Попробуйте ещё раз.';
          err.hidden = false;
          submit.disabled = false;
          submit.textContent = 'Перейти к оплате';
        });
    });
  }

  // страница после оплаты: ждём подтверждения от ЮKassa
  var box = document.querySelector('[data-pay-status]');
  if (box) {
    var order = new URLSearchParams(location.search).get('order');
    var tries = 0;
    var show = function (s) {
      box.querySelectorAll('[data-state]').forEach(function (el) { el.hidden = el.getAttribute('data-state') !== s; });
    };
    var poll = function () {
      fetch('/pay/status.php?order=' + encodeURIComponent(order || ''))
        .then(function (r) { return r.json(); })
        .then(function (r) {
          if (r.status === 'succeeded' || r.status === 'canceled' || r.status === 'not_found') return show(r.status === 'not_found' ? 'canceled' : r.status);
          if (++tries < 40) setTimeout(poll, 3000); else show('slow');
        })
        .catch(function () { if (++tries < 40) setTimeout(poll, 3000); else show('slow'); });
    };
    poll();
  }
})();
