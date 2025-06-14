import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  FileText, 
  Search,
  Filter,
  RefreshCw,
  Plus,
  Globe
} from 'lucide-react';
import axios from 'axios';
import { 
  Document, 
  DocumentsResponse, 
  AdminStats, 
  Notification as NotificationType,
  DOCUMENT_CATEGORIES 
} from '../types/api';

// Импорты компонентов
import UploadModal from './modals/UploadModal';
import DocumentModal from './modals/DocumentModal';
import StatsCards from './admin/StatsCards';
import DocumentsTable from './admin/DocumentsTable';
import Notification from './common/Notification';
import URLScraper from './URLScraper';

const AdminDashboard: React.FC = () => {
  const { t } = useTranslation();
  
  // Основные состояния
  const [documents, setDocuments] = useState<Document[]>([]);
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<AdminStats>({ total_documents: 0, total_chats: 0, categories: [] });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  // Модальные окна
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);
  const [showDocumentModal, setShowDocumentModal] = useState<boolean>(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  
  // Уведомления и вкладки
  const [notification, setNotification] = useState<NotificationType>({ message: '', type: 'info' });
  const [activeTab, setActiveTab] = useState<'documents' | 'scraper'>('documents');
  
  // Фильтры и поиск
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'category' | 'date'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Эффекты
  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterDocuments();
  }, [documents, searchTerm, selectedCategory, sortBy, sortOrder]);

  // Функция для обновления статистики на основе текущих документов
  const updateStatsFromDocuments = useCallback((docs: Document[]) => {
    const categories = Array.from(new Set(docs.map(doc => doc.category)));
    setStats(prevStats => ({
      ...prevStats,
      total_documents: docs.length,
      categories: categories
    }));
  }, []);

  // Загрузка данных
  const loadData = async (): Promise<void> => {
    setIsLoading(true);
    try {
      const timestamp = new Date().getTime();
      const [documentsResponse, statsResponse] = await Promise.all([
        axios.get<DocumentsResponse>(`/api/admin/documents?_t=${timestamp}`),
        axios.get<AdminStats>(`/api/admin/stats?_t=${timestamp}`)
      ]);
      
      const docs = documentsResponse.data.documents || [];
      const formattedDocs = docs.map((doc: any, index: number) => ({
        id: doc.id || `doc_${index}_${Date.now()}`,
        filename: doc.filename,
        content: doc.content,
        category: doc.category,
        size: doc.size,
        source: doc.source || 'Unknown',
        original_url: doc.original_url || 'N/A',
        word_count: doc.word_count || 0,
        chunks_count: doc.chunks_count || 0,
        added_at: doc.added_at || Date.now() / 1000, // Добавляем текущее время если нет даты
        metadata: doc.metadata || {}
      }));
      
      setDocuments(formattedDocs);
      
      const serverStats = statsResponse.data;
      setStats({
        ...serverStats,
        total_documents: formattedDocs.length,
        categories: Array.from(new Set(formattedDocs.map(doc => doc.category)))
      });
      
    } catch (error) {
      console.error('Error loading data:', error);
      showNotification(t('common.error'), 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Фильтрация документов
  const filterDocuments = (): void => {
    let filtered = [...documents];

    if (searchTerm) {
      filtered = filtered.filter(doc => 
        doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.content.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedCategory) {
      filtered = filtered.filter(doc => doc.category === selectedCategory);
    }

    filtered.sort((a, b) => {
      let aValue: string | number;
      let bValue: string | number;

      switch (sortBy) {
        case 'name':
          aValue = a.filename.toLowerCase();
          bValue = b.filename.toLowerCase();
          break;
        case 'size':
          aValue = a.size;
          bValue = b.size;
          break;
        case 'category':
          aValue = a.category.toLowerCase();
          bValue = b.category.toLowerCase();
          break;
        case 'date':
          aValue = a.added_at || 0;
          bValue = b.added_at || 0;
          break;
        default:
          aValue = a.filename.toLowerCase();
          bValue = b.filename.toLowerCase();
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    setFilteredDocuments(filtered);
  };

  // Показать уведомление
  const showNotification = (message: string, type: NotificationType['type']): void => {
    setNotification({ message, type });
    setTimeout(() => setNotification({ message: '', type: 'info' }), 3000);
  };

  // Обработчики событий
  const handleUpload = async (file: File, category: string): Promise<void> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', category);

      const response = await axios.post('/api/admin/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data) {
        showNotification(t('admin.documents.uploadSuccess'), 'success');
        await loadData();
      }
    } catch (error) {
      console.error('Error uploading document:', error);
      showNotification(t('admin.documents.uploadError'), 'error');
      throw error;
    }
  };

  const handleUpdateDocument = async (updatedDoc: Document): Promise<void> => {
    try {
      const updatedDocs = documents.map(doc => doc.id === updatedDoc.id ? updatedDoc : doc);
      setDocuments(updatedDocs);
      updateStatsFromDocuments(updatedDocs);
      showNotification('Document updated successfully', 'success');
    } catch (error) {
      console.error('Error updating document:', error);
      showNotification(t('common.error'), 'error');
      throw error;
    }
  };

  const handleDeleteDocument = async (docId: number): Promise<void> => {
    if (!window.confirm(t('admin.documents.deleteConfirm'))) return;

    try {
      await axios.delete(`/api/admin/documents/${docId}`);
      showNotification(t('admin.documents.deleteSuccess'), 'success');
      
      const updatedDocs = documents.filter(doc => doc.id !== docId);
      setDocuments(updatedDocs);
      updateStatsFromDocuments(updatedDocs);
      
      await loadData();
    } catch (error) {
      console.error('Error deleting document:', error);
      showNotification(t('common.error'), 'error');
      await loadData();
    }
  };

  const handleViewDocument = (doc: Document): void => {
    setSelectedDocument(doc);
    setShowDocumentModal(true);
  };

  const handleSort = (field: 'name' | 'size' | 'category' | 'date'): void => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const getCategoryDisplayName = (category: string): string => {
    return t(`admin.categories.${category}`) || category;
  };

  // Рендер загрузки
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center space-x-2">
          <RefreshCw className="animate-spin" size={20} />
          <span className="text-gray-500">{t('common.loading')}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Уведомления */}
      <Notification notification={notification} />

      {/* Заголовок с вкладками */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-800">{t('admin.title')}</h1>
          <button
            onClick={loadData}
            className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
          >
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Навигация по вкладкам */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('documents')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'documents'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <FileText size={16} />
            <span>Document Management</span>
          </button>
          <button
            onClick={() => setActiveTab('scraper')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'scraper'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <Globe size={16} />
            <span>Website Scraper</span>
          </button>
        </div>
      </div>

      {/* Контент вкладок */}
      {activeTab === 'documents' ? (
        <>
          {/* Карточки статистики */}
          <StatsCards stats={stats} />

          {/* Управление документами */}
          <div className="bg-white rounded-lg shadow-sm">
            <div className="p-6 border-b border-gray-200">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
                <h2 className="text-lg font-semibold text-gray-800">
                  {t('admin.documents.title')}
                </h2>
                
                {/* Поиск и фильтры */}
                <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
                  {/* Поиск */}
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                    <input
                      type="text"
                      placeholder="Search documents..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  {/* Фильтр по категориям */}
                  <div className="relative">
                    <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                    <select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      className="pl-10 pr-8 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
                    >
                      <option value="">All Categories</option>
                      {DOCUMENT_CATEGORIES.map((category) => (
                        <option key={category} value={category}>
                          {getCategoryDisplayName(category)}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Кнопка загрузки */}
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 whitespace-nowrap"
                  >
                    <Plus size={16} />
                    <span>{t('admin.documents.upload')}</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="p-6">
              {filteredDocuments.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {documents.length === 0 ? (
                    <>
                      <FileText size={48} className="mx-auto mb-4 text-gray-300" />
                      <p>{t('admin.documents.noDocuments')}</p>
                    </>
                  ) : (
                    <>
                      <Search size={48} className="mx-auto mb-4 text-gray-300" />
                      <p>No documents match your search criteria</p>
                    </>
                  )}
                </div>
              ) : (
                <DocumentsTable
                  documents={filteredDocuments}
                  onView={handleViewDocument}
                  onDelete={handleDeleteDocument}
                  sortBy={sortBy}
                  sortOrder={sortOrder}
                  onSort={handleSort}
                />
              )}

              {/* Информация о пагинации */}
              {filteredDocuments.length > 0 && (
                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    Showing {filteredDocuments.length} of {documents.length} documents
                    {searchTerm && (
                      <span className="ml-1">matching "{searchTerm}"</span>
                    )}
                  </div>
                  {searchTerm && (
                    <button
                      onClick={() => {
                        setSearchTerm('');
                        setSelectedCategory('');
                      }}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Clear filters
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      ) : (
        /* Вкладка скрапера сайтов */
        <URLScraper />
      )}

      {/* Модальные окна */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={handleUpload}
      />

      <DocumentModal
        document={selectedDocument}
        isOpen={showDocumentModal}
        onClose={() => {
          setShowDocumentModal(false);
          setSelectedDocument(null);
        }}
        onUpdate={handleUpdateDocument}
      />
    </div>
  );
};

export default AdminDashboard;