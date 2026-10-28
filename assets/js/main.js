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
