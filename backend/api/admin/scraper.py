# ====================================
# ФАЙЛ: backend/api/admin/scraper.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для админских endpoints парсинга сайтов
# ====================================

"""
Admin Scraper Endpoints - Админские endpoints для парсинга сайтов
"""

from fastapi import APIRouter, HTTPException, Depends
import tempfile
import logging
import os

from models.requests import URLScrapeRequest, BulkScrapeRequest, PredefinedScrapeRequest
from models.responses import ScrapeResponse, ScrapeResult, PredefinedSitesResponse
from app.dependencies import get_scraper_service, get_document_service
from app.config import UKRAINE_LEGAL_URLS, IRELAND_LEGAL_URLS

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/scrape/url", response_model=ScrapeResponse)
async def scrape_single_url(
    scrape_request: URLScrapeRequest,
    scraper_service = Depends(get_scraper_service),
    document_service = Depends(get_document_service)
):
    """Парсинг одного URL и сохранение в базу документов"""
    try:
        logger.info(f"Starting scrape for URL: {scrape_request.url}")
        
        # Парсим URL
        document = await scraper_service.scrape_legal_site(str(scrape_request.url))
        
        if not document:
            raise HTTPException(status_code=400, detail="Failed to scrape URL - no content extracted")
        
        # Проверяем минимальную длину контента
        if len(document.content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Scraped content too short")
        
        # Создаем временный файл с контентом
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
            tmp_file.write(document.content)
            tmp_file_path = tmp_file.name
        
        success = False
        try:
            # Обрабатываем и сохраняем в векторную базу
            success = await document_service.process_and_store_file(
                tmp_file_path, 
                scrape_request.category
            )
        finally:
            # Удаляем временный файл
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        
        # Формируем результат
        result = ScrapeResult(
            url=str(scrape_request.url),
            title=document.title,
            success=success,
            content_length=len(document.content),
            error=None if success else "Failed to process scraped content"
        )
        
        logger.info(f"Scrape completed for {scrape_request.url}: success={success}")
        
        return ScrapeResponse(
            message="URL scraped and processed successfully" if success else "URL scraped but processing failed",
            results=[result],
            summary={
                "total_processed": 1,
                "successful": 1 if success else 0,
                "failed": 0 if success else 1,
                "category": scrape_request.category
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scrape error for {scrape_request.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping error: {str(e)}")

@router.post("/scrape/bulk", response_model=ScrapeResponse)
async def scrape_multiple_urls(
    bulk_request: BulkScrapeRequest,
    scraper_service = Depends(get_scraper_service),
    document_service = Depends(get_document_service)
):
    """Парсинг нескольких URL"""
    try:
        # Ограничиваем количество URL
        if len(bulk_request.urls) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 URLs allowed per request")
        
        # Фильтруем валидные URL
        valid_urls = [url.strip() for url in bulk_request.urls if url.strip()]
        
        if not valid_urls:
            raise HTTPException(status_code=400, detail="No valid URLs provided")
        
        logger.info(f"Starting bulk scrape of {len(valid_urls)} URLs")
        
        # Парсим URL
        documents = await scraper_service.scrape_multiple_urls(valid_urls, bulk_request.delay)
        
        results = []
        successful = 0
        
        for i, document in enumerate(documents):
            url = valid_urls[i] if i < len(valid_urls) else "unknown"
            
            result = ScrapeResult(
                url=url,
                title=document.title if document else "Failed",
                success=False,
                content_length=0,
                error=None
            )
            
            if document and len(document.content.strip()) >= 50:
                # Создаем временный файл
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
                    tmp_file.write(document.content)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Обрабатываем документ
                    success = await document_service.process_and_store_file(tmp_file_path, bulk_request.category)
                    
                    result.success = success
                    result.content_length = len(document.content)
                    result.title = document.title
                    
                    if success:
                        successful += 1
                    else:
                        result.error = "Processing failed"
                        
                except Exception as e:
                    result.error = str(e)
                    logger.error(f"Processing error for {url}: {e}")
                finally:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
            else:
                result.error = "No content or content too short"
            
            results.append(result)
        
        logger.info(f"Bulk scrape completed: {successful}/{len(results)} successful")
        
        return ScrapeResponse(
            message=f"Processed {successful}/{len(results)} URLs successfully",
            results=results,
            summary={
                "total_processed": len(results),
                "successful": successful,
                "failed": len(results) - successful,
                "category": bulk_request.category
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk scrape error: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk scraping error: {str(e)}")

@router.get("/predefined-sites", response_model=PredefinedSitesResponse)
async def get_predefined_sites():
    """Получить список предустановленных юридических сайтов"""
    try:
        return PredefinedSitesResponse(
            ukraine=UKRAINE_LEGAL_URLS,
            ireland=IRELAND_LEGAL_URLS,
            total={
                "ukraine": len(UKRAINE_LEGAL_URLS),
                "ireland": len(IRELAND_LEGAL_URLS)
            }
        )
    except Exception as e:
        logger.error(f"Error getting predefined sites: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get predefined sites: {str(e)}")

@router.post("/scrape/predefined", response_model=ScrapeResponse)
async def scrape_predefined_sites(
    request: PredefinedScrapeRequest,
    scraper_service = Depends(get_scraper_service),
    document_service = Depends(get_document_service)
):
    """Парсинг предустановленных сайтов"""
    try:
        if request.country == "ukraine":
            urls = UKRAINE_LEGAL_URLS[:request.limit]
            category = "ukraine_legal"
        elif request.country == "ireland":
            urls = IRELAND_LEGAL_URLS[:request.limit]
            category = "ireland_legal"
        else:
            raise HTTPException(status_code=400, detail="Supported countries: ukraine, ireland")
        
        if not urls:
            raise HTTPException(status_code=400, detail=f"No predefined URLs for {request.country}")
        
        logger.info(f"Starting predefined scrape for {request.country}: {len(urls)} URLs")
        
        # Используем bulk scraping с увеличенной задержкой для уважения к серверам
        bulk_request = BulkScrapeRequest(
            urls=urls,
            category=category,
            delay=2.0  # Увеличенная задержка для предустановленных сайтов
        )
        
        return await scrape_multiple_urls(bulk_request, scraper_service, document_service)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Predefined scrape error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scrape predefined sites: {str(e)}")

@router.get("/scrape/status")
async def get_scraper_status(scraper_service = Depends(get_scraper_service)):
    """Получить статус парсера"""
    try:
        # Проверяем доступность необходимых библиотек
        scraper_info = {
            "service_available": scraper_service is not None,
            "supported_domains": list(scraper_service.legal_sites_config.keys()) if scraper_service else [],
            "predefined_sites": {
                "ukraine": len(UKRAINE_LEGAL_URLS),
                "ireland": len(IRELAND_LEGAL_URLS)
            }
        }
        
        # Проверяем библиотеки
        libraries_status = {}
        try:
            import requests
            libraries_status["requests"] = "available"
        except ImportError:
            libraries_status["requests"] = "missing"
        
        try:
            import bs4
            libraries_status["beautifulsoup4"] = "available"
        except ImportError:
            libraries_status["beautifulsoup4"] = "missing"
        
        scraper_info["libraries"] = libraries_status
        scraper_info["real_scraping_available"] = all(
            status == "available" for status in libraries_status.values()
        )
        
        return scraper_info
        
    except Exception as e:
        logger.error(f"Error getting scraper status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scraper status: {str(e)}")

@router.post("/scrape/test")
async def test_scraper(
    test_url: str = "https://example.com",
    scraper_service = Depends(get_scraper_service)
):
    """Тестовый endpoint для проверки парсера"""
    try:
        logger.info(f"Testing scraper with URL: {test_url}")
        
        # Тестируем парсинг без сохранения
        document = await scraper_service.scrape_legal_site(test_url)
        
        if document:
            test_result = {
                "url": test_url,
                "title": document.title,
                "content_preview": document.content[:200] + "..." if len(document.content) > 200 else document.content,
                "content_length": len(document.content),
                "real_scraping": document.metadata.get("real_scraping", False),
                "metadata": document.metadata,
                "success": True
            }
        else:
            test_result = {
                "url": test_url,
                "success": False,
                "error": "No document returned"
            }
        
        return {
            "message": "Scraper test completed",
            "test_result": test_result
        }
        
    except Exception as e:
        logger.error(f"Scraper test error: {e}")
        return {
            "message": "Scraper test failed",
            "test_result": {
                "url": test_url,
                "success": False,
                "error": str(e)
            }
        }

@router.delete("/scrape/cache")
async def clear_scraper_cache():
    """Очистка кэша парсера (если есть)"""
    try:
        # Пока что просто возвращаем успех
        # В будущем здесь можно добавить логику очистки кэша
        
        return {
            "message": "Scraper cache cleared successfully",
            "cleared_items": 0  # Пока что 0, так как кэша нет
        }
        
    except Exception as e:
        logger.error(f"Error clearing scraper cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

# Дополнительные utility endpoints

@router.get("/scrape/domains")
async def get_supported_domains(scraper_service = Depends(get_scraper_service)):
    """Получить список поддерживаемых доменов"""
    try:
        if not scraper_service:
            return {"domains": [], "total": 0}
        
        domains = list(scraper_service.legal_sites_config.keys())
        
        domain_info = []
        for domain in domains:
            config = scraper_service.legal_sites_config[domain]
            domain_info.append({
                "domain": domain,
                "title_selectors": config.get("title", ""),
                "content_selectors": config.get("content", ""),
                "exclude_selectors": config.get("exclude", "")
            })
        
        return {
            "domains": domain_info,
            "total": len(domain_info),
            "message": f"Found {len(domain_info)} configured domains"
        }
        
    except Exception as e:
        logger.error(f"Error getting domains: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get domains: {str(e)}")

@router.post("/scrape/validate-url")
async def validate_scrape_url(url: str):
    """Валидация URL перед парсингом"""
    try:
        from urllib.parse import urlparse
        
        # Базовая валидация URL
        parsed = urlparse(url)
        
        validation_result = {
            "url": url,
            "valid": False,
            "issues": [],
            "recommendations": []
        }
        
        # Проверки
        if not parsed.scheme:
            validation_result["issues"].append("Missing URL scheme (http/https)")
        elif parsed.scheme not in ["http", "https"]:
            validation_result["issues"].append(f"Unsupported scheme: {parsed.scheme}")
        
        if not parsed.netloc:
            validation_result["issues"].append("Missing domain name")
        
        # Проверяем на известные проблематичные домены
        problematic_domains = ["localhost", "127.0.0.1", "0.0.0.0"]
        if parsed.netloc in problematic_domains:
            validation_result["issues"].append("Local URLs are not recommended for scraping")
        
        # Рекомендации
        if parsed.netloc in ["example.com", "test.com"]:
            validation_result["recommendations"].append("This appears to be a test domain")
        
        if not validation_result["issues"]:
            validation_result["valid"] = True
            validation_result["recommendations"].append("URL appears valid for scraping")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return {
            "url": url,
            "valid": False,
            "issues": [f"Validation error: {str(e)}"],
            "recommendations": []
        }