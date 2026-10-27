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
})();
