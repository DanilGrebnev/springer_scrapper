from typing import TypedDict
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.common.by import By  

# Полный тип статьи
ArticleCard = TypedDict("ArticleCard", 
    {
        "is_access": bool, 
        "title": str, 
        "link": str, 
        "description": str,
        "type": str
    })

# Тип и доступ к статье
MetaInfo = TypedDict("MetaInfo", 
    {
            "is_access": bool, 
            "type": str
    })

def get_description_from_article(container: WebElement) -> str:
    try:
        return container.find_element(By.CLASS_NAME, 'app-card-open__description').find_element(By.TAG_NAME, 'p').text
    except:
        return container.find_element(By.CLASS_NAME, 'app-card-open__description').text

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

# Создание статьи из страницы пагинации
def create_article_card(card_container: WebElement) -> ArticleCard:
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
