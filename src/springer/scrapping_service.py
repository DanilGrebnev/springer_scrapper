from typing import TypedDict, Callable, Optional, Any
from src.springer.utils.create_url import create_url
# from src.driver import driver
from src.driver import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import multiprocessing as mp

# Глобальный драйвер
driver_factory = Driver()
driver = driver_factory.create()

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

    def _get(self, search_params, _driver=driver):
        '''driver.get with __create_search_url function'''
        def accept_cookie_dialog():
            """принятие кук"""
            try:
                cookie_btn = WebDriverWait(_driver, 4).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cc-banner__button-accept')))
                cookie_btn.click()
                return True
            except:
                return False
        
        _driver.set_page_load_timeout(5)
        try:
            _driver.get(self._create_search_url(search_params))
            
            accept_cookie_dialog()
        except:
            _driver.execute_script("window.stop();")
    
    def _create_search_url(self, search_params: dict):
        return create_url.search_page(**search_params)
    
    def _get_pages_range(self):
        '''получение количества страниц'''
        # Открываем страницу с запросом
        try:
            self._get(self.__search_params)
        except Exception as ex:
            print('Ошибка открытия страницы для подсчёта элементов пагинации')
            print(ex)
        
        pages_amount = []

        try:
            webelements_list = driver.find_elements(By.CSS_SELECTOR, "[data-page]")

            for list_pagination_item in webelements_list:
                pages_amount.append(int(list_pagination_item.get_attribute('data-page')))
        except Exception as ex:
            print('Ошибка получения элементов пагинации')
            print(ex)
            return []

        ''' 
        Если кол-во страниц больше 1, то берем номер второй и поледней страницы
        и заполняем список
        '''
        if len(pages_amount) > 1:
            pages_list = list(range(pages_amount[0], pages_amount[-1] + 1))
            return pages_list
        else:
            return pages_amount


    def _collect_articles(self, _driver=driver) -> list[ArticleCard]:
        '''Сбор статей со страницы'''
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
        self.__search_params = search_params
    
    def _pages_devide(self, pages: list[int]):
        def get_halfs(first:list[int], second:list[int]):
            '''Получение половинок'''
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
    
    def _scrapping_articles(self, pages_range: list[int], cb: Optional[Callable[[Any], None]]):
        ''' Главная функция скрапинга всех страниц со статьями'''
        driver_factory = Driver()
        driver_local = driver_factory.create()
        
        try:           
            # Если страниц нет - выходим, т.к. результатов не найдено
            if not pages_range:
                return 

            for page in pages_range:
                try:
                    time.sleep(2)
                    self._get({**self.__search_params, "page":page}, _driver=driver_local)

                    atrticles_on_current_page = self._collect_articles(_driver=driver_local)
                    
                    # Записываем в словарь с индексацией по странице 
                    article_dict = {
                        "page": page,
                        "articles": atrticles_on_current_page
                    }
                    if cb:
                        cb(article_dict)
                        
                except Exception as ex:
                    print(f"Ошибка в сборе статей")
                    print(ex)
                    continue

        except Exception as ex:
            print(f'Parsing error: {ex}') 
            driver.quit()
            return
        
    def start(self, progress_parsing_page_cb: Optional[Callable[[PageInfo], None]] = None):
        pages_range = self._get_pages_range()
        devided_pages = self._pages_devide(pages_range)
        
        articles_result = {}        
        
        def update_articles_result(article_data):
            articles_result[article_data['page']] = article_data['articles'] 
        
        if devided_pages['first_half'] and devided_pages['second_half']:
            pr_first = mp.Process(target=self._scrapping_articles, args=(devided_pages['first_half'], update_articles_result))
            pr_second = mp.Process(target=self._scrapping_articles, args=(devided_pages['second_half'], update_articles_result))
            
            pr_first.start()
            pr_second.start()
            pr_first.join()
            pr_second.join()

        
        print(articles_result)
        
        # articles = self._scrapping_articles(pages_range, progress_parsing_page_cb)
        
        # return articles
        # return []
        
       