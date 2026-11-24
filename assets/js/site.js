(function(){
  var b=document.getElementById('theme'), r=document.documentElement;
  try{ if(localStorage.getItem('sc_theme')==='light') r.setAttribute('data-theme','light'); }catch(e){}
  b.addEventListener('click',function(){
    var light=r.getAttribute('data-theme')==='light';
    if(light) r.removeAttribute('data-theme'); else r.setAttribute('data-theme','light');
    b.setAttribute('aria-label', light ? '밝게 보기' : '어둡게 보기');
    try{ localStorage.setItem('sc_theme', light ? 'dark' : 'light'); }catch(e){}
  });
  document.querySelectorAll('.chip').forEach(function(c){
    c.addEventListener('click',function(){ c.setAttribute('aria-pressed', c.getAttribute('aria-pressed')==='true'?'false':'true'); });
  });
  // 유튜브 썸네일이 아직 없으면(예약·비공개 영상은 404) 영상에서 뽑은 장면으로 대체
  document.querySelectorAll('img[data-fallback]').forEach(function(img){
    function swap(){ if(img.dataset.fallback && img.src.indexOf(img.dataset.fallback)<0){ img.src=img.dataset.fallback; } }
    // 유튜브는 썸네일이 없을 때 404 와 함께 120×90 회색 이미지를 보내므로 크기로도 확인한다
    function check(){ if(img.naturalWidth<=120) swap(); }
    img.addEventListener('error',swap);
    img.addEventListener('load',check);
    if(img.complete) check();
  });
  // 시안: 실제 전송은 2단계(구글 폼/Apps Script)에서 연결
  document.getElementById('askForm').addEventListener('submit',function(e){
    e.preventDefault();
    var t=document.getElementById('askq'); if(!t.value.trim()){ t.focus(); return; }
    t.value=''; document.getElementById('askDone').style.display='block';
  });
})();

// 쇼츠 갤러리 (2026-11-24): 시리즈 탭 · 가로 넘기기 · 미리보기 창(공개 = 유튜브 재생, 공개 예정 = 장면 + '공개 예정')
(function(){
  var root=document.getElementById('shorts'); if(!root) return;
  var tabs=[].slice.call(root.querySelectorAll('[role="tab"]'));
  function pick(t, focus){
    tabs.forEach(function(x){
      var on=x===t, p=document.getElementById(x.getAttribute('aria-controls'));
      x.setAttribute('aria-selected', on?'true':'false'); x.tabIndex=on?0:-1;
      if(p) p.hidden=!on;
    });
    if(focus) t.focus();
  }
  tabs.forEach(function(t,i){
    t.addEventListener('click',function(){ pick(t); });
    t.addEventListener('keydown',function(e){
      var j={ArrowRight:i+1,ArrowLeft:i-1,Home:0,End:tabs.length-1}[e.key];
      if(j===undefined) return;
      e.preventDefault(); pick(tabs[(j+tabs.length)%tabs.length], true);
    });
  });
  root.querySelectorAll('.sg-sb').forEach(function(b){
    b.addEventListener('click',function(){
      var r=b.closest('.sg-panel').querySelector('.sg-rail');
      r.scrollBy({left:(+b.dataset.dir)*r.clientWidth*0.85, behavior:'smooth'});
    });
  });

  var dlg=document.getElementById('sgModal');
  if(!dlg || typeof dlg.showModal!=='function') return;  // 옛 브라우저: 공개 카드는 유튜브로 바로 이동
  var $=function(id){ return document.getElementById(id); };
  var stage=$('sgStage'), list=[], idx=0, opener=null, series='';

  function show(i){
    idx=i; var c=list[i], d=c.dataset, soon=!!d.soon;
    dlg.classList.toggle('is-soon', soon);
    stage.innerHTML='';
    if(!soon){
      var f=document.createElement('iframe');
      f.src='https://www.youtube.com/embed/'+encodeURIComponent(d.id)+'?autoplay=1&playsinline=1&rel=0';
      f.title=d.title; f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';
      f.allowFullscreen=true; f.referrerPolicy='strict-origin-when-cross-origin';
      stage.appendChild(f);
    }else{
      if(d.img){ var im=document.createElement('img'); im.src=d.img; im.alt=d.title+' 미리보기 장면'; stage.appendChild(im); }
      else { var bl=document.createElement('span'); bl.className='sg-blank'; bl.textContent=d.ep; stage.appendChild(bl); }
      var s=document.createElement('span'); s.className='sg-soon'; var st=c.querySelector('.sg-state'); s.textContent=st?st.textContent:'공개 예정'; stage.appendChild(s);
    }
    $('sgEp').textContent=d.ep; $('sgSeries').textContent=series;
    $('sgTitle').textContent=d.title; $('sgWhen').textContent=d.when;
    $('sgHost').textContent=d.host ? '진행 '+d.host+' · AI 캐릭터' : '';
    var yt=$('sgYt'); yt.hidden=soon; if(!soon) yt.href='https://youtube.com/shorts/'+d.id;
    $('sgPrev').disabled=i===0; $('sgNext').disabled=i===list.length-1;
    $('sgPos').textContent=(i+1)+' / '+list.length;
  }
  function open(card){
    var p=card.closest('.sg-panel');
    list=[].slice.call(p.querySelectorAll('.sg-card')); series=p.dataset.series||'';
    dlg.style.setProperty('--acc', p.style.getPropertyValue('--acc'));
    opener=card; show(list.indexOf(card));
    document.documentElement.classList.add('sg-lock');
    dlg.showModal(); $('sgClose').focus();
  }
  function step(n){ var j=idx+n; if(j>=0 && j<list.length) show(j); }
  root.addEventListener('click',function(e){
    var c=e.target.closest('.sg-card'); if(!c) return;
    if(e.ctrlKey||e.metaKey||e.shiftKey||e.button===1) return;  // 새 탭으로 열기는 그대로
    e.preventDefault(); open(c);
  });
  $('sgClose').addEventListener('click',function(){ dlg.close(); });
  $('sgPrev').addEventListener('click',function(){ step(-1); });
  $('sgNext').addEventListener('click',function(){ step(1); });
  dlg.addEventListener('click',function(e){ if(e.target===dlg || e.target.classList.contains('sg-wrap')) dlg.close(); });  // 바깥 누르면 닫기
  dlg.addEventListener('keydown',function(e){
    if(e.key==='ArrowLeft'){ e.preventDefault(); step(-1); }
    else if(e.key==='ArrowRight'){ e.preventDefault(); step(1); }
  });
  dlg.addEventListener('close',function(){   // Esc 도 여기로 온다
    stage.innerHTML='';                       // 영상 멈추기
    document.documentElement.classList.remove('sg-lock');
    var c=list[idx]||opener; if(c){ c.focus({preventScroll:true}); c.scrollIntoView({block:'nearest',inline:'nearest'}); }
  });
  var x0=null, y0=0;                          // 휴대폰: 좌우로 밀어 넘기기 (영상 위는 유튜브가 받음)
  dlg.addEventListener('touchstart',function(e){ x0=e.touches[0].clientX; y0=e.touches[0].clientY; },{passive:true});
  dlg.addEventListener('touchend',function(e){
    if(x0===null) return;
    var dx=e.changedTouches[0].clientX-x0, dy=e.changedTouches[0].clientY-y0; x0=null;
    if(Math.abs(dx)>50 && Math.abs(dx)>Math.abs(dy)*1.5) step(dx<0?1:-1);
  },{passive:true});
})();
