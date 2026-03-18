from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  
from selenium_stealth import stealth  

options = Options()
options.add_argument("start-maximized")
# options.add_argument("--headless")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# driver = webdriver.Chrome(options=options)  # pyright: ignore

# stealth(driver,
#     languages=["en-US", "en"],
#     vendor="Google Inc.",
#     platform="Win32",
#     webgl_vendor="Intel Inc.",
#     renderer="Intel Iris OpenGL Engine",
#     fix_hairline=True,
#     page_load_strategy='eager'
# )

class Driver:
    def __init__(self):
       pass
    
    def create(self):
        options = Options()
        options.add_argument("start-maximized")
        # self.options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Создаём драйвер
        driver = webdriver.Chrome(options=options)
        
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            page_load_strategy='eager'
        )
        
        return driver
    