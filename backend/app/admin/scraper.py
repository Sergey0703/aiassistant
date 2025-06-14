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
            import os
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
        logger.error(f"Scrape error: {e}")
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
        valid_urls = bulk_request.urls
        
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
                finally:
                    import os
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
            else:
                result.error = "No content or content too short"
            
            results.append(result)
        
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
    """Получить список предустановленных