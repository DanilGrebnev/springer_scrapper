import logging
from typing import TypedDict, Callable, Optional
from src.scrapper.utils.create_url import create_url
from src.scrapper.chrome_factory import ChromeFactory
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)
driver_factory = ChromeFactory()

class PageInfo(TypedDict):
    current: int
    total: int

ArticleCard = TypedDict("ArticleCard", 
    {
        "id": str,
        "is_access": bool, 
        "title": str, 
        "link": str, 
        "description": str,
        "publications_type": str,
        "abstract": str,
        "authors": str,
        "published": str,
        "publish_name": str,
        "publish_link": str,
    })

class ScrappingService:
    def __init__(self, search_params):
        self._search_params = search_params
        
    _search_params = {
        "query":"",
        "page":"",
        "dateFrom":"",
        "dateTo":"", 
        "sortBy":"relevance",
        "openAccess": "false"
    }

    def _get(self, search_params, _driver, accept_cookies=False):
        '''Открывает страницу поиска Springer в переданном драйвере.
        accept_cookies=True — попытается закрыть баннер кук (только при первом заходе).'''
        _driver.get(self._create_search_url(search_params))

        if accept_cookies:
            try:
                cookie_btn = _driver.find_element(By.CLASS_NAME, 'cc-banner__button-accept')
                cookie_btn.click()
            except:
                pass
    
    def _create_search_url(self, search_params: dict):
        '''Собирает URL для поиска на Springer из словаря параметров (query, page, даты и т.д.)'''
        return create_url.search_page(**search_params)
    
    def _get_pages_range(self, _driver):
        '''Определяет диапазон страниц результатов поиска.
        Открывает первую страницу, находит элементы пагинации [data-page],
        извлекает номера страниц и возвращает список [1, 2, 3, ...N].
        Если результатов нет — возвращает пустой список.'''
        try:
            self._get(self._search_params, _driver, accept_cookies=True)
        except Exception as ex:
            print('Ошибка открытия страницы для подсчёта элементов пагинации')
            print(ex)
        
        pages_amount = []
        
        PAGES_SELECTOR = (By.CSS_SELECTOR, "[data-page]")
        
        try:
            wait = WebDriverWait(_driver, 10, poll_frequency=1)
            wait.until(EC.element_to_be_clickable(PAGES_SELECTOR))
            
            # Получаем список элементов пагинации
            webelements_list = _driver.find_elements(*PAGES_SELECTOR)
            
            for list_pagination_item in webelements_list:
                pages_amount.append(int(list_pagination_item.get_attribute('data-page')))
                
        except Exception as ex:
            print('Ошибка получения элементов пагинации')
            print(ex)
            return []
        
        return list(range(pages_amount[0], pages_amount[-1] + 1)) if len(pages_amount) > 1 else pages_amount 

    def _collect_article_detail(self, _driver, article_link: str) -> dict:
        '''Переходит на страницу статьи и извлекает abstract, название источника и ссылку на него.
        Возвращает словарь с ключами abstract, publish_name, publish_link.'''
        result = {"abstract": "", "publish_name": "", "publish_link": ""}
        try:
            _driver.get(article_link)
            wait = WebDriverWait(_driver, 5, poll_frequency=1)

            try:
                abstract_section = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#Abs1-content"))
                )
                paragraphs = abstract_section.find_elements(By.TAG_NAME, "p")
                result["abstract"] = " ".join(p.text for p in paragraphs)
            except Exception as ex:
                print(f"Ошибка сбора abstract для {article_link}: {ex}")

            try:
                el = _driver.find_element(By.CSS_SELECTOR, ".app-article-masthead__journal-title")
                result["publish_name"] = el.text.strip()
            except Exception:
                pass

            try:
                el = _driver.find_element(
                    By.CSS_SELECTOR,
                    ".app-article-masthead__conference-link, .app-article-masthead__journal-link",
                )
                href = el.get_attribute("href") or ""
                if href and not href.startswith("http"):
                    href = "https://link.springer.com" + href
                result["publish_link"] = href
            except Exception:
                pass

        except Exception as ex:
            print(f"Ошибка при сборе деталей статьи {article_link}: {ex}")

        return result

    # Сбор статей с 1 страницы
    def _collect_articles_list_from_page(self, _driver, page:int) -> list[ArticleCard]:
        '''Собирает все карточки статей с текущей открытой страницы.
        Для каждой карточки извлекает: title, link, description, type и is_access
        (есть ли полный доступ). Возвращает список словарей ArticleCard.'''
        def create_article_id(page, i):
            return f"{page}.{i + 1}"

        def _get_articles(card_container: WebElement, id) -> ArticleCard:
            # Тип и доступ к статье
            MetaInfo = TypedDict("MetaInfo", 
                {
                    "is_access": bool, 
                    "publications_type": str,
                    "authors": str,
                    "published": str
                })
            
            def get_meta_info(card_container: WebElement) -> MetaInfo:
                publications_type = card_container.find_element(By.CLASS_NAME, 'c-meta__type').text

                try:
                    card_container.find_element(By.CLASS_NAME, 'app-entitlement__icon--full-access')
                    is_access = True
                except Exception:
                    is_access = False

                authors = ""
                try:
                    el = card_container.find_element(By.CSS_SELECTOR, "[data-test='authors']")
                    authors = el.text
                except Exception:
                    pass

                published = ""
                try:
                    el = card_container.find_element(By.CSS_SELECTOR, "[data-test='published']")
                    published = el.text
                except Exception:
                    pass

                return {
                    "is_access": is_access, 
                    "publications_type": publications_type,
                    "authors": authors,
                    "published": published
                }
            def get_description_from_article(container: WebElement) -> str:
                try:
                    return container.find_element(By.CLASS_NAME, 'app-card-open__description').find_element(By.TAG_NAME, 'p').text
                except:
                    return container.find_element(By.CLASS_NAME, 'app-card-open__description').text    

            meta_info_result = get_meta_info(card_container)

            card_heading: WebElement = card_container.find_element(By.TAG_NAME, 'h3')

            title = card_heading.find_element(By.TAG_NAME, 'span').text
            link = card_heading.find_element(By.CLASS_NAME, 'app-card-open__link').get_attribute("href")
            description = get_description_from_article(card_container)
            
            card_meta: ArticleCard = {
                "id":id,
                "title":title,
                "link":link,
                "description":description,
                "abstract":"",
                **meta_info_result
            }

            return card_meta
        
        ARTICLE_SELECTOR = (By.CLASS_NAME, 'app-card-open__main')
        wait = WebDriverWait(_driver, 10, poll_frequency=1)
        wait.until(EC.element_to_be_clickable(ARTICLE_SELECTOR))
        
        # Получаем контейнер с текущими статьями
        card_containers_list = _driver.find_elements(*ARTICLE_SELECTOR)
        
        articles_list = [_get_articles(card_container, create_article_id(page, i)) for i, card_container in enumerate(card_containers_list)] 
        
        for article in articles_list:
            detail = self._collect_article_detail(_driver, article["link"])
            article["abstract"] = detail["abstract"]
            article["publish_name"] = detail["publish_name"]
            article["publish_link"] = detail["publish_link"]

        return articles_list
        
    def set_search_params(self, search_params):
        '''Перезаписывает параметры поиска (query, page, даты, сортировка и т.д.)'''
        self._search_params = search_params
     
    def _divide_pages(self, pages, split:int = 1) -> list[list]:
        """
            Разбивает список страниц на указанное количество подмассивов.

            Args:
                pages (list): Исходный список страниц для разбиения
                split (int, optional): Количество частей, на которые нужно разбить список. 
                                      По умолчанию 1.

            Returns:
                list[list]: Список, содержащий подмассивы страниц. Каждый подмассив - 
                           это часть исходного списка. Пустые подмассивы отфильтровываются.

            Example:
                >>> _divide_pages([1, 2, 3, 4, 5], split=2)
                [[1, 2, 3], [4, 5]]
            """
        return [page_parts.tolist() for page_parts in np.array_split(pages, split) if page_parts.tolist()]

    def _scrapping_articles_from_all_pages(self, pages_range: list[int]) -> dict:
        """
            Собирает статьи со страницы.

            Args:
                pages_range (list): Список страниц

            Returns:
                list[ArticleCard]

            Example:
                {"1": [{"is_access": bool, 
                    "title": str, 
                    "link": str, 
                    "description": str,
                    "publications_type": str,
                    "authors": str,
                    "published": str}]}
        """
        if not pages_range:
            return {}

        driver_local = driver_factory.create()

        result = {}

        try:
            for i, page in enumerate(pages_range):
                try:
                    logger.info("[Поток] Открываю страницу %d ...", page)
                    self._get(
                        {**self._search_params, "page": page},
                        _driver=driver_local,
                        accept_cookies = (i == 0)
                    )
                    
                    self._scroll_slowly(_driver=driver_local)
                    
                    articles = self._collect_articles_list_from_page(_driver=driver_local, page=page)
                    logger.info("[Поток] Страница %d: собрано %d статей", page, len(articles))
                    
                    result[page] = articles
                except Exception as ex:
                    logger.error("Ошибка в сборе статей на странице %d: %s", page, ex)
                    continue
        except Exception as ex:
            logger.error("Parsing error: %s", ex)
        finally:
            driver_local.quit()

        return result
    
    # Плавный скролл вниз страницы
    def _scroll_slowly(self, _driver, scroll_pause: float = 0.5, max_scrolls: int = 10):
        """
        Плавно скроллит страницу для подгрузки динамического контента

        Args:
            _driver: WebDriver
            scroll_pause: пауза между скроллами в секундах
            max_scrolls: максимальное количество скроллов
        """
        last_height = _driver.execute_script("return document.body.scrollHeight")

        for i in range(max_scrolls):
            # Плавный скролл вниз
            _driver.execute_script("""
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            """)

            # Ждем завершения анимации и загрузки
            time.sleep(scroll_pause)

            # Проверяем, загрузились ли новые элементы
            new_height = _driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
    # Основная функция, запускающая мультипоточное выполнение
    def _start_multythreads_scrapping(self, threads_amount:int=3) -> dict[str, list[ArticleCard]] | None:
        """
            Запускает многопоточный сбор статей со всех страниц.

            Метод выполняет следующие шаги:
            1. Получает общий список страниц для парсинга
            2. Разбивает список страниц на части согласно количеству потоков
            3. Запускает параллельный сбор статей с каждой группы страниц
            4. Объединяет результаты из всех потоков

            Args:
                threads_amount (int, optional): Количество потоков для параллельного выполнения.
                                               По умолчанию 3.

            Returns:
                dict[str, list[ArticleCard]]: Словарь, где ключи - номера страниц (в виде строк),
                                              значения - списки объектов статей типа ArticleCard.

                ArticleCard содержит следующие поля:
                    - id (str): Идентификатор статьи в формате "{page}.{index}"
                    - is_access (bool): Доступна ли статья для чтения
                    - title (str): Название статьи
                    - link (str): URL ссылка на статью
                    - description (str): Краткое описание/аннотация статьи
                    - publications_type (str): Тип публикации (например, "Article", "Review" и т.д.)
                    - authors (str): Авторы статьи
                    - published (str): Дата публикации

            Returns:
                None: В случае отсутствия страниц или ошибки при получении диапазона страниц

            Example:
                >>> result = scraper._start_multythreads_scrapping(threads_amount=4)
                >>> print(result)
                {
                    "1": [
                        {
                            "id": "1.1",
                            "title": "Microstructure in non-standard heavy section...",
                            "link": "https://link.springer.com/article/10.1007/s42243-025-01598-y",
                            "description": "Ductile iron represents an optimal solution...",
                            "is_access": false,
                            "publications_type": "Article",
                            "authors": "...",
                            "published": "22 August 2025"
                        },
                    ],
                    "2": [...]
                }

            Note:
                - Каждый поток создает свой экземпляр WebDriver
                - При возникновении ошибки на отдельной странице, она логируется и сбор продолжается
                - Результаты всех потоков объединяются в единый словарь
                - Ключи в результирующем словаре - строковые представления номеров страниц
            """
        logger.info("--- Шаг 1: Определяем диапазон страниц ---")
        driver = driver_factory.create()
        pages_range = self._get_pages_range(driver)
        driver.quit()
        logger.info("Найдено страниц: %d %s", len(pages_range), pages_range)
        
        divided_pages = self._divide_pages(pages_range, split=threads_amount)
        
        if not divided_pages:
            logger.warning("Список страниц пустой — результатов нет")
            return None

        logger.info("--- Шаг 2: Разбиваем на %d потока(ов) ---", len(divided_pages))
        for i, chunk in enumerate(divided_pages):
            logger.info("  Поток %d: страницы %s", i + 1, chunk)
        
        articles_result = {}
        
        logger.info("--- Шаг 3: Запускаем многопоточный сбор ---")
        with ThreadPoolExecutor(max_workers=len(divided_pages)) as executor:
            futures = [executor.submit(self._scrapping_articles_from_all_pages, pages) for pages in divided_pages]
            
            for future in futures:
               articles_result.update(future.result())

        logger.info("--- Шаг 4: Сбор завершён ---")
            
        return articles_result
        
    def start(self):
       return self._start_multythreads_scrapping()