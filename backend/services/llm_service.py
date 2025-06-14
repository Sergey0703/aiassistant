# ====================================
# ФАЙЛ: backend/services/llm_service.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для работы с Ollama LLM
# ====================================

"""
LLM Service - Сервис для работы с языковыми моделями через Ollama
"""

import aiohttp
import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Структура ответа от LLM"""
    content: str
    model: str
    tokens_used: int
    response_time: float
    success: bool
    error: Optional[str] = None

class OllamaService:
    """Сервис для работы с Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3:latest"):
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model
        self.session = None
        self.available_models = []
        self.service_available = False
        
        logger.info(f"🤖 Initializing Ollama service: {self.base_url}")
        
        # НЕ создаем сессию здесь - будем создавать по требованию
    
    def _create_session(self):
        """Создает новую HTTP сессию"""
        timeout = aiohttp.ClientTimeout(total=120, connect=10)
        return aiohttp.ClientSession(timeout=timeout)
    
    async def check_service_health(self) -> Dict[str, Any]:
        """Проверяет доступность Ollama сервиса"""
        session = None
        try:
            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
            
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_models = [model["name"] for model in data.get("models", [])]
                    self.service_available = True
                    
                    logger.info(f"✅ Ollama service is available with {len(self.available_models)} models")
                    
                    return {
                        "available": True,
                        "models": self.available_models,
                        "default_model": self.default_model,
                        "base_url": self.base_url
                    }
                else:
                    self.service_available = False
                    return {
                        "available": False,
                        "error": f"HTTP {response.status}",
                        "base_url": self.base_url
                    }
                    
        except aiohttp.ClientConnectorError:
            self.service_available = False
            logger.warning("❌ Ollama service not available - connection refused")
            return {
                "available": False,
                "error": "Connection refused - is Ollama running?",
                "base_url": self.base_url
            }
        except Exception as e:
            self.service_available = False
            logger.error(f"❌ Error checking Ollama service: {e}")
            return {
                "available": False,
                "error": str(e),
                "base_url": self.base_url
            }
        finally:
            # ВАЖНО: Всегда закрываем временную сессию
            if session and not session.closed:
                await session.close()
    
    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Загружает модель в Ollama"""
        session = None
        try:
            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300))  # 5 минут для загрузки
            
            payload = {"name": model_name}
            
            async with session.post(f"{self.base_url}/api/pull", json=payload) as response:
                if response.status == 200:
                    logger.info(f"✅ Model {model_name} pulled successfully")
                    await self.check_service_health()  # Обновляем список моделей
                    return {"success": True, "model": model_name}
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to pull model {model_name}: {error_text}")
                    return {"success": False, "error": error_text}
                    
        except Exception as e:
            logger.error(f"❌ Error pulling model {model_name}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            # ВАЖНО: Всегда закрываем временную сессию
            if session and not session.closed:
                await session.close()
    
    async def generate_response(self, 
                              prompt: str, 
                              model: str = None,
                              system_prompt: str = None,
                              temperature: float = 0.7,
                              max_tokens: int = 1000) -> LLMResponse:
        """Генерирует ответ от LLM"""
        
        model = model or self.default_model
        start_time = time.time()
        
        try:
            # Проверяем доступность сервиса
            if not self.service_available:
                health = await self.check_service_health()
                if not health["available"]:
                    return LLMResponse(
                        content="",
                        model=model,
                        tokens_used=0,
                        response_time=0,
                        success=False,
                        error="Ollama service not available"
                    )
            
            # Проверяем наличие модели
            if model not in self.available_models:
                logger.warning(f"Model {model} not found, attempting to pull...")
                pull_result = await self.pull_model(model)
                if not pull_result["success"]:
                    return LLMResponse(
                        content="",
                        model=model,
                        tokens_used=0,
                        response_time=time.time() - start_time,
                        success=False,
                        error=f"Model {model} not available and pull failed"
                    )
            
            session = self._create_session()  # Создаем новую сессию для каждого запроса
            
            # УПРОЩЕННЫЙ payload для тестирования
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            # Добавляем options только если нужно
            if temperature != 0.7 or max_tokens != 1000:
                payload["options"] = {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            
            # Добавляем системный промпт если есть
            if system_prompt:
                payload["system"] = system_prompt
            
            logger.debug(f"🤖 Sending request to Ollama: model={model}, prompt_length={len(prompt)}")
            
            try:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        content = data.get("response", "")
                        tokens_used = data.get("eval_count", 0)
                        response_time = time.time() - start_time
                        
                        logger.info(f"✅ LLM response generated: {len(content)} chars, {tokens_used} tokens, {response_time:.2f}s")
                        
                        return LLMResponse(
                            content=content,
                            model=model,
                            tokens_used=tokens_used,
                            response_time=response_time,
                            success=True
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ollama API error: {response.status} - {error_text}")
                        
                        return LLMResponse(
                            content="",
                            model=model,
                            tokens_used=0,
                            response_time=time.time() - start_time,
                            success=False,
                            error=f"API error: {response.status}"
                        )
            finally:
                # ВАЖНО: Всегда закрываем сессию после запроса
                if session and not session.closed:
                    await session.close()
                    
        except asyncio.TimeoutError:
            logger.error("❌ Ollama request timeout")
            return LLMResponse(
                content="",
                model=model,
                tokens_used=0,
                response_time=time.time() - start_time,
                success=False,
                error="Request timeout"
            )
        except Exception as e:
            logger.error(f"❌ Error generating LLM response: {e}")
            return LLMResponse(
                content="",
                model=model,
                tokens_used=0,
                response_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    async def close(self):
        """Закрывает HTTP сессию"""
        # Не нужно закрывать сессию, так как создаем новую для каждого запроса
        logger.debug("🔒 Ollama service cleanup completed")

class LegalAssistantLLM:
    """Основной сервис Legal Assistant с промптами для юридических запросов"""
    
    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        self.system_prompts = {
            "en": """You are a helpful legal assistant specializing in Irish and Ukrainian law. 
Your task is to provide accurate, helpful answers based on the provided legal documents.

Guidelines:
- Answer only based on the provided context
- If information is not in the context, say so clearly
- Provide specific references to laws, acts, or regulations when mentioned
- Use clear, professional language
- If asked about something outside your expertise, acknowledge limitations
- Always prioritize accuracy over completeness""",
            
            "uk": """Ви - корисний юридичний помічник, що спеціалізується на ірландському та українському праві.
Ваше завдання - надавати точні, корисні відповіді на основі наданих юридичних документів.

Рекомендації:
- Відповідайте лише на основі наданого контексту
- Якщо інформації немає в контексті, чітко про це скажіть
- Надавайте конкретні посилання на закони, акти чи постанови, коли вони згадуються
- Використовуйте зрозумілу, професійну мову
- Якщо запитують про щось поза вашою експертизою, визнайте обмеження
- Завжди надавайте перевагу точності над повнотою"""
        }
    
    async def answer_legal_question(self, 
                                  question: str, 
                                  context_documents: List[Dict[str, Any]], 
                                  language: str = "en") -> LLMResponse:
        """Отвечает на юридический вопрос на основе контекста"""
        
        # УПРОЩЕННЫЙ контекст - берем только первый документ и обрезаем
        if context_documents:
            first_doc = context_documents[0]
            content = first_doc.get("content", "")
            
            # СИЛЬНО обрезаем контекст - максимум 500 символов
            if len(content) > 500:
                content = content[:500] + "..."
            
            filename = first_doc.get("filename", "Document")
            
            # КРАТКИЙ промпт без лишних инструкций
            if language == "uk":
                prompt = f"""Документ: {filename}
Контекст: {content}

Питання: {question}

Коротка відповідь:"""
            else:
                prompt = f"""Document: {filename}
Context: {content}

Question: {question}

Brief answer:"""
        else:
            # Если нет контекста - совсем простой промпт
            if language == "uk":
                prompt = f"Питання: {question}\nКоротка відповідь:"
            else:
                prompt = f"Question: {question}\nBrief answer:"
        
        # Убираем системный промпт для упрощения
        response = await self.ollama.generate_response(
            prompt=prompt,
            system_prompt=None,  # Убираем системный промпт
            temperature=0.1,  # Очень низкая температура
            max_tokens=200    # Сильно ограничиваем длину ответа
        )
        
        return response
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Возвращает статус LLM сервиса"""
        health = await self.ollama.check_service_health()
        
        return {
            "ollama_available": health["available"],
            "models_available": health.get("models", []),
            "default_model": self.ollama.default_model,
            "base_url": self.ollama.base_url,
            "system_prompts_loaded": len(self.system_prompts),
            "supported_languages": list(self.system_prompts.keys()),
            "error": health.get("error")
        }
    
    async def close(self):
        """Закрывает сервис"""
        await self.ollama.close()

# Фабричная функция для создания сервиса
def create_llm_service(ollama_url: str = "http://localhost:11434", 
                      model: str = "llama3:latest") -> LegalAssistantLLM:
    """Создает и настраивает LLM сервис"""
    ollama_service = OllamaService(base_url=ollama_url, default_model=model)
    return LegalAssistantLLM(ollama_service)