import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Globe, 
  Plus, 
  Trash2, 
  Download, 
  AlertCircle, 
  CheckCircle, 
  Loader,
  ExternalLink 
} from 'lucide-react';
import axios from 'axios';

interface ScrapeResult {
  url: string;
  title: string;
  success: boolean;
  content_length: number;
  error?: string;
}

interface PredefinedSites {
  ukraine: string[];
  ireland: string[];
}

// Функция для безопасного извлечения сообщения об ошибке
const getErrorMessage = (error: any): string => {
  // Если это объект ошибки валидации Pydantic
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;
    
    // Если detail - это массив ошибок валидации
    if (Array.isArray(detail)) {
      return detail.map(err => {
        if (typeof err === 'object' && err.msg) {
          return `${err.loc?.join('.')}: ${err.msg}`;
        }
        return JSON.stringify(err);
      }).join('; ');
    }
    
    // Если detail - это строка
    if (typeof detail === 'string') {
      return detail;
    }
    
    // Если detail - это объект
    if (typeof detail === 'object') {
      return JSON.stringify(detail);
    }
  }
  
  // Fallback к обычным сообщениям об ошибках
  return error?.message || error?.toString() || 'Unknown error';
};

const URLScraper: React.FC = () => {
  const { t } = useTranslation();
  const [urls, setUrls] = useState<string[]>(['']);
  const [category, setCategory] = useState<string>('scraped');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [results, setResults] = useState<ScrapeResult[]>([]);
  const [predefinedSites, setPredefinedSites] = useState<PredefinedSites | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string>('ukraine');

  React.useEffect(() => {
    loadPredefinedSites();
  }, []);

  const loadPredefinedSites = async (): Promise<void> => {
    try {
      const response = await axios.get('/api/admin/predefined-sites');
      setPredefinedSites(response.data);
    } catch (error) {
      console.error('Error loading predefined sites:', error);
    }
  };

  const addUrlField = (): void => {
    setUrls([...urls, '']);
  };

  const removeUrlField = (index: number): void => {
    setUrls(urls.filter((_, i) => i !== index));
  };

  const updateUrl = (index: number, value: string): void => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const scrapeSingleUrl = async (url: string): Promise<void> => {
    if (!url.trim()) return;

    setIsLoading(true);
    try {
      const response = await axios.post('/api/admin/scrape/url', {
        url: url.trim(),
        category: category
      });

      const result: ScrapeResult = {
        url: url,
        title: response.data.title,
        success: true,
        content_length: response.data.content_length
      };

      setResults(prev => [result, ...prev]);
    } catch (error: any) {
      console.error('Scrape error:', error);
      const result: ScrapeResult = {
        url: url,
        title: 'Error',
        success: false,
        content_length: 0,
        error: getErrorMessage(error)
      };
      setResults(prev => [result, ...prev]);
    } finally {
      setIsLoading(false);
    }
  };

  const scrapeMultipleUrls = async (): Promise<void> => {
    const validUrls = urls.filter(url => url.trim());
    if (validUrls.length === 0) return;

    setIsLoading(true);
    try {
      const response = await axios.post('/api/admin/scrape/bulk', {
        urls: validUrls,
        category: category,
        delay: 1.5
      });

      setResults(response.data.results || []);
    } catch (error: any) {
      console.error('Error scraping multiple URLs:', error);
      // Создаем результаты с ошибками для каждого URL
      const errorResults = validUrls.map(url => ({
        url: url,
        title: 'Error',
        success: false,
        content_length: 0,
        error: getErrorMessage(error)
      }));
      setResults(errorResults);
    } finally {
      setIsLoading(false);
    }
  };

  const scrapePredefined = async (): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await axios.post('/api/admin/scrape/predefined', {
        country: selectedCountry,
        limit: 3  // Уменьшаем лимит для тестирования
      });

      setResults(response.data.results || []);
    } catch (error: any) {
      console.error('Error scraping predefined sites:', error);
      
      // Показываем ошибку пользователю
      const errorResult: ScrapeResult = {
        url: `Predefined ${selectedCountry} sites`,
        title: 'Error',
        success: false,
        content_length: 0,
        error: getErrorMessage(error)
      };
      setResults([errorResult]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearResults = (): void => {
    setResults([]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <Globe className="mr-2" size={24} />
          Website Scraper
        </h2>
        <p className="text-gray-600">
          Scrape legal websites and automatically add documents to the knowledge base
        </p>
      </div>

      {/* Category Selection */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Category for scraped documents
        </label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="scraped">General Scraped</option>
          <option value="legislation">Legislation</option>
          <option value="jurisprudence">Jurisprudence</option>
          <option value="government">Government</option>
          <option value="civil_rights">Civil Rights</option>
        </select>
      </div>

      {/* Manual URL Input */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Manual URL Entry</h3>
        
        <div className="space-y-3">
          {urls.map((url, index) => (
            <div key={index} className="flex items-center space-x-2">
              <input
                type="url"
                value={url}
                onChange={(e) => updateUrl(index, e.target.value)}
                placeholder="https://example.com/legal-document"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                onClick={() => scrapeSingleUrl(url)}
                disabled={!url.trim() || isLoading}
                className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                <Download size={16} />
              </button>
              {urls.length > 1 && (
                <button
                  onClick={() => removeUrlField(index)}
                  className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-md"
                >
                  <Trash2 size={16} />
                </button>
              )}
            </div>
          ))}
        </div>

        <div className="flex space-x-2 mt-4">
          <button
            onClick={addUrlField}
            className="flex items-center px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-md"
          >
            <Plus size={16} className="mr-1" />
            Add URL
          </button>
          
          <button
            onClick={scrapeMultipleUrls}
            disabled={urls.filter(u => u.trim()).length === 0 || isLoading}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {isLoading ? <Loader className="animate-spin mr-2" size={16} /> : <Download className="mr-2" size={16} />}
            Scrape All URLs
          </button>
        </div>
      </div>

      {/* Predefined Sites */}
      {predefinedSites && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Predefined Legal Sites</h3>
          
          <div className="flex items-center space-x-4 mb-4">
            <label className="text-sm font-medium text-gray-700">Country:</label>
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            >
              <option value="ukraine">Ukraine 🇺🇦</option>
              <option value="ireland">Ireland 🇮🇪</option>
            </select>
            
            <button
              onClick={scrapePredefined}
              disabled={isLoading}
              className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
            >
              {isLoading ? <Loader className="animate-spin mr-2" size={16} /> : <Globe className="mr-2" size={16} />}
              Scrape {selectedCountry === 'ukraine' ? 'Ukrainian' : 'Irish'} Sites
            </button>
          </div>

          {/* Preview of predefined sites */}
          <div className="bg-gray-50 rounded-md p-3">
            <p className="text-sm text-gray-600 mb-2">
              Available {selectedCountry === 'ukraine' ? 'Ukrainian' : 'Irish'} legal sites:
            </p>
            <div className="space-y-1">
              {(selectedCountry === 'ukraine' ? predefinedSites.ukraine : predefinedSites.ireland)
                .slice(0, 3)
                .map((site, index) => (
                  <div key={index} className="flex items-center text-xs text-gray-500">
                    <ExternalLink size={12} className="mr-1" />
                    {site}
                  </div>
                ))
              }
              {(selectedCountry === 'ukraine' ? predefinedSites.ukraine : predefinedSites.ireland).length > 3 && (
                <p className="text-xs text-gray-400">
                  ...and {(selectedCountry === 'ukraine' ? predefinedSites.ukraine : predefinedSites.ireland).length - 3} more
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Scraping Results</h3>
            <button
              onClick={clearResults}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear Results
            </button>
          </div>

          <div className="space-y-3">
            {results.map((result, index) => (
              <div key={index} className={`p-4 rounded-lg border ${
                result.success 
                  ? 'border-green-200 bg-green-50' 
                  : 'border-red-200 bg-red-50'
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      {result.success ? (
                        <CheckCircle size={16} className="text-green-600" />
                      ) : (
                        <AlertCircle size={16} className="text-red-600" />
                      )}
                      <span className="font-medium text-gray-900">
                        {result.title}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">{result.url}</p>
                    {result.success ? (
                      <p className="text-sm text-green-700">
                        ✅ Successfully scraped {result.content_length} characters
                      </p>
                    ) : (
                      <p className="text-sm text-red-700">
                        ❌ Error: {result.error}
                      </p>
                    )}
                  </div>
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <ExternalLink size={16} />
                  </a>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 p-3 bg-blue-50 rounded-md">
            <p className="text-sm text-blue-800">
              📊 Successfully processed: {results.filter(r => r.success).length} / {results.length} URLs
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default URLScraper;