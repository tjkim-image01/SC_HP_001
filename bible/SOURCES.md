# 성경 본문 출처 · 저작권 (bible/)

STUDIO.C 성경 읽기 페이지(`bible/index.html`)에 싣는 번역은 **저작권이 끝났거나 퍼블릭 도메인으로 공개된 판만** 쓴다.
본문은 `build/build_bible.py` 가 아래 원본에서 받아 `bible/data/<판>/<책번호>.json` 으로 만든다 (받은 날 2026-11-25).

| 판 (id) | 번역 | 원본 (내려받은 곳) | 저작권 | 절 수 |
|---|---|---|---|---|
| `krv` | 개역한글 (대한성서공회 1961) | bolls.life `KRV` — https://bolls.life/static/translations/KRV.zip | 퍼블릭 도메인 (한국에서 저작권 보호기간 만료). 창 1:3 「하나님이 가라사대 빛이 있으라 하시매」로 개역한글(개역개정 아님) 확인 | 31,103 |
| `kjv` | King James Version (1769 표준판, 외경 제외) | eBible.org `eng-kjv` — https://ebible.org/eng-kjv/ (`eng-kjv_vpl.zip`) | Public Domain (영국 안에서만 왕실 특허, 그 밖에서는 퍼블릭 도메인) | 31,102 |
| `lut` | Lutherbibel 1912 | eBible.org `deu1912` — https://ebible.org/deu1912/ | Public Domain | 31,102 |
| `rv1909` | Reina-Valera 1909 | eBible.org `spaRV1909` — https://ebible.org/spaRV1909/ | Public Domain (Dominio Público) | 31,084 |
| `cuvs` | 和合本 简体 (新标点和合本, 神版) | eBible.org `cmn-cu89s` — https://ebible.org/cmn-cu89s/ | Public Domain (eBible.org 표기) | 31,021 |
| `cuvt` | 和合本 繁體 (新標點和合本, 上帝版) | eBible.org `cmn-cu89t` — https://ebible.org/cmn-cu89t/ | Public Domain (eBible.org 표기) | 31,021 |
| `synod` | Синодальный перевод (1876) | eBible.org `russyn` — https://ebible.org/russyn/ | Public Domain | 31,169 |
| `kougo` | 口語訳 (日本聖書協会 1954/1955) | getBible `japkougo` — https://api.getbible.net/v2/japkougo.json (원 출처 bible.50webs.org, Crosswire 모듈 JapKougo) · 빠진 18장과 시편 표제는 bolls.life `JPKJV` (https://bolls.life/static/translations/JPKJV.zip, 「口語訳聖書(ルビあり)」)에서 루비를 지우고 보충 | Public Domain (2006년 1월 1일 저작권 만료) | 31,085 |

## 본문 손질

- **공통**: 원본의 Strong 번호·각주·`<i>`·`<S>` 같은 표시는 없다(eBible VPL 은 본문만, bolls KRV 는 표시 없음). 공백만 정리.
- **KJV**: 문단 표시 `¶` 를 지움. 이탤릭(보충어) 괄호 `[ ]` 는 VPL XML 에 이미 없어 보충어도 일반 글자로 나온다.
- **Luther 1912**: 히브리 원문식 장절 표시 `[32:1]` 같은 것을 지움.
- **RV 1909 · 和合本**: 보충어 괄호는 XML 판에서 이미 빠져 있다. 和合本은 원본에서 합친 절(예: 창 24:29-30)을 첫 절에 두고 뒤 절은 빈 칸으로 둔다 (페이지에서 `29–30` 으로 표시).
  RV 1909 는 스페인어 장절(욥 38:39-41 → 39:1-3 등)을 그대로 쓰므로 eBible 이 KJV 자리에 넣어 둔 빈 칸 18개는 뺐다.
- **시노달 역**: 러시아식(칠십인역) 장절을 그대로 둔다. 시편 번호가 한 편씩 다르고(시 23편 = Пс 22) 표제를 1절로 센다.
  페이지가 시편을 대조할 때 맞는 장을 찾아(9–10편 → 9, 114–115 → 113, 116 → 114·115, 147 → 146·147) 두 단으로 따로 보여 준다.
- **口語訳**: getBible 본을 기본으로 쓰고, 빠진 장(시 130–139, 잠 30–31, 마 25–28, 요 19, 롬 10)은 bolls JPKJV 에서 채웠다.
  bolls 본은 `<i>漢字</i><sup>,よみ</sup>` 루비를 漢字만 남기고 지웠고, 히브리식 장절을 `[口語訳 절]` 표시대로 되돌렸으며, 합친 절을 채우려 복사해 둔 `*[..]` 줄은 버렸다.
  두 원본이 겹치는 30,614절 가운데 30,479절이 글자(공백·문장부호 빼고) 그대로 같다. 다른 135절은 대부분 시편 표제·시 119편 히브리 글자 머리(アレフ 등)·`〔セラ` 괄호 차이.
  getBible 본의 HTML 엔티티(`&#x2015;` → ―)와 잘못 찍힌 `{` 를 고쳤다.

## 싣지 않는 것

- **우리말성경**(두란노), **개역개정**·**새번역**(대한성서공회), **新共同訳**·**新改訳**, **RV1960**, **NKJV** 등은 저작권이 살아 있어 싣지 않는다.
  새 공개 판을 넣을 때는 `build/build_bible.py` 의 `VERSIONS` 에 한 줄(그리고 읽는 함수)을 더하고 다시 빌드하면 페이지 목록에 저절로 나온다.
