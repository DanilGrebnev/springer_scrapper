from src.springer.scrapping_service import ScrappingService
from src.db.db_service import db_service

def main():
    search_dict = {
        "query":"surface alloying of iron castings in a casting mold",
        "page":"",
        "dateFrom":"2024",
        "dateTo":"2025", 
        "sortBy":"relevance",
        "openAccess": "false"
    }

    scrapping_service = ScrappingService(search_dict)
    articles = scrapping_service.start()
    db_service.write(articles)
                     
if __name__ == "__main__":
    main()