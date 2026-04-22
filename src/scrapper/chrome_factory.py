import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth


class ChromeFactory:
    def __init__(self):
        pass

    def _build_options(self) -> Options:
        options = Options()
        options.add_argument("start-maximized")
        options.set_capability("pageLoadStrategy", "eager")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        return options

    def create(self):
        options = self._build_options()

        remote_url = os.getenv("SELENIUM_REMOTE_URL", "").strip()

        if remote_url:
            driver = webdriver.Remote(command_executor=remote_url, options=options)
        else:
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
