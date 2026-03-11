from yarl import URL

class PageCreateUrl():
    base_url = URL('https://link.springer.com/search')

    def search_page(self, **query):
        return str(self.base_url.with_query(**query)) 
    
    def article_detail_page(self):
        pass

create_url = PageCreateUrl()