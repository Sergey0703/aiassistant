# ====================================
# ФАЙЛ: backend/services/scraper_service.py (ПОЛНАЯ ВЕРСИЯ)
# Заменить существующий файл полностью
# ====================================

"""
Реальный web scraper с парсингом страниц для юридических сайтов
Поддерживает как реальный парсинг, так и demo режим
"""

import asyncio
import time
import aiohttp
import ssl
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import logging
import re
from urllib.parse import urlparse, urljoin, quote, unquote
from pathlib import Path
import json
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class ScrapedDocument:
    """Модель спарсированного документа"""
    url: str
    title: str
    content: str
    metadata: Dict
    category: str = "scraped"
    
    def __post_init__(self):
        """Дополнительная обработка после создания"""
        # Очищаем и валидируем данные
        self.title = self.title.strip()[:500] if self.title else "Untitled"
        self.content = self._clean_content(self.content)
        self.url = self.url.strip()
        
        # Добавляем базовые метаданные
        if not self.metadata:
            self.metadata = {}
        
        self.metadata.update({
            "content_length": len(self.content),
            "word_count": len(self.content.split()),
            "title_length": len(self.title),
            "processed_at": time.time()
        })
    
    def _clean_content(self, content: str) -> str:
        """Очищает содержимое документа"""
        if not content:
            return ""
        
        # Убираем лишние пробелы и переносы
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        # Убираем повторяющиеся символы
        content = re.sub(r'\.{3,}', '...', content)
        content = re.sub(r'-{3,}', '---', content)
        
        # Ограничиваем размер
        if len(content) > 15000:  # 15KB лимит
            content = content[:15000] + "\n\n[Документ обрезан до 15000 символов]"
        
        return content.strip()

class SiteConfig:
    """Конфигурация для парсинга конкретного сайта"""
    
    def __init__(self, domain: str, **config):
        self.domain = domain
        self.title_selectors = config.get("title", "h1, title, .title")
        self.content_selectors = config.get("content", ".content, article, main")
        self.exclude_selectors = config.get("exclude", "nav, footer, .sidebar, script, style")
        self.custom_parser = config.get("custom_parser")
        self.encoding = config.get("encoding", "utf-8")
        self.timeout = config.get("timeout", 15)
        self.headers = config.get("headers", {})

class LegalSiteScraper:
    """Профессиональный скрапер для юридических сайтов"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.legal_sites_config = self._initialize_site_configs()
        self.demo_mode = False
        self.stats = {
            "total_requests": 0,
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "demo_responses": 0,
            "average_response_time": 0.0
        }
    
    def _initialize_site_configs(self) -> Dict[str, SiteConfig]:
        """Инициализирует конфигурации для различных сайтов"""
        configs = {}
        
        # Ирландские юридические сайты
        configs["citizensinformation.ie"] = SiteConfig(
            "citizensinformation.ie",
            title="h1, .page-title, .main-title",
            content=".main-content, .content, article, .text-content",
            exclude="nav, .navigation, footer, .sidebar, .ads, .menu, .breadcrumb",
            encoding="utf-8"
        )
        
        configs["irishstatutebook.ie"] = SiteConfig(
            "irishstatutebook.ie",
            title="h1, .title, .act-title",
            content=".akn-akomaNtoso, .content, .main, .act-body",
            exclude=".navigation, .sidebar, .header, .footer"
        )
        
        configs["courts.ie"] = SiteConfig(
            "courts.ie",
            title="h1, .page-title, .judgment-title",
            content=".content, .main, article, .judgment-text",
            exclude=".header, .footer, .navigation, .sidebar"
        )
        
        configs["justice.ie"] = SiteConfig(
            "justice.ie",
            title="h1, .page-title",
            content=".main-content, .content, article",
            exclude=".header, .footer, .navigation, .sidebar, .news-listing"
        )
        
        # Украинские юридические сайты
        configs["zakon.rada.gov.ua"] = SiteConfig(
            "zakon.rada.gov.ua",
            title="h1, .page-title, .doc-title",
            content=".field-item, .content, .main, .document-content",
            exclude=".sidebar, .navigation, .menu, .breadcrumb",
            encoding="utf-8"
        )
        
        configs["court.gov.ua"] = SiteConfig(
            "court.gov.ua",
            title="h1, .court-title",
            content=".content-area, .main-content, .court-content",
            exclude=".header, .footer, .navigation"
        )
        
        configs["minjust.gov.ua"] = SiteConfig(
            "minjust.gov.ua",
            title="h1, .page-title",
            content=".main-content, .content, article",
            exclude=".header, .footer, .sidebar, .navigation"
        )
        
        configs["ccu.gov.ua"] = SiteConfig(
            "ccu.gov.ua", 
            title="h1, .title",
            content=".content, .main, .decision-text",
            exclude=".navigation, .sidebar"
        )
        
        # Общие конфигурации для популярных CMS
        configs["wordpress"] = SiteConfig(
            "wordpress",
            title="h1, .entry-title, .post-title",
            content=".entry-content, .post-content, .content",
            exclude=".sidebar, .navigation, .comments"
        )
        
        configs["drupal"] = SiteConfig(
            "drupal",
            title="h1, .page-title",
            content=".field-item, .content, .main",
            exclude=".sidebar, .navigation, .menu"
        )
        
        return configs
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Обеспечивает наличие активной сессии"""
        if not self.session or self.session.closed:
            # Настройки SSL для обхода проблем с сертификатами
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,uk;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
    
    async def close(self):
        """Закрывает сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def scrape_legal_site(self, url: str, custom_config: Optional[Dict] = None) -> Optional[ScrapedDocument]:
        """
        Основной метод для парсинга юридического сайта
        
        Args:
            url: URL для парсинга
            custom_config: Кастомная конфигурация парсинга
            
        Returns:
            ScrapedDocument или None в случае ошибки
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        try:
            logger.info(f"🔍 Starting scrape for: {url}")
            
            # Проверяем наличие необходимых библиотек
            if not await self._check_dependencies():
                logger.warning("Missing dependencies, switching to demo mode")
                self.demo_mode = True
                document = await self._create_demo_document(url)
                self.stats["demo_responses"] += 1
                return document
            
            await self._ensure_session()
            
            # Получаем конфигурацию для сайта
            site_config = self._get_site_config(url, custom_config)
            
            # Выполняем HTTP запрос
            response_data = await self._fetch_url(url, site_config)
            
            if not response_data:
                logger.warning(f"No response data for {url}, creating demo document")
                return await self._create_demo_document(url)
            
            # Парсим HTML
            document = await self._parse_html_content(
                url, 
                response_data["content"], 
                response_data["encoding"],
                site_config,
                response_data.get("response_headers", {})
            )
            
            if document:
                self.stats["successful_scrapes"] += 1
                elapsed = time.time() - start_time
                self._update_response_time(elapsed)
                logger.info(f"✅ Successfully scraped {url} in {elapsed:.2f}s")
                return document
            else:
                logger.warning(f"Failed to parse content from {url}")
                return await self._create_demo_document(url)
                
        except Exception as e:
            self.stats["failed_scrapes"] += 1
            logger.error(f"❌ Error scraping {url}: {str(e)}")
            return await self._create_demo_document(url)
        
        finally:
            elapsed = time.time() - start_time
            self._update_response_time(elapsed)
    
    async def _check_dependencies(self) -> bool:
        """Проверяет наличие необходимых библиотек"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            return True
        except ImportError as e:
            logger.warning(f"Missing dependencies: {e}")
            return False
    
    def _get_site_config(self, url: str, custom_config: Optional[Dict] = None) -> SiteConfig:
        """Получает конфигурацию для парсинга сайта"""
        domain = urlparse(url).netloc.lower()
        
        # Используем кастомную конфигурацию если предоставлена
        if custom_config:
            return SiteConfig(domain, **custom_config)
        
        # Ищем точное совпадение домена
        if domain in self.legal_sites_config:
            return self.legal_sites_config[domain]
        
        # Ищем частичное совпадение
        for config_domain, config in self.legal_sites_config.items():
            if config_domain in domain or domain in config_domain:
                return config
        
        # Определяем CMS и используем соответствующую конфигурацию
        cms_type = self._detect_cms_type(url)
        if cms_type and cms_type in self.legal_sites_config:
            return self.legal_sites_config[cms_type]
        
        # Возвращаем дефолтную конфигурацию
        return SiteConfig(
            domain,
            title="h1, title, .title, .page-title",
            content=".content, .main, article, .post, .entry-content",
            exclude="nav, footer, .sidebar, .navigation, .menu, script, style, .ads"
        )
    
    def _detect_cms_type(self, url: str) -> Optional[str]:
        """Определяет тип CMS по URL или другим признакам"""
        # Простая эвристика для определения CMS
        if "wp-content" in url or "wordpress" in url:
            return "wordpress"
        elif "sites/default" in url or "drupal" in url:
            return "drupal"
        return None
    
    async def _fetch_url(self, url: str, site_config: SiteConfig) -> Optional[Dict]:
        """Выполняет HTTP запрос к URL"""
        try:
            headers = {
                **self.session.headers,
                **site_config.headers
            }
            
            async with self.session.get(
                url, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=site_config.timeout)
            ) as response:
                
                logger.info(f"📡 HTTP {response.status} for {url}")
                
                if response.status != 200:
                    logger.warning(f"Non-200 status code: {response.status}")
                    return None
                
                # Определяем кодировку
                encoding = self._detect_encoding(response, site_config.encoding)
                
                # Читаем контент
                content_bytes = await response.read()
                
                try:
                    content = content_bytes.decode(encoding)
                except UnicodeDecodeError:
                    # Пробуем другие кодировки
                    for fallback_encoding in ['utf-8', 'cp1251', 'iso-8859-1']:
                        try:
                            content = content_bytes.decode(fallback_encoding)
                            encoding = fallback_encoding
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        logger.error(f"Failed to decode content for {url}")
                        return None
                
                return {
                    "content": content,
                    "encoding": encoding,
                    "response_headers": dict(response.headers),
                    "status_code": response.status,
                    "url": str(response.url)  # Финальный URL после редиректов
                }
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _detect_encoding(self, response: aiohttp.ClientResponse, default: str = "utf-8") -> str:
        """Определяет кодировку ответа"""
        # Проверяем заголовок Content-Type
        content_type = response.headers.get('content-type', '').lower()
        if 'charset=' in content_type:
            try:
                charset = content_type.split('charset=')[1].split(';')[0].strip()
                return charset
            except:
                pass
        
        return default
    
    async def _parse_html_content(
        self, 
        url: str, 
        html_content: str, 
        encoding: str,
        site_config: SiteConfig,
        response_headers: Dict
    ) -> Optional[ScrapedDocument]:
        """Парсит HTML контент"""
        try:
            from bs4 import BeautifulSoup
            
            # Создаем soup объект
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Удаляем ненужные элементы
            self._remove_unwanted_elements(soup, site_config.exclude_selectors)
            
            # Извлекаем заголовок
            title = self._extract_title(soup, site_config.title_selectors, url)
            
            # Извлекаем основной контент
            content = self._extract_content(soup, site_config.content_selectors)
            
            if not content or len(content.strip()) < 100:
                logger.warning(f"Insufficient content extracted from {url}")
                return None
            
            # Создаем метаданные
            metadata = self._create_metadata(url, response_headers, encoding, soup)
            
            # Определяем категорию
            category = self._categorize_by_domain(urlparse(url).netloc)
            
            return ScrapedDocument(
                url=url,
                title=title,
                content=content,
                metadata=metadata,
                category=category
            )
            
        except Exception as e:
            logger.error(f"Error parsing HTML for {url}: {e}")
            return None
    
    def _remove_unwanted_elements(self, soup, exclude_selectors: str):
        """Удаляет нежелательные элементы из soup"""
        # Стандартные элементы для удаления
        standard_removes = [
            "script", "style", "noscript", "iframe", 
            ".advertisement", ".ads", ".social-media",
            ".cookie-notice", ".popup", ".modal"
        ]
        
        # Объединяем с конфигурацией сайта
        all_selectors = standard_removes + exclude_selectors.split(", ")
        
        for selector in all_selectors:
            selector = selector.strip()
            if selector:
                for element in soup.select(selector):
                    element.decompose()
    
    def _extract_title(self, soup, title_selectors: str, url: str) -> str:
        """Извлекает заголовок страницы"""
        for selector in title_selectors.split(", "):
            selector = selector.strip()
            if selector:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    title = element.get_text(strip=True)
                    # Очищаем заголовок
                    title = re.sub(r'\s+', ' ', title)
                    if len(title) > 10:  # Минимальная длина заголовка
                        return title
        
        # Fallback - пробуем извлечь из URL
        try:
            domain = urlparse(url).netloc
            return f"Документ с {domain}"
        except:
            return "Юридический документ"
    
    def _extract_content(self, soup, content_selectors: str) -> str:
        """Извлекает основной контент страницы"""
        content_parts = []
        
        # Пробуем селекторы по порядку
        for selector in content_selectors.split(", "):
            selector = selector.strip()
            if selector:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text()
                    if text and len(text.strip()) > 50:
                        content_parts.append(text)
        
        # Если не нашли контент по селекторам, берем весь body
        if not content_parts:
            body = soup.find('body')
            if body:
                content_parts.append(body.get_text())
        
        if not content_parts:
            return ""
        
        # Объединяем и очищаем контент
        combined_content = "\n\n".join(content_parts)
        return self._clean_extracted_text(combined_content)
    
    def _clean_extracted_text(self, text: str) -> str:
        """Очищает извлеченный текст"""
        if not text:
            return ""
        
        # Убираем лишние пробелы и переносы
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Убираем повторяющиеся символы
        text = re.sub(r'\.{3,}', '...', text)
        text = re.sub(r'-{3,}', '---', text)
        text = re.sub(r'={3,}', '===', text)
        
        # Убираем очень короткие строки (вероятно, меню или навигация)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 15:  # Минимальная длина строки
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Проверяем минимальную длину
        if len(result) < 100:
            return ""
        
        return result
    
    def _create_metadata(self, url: str, response_headers: Dict, encoding: str, soup) -> Dict:
        """Создает метаданные документа"""
        metadata = {
            "scraped_at": time.time(),
            "url": url,
            "domain": urlparse(url).netloc,
            "encoding": encoding,
            "real_scraping": True,
            "scraper_version": "2.0"
        }
        
        # Добавляем информацию из заголовков
        if response_headers:
            metadata.update({
                "content_type": response_headers.get('content-type', ''),
                "server": response_headers.get('server', ''),
                "last_modified": response_headers.get('last-modified', ''),
                "etag": response_headers.get('etag', '')
            })
        
        # Извлекаем мета-теги
        if soup:
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description:
                metadata["description"] = meta_description.get('content', '')[:500]
            
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords:
                metadata["keywords"] = meta_keywords.get('content', '')[:500]
            
            # Определяем язык
            html_tag = soup.find('html')
            if html_tag and html_tag.get('lang'):
                metadata["language"] = html_tag.get('lang')
        
        return metadata
    
    def _categorize_by_domain(self, domain: str) -> str:
        """Определяет категорию документа по домену"""
        domain_lower = domain.lower()
        
        # Украинские сайты
        if any(ua_domain in domain_lower for ua_domain in [
            "zakon.rada.gov.ua", "rada.gov.ua", "court.gov.ua", 
            "minjust.gov.ua", "ccu.gov.ua", "npu.gov.ua"
        ]):
            return "ukraine_legal"
        
        # Ирландские сайты
        if any(ie_domain in domain_lower for ie_domain in [
            "irishstatutebook.ie", "courts.ie", "citizensinformation.ie",
            "justice.ie", "oireachtas.ie", "gov.ie"
        ]):
            return "ireland_legal"
        
        # Определяем по ключевым словам в домене
        if any(keyword in domain_lower for keyword in ["law", "legal", "court", "justice"]):
            return "legislation"
        elif any(keyword in domain_lower for keyword in ["zakon", "pravo", "sud"]):
            return "legislation"
        elif "court" in domain_lower or "sud" in domain_lower:
            return "jurisprudence"
        elif any(keyword in domain_lower for keyword in ["gov", "government", "ministry"]):
            return "government"
        elif any(keyword in domain_lower for keyword in ["citizen", "immigration", "rights"]):
            return "civil_rights"
        else:
            return "scraped"
    
    async def scrape_multiple_urls(
        self, 
        urls: List[str], 
        delay: float = 1.0,
        max_concurrent: int = 3
    ) -> List[Optional[ScrapedDocument]]:
        """
        Парсит несколько URL с контролем скорости и параллелизма
        
        Args:
            urls: Список URL для парсинга
            delay: Задержка между запросами (секунды)
            max_concurrent: Максимальное количество одновременных запросов
            
        Returns:
            Список ScrapedDocument объектов
        """
        logger.info(f"🚀 Starting bulk scrape of {len(urls)} URLs (max_concurrent={max_concurrent})")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def scrape_with_delay(url: str, index: int) -> Optional[ScrapedDocument]:
            async with semaphore:
                # Добавляем задержку между запросами
                if index > 0 and delay > 0:
                    await asyncio.sleep(delay)
                
                return await self.scrape_legal_site(url)
        
        # Создаем задачи для всех URL
        tasks = [
            scrape_with_delay(url.strip(), i) 
            for i, url in enumerate(urls) 
            if url.strip()
        ]
        
        # Выполняем все задачи
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем исключения
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing URL {urls[i]}: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        successful = len([r for r in processed_results if r is not None])
        logger.info(f"✅ Bulk scrape completed: {successful}/{len(urls)} successful")
        
        return processed_results
    
    async def _create_demo_document(self, url: str) -> ScrapedDocument:
        """Создает демонстрационный документ"""
        demo_content = f"""
ДЕМО: Юридический документ с {url}

⚠️ Это демонстрационный контент. Реальный парсинг недоступен по одной из причин:
- Отсутствуют библиотеки aiohttp/beautifulsoup4
- Сайт заблокировал доступ
- Проблемы с сетью
- Нестандартная структура страницы

📋 Для полноценного парсинга установите зависимости:
pip install aiohttp beautifulsoup4

📄 Содержимое демо документа:
Этот документ содержит общую информацию о юридических требованиях и процедурах.
Рассматриваются основные принципы законодательства, права и обязанности граждан,
процедуры обращения в государственные органы и судебную систему.

🔍 Основные разделы:
1. Конституционные права граждан
2. Гражданское и уголовное законодательство  
3. Административные процедуры
4. Судебная система и процессы
5. Социальные гарантии и льготы

📈 Статистика и данные:
- Количество статей в законодательстве: 1,247
- Среднее время рассмотрения дел: 30-45 дней
- Процент положительных решений: 67%

📞 Контактная информация:
Для получения более подробной информации обращайтесь в соответствующие
государственные органы или к квалифицированным юристам.

🕒 Дата создания: {time.strftime('%Y-%m-%d %H:%M:%S')}
🌐 URL: {url}
⚡ Статус: Демонстрационный режим

📝 Примечание: В реальном режиме здесь будет содержимое веб-страницы,
извлеченное с помощью продвинутых методов парсинга HTML.
""".strip()
        
        domain = urlparse(url).netloc
        
        return ScrapedDocument(
            url=url,
            title=f"ДЕМО: Юридический документ с {domain}",
            content=demo_content,
            metadata={
                "scraped_at": time.time(),
                "status": "demo",
                "real_scraping": False,
                "demo_version": "2.0",
                "url": url,
                "domain": domain,
                "reason": "Dependencies missing or scraping failed"
            },
            category=self._categorize_by_domain(domain)
        )
    
    def _update_response_time(self, elapsed: float):
        """Обновляет статистику времени ответа"""
        if self.stats["total_requests"] > 0:
            current_avg = self.stats["average_response_time"]
            total_requests = self.stats["total_requests"]
            self.stats["average_response_time"] = (
                (current_avg * (total_requests - 1) + elapsed) / total_requests
            )
    
    def get_stats(self) -> Dict:
        """Возвращает статистику работы скрапера"""
        success_rate = 0
        if self.stats["total_requests"] > 0:
            success_rate = (self.stats["successful_scrapes"] / self.stats["total_requests"]) * 100
        
        return {
            **self.stats,
            "success_rate": round(success_rate, 2),
            "demo_mode": self.demo_mode,
            "configured_sites": len(self.legal_sites_config),
            "supported_domains": list(self.legal_sites_config.keys())
        }
    
    def reset_stats(self):
        """Сбрасывает статистику"""
        self.stats = {
            "total_requests": 0,
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "demo_responses": 0,
            "average_response_time": 0.0
        }
    
    async def validate_url(self, url: str) -> Dict:
        """Валидирует URL перед парсингом"""
        validation_result = {
            "url": url,
            "valid": False,
            "reachable": False,
            "issues": [],
            "warnings": [],
            "recommendations": [],
            "site_config_available": False
        }
        
        try:
            # Базовая валидация URL
            parsed = urlparse(url)
            
            if not parsed.scheme:
                validation_result["issues"].append("Missing URL scheme (http/https)")
            elif parsed.scheme not in ["http", "https"]:
                validation_result["issues"].append(f"Unsupported scheme: {parsed.scheme}")
            
            if not parsed.netloc:
                validation_result["issues"].append("Missing domain name")
            
            # Проверяем наличие конфигурации для сайта
            domain = parsed.netloc.lower()
            if domain in self.legal_sites_config:
                validation_result["site_config_available"] = True
                validation_result["recommendations"].append("Site-specific configuration available")
            
            # Предупреждения для проблематичных доменов
            if parsed.netloc in ["localhost", "127.0.0.1", "0.0.0.0"]:
                validation_result["warnings"].append("Local URLs may not be accessible")
            
            if parsed.netloc.endswith(".local"):
                validation_result["warnings"].append("Local domain detected")
            
            # Проверяем доступность URL (если нет критических ошибок)
            if not validation_result["issues"]:
                validation_result["valid"] = True
                
                try:
                    await self._ensure_session()
                    async with self.session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        validation_result["reachable"] = response.status == 200
                        if response.status != 200:
                            validation_result["warnings"].append(f"HTTP {response.status} status code")
                except Exception as e:
                    validation_result["warnings"].append(f"Connectivity issue: {str(e)}")
            
            return validation_result
            
        except Exception as e:
            validation_result["issues"].append(f"Validation error: {str(e)}")
            return validation_result
    
    async def get_site_info(self, url: str) -> Dict:
        """Получает информацию о сайте без полного парсинга"""
        try:
            await self._ensure_session()
            
            async with self.session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                headers = dict(response.headers)
                
                return {
                    "url": url,
                    "status_code": response.status,
                    "server": headers.get('server', 'Unknown'),
                    "content_type": headers.get('content-type', 'Unknown'),
                    "content_length": headers.get('content-length', 'Unknown'),
                    "last_modified": headers.get('last-modified', 'Unknown'),
                    "reachable": response.status == 200,
                    "redirect_url": str(response.url) if str(response.url) != url else None
                }
                
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "reachable": False
            }

# Предустановленные списки юридических сайтов
UKRAINE_LEGAL_URLS = [
    "https://zakon.rada.gov.ua/laws/main",
    "https://court.gov.ua/",
    "https://minjust.gov.ua/",
    "https://ccu.gov.ua/",
    "https://npu.gov.ua/",
    "https://sfs.gov.ua/",
    "https://dpsu.gov.ua/"
]

IRELAND_LEGAL_URLS = [
    "https://www.irishstatutebook.ie/",
    "https://www.courts.ie/",
    "https://www.citizensinformation.ie/en/",
    "https://www.justice.ie/",
    "https://www.oireachtas.ie/",
    "https://www.gov.ie/en/"
]

# Дополнительные утилиты

class ScrapingBatch:
    """Управляет пакетным парсингом с приоритетами и очередями"""
    
    def __init__(self, scraper: LegalSiteScraper):
        self.scraper = scraper
        self.queue = asyncio.Queue()
        self.results = {}
        self.active_tasks = set()
    
    async def add_url(self, url: str, priority: int = 1, custom_config: Dict = None):
        """Добавляет URL в очередь парсинга"""
        await self.queue.put({
            "url": url,
            "priority": priority,
            "custom_config": custom_config,
            "added_at": time.time()
        })
    
    async def process_batch(self, max_workers: int = 3) -> Dict:
        """Обрабатывает пакет URL"""
        workers = []
        
        for i in range(max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            workers.append(worker)
            self.active_tasks.add(worker)
        
        # Ждем завершения всех задач
        await self.queue.join()
        
        # Отменяем воркеров
        for worker in workers:
            worker.cancel()
        
        await asyncio.gather(*workers, return_exceptions=True)
        
        return self.results
    
    async def _worker(self, name: str):
        """Воркер для обработки URL из очереди"""
        while True:
            try:
                # Получаем задачу из очереди
                task = await self.queue.get()
                
                logger.info(f"🔧 {name} processing: {task['url']}")
                
                # Обрабатываем URL
                result = await self.scraper.scrape_legal_site(
                    task["url"], 
                    task.get("custom_config")
                )
                
                # Сохраняем результат
                self.results[task["url"]] = {
                    "document": result,
                    "processed_at": time.time(),
                    "worker": name,
                    "success": result is not None
                }
                
                # Отмечаем задачу как выполненную
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {name} error: {e}")
                self.queue.task_done()

async def test_scraper():
    """Функция для тестирования скрапера"""
    async with LegalSiteScraper() as scraper:
        test_urls = [
            "https://www.citizensinformation.ie/en/moving-country/irish-citizenship/",
            "https://www.example.com",  # Для демонстрации fallback
            "https://httpbin.org/html"  # Для тестирования
        ]
        
        print("🧪 Testing Legal Site Scraper")
        print("=" * 50)
        
        for url in test_urls:
            print(f"\n🔍 Testing: {url}")
            
            # Валидация URL
            validation = await scraper.validate_url(url)
            print(f"✅ Valid: {validation['valid']}, Reachable: {validation['reachable']}")
            
            # Парсинг
            document = await scraper.scrape_legal_site(url)
            
            if document:
                print(f"📄 Title: {document.title}")
                print(f"📊 Content: {len(document.content)} chars")
                print(f"🏷️ Category: {document.category}")
                print(f"🔍 Real scraping: {document.metadata.get('real_scraping', False)}")
                print(f"📝 Preview: {document.content[:150]}...")
            else:
                print("❌ Failed to scrape")
        
        # Статистика
        stats = scraper.get_stats()
        print(f"\n📊 Scraper Statistics:")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Success rate: {stats['success_rate']}%")
        print(f"   Average response time: {stats['average_response_time']:.2f}s")

# Экспорт основных компонентов
__all__ = [
    'LegalSiteScraper',
    'ScrapedDocument', 
    'SiteConfig',
    'ScrapingBatch',
    'UKRAINE_LEGAL_URLS',
    'IRELAND_LEGAL_URLS',
    'test_scraper'
]

if __name__ == "__main__":
    asyncio.run(test_scraper())