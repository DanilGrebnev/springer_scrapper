from typing import TypedDict, Callable, Optional
from src.springer.utils.create_url import create_url
from src.driver import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np

driver_factory = Driver()

class PageInfo(TypedDict):
    current: int
    total: int

ArticleCard = TypedDict("ArticleCard", 
    {
        "is_access": bool, 
        "title": str, 
        "link": str, 
        "description": str,
        "type": str
    })

class ScrappingService:
    def __init__(self, search_params):
        self._search_params = search_params
        
    _search_params = {
        "query":"",
        "page":"",
        "dateFrom":"",
        "dateTo":"", 
        "sortBy":"relevance",
        "openAccess": "false"
    }

    def _get(self, search_params, _driver, accept_cookies=False):
        '''Открывает страницу поиска Springer в переданном драйвере.
        accept_cookies=True — попытается закрыть баннер кук (только при первом заходе).'''
        _driver.get(self._create_search_url(search_params))

        if accept_cookies:
            try:
                cookie_btn = _driver.find_element(By.CLASS_NAME, 'cc-banner__button-accept')
                cookie_btn.click()
            except:
                pass
    
    def _create_search_url(self, search_params: dict):
        '''Собирает URL для поиска на Springer из словаря параметров (query, page, даты и т.д.)'''
        return create_url.search_page(**search_params)
    
    def _get_pages_range(self, _driver):
        '''Определяет диапазон страниц результатов поиска.
        Открывает первую страницу, находит элементы пагинации [data-page],
        извлекает номера страниц и возвращает список [1, 2, 3, ...N].
        Если результатов нет — возвращает пустой список.'''
        try:
            self._get(self._search_params, _driver, accept_cookies=True)
        except Exception as ex:
            print('Ошибка открытия страницы для подсчёта элементов пагинации')
            print(ex)
        
        pages_amount = []
        
        PAGES_SELECTOR = (By.CSS_SELECTOR, "[data-page]")
        
        try:
            wait = WebDriverWait(_driver, 10, poll_frequency=1)
            wait.until(EC.element_to_be_clickable(PAGES_SELECTOR))
            
            # Получаем список элементов пагинации
            webelements_list = _driver.find_elements(*PAGES_SELECTOR)
            
            for list_pagination_item in webelements_list:
                pages_amount.append(int(list_pagination_item.get_attribute('data-page')))
                
        except Exception as ex:
            print('Ошибка получения элементов пагинации')
            print(ex)
            return []
        
        return list(range(pages_amount[0], pages_amount[-1] + 1)) if len(pages_amount) > 1 else pages_amount 

    # Сбор статей с 1 страницы
    def _collect_articles_from_page(self, _driver) -> list[ArticleCard]:
        '''Собирает все карточки статей с текущей открытой страницы.
        Для каждой карточки извлекает: title, link, description, type и is_access
        (есть ли полный доступ). Возвращает список словарей ArticleCard.'''
        def _get_articles(card_container: WebElement) -> ArticleCard:
            # Тип и доступ к статье
            MetaInfo = TypedDict("MetaInfo", 
                {
                        "is_access": bool, 
                        "type": str
                })

            def get_meta_info(card_container: WebElement) -> MetaInfo:
                type = card_container.find_element(By.CLASS_NAME, 'c-meta__type').text

                try:
                    card_container.find_element(By.CLASS_NAME, 'app-entitlement__icon--full-access')
                    is_access = True
                except:
                    is_access = False

                return {
                    "is_access": is_access, 
                    "type":type
                    }
            def get_description_from_article(container: WebElement) -> str:
                try:
                    return container.find_element(By.CLASS_NAME, 'app-card-open__description').find_element(By.TAG_NAME, 'p').text
                except:
                    return container.find_element(By.CLASS_NAME, 'app-card-open__description').text    

            card_meta: ArticleCard = {
                "is_access": False,
                "title": "",
                "link": "",
                "description": "",
                "type": '' 
            }

            meta_info_result = get_meta_info(card_container)

            card_heading: WebElement = card_container.find_element(By.TAG_NAME, 'h3')

            title = card_heading.find_element(By.TAG_NAME, 'span').text
            link = card_heading.find_element(By.CLASS_NAME, 'app-card-open__link').get_attribute("href")
            description = get_description_from_article(card_container)

            card_meta['is_access'] = meta_info_result['is_access']
            card_meta['type'] = meta_info_result['type']
            card_meta['title'] = title
            card_meta['link'] = link
            card_meta['description'] = description

            return card_meta
        
        ARTICLE_SELECTOR = (By.CLASS_NAME, 'app-card-open__main')
        wait = WebDriverWait(_driver, 10, poll_frequency=1)
        wait.until(EC.element_to_be_clickable(ARTICLE_SELECTOR))
        
        # Получаем контейнер с текущими статьями
        card_containers_list = _driver.find_elements(*ARTICLE_SELECTOR)
        
        return [_get_articles(card_container) for card_container in card_containers_list]

    def set_search_params(self, search_params):
        '''Перезаписывает параметры поиска (query, page, даты, сортировка и т.д.)'''
        self._search_params = search_params
     
    def _divide_pages(self, pages) -> list[list]:
        '''Возвращает массив разбитый на подмассива страниц'''
        return [page_parts.tolist() for page_parts in np.array_split(pages, 3) if page_parts.tolist()]

    def _scrapping_articles_from_all_pages(self, pages_range: list[int]) -> dict:
        """
            Собирает статьи со страницы.

            Args:
                pages_range (list): Список страниц

            Returns:
                list[ArticleCard]

            Example:
                {"1": [{"is_access": bool, 
                    "title": str, 
                    "link": str, 
                    "description": str,
                    "type": str]}
                }
        """
        if not pages_range:
            return {}

        driver_local = driver_factory.create()

        result = {}

        try:
            for i, page in enumerate(pages_range):
                try:
                    self._get(
                        {**self._search_params, "page": page},
                        _driver=driver_local,
                        accept_cookies = (i == 0)
                    )
                    
                    self._scroll_slowly(_driver=driver_local)
                    
                    articles = self._collect_articles_from_page(_driver=driver_local)
                    
                    result[page] = articles
                except Exception as ex:
                    print(f"Ошибка в сборе статей на странице {page}: {ex}")
                    continue
        except Exception as ex:
            print(f'Parsing error: {ex}')
        finally:
            driver_local.quit()

        return result
    
    # Плавный скролл вниз страницы
    def _scroll_slowly(self, _driver, scroll_pause: float = 0.5, max_scrolls: int = 10):
        """
        Плавно скроллит страницу для подгрузки динамического контента

        Args:
            _driver: WebDriver
            scroll_pause: пауза между скроллами в секундах
            max_scrolls: максимальное количество скроллов
        """
        last_height = _driver.execute_script("return document.body.scrollHeight")

        for i in range(max_scrolls):
            # Плавный скролл вниз
            _driver.execute_script("""
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            """)

            # Ждем завершения анимации и загрузки
            time.sleep(scroll_pause)

            # Проверяем, загрузились ли новые элементы
            new_height = _driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(f"Достигнут конец страницы после {i+1} скроллов")
                break
            last_height = new_height
            
    # Основная функция, запускающая всё остальное
    def _start_multythreads_scrapping(self):
        driver = driver_factory.create()
        pages_range = self._get_pages_range(driver)
        driver.quit()
        divided_pages = self._divide_pages(pages_range)
        
        if not divided_pages:
            print(f"Список страниц пустой")
            return None
        
        articles_result = {}
        
        with ThreadPoolExecutor(max_workers=len(divided_pages)) as executor:
            futures = [executor.submit(self._scrapping_articles_from_all_pages, pages) for pages in divided_pages]
            
            for future in futures:
               articles_result.update(future.result())
            
        return  articles_result
        
    def start(self):
       return self._start_multythreads_scrapping()