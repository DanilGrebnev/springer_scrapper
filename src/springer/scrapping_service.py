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

    def __create_search_url(self, search_params: dict):
        return create_url.search_page(**search_params)
    
    def __get_pages_range(self):
        '''получение количества страниц'''
        pages_amount = []

        try:
            webelements_list = driver.find_elements(By.CSS_SELECTOR, "[data-page]")

            for list_pagination_item in webelements_list:
                pages_amount.append(int(list_pagination_item.get_attribute('data-page')))
        except:
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

    def __get(self, search_params):
        '''driver.get with __create_search_url function'''
        driver.get(self.__create_search_url(search_params))

    def __get_articles(self, card_container: WebElement) -> ArticleCard:
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
    
    def __accept_cookie_dialog(self):
        """принятие кук"""
        try:
            cookie_btn = WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cc-banner__button-accept')))
            cookie_btn.click()
            return True
        except:
            return False

    def __scroll_slowly(self, scroll_pause=1):
        """Медленно скроллит страницу, имитируя поведение пользователя"""
        # Получаем высоту страницы
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Скроллим вниз
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Ждем загрузки
            time.sleep(scroll_pause)

            # Проверяем, загрузились ли новые элементы
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # Достигли конца
            last_height = new_height

    def __collect_articles(self) -> list[ArticleCard]:
        # Получаем контейнер с текущими статьями
        card_containers_list = driver.find_elements(By.CLASS_NAME, 'app-card-open__main')
        # Статьи с текущей страницы
        atrticles_on_current_page = []
        # Собираем каждую статью на текущей странице
        for card_container in card_containers_list:
            atrticles_on_current_page.append(self.__get_articles(card_container))
        
        return atrticles_on_current_page

    def set_search_params(self, search_params):
        self.__search_params = search_params
    
    def start(self, progress_parsing_page_cb: Optional[Callable[[PageInfo], None]] = None):
        try:
            '''
            Args:
                progress_parsing_page_cb: Опциональный callback, вызываемый после обработки каждой страницы.
                               Принимает PageInfo с полями:
                               - current: номер текущей страницы в списке
                               - total: общее количество страниц
            '''
            # Открываем страницу браузера и сразу оказываемся на первой странице
            self.__get(self.__search_params)
            # Принимаем окно с куками
            self.__accept_cookie_dialog()
            # Получаем количество страниц
            pages_range = self.__get_pages_range()

            # Если страниц нет - выходим, т.к. результатов не найдено
            if not pages_range:
                return 

            article_dict = {}

            for page in pages_range:
                time.sleep(2)
                self.__get({**self.__search_params, "page":page})

                atrticles_on_current_page = self.__collect_articles()

                # Записываем в словарь с индексацией по странице 
                article_dict[page] = atrticles_on_current_page

                if progress_parsing_page_cb:
                    progress_parsing_page_cb({"current":page, "total":len(pages_range)})

            return article_dict
        except Exception as ex:
            print(f'Parsing error: {ex}') 
            driver.quit()
            return