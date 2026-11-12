import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:5173"

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Desktop Screenshots (1280 x 900)
        context_desktop = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context_desktop.new_page()

        # Screen 1: Weekly Pulse
        print("Capturing 01_desktop_weekly_pulse.png...")
        page.goto(f"{BASE_URL}/")
        page.wait_for_selector("text=Weekly Review Pulse")
        time.sleep(1.0)
        page.screenshot(path=str(OUTPUT_DIR / "01_desktop_weekly_pulse.png"), full_page=True)

        # Screen 2: Themes Explorer
        print("Capturing 02_desktop_themes.png...")
        page.goto(f"{BASE_URL}/themes")
        page.wait_for_selector("text=Themes Explorer")
        time.sleep(1.0)
        page.screenshot(path=str(OUTPUT_DIR / "02_desktop_themes.png"), full_page=True)

        # Screen 2: Themes Drawer open
        print("Capturing 02_desktop_theme_drawer.png...")
        page.goto(f"{BASE_URL}/themes?themeId=theme-kyc")
        page.wait_for_selector("text=Rating Breakdown")
        time.sleep(1.0)
        page.screenshot(path=str(OUTPUT_DIR / "02_desktop_theme_drawer.png"), full_page=True)

        # Screen 3: Run & Publish
        print("Capturing 03_desktop_run_publish.png...")
        page.goto(f"{BASE_URL}/run")
        page.wait_for_selector("text=Run & Publish Pipeline")
        time.sleep(1.0)
        page.screenshot(path=str(OUTPUT_DIR / "03_desktop_run_publish.png"), full_page=True)

        # Screen 3: Run & Publish (Validation Failed Flatline)
        print("Capturing 03_desktop_run_validation_failed.png...")
        page.goto(f"{BASE_URL}/run?scenario=validation-failed")
        page.wait_for_selector("text=Validation Gate Failed")
        time.sleep(1.0)
        page.screenshot(path=str(OUTPUT_DIR / "03_desktop_run_validation_failed.png"), full_page=True)

        # Screen 4: Data Import
        print("Capturing 04_desktop_data_import.png...")
        page.goto(f"{BASE_URL}/import")
        page.wait_for_selector("text=Data Ingestion & Hygiene")
        time.sleep(1.0)
        page.screenshot(path=str(OUTPUT_DIR / "04_desktop_data_import.png"), full_page=True)

        # Screen 4: Data Import Low Coverage
        print("Capturing 04_desktop_data_import_low_coverage.png...")
        page.goto(f"{BASE_URL}/import?scenario=low-coverage")
        page.wait_for_selector("text=Low coverage alert")
        time.sleep(1.0)
        page.screenshot(path=str(OUTPUT_DIR / "04_desktop_data_import_low_coverage.png"), full_page=True)

        # Screen 5: Help & Knowledge Base
        print("Capturing 05_desktop_help_guide.png...")
        page.goto(f"{BASE_URL}/help")
        page.wait_for_selector("text=App Guide & Knowledge Base")
        time.sleep(1.0)
        page.screenshot(path=str(OUTPUT_DIR / "05_desktop_help_guide.png"), full_page=True)

        context_desktop.close()

        # 2. Mobile Screenshots (375 x 812)
        context_mobile = browser.new_context(viewport={"width": 375, "height": 812})
        m_page = context_mobile.new_page()

        print("Capturing 01_mobile_weekly_pulse.png...")
        m_page.goto(f"{BASE_URL}/")
        m_page.wait_for_selector("text=Weekly Review Pulse")
        time.sleep(1.0)
        m_page.screenshot(path=str(OUTPUT_DIR / "01_mobile_weekly_pulse.png"), full_page=True)

        print("Capturing 02_mobile_themes.png...")
        m_page.goto(f"{BASE_URL}/themes")
        m_page.wait_for_selector("text=Themes Explorer")
        time.sleep(1.0)
        m_page.screenshot(path=str(OUTPUT_DIR / "02_mobile_themes.png"), full_page=True)

        print("Capturing 03_mobile_run_publish.png...")
        m_page.goto(f"{BASE_URL}/run")
        m_page.wait_for_selector("text=Run & Publish Pipeline")
        time.sleep(1.0)
        m_page.screenshot(path=str(OUTPUT_DIR / "03_mobile_run_publish.png"), full_page=True)

        print("Capturing 04_mobile_data_import.png...")
        m_page.goto(f"{BASE_URL}/import")
        m_page.wait_for_selector("text=Data Ingestion & Hygiene")
        time.sleep(1.0)
        m_page.screenshot(path=str(OUTPUT_DIR / "04_mobile_data_import.png"), full_page=True)

        print("Capturing 05_mobile_help_guide.png...")
        m_page.goto(f"{BASE_URL}/help")
        m_page.wait_for_selector("text=App Guide & Knowledge Base")
        time.sleep(1.0)
        m_page.screenshot(path=str(OUTPUT_DIR / "05_mobile_help_guide.png"), full_page=True)

        context_mobile.close()
        browser.close()
        print(f"All screenshots successfully saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    capture()
