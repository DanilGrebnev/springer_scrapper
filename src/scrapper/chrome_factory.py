import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


class ChromeFactory:
    def __init__(self):
        pass

    def _build_options(self) -> Options:
        options = Options()
        options.add_argument("start-maximized")
        options.set_capability("pageLoadStrategy", "eager")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        if _is_truthy(os.getenv("CHROME_HEADLESS", "")):
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

        return options

    def create(self):
        options = self._build_options()

        driver = webdriver.Chrome(options=options)
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            page_load_strategy="eager",
        )
        return driver
