import json
from typing import Optional

class DB_Service:
    url_to_file = ''
    def __init__(self, url_to_file):
        self.url_to_file = url_to_file

    def write(self, payload, file_name: Optional[str | None]):
        string_data = json.dumps(payload, indent=2, ensure_ascii=False)
        
        with open(file_name if file_name else self.url_to_file, "w", encoding='utf-8') as file:
            file.write(string_data)


db_service = DB_Service(F'articles.txt')