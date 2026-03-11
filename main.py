from src.springer.utils.create_article_card import create_article_card
from src.springer.utils.create_url import create_url
from src.driver import driver
from selenium.webdriver.common.by import By  
from pprint import pprint


search_page_url = create_url.search_page(
    query='surface alloying of iron castings in a casting mold', 
    page=1, 
    sortBy='relevance',
    # openAccess='true'
)

def main():
    driver.get(search_page_url)
    card_containers_list = driver.find_elements(By.CLASS_NAME, 'app-card-open__main')

    for card_container in card_containers_list:
        article = create_article_card(card_container)
        pprint(article, sort_dicts=False)

             
if __name__ == "__main__":
    main()