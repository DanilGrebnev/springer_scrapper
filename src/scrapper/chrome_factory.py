import logging
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth

logger = logging.getLogger(__name__)


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


class ChromeFactory:
    def __init__(self):
        pass

    def _build_options(self, headless: bool) -> Options:
        options = Options()
        options.set_capability("pageLoadStrategy", "eager")

        if headless:
            # Контейнерный headless-режим: минимум опций, максимум стабильности.
            # experimental_option("excludeSwitches"/"useAutomationExtension") в новых
            # Chrome 120+ на Linux приводит к "Chrome instance exited" на старте —
            # не используем их в headless.
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--lang=en-US")
        else:
            options.add_argument("start-maximized")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

        return options

    def create(self):
        headless = _is_truthy(os.getenv("CHROME_HEADLESS", ""))
        options = self._build_options(headless=headless)

        driver = webdriver.Chrome(options=options)

        if headless:
            # selenium_stealth в комбинации с Chrome --headless=new
            # иногда сам ломает контекст (часть подмен не применяется корректно).
            # Для headless делаем лёгкий CDP-override навигатора — этого достаточно
            # для обхода базовой детекции автоматизации.
            try:
                driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {
                        "source": (
                            "Object.defineProperty(navigator, 'webdriver', "
                            "{get: () => undefined});"
                            "Object.defineProperty(navigator, 'languages', "
                            "{get: () => ['en-US', 'en']});"
                            "Object.defineProperty(navigator, 'plugins', "
                            "{get: () => [1, 2, 3, 4, 5]});"
                            "window.chrome = window.chrome || { runtime: {} };"
                        )
                    },
                )
            except Exception as ex:
                logger.warning("CDP stealth override не применился: %s", ex)
            return driver

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
