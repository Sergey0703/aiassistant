"""
Реальный web scraper с парсингом страниц
"""
import asyncio
import time
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

@dataclass
class ScrapedDocument:
    url: str
    title: str
    content: str
    metadata: Dict
    category: str = "scraped"

class LegalSiteScraper:
    """Реальный скрапер с поддержкой парсинга HTML"""
    
    def __init__(self):
        self.legal_sites_config = {
            # Ирландские сайты
            "citizensinformation.ie": {
                "title": "h1, .page-title, .main-title",
                "content": ".main-content, .content, article, .text-content",
                "exclude": "nav, .navigation, footer, .sidebar, .ads, .menu"
            },
            "irishstatutebook.ie": {
                "title": "h1, .title",
                "content": ".akn-akomaNtoso, .content, .main",
                "exclude": ".navigation, .sidebar"
            },
            "courts.ie": {
                "title": "h1, .page-title",
                "content": ".content, .main, article",
                "exclude": ".header, .footer, .navigation"
            },
            # Украинские сайты
            "zakon.rada.gov.ua": {
                "title": "h1, .page-title",
                "content": ".field-item, .content, .main",
                "exclude": ".sidebar, .navigation, .menu"
            },
            "court.gov.ua": {
                "title": "h1",
                "content": ".content-area, .main-content",
                "exclude": ".header, .footer"
            }
        }
    
    async def scrape_legal_site(self, url: str) -> Optional[ScrapedDocument]:
        """Парсит веб-страницу"""
        try:
            # Импортируем библиотеки только при необходимости
            try:
                import requests
                from bs4 import BeautifulSoup
                from urllib.parse import urlparse
            except ImportError:
                logger.warning("requests или beautifulsoup4 не установлены, используем демо режим")
                return await self._create_demo_document(url)
            
            # Настройки для запроса
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Делаем запрос с таймаутом
            logger.info(f"Fetching: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Парсим HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Получаем конфигурацию для домена
            domain = urlparse(url).netloc
            selectors = self.legal_sites_config.get(domain, {})
            
            # Извлекаем заголовок
            title = self._extract_title(soup, selectors) or f"Документ с {domain}"
            
            # Извлекаем контент
            content = self._extract_content(soup, selectors)
            
            if not content or len(content.strip()) < 100:
                logger.warning(f"Мало контента получено с {url}, используем демо")
                return await self._create_demo_document(url)
            
            # Создаем метаданные
            metadata = {
                "scraped_at": time.time(),
                "status_code": response.status_code,
                "content_type": response.headers.get('content-type', ''),
                "domain": domain,
                "url": url,
                "word_count": len(content.split()),
                "char_count": len(content),
                "real_scraping": True
            }
            
            logger.info(f"✅ Успешно спарсено {len(content)} символов с {url}")
            
            return ScrapedDocument(
                url=url,
                title=title,
                content=content,
                metadata=metadata,
                category=self._categorize_by_domain(domain)
            )
            
        except Exception as e:
            logger.error(f"Ошибка парсинга {url}: {str(e)}")
            # В случае ошибки возвращаем демо документ
            return await self._create_demo_document(url)
    
    async def _create_demo_document(self, url: str) -> ScrapedDocument:
        """Создает демо документ если реальный парсинг не удался"""
        demo_content = f"""
ДЕМО: Документ с {url}

⚠️ Это демонстрационный контент. Реальный парсинг не удался по одной из причин:
- Отсутствуют библиотеки requests/beautifulsoup4
- Сайт заблокировал доступ
- Проблемы с сетью
- Нестандартная структура страницы

Для полноценного парсинга установите:
pip install requests beautifulsoup4

Содержимое demo документа:
Этот документ содержит общую информацию о юридических требованиях и процедурах.
Основные разделы включают информацию о документах, сроках и требованиях.

URL: {url}
Дата создания: {time.strftime('%Y-%m-%d %H:%M:%S')}
Статус: Демо режим
"""
        
        return ScrapedDocument(
            url=url,
            title=f"ДЕМО: Документ с {url}",
            content=demo_content.strip(),
            metadata={
                "scraped_at": time.time(),
                "status": "demo",
                "real_scraping": False,
                "word_count": len(demo_content.split()),
                "char_count": len(demo_content),
                "url": url
            },
            category="demo"
        )
    
    def _extract_title(self, soup, selectors: Dict[str, str] = None) -> str:
        """Извлекает заголовок страницы"""
        if selectors and "title" in selectors:
            for selector in selectors["title"].split(", "):
                title_elem = soup.select_one(selector.strip())
                if title_elem and title_elem.get_text(strip=True):
                    return title_elem.get_text(strip=True)
        
        # Fallback селекторы
        for selector in ['h1', 'title', '.title', '.page-title', '.main-title']:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                return elem.get_text(strip=True)
        
        return "Без заголовка"
    
    def _extract_content(self, soup, selectors: Dict[str, str] = None) -> str:
        """Извлекает основной контент страницы"""
        
        # Удаляем ненужные элементы
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]):
            tag.decompose()
        
        # Удаляем элементы по exclude селекторам
        if selectors and "exclude" in selectors:
            for selector in selectors["exclude"].split(", "):
                for elem in soup.select(selector.strip()):
                    elem.decompose()
        
        content_text = ""
        
        # Пробуем извлечь по content селекторам
        if selectors and "content" in selectors:
            for selector in selectors["content"].split(", "):
                content_elem = soup.select_one(selector.strip())
                if content_elem:
                    content_text = content_elem.get_text()
                    break
        
        # Fallback селекторы
        if not content_text:
            for selector in ['.main-content', '.content', 'article', '.post', 'main', '.main']:
                elem = soup.select_one(selector)
                if elem:
                    content_text = elem.get_text()
                    break
        
        # Последний fallback - весь body
        if not content_text:
            body = soup.find('body')
            if body:
                content_text = body.get_text()
        
        # Очищаем текст
        return self._clean_text(content_text)
    
    def _clean_text(self, text: str) -> str:
        """Очищает и форматирует текст"""
        if not text:
            return ""
        
        # Убираем лишние пробелы и переносы
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Убираем повторяющиеся символы
        text = re.sub(r'\.{3,}', '...', text)
        text = re.sub(r'-{3,}', '---', text)
        
        # Убираем очень короткие строки (меню, навигация)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 10:  # Оставляем только строки длиннее 10 символов
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Ограничиваем размер документа
        if len(result) > 10000:
            result = result[:10000] + "\n\n[Документ обрезан до 10000 символов]"
        
        return result
    
    def _categorize_by_domain(self, domain: str) -> str:
        """Определяет категорию по домену"""
        if "zakon" in domain or "law" in domain:
            return "legislation"
        elif "court" in domain:
            return "jurisprudence"  
        elif "justice" in domain or "minjust" in domain:
            return "government"
        elif "citizen" in domain or "immigration" in domain:
            return "civil_rights"
        elif "rada.gov.ua" in domain:
            return "ukraine_legal"
        elif any(irish in domain for irish in ["courts.ie", "irishstatutebook.ie", "citizensinformation.ie"]):
            return "ireland_legal"
        else:
            return "scraped"
    
    async def scrape_multiple_urls(self, urls: List[str], delay: float = 1.0) -> List[ScrapedDocument]:
        """Парсит несколько URL с задержкой"""
        documents = []
        
        for i, url in enumerate(urls):
            logger.info(f"Парсинг {i+1}/{len(urls)}: {url}")
            
            document = await self.scrape_legal_site(url)
            if document:
                documents.append(document)
                if document.metadata.get("real_scraping", False):
                    logger.info(f"✅ Реально спарсено: {document.title}")
                else:
                    logger.info(f"⚠️ Демо документ: {document.title}")
            else:
                logger.warning(f"❌ Не удалось парсить: {url}")
            
            # Задержка между запросами для вежливости к серверам
            if delay > 0 and i < len(urls) - 1:
                await asyncio.sleep(delay)
        
        return documents

# Предопределенные списки юридических сайтов
UKRAINE_LEGAL_URLS = [
    "https://zakon.rada.gov.ua/laws/main",
    "https://court.gov.ua/",
    "https://minjust.gov.ua/",
    "https://ccu.gov.ua/",
    "https://npu.gov.ua/"
]

IRELAND_LEGAL_URLS = [
    "https://www.irishstatutebook.ie/",
    "https://www.courts.ie/",
    "https://www.citizensinformation.ie/en/",
    "https://www.justice.ie/",
    "https://www.oireachtas.ie/"
]

# Функция для тестирования
async def test_real_scraper():
    """Тестирует реальный парсинг"""
    scraper = LegalSiteScraper()
    
    test_urls = [
        "https://www.citizensinformation.ie/en/moving-country/irish-citizenship/",
        "https://www.example.com"  # Для демонстрации fallback
    ]
    
    for url in test_urls:
        print(f"\n🔍 Тестируем: {url}")
        document = await scraper.scrape_legal_site(url)
        
        if document:
            print(f"✅ Заголовок: {document.title}")
            print(f"📊 Размер: {len(document.content)} символов")
            print(f"🔍 Реальный парсинг: {document.metadata.get('real_scraping', False)}")
            print(f"📄 Превью: {document.content[:200]}...")
        else:
            print(f"❌ Не удалось спарсить")

if __name__ == "__main__":
    asyncio.run(test_real_scraper())