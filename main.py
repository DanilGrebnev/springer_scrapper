from src.springer.scrapping_service import ScrappingService
from src.db.db_service import db_service
import time

def main():
    search_dict = {
        "query":"surface alloying of iron castings in a casting mold",
        "page":"",
        "dateFrom":"2016",
        "dateTo":"2017", 
        "sortBy":"relevance",
        "openAccess": "false"
    }
    start = time.time()
    scrapping_service = ScrappingService(search_dict)
    
    articles = scrapping_service.start()
    end = time.time()
    print(f"Время выполнения: {end - start:.2f} секунд")
    
    if not articles:
        return
    
    db_service.write(articles, file_name=f'articles_{search_dict['dateFrom']}-{search_dict['dateTo']}.json')
                     
if __name__ == "__main__":
    main()