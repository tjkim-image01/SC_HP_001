# -*- coding: utf-8 -*-
"""성경 읽기 페이지(bible/) 데이터 만들기 — 2026-11-25

공개(퍼블릭 도메인) 성경 본문만 쓴다. 출처·저작권은 bible/SOURCES.md 에 적는다.
  krv    개역한글 (1961)            bolls.life KRV.zip
  kjv    King James Version (1769)  eBible.org eng-kjv (외경 제외, 66권)
  lut    Luther 1912                eBible.org deu1912
  rv1909 Reina-Valera 1909          eBible.org spaRV1909
  cuvs   和合本 简体 (新标点)        eBible.org cmn-cu89s
  cuvt   和合本 繁體 (新標點)        eBible.org cmn-cu89t
  synod  Синодальный перевод 1876   eBible.org russyn (러시아식 장·절 번호 그대로)
  kougo  口語訳 1955                api.getbible.net japkougo (빠진 장은 bolls.life JPKJV 에서 루비 지우고 보충)

쓰는 법 (Windows, venv 파이썬):
  set PYTHONUTF8=1
  python -I build/build_bible.py --download          # 원본을 build/_bible_src/ 에 받고 만든다
  python -I build/build_bible.py --src <원본 폴더>    # 이미 받은 원본으로 만든다
결과: bible/data/versions.json + bible/data/<판>/<책번호>.json  ({"c":[[1절,2절,…],…]}, 빈 문자열 = 앞 절에 합쳐진 절)
새 판을 넣으려면 VERSIONS 에 한 줄 + 읽는 함수만 더하면 된다 (페이지는 versions.json 을 읽어 목록을 만든다).
"""
import argparse, html, io, json, os, re, sys, urllib.request, zipfile, xml.etree.ElementTree as ET
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'bible', 'data')

# eBible XML 책 코드(SIL/UBS) → 1..66
UBS = ('GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB PSA PRO ECC SNG ISA JER LAM '
       'EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC MAL MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL '
       '1TH 2TH 1TI 2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV').split()
UBS_NO = {c: i + 1 for i, c in enumerate(UBS)}

NAMES = {
 'ko': '창세기 출애굽기 레위기 민수기 신명기 여호수아 사사기 룻기 사무엘상 사무엘하 열왕기상 열왕기하 역대상 역대하 에스라 느헤미야 에스더 욥기 시편 잠언 전도서 아가 이사야 예레미야 예레미야애가 에스겔 다니엘 호세아 요엘 아모스 오바댜 요나 미가 나훔 하박국 스바냐 학개 스가랴 말라기 마태복음 마가복음 누가복음 요한복음 사도행전 로마서 고린도전서 고린도후서 갈라디아서 에베소서 빌립보서 골로새서 데살로니가전서 데살로니가후서 디모데전서 디모데후서 디도서 빌레몬서 히브리서 야고보서 베드로전서 베드로후서 요한일서 요한이서 요한삼서 유다서 요한계시록',
 'ko_abbr': '창 출 레 민 신 수 삿 룻 삼상 삼하 왕상 왕하 대상 대하 스 느 에 욥 시 잠 전 아 사 렘 애 겔 단 호 욜 암 옵 욘 미 나 합 습 학 슥 말 마 막 눅 요 행 롬 고전 고후 갈 엡 빌 골 살전 살후 딤전 딤후 딛 몬 히 약 벧전 벧후 요일 요이 요삼 유 계',
 'en': 'Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|1 Samuel|2 Samuel|1 Kings|2 Kings|1 Chronicles|2 Chronicles|Ezra|Nehemiah|Esther|Job|Psalms|Proverbs|Ecclesiastes|Song of Solomon|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|1 Corinthians|2 Corinthians|Galatians|Ephesians|Philippians|Colossians|1 Thessalonians|2 Thessalonians|1 Timothy|2 Timothy|Titus|Philemon|Hebrews|James|1 Peter|2 Peter|1 John|2 John|3 John|Jude|Revelation',
 'de': '1 Mose|2 Mose|3 Mose|4 Mose|5 Mose|Josua|Richter|Ruth|1 Samuel|2 Samuel|1 Könige|2 Könige|1 Chronik|2 Chronik|Esra|Nehemia|Esther|Hiob|Psalm|Sprüche|Prediger|Hohelied|Jesaja|Jeremia|Klagelieder|Hesekiel|Daniel|Hosea|Joel|Amos|Obadja|Jona|Micha|Nahum|Habakuk|Zephanja|Haggai|Sacharja|Maleachi|Matthäus|Markus|Lukas|Johannes|Apostelgeschichte|Römer|1 Korinther|2 Korinther|Galater|Epheser|Philipper|Kolosser|1 Thessalonicher|2 Thessalonicher|1 Timotheus|2 Timotheus|Titus|Philemon|Hebräer|Jakobus|1 Petrus|2 Petrus|1 Johannes|2 Johannes|3 Johannes|Judas|Offenbarung',
 'es': 'Génesis|Éxodo|Levítico|Números|Deuteronomio|Josué|Jueces|Rut|1 Samuel|2 Samuel|1 Reyes|2 Reyes|1 Crónicas|2 Crónicas|Esdras|Nehemías|Ester|Job|Salmos|Proverbios|Eclesiastés|Cantares|Isaías|Jeremías|Lamentaciones|Ezequiel|Daniel|Oseas|Joel|Amós|Abdías|Jonás|Miqueas|Nahum|Habacuc|Sofonías|Hageo|Zacarías|Malaquías|Mateo|Marcos|Lucas|Juan|Hechos|Romanos|1 Corintios|2 Corintios|Gálatas|Efesios|Filipenses|Colosenses|1 Tesalonicenses|2 Tesalonicenses|1 Timoteo|2 Timoteo|Tito|Filemón|Hebreos|Santiago|1 Pedro|2 Pedro|1 Juan|2 Juan|3 Juan|Judas|Apocalipsis',
 'zh-Hans': '创世记 出埃及记 利未记 民数记 申命记 约书亚记 士师记 路得记 撒母耳记上 撒母耳记下 列王纪上 列王纪下 历代志上 历代志下 以斯拉记 尼希米记 以斯帖记 约伯记 诗篇 箴言 传道书 雅歌 以赛亚书 耶利米书 耶利米哀歌 以西结书 但以理书 何西阿书 约珥书 阿摩司书 俄巴底亚书 约拿书 弥迦书 那鸿书 哈巴谷书 西番雅书 哈该书 撒迦利亚书 玛拉基书 马太福音 马可福音 路加福音 约翰福音 使徒行传 罗马书 哥林多前书 哥林多后书 加拉太书 以弗所书 腓立比书 歌罗西书 帖撒罗尼迦前书 帖撒罗尼迦后书 提摩太前书 提摩太后书 提多书 腓利门书 希伯来书 雅各书 彼得前书 彼得后书 约翰一书 约翰二书 约翰三书 犹大书 启示录',
 'zh-Hant': '創世記 出埃及記 利未記 民數記 申命記 約書亞記 士師記 路得記 撒母耳記上 撒母耳記下 列王紀上 列王紀下 歷代志上 歷代志下 以斯拉記 尼希米記 以斯帖記 約伯記 詩篇 箴言 傳道書 雅歌 以賽亞書 耶利米書 耶利米哀歌 以西結書 但以理書 何西阿書 約珥書 阿摩司書 俄巴底亞書 約拿書 彌迦書 那鴻書 哈巴谷書 西番雅書 哈該書 撒迦利亞書 瑪拉基書 馬太福音 馬可福音 路加福音 約翰福音 使徒行傳 羅馬書 哥林多前書 哥林多後書 加拉太書 以弗所書 腓立比書 歌羅西書 帖撒羅尼迦前書 帖撒羅尼迦後書 提摩太前書 提摩太後書 提多書 腓利門書 希伯來書 雅各書 彼得前書 彼得後書 約翰一書 約翰二書 約翰三書 猶大書 啟示錄',
 'ru': 'Бытие|Исход|Левит|Числа|Второзаконие|Иисус Навин|Судей|Руфь|1 Царств|2 Царств|3 Царств|4 Царств|1 Паралипоменон|2 Паралипоменон|Ездра|Неемия|Есфирь|Иов|Псалтирь|Притчи|Екклесиаст|Песнь Песней|Исаия|Иеремия|Плач Иеремии|Иезекииль|Даниил|Осия|Иоиль|Амос|Авдий|Иона|Михей|Наум|Аввакум|Софония|Аггей|Захария|Малахия|От Матфея|От Марка|От Луки|От Иоанна|Деяния|К Римлянам|1 Коринфянам|2 Коринфянам|К Галатам|К Ефесянам|К Филиппийцам|К Колоссянам|1 Фессалоникийцам|2 Фессалоникийцам|1 Тимофею|2 Тимофею|К Титу|К Филимону|К Евреям|Иакова|1 Петра|2 Петра|1 Иоанна|2 Иоанна|3 Иоанна|Иуды|Откровение',
 'ja': '創世記 出エジプト記 レビ記 民数記 申命記 ヨシュア記 士師記 ルツ記 サムエル記上 サムエル記下 列王紀上 列王紀下 歴代志上 歴代志下 エズラ記 ネヘミヤ記 エステル記 ヨブ記 詩篇 箴言 伝道の書 雅歌 イザヤ書 エレミヤ書 哀歌 エゼキエル書 ダニエル書 ホセア書 ヨエル書 アモス書 オバデヤ書 ヨナ書 ミカ書 ナホム書 ハバクク書 ゼパニヤ書 ハガイ書 ゼカリヤ書 マラキ書 マタイによる福音書 マルコによる福音書 ルカによる福音書 ヨハネによる福音書 使徒行伝 ローマ人への手紙 コリント人への第一の手紙 コリント人への第二の手紙 ガラテヤ人への手紙 エペソ人への手紙 ピリピ人への手紙 コロサイ人への手紙 テサロニケ人への第一の手紙 テサロニケ人への第二の手紙 テモテへの第一の手紙 テモテへの第二の手紙 テトスへの手紙 ピレモンへの手紙 ヘブル人への手紙 ヤコブの手紙 ペテロの第一の手紙 ペテロの第二の手紙 ヨハネの第一の手紙 ヨハネの第二の手紙 ヨハネの第三の手紙 ユダの手紙 ヨハネの黙示録',
}


def names(lang):
    s = NAMES[lang]
    out = s.split('|') if '|' in s else s.split()
    assert len(out) == 66, (lang, len(out))
    return out


# ---------------------------------------------------------------- 읽기
def ws(t):
    # 和合本 神版의 '　神'(전각 공백, 하나님 이름 앞 띄움)은 그대로 둔다
    t = re.sub(r'[ \t\r\n\xa0]+', ' ', html.unescape(t))
    t = t.strip(' ')
    return t if t.strip() else ''


def read_ebible(src, eid, clean=None):
    """eBible.org *_vpl.xml → {(책, 장, 절): 본문}. v="29-30" 같은 합친 절은 첫 절에 본문, 나머지는 ''."""
    path = os.path.join(src, eid, eid + '_vpl.xml')
    d = {}
    for el in ET.parse(path).getroot().iter('v'):
        b = UBS_NO.get(el.get('b'))
        if not b:
            continue  # 외경
        c = int(el.get('c'))
        vs = el.get('v')
        t = ws(''.join(el.itertext()).replace('¶', ''))
        if clean:
            t = clean(t)
        if '-' in vs:
            a, z = (int(x) for x in vs.split('-'))
            d[(b, c, a)] = t
            for v in range(a + 1, z + 1):
                d.setdefault((b, c, v), '')
        else:
            v = int(vs)
            if not t:
                continue  # eBible 이 KJV 절 자리에 넣어 둔 빈 칸 (RV1909 욥 38:39-41 등은 다음 장 앞에 있다)
            d[(b, c, v)] = (d[(b, c, v)] + ' ' + t).strip() if d.get((b, c, v)) else t
    return d


def clean_deu(t):
    # Luther 1912: 히브리 원문식 장절 표시 "[32:1]" · "[21:1b]" 를 지운다
    return ws(re.sub(r'\[\d+(?::\d+)?[ab]?\]', ' ', t))


def read_bolls(src, code):
    path = os.path.join(src, 'bolls_' + code, code + '.json')
    return json.load(open(path, encoding='utf-8'))


def read_krv(src):
    d = {}
    for v in read_bolls(src, 'KRV'):
        if v['book'] <= 66:
            d[(v['book'], v['chapter'], v['verse'])] = ws(v['text'])
    return d


def kougo_from_bolls(src):
    """bolls.life JPKJV (口語訳, 루비 포함, 히브리식 장절 + [口語訳 절] 표시) → 口語訳 장절로 되돌린다.
    <i>漢字</i><sup>,よみ</sup> 루비는 漢字만 남기고, *[..] 는 합친 절을 채우려고 복사한 줄이라 버린다.
    돌려주는 것: (본문 dict, 시편 표제 dict{(책, 장): 표제})"""
    d, titles = {}, {}
    prev = None  # (bolls 책, bolls 장, 표시가 있었나, 마지막 (장, 절))
    for v in read_bolls(src, 'JPKJV'):
        b, bc, bv = v['book'], v['chapter'], v['verse']
        if b > 66:
            continue
        t = re.sub(r'<sup>[^<]*</sup>', '', v['text'])
        t = t.replace('<br/>', ' ').replace('<i>', '').replace('</i>', '')
        t = re.sub(r'<[^>]+>', '', t)
        if t.startswith('*['):
            continue
        parts = re.split(r'(\[[^\]]*\])', t)
        same_ch = prev and prev[0] == b and prev[1] == bc
        if parts[0].strip():
            if same_ch and prev[2]:
                tgt = (prev[3][0], prev[3][1] + 1)  # 앞 절이 옮겨졌으면 이어서 센다
            else:
                tgt = (bc, bv)
            segs = [(tgt, parts[0])]
        else:
            segs = []
        marked = False
        for i in range(1, len(parts), 2):
            lab, body = parts[i][1:-1], parts[i + 1]
            marked = True
            m = re.fullmatch(r'(?:(\d+):)?(\d+)([ab]?)(?:-(\d+))?', lab)
            if not m:
                raise ValueError('JP label %r at %s' % (lab, (b, bc, bv)))
            c = int(m.group(1)) if m.group(1) else (segs[-1][0][0] if segs else bc)
            vv = int(m.group(2))
            if vv == 0:
                titles[(b, c)] = ws(body)
                continue
            segs.append(((c, vv), body, int(m.group(4)) if m.group(4) else vv))
            if m.group(4):
                for x in range(vv + 1, int(m.group(4)) + 1):
                    d.setdefault((b, c, x), '')
        if segs and len(segs[0]) == 2:
            segs[0] = (segs[0][0], segs[0][1], segs[0][0][1])
        last = prev[3] if same_ch else (bc, bv)
        for (c, vv), body, end in segs:
            body = ws(body)
            k = (b, c, vv)
            d[k] = (d[k] + body) if d.get(k) else body
            last = (c, end)
        prev = (b, bc, marked, last)
    return d, titles


def read_kougo(src, log):
    gb = json.load(open(os.path.join(src, 'gb_japkougo', 't.json'), encoding='utf-8'))
    g = {}
    for bk in gb['books']:
        for ch in bk['chapters']:
            for v in ch['verses']:
                t = ws(v['text']).replace('{', '').replace('[セラ', '〔セラ')  # getBible 본의 잘못 찍힌 글자
                g[(bk['nr'], ch['chapter'], v['verse'])] = t
    r, titles = kougo_from_bolls(src)
    norm = lambda s: re.sub(r'[\s、。「」『』・―〔〕\[\]（），：；！？]', '', s)
    gch = {(b, c) for b, c, v in g}
    rch = {(b, c) for b, c, v in r}
    d = {}
    filled = []
    gaps = []
    for (b, c) in sorted(gch | rch):
        if (b, c) in gch:
            for (bb, cc, v), t in g.items():
                if (bb, cc) == (b, c):
                    d[(b, c, v)] = t
        else:
            filled.append((b, c))
            for (bb, cc, v), t in r.items():
                if (bb, cc) == (b, c):
                    d[(b, c, v)] = t
    # getBible 본에서 빠진 절: bolls 본문이 이웃 절과 겹치지 않을 때만 채운다 (합친 절은 빈 칸으로 둔다)
    for (b, c, v), t in r.items():
        if (b, c) in gch and (b, c, v) not in g and t:
            near = norm(g.get((b, c, v - 1), '') + g.get((b, c, v + 1), ''))
            if norm(t) not in near:
                d[(b, c, v)] = t
                gaps.append((b, c, v))
            elif (b, c, v + 1) in g and norm(t) == norm(g[(b, c, v + 1)]) and r.get((b, c, v + 1)) == '':
                # getBible 은 합친 절(4-5)을 뒤 절에 두었다 → 和合本처럼 앞 절에 본문, 뒤 절은 빈 칸
                d[(b, c, v)] = g[(b, c, v + 1)]
                d[(b, c, v + 1)] = ''
                gaps.append((b, c, '%d-%d' % (v, v + 1)))
    # 시편 표제(getBible 본은 표제가 빠져 있다): bolls 에서 가져와 1절 앞에 붙인다 (KJV·和合本처럼)
    nt = 0
    for c in range(1, 151):
        title = titles.get((19, c))
        if not title:
            m = re.match(r'(【[^】]*】)', r.get((19, c, 1), ''))
            title = m.group(1) if m else None
        if title and d.get((19, c, 1)) and title not in d[(19, c, 1)]:
            d[(19, c, 1)] = title + ' ' + d[(19, c, 1)]
            nt += 1
    log('kougo: verses filled from bolls into getBible gaps %d: %s' % (len(gaps), gaps))
    # 두 원본 대조 (공백·문장부호 빼고 같은지)
    same = diff = 0
    samples = []
    for k, t in g.items():
        if k in r and r[k] and t:
            if norm(t) == norm(r[k]):
                same += 1
            else:
                diff += 1
                if len(samples) < 8:
                    samples.append((k, t[:40], r[k][:40]))
    log('kougo: getBible chapters %d, filled from bolls %d: %s' % (len(gch), len(filled), filled))
    log('kougo: psalm titles added %d; getBible vs bolls same %d diff %d' % (nt, same, diff))
    for s in samples:
        log('   diff %s | gb %s | bolls %s' % s)
    return d


# ---------------------------------------------------------------- 판 목록
VERSIONS = [
    dict(id='krv', name='개역한글', label='개역한글 (1961)', lang='ko', names='ko', year='1961', versif='std',
         read=lambda s, log: read_krv(s),
         source='https://bolls.life/static/translations/KRV.zip',
         license='퍼블릭 도메인 (대한성서공회 1961년판, 저작권 보호기간 만료)'),
    dict(id='kjv', name='KJV', label='English · King James Version (1769)', lang='en', names='en', year='1769', versif='std',
         read=lambda s, log: read_ebible(s, 'eng-kjv'),
         source='https://ebible.org/eng-kjv/', license='Public Domain (outside the UK Crown patent)'),
    dict(id='lut', name='Luther 1912', label='Deutsch · Lutherbibel 1912', lang='de', names='de', year='1912', versif='std',
         read=lambda s, log: read_ebible(s, 'deu1912', clean_deu),
         source='https://ebible.org/deu1912/', license='Public Domain'),
    dict(id='rv1909', name='RV 1909', label='Español · Reina-Valera 1909', lang='es', names='es', year='1909', versif='std',
         read=lambda s, log: read_ebible(s, 'spaRV1909'),
         source='https://ebible.org/spaRV1909/', license='Public Domain (Dominio Público)'),
    dict(id='cuvs', name='和合本 简体', label='中文 · 和合本 (简体)', lang='zh-Hans', names='zh-Hans', year='1919', versif='std',
         read=lambda s, log: read_ebible(s, 'cmn-cu89s'),
         source='https://ebible.org/cmn-cu89s/', license='Public Domain'),
    dict(id='cuvt', name='和合本 繁體', label='中文 · 和合本 (繁體)', lang='zh-Hant', names='zh-Hant', year='1919', versif='std',
         read=lambda s, log: read_ebible(s, 'cmn-cu89t'),
         source='https://ebible.org/cmn-cu89t/', license='Public Domain'),
    dict(id='synod', name='Синодальный', label='Русский · Синодальный перевод (1876)', lang='ru', names='ru', year='1876', versif='rus',
         read=lambda s, log: read_ebible(s, 'russyn'),
         source='https://ebible.org/russyn/', license='Public Domain'),
    dict(id='kougo', name='口語訳', label='日本語 · 口語訳 (1955)', lang='ja', names='ja', year='1955', versif='std',
         read=read_kougo,
         source='https://api.getbible.net/v2/japkougo.json (+ https://bolls.life/static/translations/JPKJV.zip)',
         license='Public Domain (日本聖書協会 1954/1955年版, 著作権保護期間満了)'),
]

DOWNLOADS = [
    ('eng-kjv', 'https://ebible.org/Scriptures/eng-kjv_vpl.zip'),
    ('deu1912', 'https://ebible.org/Scriptures/deu1912_vpl.zip'),
    ('spaRV1909', 'https://ebible.org/Scriptures/spaRV1909_vpl.zip'),
    ('cmn-cu89s', 'https://ebible.org/Scriptures/cmn-cu89s_vpl.zip'),
    ('cmn-cu89t', 'https://ebible.org/Scriptures/cmn-cu89t_vpl.zip'),
    ('russyn', 'https://ebible.org/Scriptures/russyn_vpl.zip'),
    ('bolls_KRV', 'https://bolls.life/static/translations/KRV.zip'),
    ('bolls_JPKJV', 'https://bolls.life/static/translations/JPKJV.zip'),
    ('gb_japkougo', 'https://api.getbible.net/v2/japkougo.json'),
]


def download(src):
    for folder, url in DOWNLOADS:
        dst = os.path.join(src, folder)
        os.makedirs(dst, exist_ok=True)
        print('download', url)
        data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'bible-builder'}), timeout=300).read()
        if url.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for n in z.namelist():
                    if n.endswith(('.json', '_vpl.xml')) and '/' not in n and '..' not in n:
                        open(os.path.join(dst, n), 'wb').write(z.read(n))
        else:
            open(os.path.join(dst, 't.json'), 'wb').write(data)


# ---------------------------------------------------------------- 쓰기
def build(src, report_path=None):
    lines = []
    log = lambda s: (lines.append(s), print(s.encode('ascii', 'backslashreplace').decode()))
    meta = []
    os.makedirs(OUT, exist_ok=True)
    for V in VERSIONS:
        d = V['read'](src, log)
        by_book = defaultdict(lambda: defaultdict(dict))
        for (b, c, v), t in d.items():
            if 1 <= b <= 66 and v >= 1:
                by_book[b][c][v] = t
        vdir = os.path.join(OUT, V['id'])
        os.makedirs(vdir, exist_ok=True)
        bk_meta, filled, merged, size = [], 0, 0, 0
        nm = names(V['names'])
        for b in range(1, 67):
            chs = by_book.get(b, {})
            nch = max(chs) if chs else 0
            arr = []
            for c in range(1, nch + 1):
                vs = chs.get(c, {})
                n = max(vs) if vs else 0
                row = [vs.get(v, '') for v in range(1, n + 1)]
                filled += sum(1 for x in row if x)
                merged += sum(1 for x in row if not x)
                arr.append(row)
            js = json.dumps({'c': arr}, ensure_ascii=False, separators=(',', ':'))
            p = os.path.join(vdir, '%d.json' % b)
            open(p, 'w', encoding='utf-8', newline='\n').write(js)
            size += os.path.getsize(p)
            bk_meta.append(nch)
        m = {k: V[k] for k in ('id', 'name', 'label', 'lang', 'year', 'versif', 'source', 'license')}
        m['books'] = nm
        m['chapters'] = bk_meta
        m['verses'] = filled
        meta.append(m)
        log('%-7s verses %6d  empty/merged %4d  books %d  size %.2f MB' % (V['id'], filled, merged, sum(1 for x in bk_meta if x), size / 1e6))
    out = {'abbr': NAMES['ko_abbr'].split(), 'ko': names('ko'), 'versions': meta}
    open(os.path.join(OUT, 'versions.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps(out, ensure_ascii=False, separators=(',', ':')))
    if report_path:
        open(report_path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=os.path.join(ROOT, 'build', '_bible_src'))
    ap.add_argument('--download', action='store_true')
    ap.add_argument('--report')
    a = ap.parse_args()
    if a.download:
        download(a.src)
    build(a.src, a.report)
