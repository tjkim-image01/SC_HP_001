"""바이블캐스트톡 「전체 답」 페이지 — qna/QNNN.html + qna/index.html (2026-11-25)

대표님 (2026-11-25): Q51 부터 쇼츠 끝 문장이 "전체 답은 스튜디오 교회 홈페이지에 있어요" → "질문마다 전체 답 페이지를 만들어 주세요".
원고: STUDIO_C/05_SNS/카페_바이블캐스트톡/QNNN_*.md (카페 글과 같은 원고, 지침 03_시리즈/바이블캐스트톡_100/기획/전체답_작성지침_v1.md).
쇼츠 공개 시각(예약 md 의 날짜 20:00, 없으면 Q17 = 2026-11-05 부터 매일 20:00)이 지난 회차만 페이지를 만든다 —
공개 전 원고는 저장소에 올리지 않는다(만들어 둔 페이지가 있으면 지움). build_site.py 가 부르고, 자동 갱신 작업이 날마다 하나씩 연다.
성경 장절(개역한글 책 이름 전체)은 성경 읽기 페이지(bible/#krv/책/장/절)로 잇는다.
"""
import datetime as dt
import html
import re
from pathlib import Path

BOOKS = ("창세기 출애굽기 레위기 민수기 신명기 여호수아 사사기 룻기 사무엘상 사무엘하 열왕기상 열왕기하 역대상 역대하 에스라 느헤미야 에스더 욥기 시편 잠언 "
         "전도서 아가 이사야 예레미야 예레미야애가 에스겔 다니엘 호세아 요엘 아모스 오바댜 요나 미가 나훔 하박국 스바냐 학개 스가랴 말라기 "
         "마태복음 마가복음 누가복음 요한복음 사도행전 로마서 고린도전서 고린도후서 갈라디아서 에베소서 빌립보서 골로새서 데살로니가전서 데살로니가후서 "
         "디모데전서 디모데후서 디도서 빌레몬서 히브리서 야고보서 베드로전서 베드로후서 요한일서 요한이서 요한삼서 유다서 요한계시록").split()
BOOKNO = {b: i + 1 for i, b in enumerate(BOOKS)}
# 긴 이름부터 (예레미야애가 > 예레미야, 요한일서 > 요한…)
REF = re.compile(r"(" + "|".join(sorted(map(re.escape, BOOKS), key=len, reverse=True)) + r")\s?(\d+)(?:편|장)?\s?:\s?(\d+)")
Q17 = dt.datetime(2026, 11, 5, 20, 0)


def esc(s):
    return html.escape(str(s), quote=True)


def inline(t: str) -> str:
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(https?://[^\s<)]+)", r'<a href="\1">\1</a>', t)

    def ref(m):
        b, c, v = m.group(1), int(m.group(2)), int(m.group(3))
        return f'<a class="ref" href="../bible/#krv/{BOOKNO[b]}/{c}/{v}">{m.group(0)}</a>'
    # 이미 만든 <a …>…</a> 안은 건드리지 않음
    parts = re.split(r"(<a [^>]*>.*?</a>)", t)
    return "".join(p if p.startswith("<a ") else REF.sub(ref, p) for p in parts)


def md_to_html(body: str) -> str:
    out, lst = [], None
    for line in body.split("\n"):
        s = line.strip()
        if lst and not re.match(r"^(- |\d+\. )", s):
            out.append(f"</{lst}>"); lst = None
        if not s:
            continue
        if s.startswith("## "):
            out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.startswith("> "):
            out.append(f'<blockquote class="short">{inline(s[2:])}</blockquote>')
        elif s.startswith("- "):
            if lst != "ul":
                out.append("<ul>"); lst = "ul"
            out.append(f"<li>{inline(s[2:])}</li>")
        elif re.match(r"^\d+\. ", s):
            if lst != "ol":
                out.append("<ol>"); lst = "ol"
            out.append(f"<li>{inline(re.sub(r'^\d+\. ', '', s))}</li>")
        else:
            out.append(f"<p>{inline(s)}</p>")
    if lst:
        out.append(f"</{lst}>")
    return "\n".join(out)


def parse(p: Path) -> dict:
    raw = re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8"), flags=re.S).strip()
    lines = raw.split("\n")
    m = re.match(r"\[바이블캐스트톡 Q\.(\d+)\]\s*(.+)", lines[0].strip())
    no, title = int(m.group(1)), m.group(2).strip()
    rest = lines[1:]
    intro = rest[0].strip() if rest and not rest[0].startswith("#") else ""
    rest = rest[1:] if intro else rest
    # 본문 = 첫 ## 부터 ▶ 줄 앞까지. ▶ 줄·해시태그·'댓글' 안내는 페이지 아래에서 따로
    body, tail = [], []
    for ln in rest:
        (tail if ln.strip().startswith(("▶", "◀", "💬", "#", "성경 본문은")) and not ln.startswith("## ") else body).append(ln)
    short = next((l.strip()[2:] for l in body if l.strip().startswith("> ")), "")
    shorts_url = next((re.search(r"https://youtube\.com/shorts/[\w-]{11}", l).group(0) for l in tail if "쇼츠 보기" in l and "youtube.com/shorts/" in l), None)
    return dict(no=no, title=title, intro=intro, body="\n".join(body), short=short, shorts=shorts_url, file=p.name)


HEAD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<link rel="icon" href="../assets/img/logo_white.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="../assets/css/site.css">
<link rel="stylesheet" href="qna.css?v=1">
<script>try{{if(localStorage.getItem('sc_theme')==='light')document.documentElement.setAttribute('data-theme','light');}}catch(e){{}}</script>
</head>
<body class="qna-page">
<a class="skip" href="#main">본문 바로가기</a>
<header>
  <div class="wrap bar">
    <a class="brand" href="../" aria-label="STUDIO.C 홈"><img src="../assets/img/logo_white.png" alt=""><span>STUDIO<b>.</b>C</span></a>
    <nav class="main" aria-label="주 메뉴">
      <a href="../">오늘</a><a href="../#shorts">쇼츠</a><a href="./" aria-current="page">질문 100</a><a href="../#word">말씀</a><a href="../bible/">성경</a><a href="../#toon">웹툰</a><a href="../#meet">교회</a>
    </nav>
    <div class="tools"><button class="btn icon" type="button" id="theme" aria-label="밝게 보기"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button></div>
  </div>
</header>
<main id="main" class="wrap qna">
"""
FOOT = """</main>
<footer class="wrap qna-foot"><p>STUDIO.C 스튜디오 교회 · 성경 본문은 개역한글판을 따릅니다 · 진행자 조아름은 AI로 만든 캐릭터입니다</p></footer>
<script>(function(){var b=document.getElementById('theme');if(!b)return;b.addEventListener('click',function(){var r=document.documentElement,l=r.getAttribute('data-theme')==='light';if(l){r.removeAttribute('data-theme');}else{r.setAttribute('data-theme','light');}try{localStorage.setItem('sc_theme',l?'dark':'light');}catch(e){}});})();</script>
</body>
</html>
"""
CSS = """.qna{max-width:760px;padding-top:28px;padding-bottom:48px}
.qna .crumb{font:500 14px/1.4 var(--sans);color:var(--muted);margin:0 0 10px}
.qna .crumb a{color:var(--muted)}
.qna h1{font:700 clamp(26px,5vw,36px)/1.35 'Noto Serif KR',serif;margin:6px 0 12px}
.qna .badge{display:inline-block;font:700 13px/1 var(--sans);padding:6px 10px;border-radius:999px;background:var(--light-soft);color:var(--light)}
.qna .intro{color:var(--muted);margin:0 0 18px}
.qna h2{font:700 21px/1.4 var(--sans);margin:34px 0 10px;padding-top:14px;border-top:1px solid var(--line)}
.qna blockquote.short{margin:10px 0;padding:16px 18px;border-left:4px solid var(--light);background:var(--surface);border-radius:0 12px 12px 0;font-size:18px}
.qna p{margin:10px 0}
.qna ul,.qna ol{padding-left:22px}
.qna li{margin:6px 0}
.qna a.ref{color:var(--light);text-decoration:underline;text-underline-offset:3px}
.qna .actions{display:flex;flex-wrap:wrap;gap:10px;margin:30px 0 0}
.qna .nextprev{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:22px}
.qna .nextprev a{display:block;padding:14px 16px;border:1px solid var(--line);border-radius:12px;color:var(--ink);text-decoration:none;background:var(--surface)}
.qna .nextprev small{display:block;color:var(--muted);font-size:13px}
.qna .nextprev .next{text-align:right}
.qna-list{list-style:none;padding:0;margin:18px 0}
.qna-list li{margin:0;border-bottom:1px solid var(--line)}
.qna-list a{display:flex;gap:14px;align-items:baseline;padding:14px 4px;color:var(--ink);text-decoration:none}
.qna-list a:hover{background:var(--surface)}
.qna-list .n{flex:0 0 58px;font:700 14px/1 var(--sans);color:var(--light)}
.qna-list .soon{color:var(--muted)}
.qna-foot{color:var(--muted);font-size:13px;padding-bottom:40px}
@media (max-width:520px){.qna .nextprev{grid-template-columns:1fr}.qna .nextprev .next{text-align:left}}
"""


def page(a: dict, prev: dict | None, nxt: dict | None, cafe: str) -> str:
    title = f"Q.{a['no']} {a['title']} · 바이블캐스트톡 전체 답 · STUDIO.C"
    acts = []
    if a["shorts"]:
        acts.append(f'<a class="btn primary" href="{esc(a["shorts"])}">쇼츠로 보기</a>')
    acts.append(f'<a class="btn" href="../bible/">성경 읽기</a><a class="btn" href="{esc(cafe)}">카페에서 질문 남기기</a>')
    np_ = ['<nav class="nextprev" aria-label="이전·다음 질문">']
    np_.append(f'<a href="Q{prev["no"]:03d}.html"><small>← 이전 질문 Q.{prev["no"]}</small>{esc(prev["title"])}</a>' if prev else "<span></span>")
    np_.append(f'<a class="next" href="Q{nxt["no"]:03d}.html"><small>다음 질문 Q.{nxt["no"]} →</small>{esc(nxt["title"])}</a>' if nxt else "<span></span>")
    np_.append("</nav>")
    return (HEAD.format(title=esc(title), desc=esc(a["short"][:150] or a["title"])) +
            f'<p class="crumb"><a href="./">바이블캐스트톡 · 기독교인이 궁금한 100가지</a></p>'
            f'<span class="badge">Q.{a["no"]} / 100</span><h1>{esc(a["title"])}</h1>' +
            (f'<p class="intro">{inline(a["intro"])}</p>' if a["intro"] else "") +
            md_to_html(a["body"]) +
            f'<div class="actions">{"".join(acts)}</div>' + "".join(np_) + FOOT)


def index(pub: list[dict], soon: list[tuple[int, str, dt.datetime]]) -> str:
    li = "".join(f'<li><a href="Q{a["no"]:03d}.html"><span class="n">Q.{a["no"]}</span><span>{esc(a["title"])}</span></a></li>' for a in reversed(pub))
    up = "".join(f'<li><a aria-disabled="true"><span class="n">Q.{n}</span><span class="soon">{esc(t)} · {w.month}/{w.day} 저녁 8시 공개</span></a></li>' for n, t, w in soon)
    return (HEAD.format(title="바이블캐스트톡 전체 답 · 기독교인이 궁금한 100가지 · STUDIO.C",
                        desc="기독교인이 궁금한 100가지 질문에 대한 스튜디오 교회의 전체 답. 쇼츠는 매일 저녁 8시.") +
            '<span class="badge">바이블캐스트톡</span><h1>기독교인이 궁금한 100가지 · 전체 답</h1>'
            f'<p class="intro">쇼츠로 짧게 듣고, 여기서 성경 구절과 함께 더 깊이 읽어 보세요. 지금 {len(pub)}개의 답이 열려 있어요. 쇼츠가 공개되는 날 저녁 8시에 하나씩 더 열립니다.</p>'
            + (f'<h2>곧 열리는 질문</h2><ul class="qna-list">{up}</ul>' if up else "")
            + f'<h2>열린 답 (최신순)</h2><ul class="qna-list">{li}</ul>' + FOOT)


def build(root: Path, sc: Path, bct_eps: list[dict], now: dt.datetime, cafe: str) -> dict[int, str]:
    """공개된 회차 번호 → 페이지 상대경로 (qna/QNNN.html)"""
    src = sc / "05_SNS" / "카페_바이블캐스트톡"
    when = {e["no"]: e["when"] for e in bct_eps if e.get("when")}
    ans = sorted((parse(p) for p in src.glob("Q[0-9][0-9][0-9]_*.md")), key=lambda a: a["no"])
    for a in ans:
        a["when"] = when.get(a["no"]) or (Q17 + dt.timedelta(days=a["no"] - 17) if a["no"] >= 17 else Q17)
        if not a["shorts"]:
            vid = next((e.get("id") for e in bct_eps if e["no"] == a["no"] and e.get("id")), None)
            a["shorts"] = f"https://youtube.com/shorts/{vid}" if vid and a["when"] <= now else None
    pub = [a for a in ans if a["when"] <= now]
    soon = [(a["no"], a["title"], a["when"]) for a in ans if a["when"] > now][:3]
    out = root / "qna"
    out.mkdir(exist_ok=True)
    (out / "qna.css").write_text(CSS, encoding="utf-8")
    keep = {"index.html", "qna.css"}
    for i, a in enumerate(pub):
        name = f"Q{a['no']:03d}.html"
        keep.add(name)
        (out / name).write_text(page(a, pub[i - 1] if i else None, pub[i + 1] if i + 1 < len(pub) else None, cafe), encoding="utf-8")
    for f in out.glob("Q*.html"):
        if f.name not in keep:
            f.unlink()   # 공개 시각이 미뤄진 회차 등 — 공개 전 원고는 올리지 않음
    (out / "index.html").write_text(index(pub, soon), encoding="utf-8")
    print(f"  전체 답: 원고 {len(ans)}편 · 공개 {len(pub)}편 (Q.{pub[0]['no']}~Q.{pub[-1]['no']})" if pub else f"  전체 답: 원고 {len(ans)}편 · 공개 0")
    return {a["no"]: f"qna/Q{a['no']:03d}.html" for a in pub}
