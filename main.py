from src.springer.scrapping_service import ScrappingService
from src.db.db_service import db_service
import time


def main():
    search_dict = {
        "query":"surface alloying of iron castings in a casting mold",
        "page":"",
        "dateFrom":"2024",
        "dateTo":"2025", 
        "sortBy":"relevance",
        "openAccess": "false"
    }
    start = time.time()
    scrapping_service = ScrappingService(search_dict)
    
    articles = scrapping_service.start()
    end = time.time()
    print(f"Время выполнения: {end - start:.2f} секунд")
    db_service.write(articles)
                     
if __name__ == "__main__":
    main()