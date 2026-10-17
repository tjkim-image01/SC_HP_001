# SC_HP_001 · STUDIO.C 홈페이지

김포 스튜디오 처치(STUDIO.C) 홈페이지. **질문이 생기면 먼저 찾아오는 교회.**
기획: `youtebe3/project/SC_HOMEPAGE_001/` (기획서 v2 · 웹툰 코너 설계 · 홈 시안 v2)

## 만드는 법

```bash
python build/build_site.py                      # 지금 시각 기준으로 index.html 생성
python build/build_site.py --now "2026-10-23 20:05"   # 그 시각 기준 미리 보기
```

필요: Python 3 + Pillow, ffmpeg (공개 전 쇼츠의 대체 장면을 뽑을 때)

## 어디서 읽나

| 구역 | 원본 |
|---|---|
| 절기 띠 · 이번 주일 · 말씀 | `painter'sroom/STUDIO_C/05_SNS/카페_주보/NN주_*.md` + `01_주보/<연도>/<월>/cover/` |
| 트렌드 쇼츠 · 바이블캐스트톡 | `STUDIO_C/05_SNS/업로드일정.md` (유튜브 ID · 공개 시각) |
| 다음 질문 | `STUDIO_C/03_시리즈/바이블캐스트톡_100/질문목록_v1.md` |
| 질문 답변 | `content/qna/QNNN.json` (이 저장소) |
| 웹툰 | `webtoon2/project/p001/web/data.js` (퓨어데이) · `s001/web/episodes_data.js` (여호수아) — 그림은 각 사이트에서 불러옴 |
| 교회 정보 · 기도제목 · 링크 | `build/config.json` |

## 원칙

- 성도 이름·연락처는 싣지 않는다. 교회 연락처만.
- 주보 PDF 는 순서 담당 이름이 있어 링크하지 않는다 (이름 가린 판이 생기면 연결).
- 유튜브 공개 시각 전에는 영상을 '공개 예정'으로만 보여 준다. 썸네일은 `i.ytimg.com/vi/<ID>/oar2.jpg`, 없으면 mp4 에서 뽑은 장면.
- 성경 인용은 개역한글.
- `index.html` 은 빌드 결과물이다. 고칠 때는 `build/templates/home.html`, `assets/`, 데이터를 고친 뒤 다시 빌드한다.
