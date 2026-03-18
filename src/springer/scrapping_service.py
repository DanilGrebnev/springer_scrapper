from typing import TypedDict, Callable, Optional
from src.springer.utils.create_url import create_url
from src.driver import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
import time
import random
from concurrent.futures import ThreadPoolExecutor

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
        self.__search_params = search_params
        
    __search_params = {
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
            self._get(self.__search_params, _driver, accept_cookies=True)
        except Exception as ex:
            print('Ошибка открытия страницы для подсчёта элементов пагинации')
            print(ex)
        
        pages_amount = []

        try:
            webelements_list = _driver.find_elements(By.CSS_SELECTOR, "[data-page]")

            for list_pagination_item in webelements_list:
                pages_amount.append(int(list_pagination_item.get_attribute('data-page')))
        except Exception as ex:
            print('Ошибка получения элементов пагинации')
            print(ex)
            return []

        if len(pages_amount) > 1:
            pages_list = list(range(pages_amount[0], pages_amount[-1] + 1))
            return pages_list
        else:
            return pages_amount

    def _collect_articles(self, _driver) -> list[ArticleCard]:
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
        
        # Получаем контейнер с текущими статьями
        card_containers_list = _driver.find_elements(By.CLASS_NAME, 'app-card-open__main')
        # Статьи с текущей страницы
        atrticles_on_current_page = []
        
        # Собираем каждую статью на текущей странице
        for card_container in card_containers_list:
            atrticles_on_current_page.append(_get_articles(card_container))
        return atrticles_on_current_page

    def set_search_params(self, search_params):
        '''Перезаписывает параметры поиска (query, page, даты, сортировка и т.д.)'''
        self.__search_params = search_params
    
    def _pages_divide(self, pages: list[int]):
        '''Делит список страниц пополам для параллельного скрапинга двумя потоками.
        Например [1,2,3,4] -> first_half=[1,2], second_half=[3,4].
        Если страница одна — second_half будет пустым.'''
        def get_halfs(first:list[int], second:list[int]):
            return {
                "first_half": first, 
                "second_half": second
            }

        total_pages = len(pages)

        if not total_pages:
            return get_halfs([], [])

        if total_pages == 1:
            return get_halfs(pages, [])

        mid = len(pages) // 2
        first_half = pages[:mid]
        second_half = pages[mid:]

        return get_halfs(first_half, second_half)
    
    def _scrapping_articles(self, pages_range: list[int]) -> dict:
        '''Скрапит свою часть страниц в отдельном потоке.
        Создаёт собственный Chrome-драйвер, последовательно обходит каждую страницу
        из pages_range, собирает статьи и складывает в dict {номер_страницы: [статьи]}.
        В конце закрывает драйвер (finally). Пауза 2сек между страницами — защита от бана.'''
        if not pages_range:
            return {}

        driver_local = driver_factory.create()
        result = {}

        try:
            for i, page in enumerate(pages_range):
                try:
                    if i > 0:
                        time.sleep(random.uniform(0.5, 1.5))
                    self._get(
                        {**self.__search_params, "page": page},
                        _driver=driver_local,
                        accept_cookies=(i == 0)
                    )
                    articles = self._collect_articles(_driver=driver_local)
                    result[page] = articles
                except Exception as ex:
                    print(f"Ошибка в сборе статей на странице {page}: {ex}")
                    continue
        except Exception as ex:
            print(f'Parsing error: {ex}')
        finally:
            driver_local.quit()

        return result
        
    def start(self, progress_parsing_page_cb: Optional[Callable[[PageInfo], None]] = None):
        '''Точка входа. Весь процесс:
        1) Создаёт драйвер, определяет сколько страниц в результатах, закрывает драйвер.
        2) Делит страницы пополам через _pages_divide.
        3) Запускает 2 потока (ThreadPoolExecutor), каждый скрапит свою половину
           страниц в собственном браузере (_scrapping_articles).
        4) Собирает результаты из обоих потоков в один dict и возвращает.'''
        main_driver = driver_factory.create()
        pages_range = self._get_pages_range(main_driver)
        main_driver.quit()

        divided_pages = self._pages_divide(pages_range)
        articles_result = {}

        halves = [h for h in [divided_pages['first_half'], divided_pages['second_half']] if h]

        if not halves:
            return articles_result

        with ThreadPoolExecutor(max_workers=len(halves)) as executor:
            futures = [executor.submit(self._scrapping_articles, half) for half in halves]

            for future in futures:
                articles_result.update(future.result())

        return articles_result