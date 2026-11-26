(function () {
  'use strict';
  var reduced = matchMedia('(prefers-reduced-motion: reduce)');
  var logo = document.querySelector('pre.logo');
  function fit() {
    document.querySelectorAll('pre.fitted').forEach(function (pre) {
      var box = pre.parentElement;
      var inner = box.clientWidth - parseFloat(getComputedStyle(box).paddingLeft) - parseFloat(getComputedStyle(box).paddingRight);
      pre.style.fontSize = '16px';
      var natural = pre.scrollWidth;
      if (natural) pre.style.fontSize = Math.min(16 * inner / natural, 17) + 'px';
    });
  }
  fit();
  addEventListener('resize', fit);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);

  if (logo && !reduced.matches) {
    var finalText = logo.textContent;
    var lines = finalText.split('\n');
    var width = Math.max.apply(null, lines.map(function (line) { return line.length; }));
    var noise = '░▒▓▖▗▘▙▚▛▜▝▞▟■▪◆◇○●';
    var lock = lines.map(function (line) {
      return Array.from(line, function (ch, x) { return ch === ' ' ? 0 : 250 + x / width * 1100 + Math.random() * 500; });
    });
    var start = null;
    requestAnimationFrame(function frame(now) {
      if (reduced.matches) { logo.textContent = finalText; return; }
      if (start === null) start = now;
      var t = now - start, done = true, out = '';
      lines.forEach(function (line, y) {
        Array.from(line).forEach(function (ch, x) {
          if (ch === ' ' || t >= lock[y][x]) { out += ch; return; }
          done = false;
          out += '<span class="' + (t > lock[y][x] - 250 ? 's2' : 's') + '">' + noise[Math.floor(Math.random() * noise.length)] + '</span>';
        });
        if (y < lines.length - 1) out += '\n';
      });
      logo.innerHTML = out;
      if (!done) requestAnimationFrame(frame); else logo.textContent = finalText;
    });
  }

  var canvas = document.getElementById('px'), ctx = canvas.getContext('2d');
  var CELL = 14, DOT = 10, GAP = 48, cells = [];
  var dark = ['#1f2335', '#24283b', '#292e42', '#414868'];
  var lit = ['#7aa2f7', '#bb9af7', '#3d59a1'];
  function roll(cell) {
    var r = Math.random();
    cell.fill = r > Math.pow(cell.d, 1.6) * 0.6 ? null : Math.random() < 0.07 ? lit[Math.floor(Math.random() * lit.length)] : dark[Math.floor(Math.random() * dark.length)];
  }
  function draw(cell) {
    ctx.clearRect(cell.x, cell.y, CELL, CELL);
    if (cell.fill) { ctx.fillStyle = cell.fill; ctx.fillRect(cell.x, cell.y, DOT, DOT); }
  }
  function field() {
    var dpr = devicePixelRatio || 1, w = innerWidth, h = innerHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var rect = document.querySelector('main').getBoundingClientRect();
    var left = rect.left - GAP, right = rect.right + GAP;
    cells = [];
    if (w <= 900 || left < CELL * 3 || right >= w) return;
    for (var x = 0; x < w; x += CELL) {
      var d = x + CELL <= left ? (left - x) / left : x >= right ? (x - right + CELL) / (w - right) : -1;
      if (d < 0) continue;
      for (var y = 0; y < h; y += CELL) {
        var cell = { x: x, y: y, d: d }; roll(cell); draw(cell); cells.push(cell);
      }
    }
  }
  field();
  addEventListener('resize', field);
  setInterval(function () {
    if (reduced.matches) return;
    for (var i = 0, n = Math.ceil(cells.length * 0.015); i < n; i++) {
      var cell = cells[Math.floor(Math.random() * cells.length)]; roll(cell); draw(cell);
    }
  }, 120);
})();
