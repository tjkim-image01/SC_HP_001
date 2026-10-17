"""STUDIO.C 홈페이지 빌드 — STUDIO_C 콘텐츠 폴더와 웹툰 데이터를 읽어 index.html 을 만든다.

사용:  python build/build_site.py            (지금 시각 기준)
       python build/build_site.py --now "2026-10-23 20:05"   (그 시각 기준으로 미리 보기)

읽는 곳 (build/config.json 의 paths):
  - 주보: STUDIO_C/05_SNS/카페_주보/NN주_*.md  + 01_주보/<연도>/<월>/cover/cover_week_NN_v*.png
  - 업로드 일정: STUDIO_C/05_SNS/업로드일정.md  (트렌드 쇼츠 · 바이블캐스트톡 표 — 유튜브 ID·공개 시각)
  - 질문 목록: STUDIO_C/03_시리즈/바이블캐스트톡_100/질문목록_v1.md (첫 10문항)
  - 답변: content/qna/QNNN.json (홈페이지 쪽에서 관리)
  - 웹툰: webtoon2 p001/web/data.js (퓨어데이) · s001/web/episodes_data.js (여호수아) — 그림은 각 사이트 주소에서 불러온다

지키는 것: 성도 이름은 싣지 않는다(교회 연락처만). 주보 PDF 는 이름이 들어 있어 링크하지 않는다.
유튜브 공개 시각 전에는 영상 링크를 '공개 예정'으로만 보여 준다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
WEEKDAYS = "월화수목금토일"


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def md_date(d: dt.datetime) -> str:
    return f"{d.month}/{d.day}({WEEKDAYS[d.weekday()]})"


# ---------------------------------------------------------------- 읽기

def read_bulletins(sc: Path) -> list[dict]:
    """카페 주보 원고 md 에서 주차별 정보를 읽는다."""
    out = []
    for f in sorted((sc / "05_SNS" / "카페_주보").glob("*주_*.md")):
        m = re.match(r"(\d+)주_", f.name)
        if not m:
            continue
        t = f.read_text(encoding="utf-8")
        week = int(m.group(1))
        dm = re.search(r"(\d{4})년 (\d{1,2})월 (\d{1,2})일", t)
        if not dm:
            continue
        date = dt.date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
        b = {"week": week, "date": date, "file": f}
        lm = re.search(r"\*\*(.+?주일[^*]*)\*\*", t)
        b["liturgical"] = lm.group(1).strip() if lm else ""
        pm = re.search(r"\*\*본문\*\*\s*(.+?)\s{2,}\*\*찬송\*\*\s*(.+)", t)
        b["passage"], b["hymn"] = (pm.group(1).strip(), pm.group(2).strip()) if pm else ("", "")
        sm = re.search(r"\*\*설교\*\*\s*「(.+?)」", t)
        b["sermon"] = sm.group(1) if sm else ""
        fm = re.search(r"## 말씀의 흐름\s*\n+(.+)", t)
        b["flow"] = [x.strip() for x in fm.group(1).split("→")] if fm else []
        mm = re.search(r"## 묵상\s*\n+(.+?)(?:\n\s*\n|\Z)", t, re.S)
        b["meditation"] = mm.group(1).strip() if mm else ""
        covers = sorted((sc / "01_주보" / str(date.year) / f"{date.month:02d}" / "cover").glob(f"cover_week_{week:02d}_v*.png"),
                        key=lambda p: int(re.search(r"_v(\d+)", p.stem).group(1)))
        b["cover"] = covers[-1] if covers else None
        out.append(b)
    return sorted(out, key=lambda b: b["date"])


def md_table(text: str, heading_re: str) -> list[list[str]]:
    """제목(정규식) 아래 첫 표의 데이터 행을 칸 목록으로 돌려준다."""
    m = re.search(heading_re + r".*?\n(\|.+?)(?:\n\s*\n|\n#|\Z)", text, re.S)
    if not m:
        return []
    rows = [r for r in m.group(1).splitlines() if r.startswith("|")]
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    return [c for c in cells[2:] if c]  # 머리줄·구분줄 제외


def yt_id(cell: str) -> str | None:
    m = re.search(r"\[([A-Za-z0-9_-]{11})\]\(https://youtube\.com/shorts/", cell)
    return m.group(1) if m else None


def parse_when(cell: str) -> dt.datetime | None:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})", cell)
    return dt.datetime(*map(int, m.groups())) if m else None


def read_schedule(sc: Path) -> tuple[list[dict], list[dict]]:
    t = (sc / "05_SNS" / "업로드일정.md").read_text(encoding="utf-8")
    trend, last_dir = [], None
    for c in md_table(t, r"## 쇼츠 · 『한국 교회 트렌드 2027』"):
        if len(c) < 5:
            continue
        when, vid = parse_when(c[1]), yt_id(c[4])
        if not when or not vid:
            continue
        cm = re.match(r"(\d+)\s+(.+?)\s+(\d+)편\s+「(.+?)」", c[2])
        f = c[3].split(" ")[0]
        if f.startswith("…/") and last_dir:
            f = last_dir + f[1:]
        elif "/" in f:
            last_dir = f.rsplit("/result/", 1)[0] if "/result/" in f else f.rsplit("/", 1)[0]
        trend.append({"when": when, "id": vid, "chapter": cm.group(1) if cm else "", "chapter_title": cm.group(2) if cm else "",
                      "ep": cm.group(3) if cm else "", "title": cm.group(4) if cm else c[2], "mp4": sc / f if f.endswith(".mp4") else None})
    bct = []
    for c in md_table(t, r"## 매주 금요일 20:00 · 바이블캐스트톡"):
        if len(c) < 5 or not c[0].isdigit():
            continue
        f = c[3].split(" ")[0]
        bct.append({"no": int(c[0]), "when": parse_when(c[1] + " 20:00") if parse_when(c[1]) is None else parse_when(c[1]),
                    "question": c[2], "id": yt_id(c[4]), "mp4": sc / f if f.endswith(".mp4") else None})
    return trend, bct


def read_first_questions(sc: Path, rel: str) -> list[dict]:
    t = (sc / rel).read_text(encoding="utf-8")
    out = []
    for c in md_table(t, r"## 첫 10문항"):
        if c and c[0].isdigit():
            out.append({"no": int(c[0]), "question": c[1], "category": c[2]})
    return out


def read_js_objects(path: Path) -> dict:
    """`window.X = {...};` 꼴의 JS 파일에서 객체들을 꺼낸다."""
    t = path.read_text(encoding="utf-8")
    dec, out = json.JSONDecoder(), {}
    for m in re.finditer(r"window\.(\w+)\s*=\s*", t):
        obj, _ = dec.raw_decode(t, m.end())
        out[m.group(1)] = obj
    return out


# ---------------------------------------------------------------- 그림

def frame(mp4: Path | None, out: Path, sec: float, ffmpeg: str) -> bool:
    """유튜브 썸네일이 아직 없을 때 쓸 장면을 mp4 에서 뽑는다 (이미 있으면 그대로)."""
    if out.exists():
        return True
    if not mp4 or not mp4.exists() or not shutil.which(ffmpeg):
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([ffmpeg, "-loglevel", "error", "-y", "-ss", str(sec), "-i", str(mp4), "-frames:v", "1",
                        "-vf", "scale=360:-2", "-q:v", "4", str(out)], capture_output=True)
    return r.returncode == 0 and out.exists()


def cover_jpg(src: Path | None, out: Path) -> bool:
    if not src or not src.exists():
        return False
    if out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
        return True
    from PIL import Image  # 표지만 쓰므로 필요할 때 불러온다
    out.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    im.thumbnail((700, 900))
    im.save(out, quality=86)
    return True


def yt_img(vid: str, fallback: str | None, alt: str = "") -> str:
    fb = f' data-fallback="{esc(fallback)}"' if fallback else ""
    return f'<img src="https://i.ytimg.com/vi/{esc(vid)}/oar2.jpg"{fb} alt="{esc(alt)}" loading="lazy">'


# ---------------------------------------------------------------- 구역

def sec_strip(b: dict | None) -> str:
    if not b:
        return ""
    d = b["date"]
    return (f'<div class="strip"><div class="wrap"><span><span class="dot"></span><strong>{esc(b["liturgical"])}</strong></span>'
            f'<span>{d.year}년 {d.month}월 {d.day}일 · {esc(b["passage"])}</span><a href="#sunday">이번 주 주보 ›</a></div></div>')


def sec_sunday(b: dict | None, cover_rel: str | None, cafe_url: str | None) -> str:
    if not b:
        return ""
    img = f'<img src="{esc(cover_rel)}" alt="{b["week"]}주 주보 표지 수채화">' if cover_rel else ""
    links = []
    if cafe_url:
        links.append(f'<a href="{esc(cafe_url)}">주보 보기</a>')
    links.append('<a href="#word">말씀의 흐름</a>')
    links.append('<a href="#meet">오시는 길</a>')
    return (f'<article class="card sunday" aria-label="이번 주일 예배">{img}<div>'
            f'<p class="wk">이번 주일 · {b["date"].year}년 {b["week"]}주</p><h3>{esc(b["sermon"])}</h3>'
            f'<dl><dt>본문</dt><dd>{esc(b["passage"])}</dd><dt>찬송</dt><dd>{esc(b["hymn"])}</dd><dt>예배</dt><dd>주일 오전 10:30</dd></dl>'
            f'<div class="links">{"".join(links)}</div></div></article>')


def sec_word(b: dict | None, pastor: str) -> str:
    if not b:
        return ""
    flow = "".join(f"<li>{esc(x)}</li>" for x in b["flow"])
    return f'''<section class="paper" id="word" aria-labelledby="h-word">
    <div class="wrap">
      <div class="head"><div>
        <p class="eyebrow">이번 주 말씀 · 매일성경 주일 본문</p>
        <h2 id="h-word">{esc(b["sermon"])}</h2>
        <p class="lead">{esc(b["passage"])} · {esc(pastor)} 담임목사</p>
      </div></div>
      <div class="word">
        <div class="card flow"><h3>말씀의 흐름</h3><ol>{flow}</ol></div>
        <div class="card medi"><h3>묵상</h3><p>{esc(b["meditation"])}</p></div>
      </div>
    </div>
  </section>'''


def sec_trend(items: list[dict], now: dt.datetime) -> str:
    pub = [x for x in items if x["when"] <= now]
    up = [x for x in items if x["when"] > now]
    show = (pub[-3:] + up[:1]) if pub else up[:4]
    show = show[-4:]
    if not show:
        return '<p class="lead">곧 첫 영상이 올라옵니다.</p>'
    cards = []
    for x in show:
        if x["when"] <= now:
            badge = '<span class="badge">오늘 공개</span>' if x["when"].date() == now.date() else ""
            href = f'https://youtube.com/shorts/{x["id"]}'
        else:
            badge = f'<span class="badge soon">{md_date(x["when"])} {x["when"]:%H:%M}</span>'
            href = "#trend"
        cards.append(f'<a class="short" href="{href}"><div class="thumb">{yt_img(x["id"], x.get("fallback"))}{badge}'
                     f'<span class="play">쇼츠</span></div><h3>{esc(x["title"])}</h3>'
                     f'<p>{esc(x["chapter"])} {esc(x["chapter_title"])} · {esc(x["ep"])}편</p></a>')
    return f'<div class="rail">{"".join(cards)}</div>'


def sec_qna(bct: list[dict], firsts: list[dict], now: dt.datetime, cafe: str) -> str:
    if not bct:
        return ""
    pub = [q for q in bct if q["when"] and q["when"] <= now]
    cur = pub[-1] if pub else bct[0]
    released = cur["when"] <= now
    ans_f = ROOT / "content" / "qna" / f"Q{cur['no']:03d}.json"
    a = json.loads(ans_f.read_text(encoding="utf-8")) if ans_f.exists() else None
    tag = "" if released else f'<span class="tag">{md_date(cur["when"])} {cur["when"]:%H:%M} 공개</span>'
    href = f'https://youtube.com/shorts/{cur["id"]}' if cur["id"] else cafe
    thumb = ""
    if cur["id"]:
        thumb = (f'<a class="yt-big" href="{href}" aria-label="유튜브 쇼츠로 보기: {esc(cur["question"])}">'
                 f'{yt_img(cur["id"], cur.get("fallback"), "바이블캐스트톡 진행자 조아름")}'
                 f'<span class="yt-play" aria-hidden="true"></span>'
                 f'<span class="yt-label">영상으로 보기{(" · " + esc(a["duration"])) if a and a.get("duration") else ""}</span></a>')
    asked = a["asked"] if a else cur["question"]
    cat = a["category"] if a else ""
    host = esc(a.get("host", "조아름")) if a else "조아름"
    parts = [f'<article class="card thread" aria-label="이번 주 답변"><div class="thread-head"><h3>이번 주 답변</h3>'
             f'<span><span class="qbadge">Q.{cur["no"]} / 100</span> {tag}</span></div>',
             f'<div class="thread-top">{thumb}<div class="top-side"><div class="bubble q"><small>성도 질문{(" · " + esc(cat)) if cat else ""}</small>{esc(asked)}</div>'
             f'<p class="host">진행 <b>{host}</b> · 바이블캐스트톡<br>쇼츠로 먼저 들어 보세요</p></div></div>']
    if a:
        parts.append(f'<div class="who"><img src="assets/img/logo_white.png" alt=""><b>STUDIO.C</b> · {esc(a["answer_by"])} 답변</div>'
                     f'<div class="bubble a"><p class="big">{esc(a["conclusion"])}</p><p>{esc(a["body"])}</p>'
                     f'<blockquote class="verse">{esc(a["verse"])}<cite>{esc(a["verse_ref"])}</cite></blockquote>'
                     f'<div class="todo"><b>오늘 할 일</b> · {esc(a["today"])}</div></div>')
    else:
        parts.append('<div class="bubble a"><p class="big">답변을 준비하고 있어요.</p></div>')
    parts.append(f'<div class="a-actions"><a class="btn" href="{esc(cafe)}">카페에서 이야기 나누기</a></div>')
    # 다음에 답할 질문: 일정표에 날짜가 있으면 그 날짜, 없으면 첫 회부터 매주 금요일로 계산
    sched = {q["no"]: q for q in bct}
    base = bct[0]["when"] - dt.timedelta(days=7 * (bct[0]["no"] - 1))
    nxt = [q for q in firsts if q["no"] > cur["no"]][:3]
    if nxt:
        li = []
        for q in nxt:
            when = sched.get(q["no"], {}).get("when") or base + dt.timedelta(days=7 * (q["no"] - 1))
            li.append(f'<li>{esc(q["question"])} <span>Q.{q["no"]} · {md_date(when)}</span></li>')
        parts.append(f'<div class="pending"><h4>다음에 답할 질문</h4><ol>{"".join(li)}</ol></div>')
    parts.append("</article>")
    return "".join(parts)


def next_release(now: dt.datetime, weekday: int, hour: int) -> dt.datetime:
    d = now.replace(hour=hour, minute=0, second=0, microsecond=0) + dt.timedelta(days=(weekday - now.weekday()) % 7)
    return d if d > now else d + dt.timedelta(days=7)


def sec_toons(cfg: dict, now: dt.datetime) -> str:
    w, p = cfg["webtoon"], cfg["paths"]
    cards = []
    try:
        portal = read_js_objects(Path(p["pureday_data"]))["PORTAL"]
        s = next(x for x in portal["series"] if x.get("id") == "pureday")
        eps = sorted(s["episodes"], key=lambda e: e["num"])
        last = eps[-1]
        pw = w["pureday"]
        nr = next_release(now, 5, 10)  # 토요일 10:00
        nxt = f' · 다음 {last["num"] + 1}화 「{esc(pw["next_title"])}」 {md_date(nr)} 10:00' if pw.get("next_title") else ""
        cards.append(f'<a class="card toon" href="{esc(pw["url"])}"><div class="cv"><img src="{esc(pw["img_base"] + s["cover"])}" alt="퓨어데이 표지" loading="lazy"></div><div>'
                     f'<div class="state"><span class="tag new">최신 {last["num"]}화</span><span class="tag">연재 중</span><span class="tag ai">AI 활용</span></div>'
                     f'<h3>{esc(pw["title"])} · {esc(pw["season_title"])}</h3><p class="en">{esc(pw["en"])}</p>'
                     f'<p>{last["num"]}화 「{esc(last["title"])}」{nxt}</p><span class="go">이어 보기 ›</span></div></a>')
    except Exception as e:  # 웹툰 데이터가 없어도 나머지는 만든다
        print(f"  ! 퓨어데이 데이터 읽기 실패: {e}", file=sys.stderr)
    try:
        js = read_js_objects(Path(p["joshua_data"]))
        info, eps = js["SERIES_INFO"], js["EPISODES"]
        jw = w["joshua"]
        thumb = eps["1"]["thumb"]
        done = info.get("totalEpisodes", len(eps))
        cards.append(f'<a class="card toon" href="{esc(jw["url"])}"><div class="cv"><img src="{esc(jw["img_base"] + thumb)}" alt="여호수아 1화" loading="lazy"></div><div>'
                     f'<div class="state"><span class="tag">시즌1 {done}화 완결</span><span class="tag ai">AI 활용</span></div>'
                     f'<h3>{esc(jw["title"])}</h3><p class="en">{esc(jw["en"])}</p><p>{esc(jw["blurb"])}</p><span class="go">1화부터 정주행 ›</span></div></a>')
    except Exception as e:
        print(f"  ! 여호수아 데이터 읽기 실패: {e}", file=sys.stderr)
    return f'<div class="toons">{"".join(cards)}</div>'


def sec_gallery(g: dict) -> str:
    """갓페인터 뮤지움(크리스찬 갤러리) 바로가기. 주소가 비어 있으면 '연결 준비 중'으로 둔다."""
    base = g.get("url", "").rstrip("/")
    def link(path: str = "") -> str:
        return f"{base}/{path}".rstrip("/") if base else "#gallery"
    soon = "" if base else '<span class="tag">주소 연결 준비 중</span>'
    ex = "".join(
        f'<a class="ex" href="{esc(link(e["path"]))}"><span class="ex-img"><img src="{esc(e["img"])}" alt="" loading="lazy"></span>'
        f'<span class="ex-t"><b>{esc(e["title"])}</b><small>{esc(e["year"])} · {esc(e["work"])}</small></span></a>'
        for e in g.get("exhibitions", []))
    return f'''<section class="museum" id="gallery" aria-labelledby="h-gallery">
    <div class="wrap">
      <div class="head"><div>
        <p class="eyebrow"><img src="assets/img/gallery/museum_icon.svg" alt="" width="20" height="20"> 크리스찬 갤러리</p>
        <h2 id="h-gallery">{esc(g["name"])} <span class="en">{esc(g["en"])}</span></h2>
        <p class="lead">{esc(g["desc"])}</p>
      </div>{soon}</div>
      <div class="museum-grid">
        <a class="museum-door" href="{esc(link())}" aria-label="{esc(g["name"])} 입장">
          <img src="assets/img/gallery/museum_og.jpg" alt="{esc(g["en"])} 대표 그림" loading="lazy">
          <span class="door-btn">갤러리 입장 ›</span>
        </a>
        <div class="ex-list">
          <p class="ex-head">지금 열린 전시</p>
          {ex}
        </div>
      </div>
    </div>
  </section>'''


def cafe_link_for_week(sc: Path, week: int) -> str | None:
    t = (sc / "05_SNS" / "업로드일정.md").read_text(encoding="utf-8")
    for c in md_table(t, r"## 주보 \(카페\)"):
        if c and c[0] == str(week):
            m = re.search(r"\((https://cafe\.naver\.com/[^)]+)\)", "|".join(c))
            return m.group(1) if m else None
    return None


# ---------------------------------------------------------------- 메인

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", help='기준 시각 "YYYY-MM-DD HH:MM" (미리 보기용)')
    args = ap.parse_args()
    now = dt.datetime.strptime(args.now, "%Y-%m-%d %H:%M") if args.now else dt.datetime.now().replace(second=0, microsecond=0)
    cfg = json.loads((BUILD / "config.json").read_text(encoding="utf-8"))
    sc = Path(cfg["paths"]["studio_c"])
    ff = cfg["paths"]["ffmpeg"]
    print(f"STUDIO.C 빌드 · 기준 {now:%Y-%m-%d %H:%M}")

    bulletins = read_bulletins(sc)
    b = next((x for x in bulletins if x["date"] >= now.date()), bulletins[-1] if bulletins else None)
    cover_rel = None
    if b and cover_jpg(b["cover"], ROOT / "assets" / "img" / "cover" / f"week_{b['date'].year}_{b['week']:02d}.jpg"):
        cover_rel = f"assets/img/cover/week_{b['date'].year}_{b['week']:02d}.jpg"
    print(f"  주보: {b['week']}주 {b['date']} 「{b['sermon']}」" if b else "  주보: 없음")

    trend, bct = read_schedule(sc)
    for x in trend + bct:
        if x.get("id"):
            out = ROOT / "assets" / "img" / "yt" / f"{x['id']}.jpg"
            if frame(x.get("mp4"), out, 5 if x in bct else 3, ff):
                x["fallback"] = f"assets/img/yt/{x['id']}.jpg"
    print(f"  트렌드 쇼츠 {len(trend)}편 · 바이블캐스트톡 {len(bct)}편")
    firsts = read_first_questions(sc, cfg["paths"]["bct_questions"])

    c, ch, lk = cfg["site"], cfg["church"], cfg["links"]
    rep = {
        "BUILD_INFO": f"빌드 {now:%Y-%m-%d %H:%M}",
        "TAGLINE": c["tagline_html"], "SUB": esc(c["sub"]), "OFFICIAL": esc(c["official"]), "PASTOR": esc(c["pastor"]),
        "STRIP": sec_strip(b),
        "SUNDAY": sec_sunday(b, cover_rel, cafe_link_for_week(sc, b["week"]) if b else None),
        "QNA_THREAD": sec_qna(bct, firsts, now, lk["cafe"]),
        "TREND_RAIL": sec_trend(trend, now),
        "WORD": sec_word(b, c["pastor"]),
        "TOONS": sec_toons(cfg, now),
        "GALLERY": sec_gallery(cfg["gallery"]),
        "PUREDAY_RELEASE": esc(cfg["webtoon"]["pureday"]["release"]),
        "PRAYER": "".join(f"<li>{esc(x)}</li>" for x in cfg["prayer_topics"]),
        "SERVE": "".join(f"<li>{esc(x)}</li>" for x in cfg["serve_gifts"]),
        "WORSHIP": esc(ch["worship"]), "PLACE": esc(ch["place"]), "ADDRESS1": esc(ch["address1"]), "ADDRESS2": esc(ch["address2"]),
        "PHONE": esc(ch["phone"]), "EMAIL": esc(ch["email"]), "MAP": esc(ch["map"]),
        "YOUTUBE": esc(lk["youtube"]), "YOUTUBE_SHORTS": esc(lk["youtube_shorts"]), "CAFE": esc(lk["cafe"]), "INSTAGRAM": esc(lk["instagram"]),
        "YEAR": str(now.year),
    }
    page = (BUILD / "templates" / "home.html").read_text(encoding="utf-8")
    for k, v in rep.items():
        page = page.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", page)
    if left:
        sys.exit(f"채우지 못한 자리: {left}")
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print(f"  → {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
