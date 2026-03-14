from typing import TypedDict
from src.springer.utils.create_url import create_url
from src.driver import driver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
from src.db.db_service import db_service


ArticleCard = TypedDict("ArticleCard", 
    {
        "is_access": bool, 
        "title": str, 
        "link": str, 
        "description": str,
        "type": str
    })

search_dict = {
    "query":"",
    "page":"",
    "dateFrom":"2025",
    "dateTo":"2025", 
    "sortBy":"relevance",
    "openAccess": "false"
}

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

    def __create_search_url(self, search_params):
        return create_url.search_page(**search_params)

    def __get_pages_list(self):
        driver.get(self.__create_search_url(self.__search_params))
        pages_amount = []

        try:
            webelements_list = driver.find_elements(By.CSS_SELECTOR, "[data-page]")

            for list_pagination_item in webelements_list:
                pages_amount.append(int(list_pagination_item.get_attribute('data-page')))
        except:
            return []

        ''' 
        Если кол-во страниц больше 1, то берем номер первой и поледней страницы
        и заполняем список
        '''
        if len(pages_amount) > 1:
            pages_list = list(range(pages_amount[0], pages_amount[-1] + 1))
            return pages_list
        else:
            return pages_amount

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

    def set_search_params(self, search_params):
        self.__search_params = search_params

    def start(self):
        # Сначала получаем количество страниц
        pages_list = self.__get_pages_list()

        # Если страниц нет - выходим, т.к. результатов не найдено
        if not pages_list:
            return 

        article_dict = {}
        # Открываем каждую страницу
        for page in pages_list:
            # Открываем страницу
            driver.get(self.__create_search_url({**self.__search_params, "page": page}))

            # Получаем контейнер с текущими статьями
            card_containers_list = driver.find_elements(By.CLASS_NAME, 'app-card-open__main')
            # Статьи с текущей страницы
            atrticles_on_current_page = []

            # Собираем каждую статью на текущей странице
            for card_container in card_containers_list:
                atrticles_on_current_page.append(self.__get_articles(card_container))

            # Записываем в словарь с индексацией по странице 
            article_dict[page] = atrticles_on_current_page

        return article_dict