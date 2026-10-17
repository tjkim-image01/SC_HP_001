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
