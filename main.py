from src.springer.utils.create_article_card import create_article_card
from src.springer.utils.create_url import create_url
from src.driver import driver
from selenium.webdriver.common.by import By
import time  
from pprint import pprint

def get_url(page: int = 1, open_access: bool = False):
    return create_url.search_page(
    query='surface alloying of iron castings in a casting mold', 
    page=page,
    dateFrom=2025,
    dateTo=2025, 
    sortBy='relevance',
    openAccess = str(open_access).lower() 
)

def get_pagination_range() -> list[int]:
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
        return list(range(pages_amount[0], pages_amount[-1] + 1))
    else:
        return pages_amount







def main():
    # Изначальное открытие браузера для подсчета количества страниц
    driver.get(get_url())

    article_dict = {}

    # Получаем список страниц по запросу
    page_list = get_pagination_range()
    
    # Если список страниц пустой - прекращаем выполнение
    if not page_list:
        return

    # Открываем каждую страницу
    for page in page_list:
        driver.get(get_url(page=page))
        # Получаем контейнер с текущими статьями
        card_containers_list = driver.find_elements(By.CLASS_NAME, 'app-card-open__main')
        atricles_on_current_page = []

        for card_container in card_containers_list:
            article = create_article_card(card_container)
            atricles_on_current_page.append(article)

        time.sleep(1)

    


             
if __name__ == "__main__":
    main()