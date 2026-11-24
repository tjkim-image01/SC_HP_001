/* STUDIO.C 성경 읽기 (2026-11-25)
   data/versions.json  — 판 목록(이름·언어·장 수·출처). build/build_bible.py 가 만든다.
   data/<판>/<책>.json — {"c":[[1절,2절,…],…]} 빈 문자열 = 앞 절에 합쳐진 절.
   주소: #krv/43/3 (요한복음 3장) · #krv+kjv/43/3 (나란히) · #krv/43/3/16 (16절 표시) */
(function(){
  'use strict';
  var $ = function(id){ return document.getElementById(id); };
  var LS = 'sc_bible';
  var META = null, VERS = {}, cache = {};
  var S = {v:'krv', p:'', b:1, c:1, hl:0, fs:18};
  var PS = 19; // 시편

  /* ---------- 테마 (홈과 같은 sc_theme) ---------- */
  (function(){
    var b = $('theme'), r = document.documentElement;
    function lab(){ b.setAttribute('aria-label', r.getAttribute('data-theme')==='light' ? '어둡게 보기' : '밝게 보기'); }
    lab();
    b.addEventListener('click', function(){
      var light = r.getAttribute('data-theme')==='light';
      if(light) r.removeAttribute('data-theme'); else r.setAttribute('data-theme','light');
      lab();
      try{ localStorage.setItem('sc_theme', light ? 'dark' : 'light'); }catch(e){}
    });
  })();

  /* ---------- 저장 · 주소 ---------- */
  function save(){
    try{ localStorage.setItem(LS, JSON.stringify({v:S.v, p:S.p, b:S.b, c:S.c, fs:S.fs})); }catch(e){}
  }
  function restore(){
    try{
      var o = JSON.parse(localStorage.getItem(LS) || 'null');
      if(o && typeof o === 'object'){
        if(VERS[o.v]) S.v = o.v;
        if(o.p === '' || VERS[o.p]) S.p = o.p || '';
        if(o.b >= 1 && o.b <= 66) S.b = o.b|0;
        if(o.c >= 1) S.c = o.c|0;
        if(o.fs >= 14 && o.fs <= 28) S.fs = o.fs|0;
      }
    }catch(e){}
  }
  function parseHash(){
    var h = decodeURIComponent(location.hash.replace(/^#/, ''));
    if(!h) return false;
    var m = h.split('/');
    var vv = (m[0] || '').toLowerCase().split(/[+,]/);
    var ok = false;
    if(VERS[vv[0]]){ S.v = vv[0]; ok = true; S.p = (vv[1] && VERS[vv[1]] && vv[1] !== vv[0]) ? vv[1] : ''; }
    var b = parseInt(m[1], 10), c = parseInt(m[2], 10), v = parseInt(m[3], 10);
    if(b >= 1 && b <= 66){
      S.b = b; ok = true;
      S.c = c >= 1 ? c : 1;
      S.hl = v >= 1 ? v : 0;
    }
    return ok;
  }
  function hashOf(hl){
    return '#' + S.v + (S.p ? '+' + S.p : '') + '/' + S.b + '/' + S.c + (hl ? '/' + hl : '');
  }
  function writeHash(){
    var h = hashOf(S.hl);
    if(location.hash !== h){ try{ history.replaceState(null, '', h); }catch(e){ location.hash = h; } }
  }

  /* ---------- 데이터 ---------- */
  function book(id, b){
    var k = id + '/' + b;
    if(!cache[k]){
      cache[k] = fetch('data/' + id + '/' + b + '.json').then(function(r){
        if(!r.ok) throw new Error(r.status);
        return r.json();
      }).then(function(j){ return j.c; });
      cache[k].catch(function(){ delete cache[k]; });
    }
    return cache[k];
  }
  function nch(id, b){ return (VERS[id].chapters[b-1]) || 0; }
  function optName(V){ return V.lang === 'ko' ? V.name : V.label.split(' · ')[0] + ' ' + V.name; }
  function unit(b){ return b === PS ? '편' : '장'; }
  function koRef(b, c, v){ return META.ko[b-1] + ' ' + c + (v ? ':' + v : unit(b)); }

  /* 러시아 시노달 역 시편 번호(칠십인역) ↔ 히브리·한국어 번호 */
  function psMap(c, from, to){
    if(from === to) return [c];
    if(from === 'std' && to === 'rus'){
      if(c <= 8 || c >= 148) return [c];
      if(c === 9 || c === 10) return [9];
      if(c <= 113) return [c-1];
      if(c === 114 || c === 115) return [113];
      if(c === 116) return [114, 115];
      if(c <= 146) return [c-1];
      return [146, 147];
    }
    if(from === 'rus' && to === 'std'){
      if(c <= 8 || c >= 148) return [c];
      if(c === 9) return [9, 10];
      if(c <= 112) return [c+1];
      if(c === 113) return [114, 115];
      if(c === 114 || c === 115) return [116];
      if(c <= 145) return [c+1];
      return [147];
    }
    return [c];
  }
  function mapCh(b, c, fromId, toId){
    if(b !== PS) return [c];
    return psMap(c, VERS[fromId].versif, VERS[toId].versif);
  }

  /* ---------- 그리기 ---------- */
  function el(tag, cls, text){
    var e = document.createElement(tag);
    if(cls) e.className = cls;
    if(text != null) e.textContent = text;
    return e;
  }
  function verseLabels(arr){
    // 합쳐진 절(빈 칸)은 앞 절 번호에 붙인다: 29–30
    var out = [];
    for(var i = 0; i < arr.length; i++){
      if(!arr[i]) continue;
      var j = i;
      while(j + 1 < arr.length && !arr[j+1]) j++;
      out.push({v: i+1, lab: j > i ? (i+1) + '–' + (j+1) : String(i+1), t: arr[i]});
    }
    return out;
  }
  function vnode(lab, t, lang){
    var d = el('span', 'cell');
    if(lang) d.lang = lang;
    d.appendChild(el('span', 'vn', lab));
    d.appendChild(document.createTextNode(t));
    return d;
  }

  var renderSeq = 0;
  function render(scroll){
    var seq = ++renderSeq;
    var V = VERS[S.v], P = S.p ? VERS[S.p] : null;
    var max = nch(S.v, S.b);
    if(!max){ // 이 판에 없는 책 (지금은 없음)
      S.b = 1; max = nch(S.v, 1);
    }
    if(S.c > max) S.c = max;
    if(S.c < 1) S.c = 1;
    writeHash(); save(); syncControls();

    // 러시아 시편은 제목을 한국어 번호로 (예: Псалтирь 22 → 시편 23편), 러시아 번호는 아래 줄에
    var title = (S.b === PS && V.versif !== 'std')
      ? META.ko[S.b-1] + ' ' + psMap(S.c, V.versif, 'std').join('·') + '편'
      : koRef(S.b, S.c);
    $('ctitle').textContent = title;
    $('pickLabel').textContent = title;
    document.title = title + ' · ' + V.name + ' · STUDIO.C 성경';
    var sub = V.lang === 'ko' ? V.label : V.books[S.b-1] + ' ' + S.c + ' · ' + V.name;
    if(P) sub += '  |  ' + P.books[S.b-1] + ' ' + mapCh(S.b, S.c, S.v, S.p).join('·') + ' · ' + P.name;
    $('csub').textContent = sub;
    $('prev').disabled = $('prev2').disabled = (S.b === 1 && S.c === 1);
    $('next').disabled = $('next2').disabled = (S.b === 66 && S.c === nch(S.v, 66));

    var note = '';
    if(S.b === PS && (V.versif === 'rus' || (P && P.versif === 'rus'))){
      note = '러시아 시노달 역은 시편을 칠십인역 번호로 셉니다 (예: 시편 23편 = Псалом 22). 대조할 때는 맞는 장을 찾아 함께 보여 줍니다. 표제도 1절로 세어 절 번호가 하나씩 밀릴 수 있습니다.';
    } else if(P && (V.versif !== P.versif)){
      note = '러시아 시노달 역은 몇몇 책의 장·절 나누기가 조금 다릅니다. 절 번호가 어긋나면 앞뒤 절을 함께 보세요.';
    }
    $('note').hidden = !note; $('note').textContent = note;

    var box = $('text');
    var jobs = [book(S.v, S.b)];
    var pch = P ? mapCh(S.b, S.c, S.v, S.p) : [];
    if(P) jobs.push(book(S.p, S.b));
    Promise.all(jobs).then(function(res){
      if(seq !== renderSeq) return;
      var a = res[0][S.c-1] || [];
      box.textContent = '';
      box.lang = V.lang;
      if(!P){
        verseLabels(a).forEach(function(x){
          var d = el('div', 'v'); d.id = 'v' + x.v; d.dataset.v = x.v;
          d.appendChild(vnode(x.lab, x.t));
          box.appendChild(d);
        });
      } else if(pch.length === 1 && pch[0] === S.c && !(S.b === PS && V.versif !== P.versif)){
        var bArr = res[1][S.c-1] || [];
        var hd = el('div', 'colhead');
        hd.appendChild(el('span', '', V.label)); hd.appendChild(el('span', '', P.label));
        box.appendChild(hd);
        var n = Math.max(a.length, bArr.length);
        for(var i = 0; i < n; i++){
          if(!a[i] && !bArr[i]) continue;
          var d = el('div', 'v row'); d.id = 'v' + (i+1); d.dataset.v = i+1;
          d.appendChild(a[i] ? vnode(String(i+1), a[i], V.lang) : mergedCell(V.lang, i < a.length));
          var cb = bArr[i] ? vnode(String(i+1), bArr[i], P.lang) : mergedCell(P.lang, i < bArr.length);
          cb.classList.add('b');
          d.appendChild(cb);
          box.appendChild(d);
        }
      } else {
        // 장 번호가 다를 때(러시아 시편): 두 단을 따로 그린다
        var cols = el('div', 'cols');
        var ca = el('div', ''); ca.lang = V.lang;
        ca.appendChild(el('h2', '', V.books[S.b-1] + ' ' + S.c + ' · ' + V.name));
        verseLabels(a).forEach(function(x){
          var d = el('div', 'v'); d.id = 'v' + x.v; d.dataset.v = x.v;
          d.appendChild(vnode(x.lab, x.t)); ca.appendChild(d);
        });
        var cbx = el('div', ''); cbx.lang = P.lang;
        pch.forEach(function(pc){
          cbx.appendChild(el('h2', '', P.books[S.b-1] + ' ' + pc + ' · ' + P.name + '  (= ' + V.books[S.b-1] + ' ' + S.c + ')'));
          var arr = res[1][pc-1] || [];
          if(!arr.length) cbx.appendChild(el('p', 'merged', '이 번역에는 해당 장이 없습니다.'));
          verseLabels(arr).forEach(function(x){
            var d = el('div', 'v'); d.dataset.pv = x.v;
            d.appendChild(vnode(x.lab, x.t)); cbx.appendChild(d);
          });
        });
        cols.appendChild(ca); cols.appendChild(cbx);
        box.appendChild(cols);
      }
      if(!box.childNodes.length) box.appendChild(el('p', 'err', '이 장의 본문이 없습니다.'));
      markSel();
      if(S.hl && $('v' + S.hl)){
        $('v' + S.hl).scrollIntoView({block:'center'});
      } else if(scroll){
        window.scrollTo(0, 0);
      }
      prefetch();
    }).catch(function(){
      if(seq !== renderSeq) return;
      box.textContent = '';
      box.appendChild(el('p', 'err', '본문을 불러오지 못했습니다. 인터넷 연결을 확인하고 다시 시도해 주세요.'));
    });
  }
  function mergedCell(lang, inside){
    var d = el('span', 'cell');
    if(lang) d.lang = lang;
    d.appendChild(el('span', 'merged', inside ? '(앞 절에 포함)' : ''));
    return d;
  }
  function prefetch(){
    // 다음 책을 미리 받아 둔다 (장 끝에서 넘길 때 빠르게)
    if(S.c === nch(S.v, S.b) && S.b < 66) book(S.v, S.b + 1);
  }

  /* ---------- 이동 ---------- */
  function go(b, c, opts){
    S.b = b; S.c = c; S.hl = (opts && opts.hl) || 0;
    render(!(opts && opts.keepScroll));
  }
  function step(d){
    var b = S.b, c = S.c + d;
    if(c < 1){ if(b === 1) return; b--; c = nch(S.v, b); }
    else if(c > nch(S.v, b)){ if(b === 66) return; b++; c = 1; }
    go(b, c);
  }
  ['prev', 'prev2'].forEach(function(id){ $(id).addEventListener('click', function(){ step(-1); }); });
  ['next', 'next2'].forEach(function(id){ $(id).addEventListener('click', function(){ step(1); }); });
  document.addEventListener('keydown', function(e){
    if(e.target.closest && e.target.closest('input,select,textarea,dialog')) return;
    if(e.altKey || e.ctrlKey || e.metaKey) return;
    if(e.key === 'ArrowLeft'){ step(-1); }
    else if(e.key === 'ArrowRight'){ step(1); }
  });
  window.addEventListener('hashchange', function(){ if(parseHash()) render(false); });

  /* ---------- 번역 고르기 ---------- */
  function syncControls(){
    $('ver').value = S.v;
    var par = $('par');
    par.textContent = '';
    var o0 = el('option', '', '대조 없음'); o0.value = ''; par.appendChild(o0);
    META.versions.forEach(function(V){
      if(V.id === S.v) return;
      var o = el('option', '', '+ ' + optName(V)); o.value = V.id; o.title = V.label; par.appendChild(o);
    });
    par.value = S.p;
    $('text').style.setProperty('--bfs', S.fs + 'px');
  }
  $('ver').addEventListener('change', function(){
    var old = S.v, nv = this.value;
    S.c = mapCh(S.b, S.c, old, nv)[0];
    S.v = nv;
    if(S.p === nv) S.p = old;
    S.hl = 0;
    render(false);
  });
  $('par').addEventListener('change', function(){ S.p = this.value; S.hl = 0; render(false); });
  $('fsDown').addEventListener('click', function(){ S.fs = Math.max(14, S.fs - 1); syncControls(); save(); });
  $('fsUp').addEventListener('click', function(){ S.fs = Math.min(28, S.fs + 1); syncControls(); save(); });

  /* ---------- 절 고르기 · 복사 ---------- */
  function markSel(){
    [].forEach.call($('text').querySelectorAll('.v.on'), function(x){ x.classList.remove('on'); });
    var t = S.hl && $('v' + S.hl);
    if(t){
      t.classList.add('on');
      $('selRef').textContent = koRef(S.b, S.c, S.hl);
      $('selbar').hidden = false;
    } else {
      $('selbar').hidden = true;
    }
  }
  $('text').addEventListener('click', function(e){
    var d = e.target.closest('.v');
    if(!d || !d.dataset.v) return;
    if(window.getSelection && String(window.getSelection()).length > 1) return; // 글자를 끌어 고르는 중
    var v = +d.dataset.v;
    S.hl = (S.hl === v) ? 0 : v;
    writeHash(); markSel();
  });
  $('selClose').addEventListener('click', function(){ S.hl = 0; writeHash(); markSel(); });
  function copy(text, btn){
    function done(){ var t = btn.textContent; btn.textContent = '복사됨'; setTimeout(function(){ btn.textContent = t; }, 1200); }
    if(navigator.clipboard && window.isSecureContext){
      navigator.clipboard.writeText(text).then(done, fallback);
    } else fallback();
    function fallback(){
      var ta = el('textarea'); ta.value = text; ta.setAttribute('readonly', '');
      ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try{ document.execCommand('copy'); done(); }catch(e){}
      document.body.removeChild(ta);
    }
  }
  $('copyText').addEventListener('click', function(){
    var d = S.hl && $('v' + S.hl); if(!d) return;
    var parts = [].map.call(d.querySelectorAll('.cell'), function(c){
      var t = c.cloneNode(true); var n = t.querySelector('.vn'); if(n) n.remove();
      return t.textContent.trim();
    }).filter(Boolean);
    var names = VERS[S.v].name + (S.p && parts.length > 1 ? ' / ' + VERS[S.p].name : '');
    copy(parts.join('\n') + '\n— ' + koRef(S.b, S.c, S.hl) + ' (' + names + ')', this);
  });
  $('copyLink').addEventListener('click', function(){
    copy(location.href.split('#')[0] + hashOf(S.hl), this);
  });

  /* ---------- 책·장 고르기 창 ---------- */
  var nav = $('nav'), navBook = 0;
  function openDlg(d){ if(typeof d.showModal === 'function'){ d.showModal(); } else { d.setAttribute('open', ''); } }
  function closeDlg(d){ if(typeof d.close === 'function'){ d.close(); } else { d.removeAttribute('open'); } }
  function fillBooks(){
    ['ot', 'nt'].forEach(function(id){ $(id).textContent = ''; });
    META.ko.forEach(function(name, i){
      var b = i + 1, btn = el('button', '', name);
      btn.type = 'button';
      if(b === S.b) btn.setAttribute('aria-current', 'true');
      btn.addEventListener('click', function(){ showChaps(b); });
      $(b <= 39 ? 'ot' : 'nt').appendChild(btn);
    });
  }
  function showChaps(b){
    navBook = b;
    var n = nch(S.v, b), g = $('chaps');
    g.textContent = '';
    for(var c = 1; c <= n; c++){
      (function(c){
        var btn = el('button', '', String(c));
        btn.type = 'button';
        btn.setAttribute('aria-label', koRef(b, c));
        if(b === S.b && c === S.c) btn.setAttribute('aria-current', 'true');
        btn.addEventListener('click', function(){ closeDlg(nav); go(b, c); });
        g.appendChild(btn);
      })(c);
    }
    $('navTitle').textContent = META.ko[b-1] + ' · ' + (b === PS ? '편' : '장') + ' 고르기';
    $('navBooks').hidden = true; $('navChaps').hidden = false; $('navBack').hidden = false;
    if(n === 1){ closeDlg(nav); go(b, 1); }
  }
  function showBooks(){
    $('navTitle').textContent = '책 고르기';
    $('navBooks').hidden = false; $('navChaps').hidden = true; $('navBack').hidden = true;
    fillBooks();
  }
  $('pick').addEventListener('click', function(){ showBooks(); openDlg(nav); });
  $('navBack').addEventListener('click', showBooks);
  $('navClose').addEventListener('click', function(){ closeDlg(nav); });
  [nav, $('find')].forEach(function(d){
    d.addEventListener('click', function(e){ if(e.target === d) closeDlg(d); }); // 바깥 누르면 닫기
  });

  /* ---------- 찾기 ---------- */
  var find = $('find'), findSeq = 0;
  $('findBtn').addEventListener('click', function(){
    openDlg(find);
    setTimeout(function(){ $('q').focus(); }, 30);
  });
  $('findClose').addEventListener('click', function(){ closeDlg(find); });
  function norm(s){ return s.toLowerCase().replace(/[́]/g, '').replace(/ё/g, 'е'); }
  $('findForm').addEventListener('submit', function(e){
    e.preventDefault();
    var q = $('q').value.trim();
    var words = norm(q).split(/\s+/).filter(Boolean);
    var list = $('results'); list.textContent = '';
    if(!words.length){ $('q').focus(); return; }
    var scope = $('scope').value, books = [];
    for(var b = 1; b <= 66; b++){
      if(scope === 'all' || (scope === 'ot' && b <= 39) || (scope === 'nt' && b >= 40) || (scope === 'book' && b === S.b)) books.push(b);
    }
    var seq = ++findSeq, id = S.v, V = VERS[id], hits = [], LIMIT = 300, done = 0;
    var info = $('findInfo');
    info.textContent = '찾는 중… (' + V.name + ')';
    // 책 파일을 6개씩 받아 가며 찾는다
    var queue = books.slice(), results = {};
    function worker(){
      if(!queue.length) return Promise.resolve();
      var b = queue.shift();
      return book(id, b).then(function(chs){
        if(seq !== findSeq) return;
        var r = [];
        chs.forEach(function(vs, ci){
          vs.forEach(function(t, vi){
            if(!t) return;
            var n = norm(t);
            for(var k = 0; k < words.length; k++){ if(n.indexOf(words[k]) < 0) return; }
            r.push([ci+1, vi+1, t]);
          });
        });
        results[b] = r; done++;
        if(books.length > 1) info.textContent = '찾는 중… ' + done + '/' + books.length + '권';
      }, function(){ results[b] = []; done++; }).then(worker);
    }
    var ws = []; for(var i = 0; i < 6; i++) ws.push(worker());
    Promise.all(ws).then(function(){
      if(seq !== findSeq) return;
      books.forEach(function(b){ (results[b] || []).forEach(function(h){ hits.push([b, h[0], h[1], h[2]]); }); });
      info.textContent = '「' + q + '」 ' + hits.length + '절' + (hits.length > LIMIT ? ' (앞의 ' + LIMIT + '절만 보여 줍니다)' : '') + ' · ' + V.name;
      hits.slice(0, LIMIT).forEach(function(h){
        var li = el('li'), a = el('a');
        a.href = '#' + id + (S.p ? '+' + S.p : '') + '/' + h[0] + '/' + h[1] + '/' + h[2];
        a.appendChild(el('b', '', META.ko[h[0]-1] + ' ' + h[1] + ':' + h[2] + (V.lang !== 'ko' ? '  ·  ' + V.books[h[0]-1] + ' ' + h[1] + ':' + h[2] : '')));
        var sp = el('span'); sp.lang = V.lang;
        highlight(sp, h[3], words);
        a.appendChild(sp);
        a.addEventListener('click', function(ev){
          ev.preventDefault();
          closeDlg(find);
          S.v = id; go(h[0], h[1], {hl: h[2]});
        });
        li.appendChild(a); list.appendChild(li);
      });
    });
  });
  function highlight(node, text, words){
    var n = norm(text), marks = [];
    words.forEach(function(w){
      var i = 0;
      while((i = n.indexOf(w, i)) >= 0){ marks.push([i, i + w.length]); i += w.length; }
    });
    marks.sort(function(x, y){ return x[0] - y[0]; });
    var pos = 0;
    marks.forEach(function(m){
      if(m[0] < pos) return;
      node.appendChild(document.createTextNode(text.slice(pos, m[0])));
      node.appendChild(el('mark', '', text.slice(m[0], m[1])));
      pos = m[1];
    });
    node.appendChild(document.createTextNode(text.slice(pos)));
  }

  /* ---------- 시작 ---------- */
  fetch('data/versions.json').then(function(r){ return r.json(); }).then(function(m){
    META = m;
    m.versions.forEach(function(V){ VERS[V.id] = V; });
    var sel = $('ver');
    m.versions.forEach(function(V){ var o = el('option', '', optName(V)); o.value = V.id; o.title = V.label; sel.appendChild(o); });
    var ul = $('srcList');
    m.versions.forEach(function(V){
      var li = el('li');
      li.appendChild(el('strong', '', V.label));
      li.appendChild(document.createTextNode(' — ' + V.license + ' · 출처 '));
      var url = V.source.split(' ')[0];
      var a = el('a', '', url.replace(/^https?:\/\//, '')); a.href = url; a.rel = 'noopener';
      li.appendChild(a);
      ul.appendChild(li);
    });
    restore();
    parseHash();
    render(false);
  }).catch(function(){
    $('text').textContent = '';
    $('text').appendChild(el('p', 'err', '성경 목록을 불러오지 못했습니다. 잠시 뒤 다시 열어 주세요.'));
  });
})();
