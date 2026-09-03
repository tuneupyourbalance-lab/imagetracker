"""인스타 전용 Playwright 프로필에 직접 로그인하는 창을 띄운다.

크롬 프로필 쿠키를 복사해 쓰던 방식(scrape_ig_chrome.py)이 세션 만료로 0컷을 뱉어서,
Playwright가 소유하는 영속 프로필(.ig_profile)을 따로 두고 거기에 한 번 로그인해둔다.
이후 스크래퍼는 이 프로필을 그대로 재사용하므로 다시 로그인할 일이 없다.

실행: python3 ig_login.py   → 창이 뜨면 로그인만 하면 됨 (자동 감지 후 닫힘)
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

PROFILE = Path(__file__).parent / ".ig_profile"
WAIT_MINUTES = 12


def logged_in(ctx) -> bool:
    for c in ctx.cookies():
        if c["name"] == "sessionid" and "instagram" in c["domain"] and c["value"]:
            return True
    return False


def main():
    PROFILE.mkdir(exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE), channel="chrome", headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--no-first-run", "--no-default-browser-check"],
        )
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        pg.goto("https://www.instagram.com/accounts/login/", wait_until="load", timeout=60000)
        print("창을 띄웠습니다. 인스타그램에 로그인해주세요. (최대 %d분 대기)" % WAIT_MINUTES, flush=True)

        deadline = time.time() + WAIT_MINUTES * 60
        while time.time() < deadline:
            if logged_in(ctx):
                # 세션이 실제로 먹히는지 프로필 페이지로 확인
                pg.goto("https://www.instagram.com/heytea.kr/", wait_until="load", timeout=60000)
                pg.wait_for_timeout(3000)
                txt = pg.evaluate("() => document.body.innerText")[:300]
                ok = "가입하기" not in txt
                print(f"✅ 로그인 감지됨 · 프로필 페이지 접근 {'정상' if ok else '아직 로그아웃 상태'}", flush=True)
                if ok:
                    pg.wait_for_timeout(1500)
                    ctx.close()
                    print("프로필 저장 완료:", PROFILE, flush=True)
                    return 0
            time.sleep(3)

        print("시간 초과 — 로그인이 감지되지 않았습니다.", flush=True)
        ctx.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
