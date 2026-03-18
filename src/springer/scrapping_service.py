from typing import TypedDict, Callable, Optional
from src.springer.utils.create_url import create_url
from src.driver import driver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    def _get(self, search_params):
        '''driver.get with __create_search_url function'''
        driver.set_page_load_timeout(5)
        try:
            driver.get(self._create_search_url(search_params))
            time.sleep(1)
            self._accept_cookie_dialog()
        except:
            driver.execute_script("window.stop();")
    
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

    def _get_articles(self, card_container: WebElement) -> ArticleCard:
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
    
    def _accept_cookie_dialog(self):
        """принятие кук"""
        try:
            cookie_btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cc-banner__button-accept')))
            cookie_btn.click()
            return True
        except:
            return False

    def _collect_articles(self) -> list[ArticleCard]:
        # Получаем контейнер с текущими статьями
        card_containers_list = driver.find_elements(By.CLASS_NAME, 'app-card-open__main')
        # Статьи с текущей страницы
        atrticles_on_current_page = []
        
        # Собираем каждую статью на текущей странице
        for card_container in card_containers_list:
            atrticles_on_current_page.append(self._get_articles(card_container))
        return atrticles_on_current_page

    def set_search_params(self, search_params):
        self.__search_params = search_params
    
    def _scrapping_articles(self, progress_parsing_page_cb: Optional[Callable[[PageInfo], None]] = None):
        try:           
            # Получаем количество страниц
            pages_range = self._get_pages_range()
            # Если страниц нет - выходим, т.к. результатов не найдено
            if not pages_range:
                return 

            article_dict = {}

            for page in pages_range:
                try:
                    time.sleep(2)
                    self._get({**self.__search_params, "page":page})

                    atrticles_on_current_page = self._collect_articles()

                    # Записываем в словарь с индексацией по странице 
                    article_dict[page] = atrticles_on_current_page

                    if progress_parsing_page_cb:
                        progress_parsing_page_cb({"current":page, "total":len(pages_range)})
                except Exception as ex:
                    print(f"Ошибка в сборе статей")
                    print(ex)
                    continue
            
            return article_dict
        except Exception as ex:
            print(f'Parsing error: {ex}') 
            driver.quit()
            return
        
    def start(self, progress_parsing_page_cb: Optional[Callable[[PageInfo], None]] = None):
        articles = self._scrapping_articles(progress_parsing_page_cb)
        return articles
        
       