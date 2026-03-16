from src.springer.scrapping_service import ScrappingService
from src.db.db_service import db_service
from src.springer.scrapping_service import PageInfo

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
    
    def print_parsed_page(page: PageInfo):
        print(f"[+] {page['current']} / {page['total']}")

    articles = scrapping_service.start(progress_parsing_page_cb=print_parsed_page)
    # db_service.write(articles)
                     
if __name__ == "__main__":
    main()