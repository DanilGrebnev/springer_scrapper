import json

class DB_Service:
    url_to_file = ''
    def __init__(self, url_to_file):
        self.url_to_file = url_to_file

    def write(self, payload):
        string_data = json.dumps(payload, indent=2, ensure_ascii=False)
        
        with open(self.url_to_file, "w", encoding='utf-8') as file:
            file.write(string_data)


db_service = DB_Service('articles.txt')