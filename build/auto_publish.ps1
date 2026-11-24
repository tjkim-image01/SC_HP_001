# STUDIO.C 홈페이지 자동 갱신 (2026-11-24 대표님 "매일 아침 자동으로 다시 만들어 올리는 예약 작업")
# Windows 작업 스케줄러 「STUDIO.C 홈페이지 자동 갱신」이 하루 4번(07:05 · 20:05 · 21:05 · 22:05) 실행 —
# 글로벌 웨더 07:00, 바이블캐스트톡 20:00, 크리스찬 데일리톡 21:00, 넥스트제너레이션 22:00 공개 직후.
# 하는 일: build_site.py 로 index.html 다시 만들기 → 바뀐 것이 있으면 commit → push (GitHub Pages 가 1분 안팎에 반영)
# 기록: build/auto_publish.log (최근 500줄만 남김)
$ErrorActionPreference = "Continue"
$Root = "C:\Users\USER\Downloads\app\SC_HP_001"
$Py = "C:\Users\USER\Downloads\app\youtubeauto\.local\venv\Scripts\python.exe"
$Log = Join-Path $Root "build\auto_publish.log"
$env:PYTHONUTF8 = "1"
$env:GIT_TERMINAL_PROMPT = "0"
Set-Location $Root
function Write-Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" | Out-File -FilePath $Log -Append -Encoding utf8 }

Write-Log "시작"
$out = & $Py build/build_site.py 2>&1 | Out-String
Write-Log ("빌드: " + (($out -split "`n" | Where-Object { $_ -match "기준|주보:|쇼츠 갤러리|Error|Traceback" }) -join " / "))
if ($LASTEXITCODE -ne 0) { Write-Log "빌드 실패 (exit $LASTEXITCODE) — 올리지 않음"; exit 1 }

git add -A 2>&1 | Out-Null
$changed = git status --porcelain
if (-not $changed) { Write-Log "바뀐 것 없음 — 올리지 않음"; exit 0 }
git commit -q -m "자동 갱신 $(Get-Date -Format 'yyyy-MM-dd HH:mm') (쇼츠 갤러리·이번 주 답변·주보)" 2>&1 | Out-Null
$push = git push -q 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) { Write-Log "push 실패: $push"; exit 1 }
Write-Log "올림 완료"

# 기록이 너무 길어지지 않게
$lines = Get-Content $Log -Encoding utf8
if ($lines.Count -gt 500) { $lines | Select-Object -Last 500 | Set-Content $Log -Encoding utf8 }
