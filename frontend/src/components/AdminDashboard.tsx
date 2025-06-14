import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Upload, 
  FileText, 
  Trash2, 
  Users, 
  FolderOpen, 
  Download,
  Eye,
  Edit3,
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  X,
  Plus,
  Globe
} from 'lucide-react';
import axios from 'axios';
import { 
  Document, 
  DocumentsResponse, 
  AdminStats, 
  DocumentUpload, 
  Notification,
  DocumentCategory,
  DOCUMENT_CATEGORIES 
} from '../types/api';
import URLScraper from './URLScraper';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File, category: string) => Promise<void>;
}

interface DocumentModalProps {
  document: Document | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (updatedDoc: Document) => Promise<void>;
}

const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onUpload }) => {
  const { t } = useTranslation();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState<string>('');
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [dragActive, setDragActive] = useState<boolean>(false);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleUpload = async (): Promise<void> => {
    if (!selectedFile) return;
    
    setIsUploading(true);
    try {
      await onUpload(selectedFile, uploadCategory || 'general');
      setSelectedFile(null);
      setUploadCategory('');
      onClose();
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getCategoryDisplayName = (category: string): string => {
    return t(`admin.categories.${category}`) || category;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            {t('admin.upload.title')}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="space-y-4">
          {/* Drag & Drop Area */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
              dragActive 
                ? 'border-blue-400 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              onChange={handleFileSelect}
              accept=".txt,.pdf,.docx,.md,.doc"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-sm text-gray-600">
              {t('admin.upload.selectFile')}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {t('admin.upload.dragDrop')}
            </p>
            <p className="text-xs text-gray-400 mt-2">
              {t('admin.upload.supportedFormats')}
            </p>
          </div>

          {/* Category Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('admin.upload.category')}
            </label>
            <select
              value={uploadCategory}
              onChange={(e) => setUploadCategory(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">{t('admin.upload.categoryPlaceholder')}</option>
              {DOCUMENT_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {getCategoryDisplayName(category)}
                </option>
              ))}
            </select>
          </div>

          {/* Selected File Info */}
          {selectedFile && (
            <div className="p-3 bg-gray-50 rounded-md border">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <FileText size={16} className="text-gray-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="text-gray-400 hover:text-red-500"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Modal Actions */}
        <div className="flex space-x-3 mt-6">
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className="flex-1 flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUploading ? (
              <RefreshCw className="animate-spin mr-2" size={16} />
            ) : (
              <Upload className="mr-2" size={16} />
            )}
            {isUploading ? t('common.loading') : t('admin.upload.upload')}
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            {t('admin.upload.cancel')}
          </button>
        </div>
      </div>
    </div>
  );
};

const DocumentModal: React.FC<DocumentModalProps> = ({ document, isOpen, onClose, onUpdate }) => {
  const { t } = useTranslation();
  const [editedDoc, setEditedDoc] = useState<Document | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);

  useEffect(() => {
    if (document) {
      setEditedDoc({ ...document });
    }
  }, [document]);

  const handleSave = async (): Promise<void> => {
    if (!editedDoc) return;
    
    try {
      await onUpdate(editedDoc);
      setIsEditing(false);
      onClose();
    } catch (error) {
      console.error('Update error:', error);
    }
  };

  const getCategoryDisplayName = (category: string): string => {
    return t(`admin.categories.${category}`) || category;
  };

  if (!isOpen || !document || !editedDoc) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            {document.filename}
          </h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="text-gray-500 hover:text-blue-600"
            >
              <Edit3 size={20} />
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="space-y-4">
          {/* Document Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="text-sm font-medium text-gray-500">Category</label>
              {isEditing ? (
                <select
                  value={editedDoc.category}
                  onChange={(e) => setEditedDoc({ ...editedDoc, category: e.target.value })}
                  className="mt-1 block w-full px-3 py-1 border border-gray-300 rounded-md text-sm"
                >
                  {DOCUMENT_CATEGORIES.map((category) => (
                    <option key={category} value={category}>
                      {getCategoryDisplayName(category)}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="text-sm text-gray-900">{getCategoryDisplayName(document.category)}</p>
              )}
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Size</label>
              <p className="text-sm text-gray-900">{(document.size / 1024).toFixed(1)} KB</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">ID</label>
              <p className="text-sm text-gray-900">#{document.id}</p>
            </div>
          </div>

          {/* Document Content */}
          <div>
            <label className="text-sm font-medium text-gray-500 mb-2 block">Content Preview</label>
            {isEditing ? (
              <textarea
                value={editedDoc.content}
                onChange={(e) => setEditedDoc({ ...editedDoc, content: e.target.value })}
                className="w-full h-64 px-3 py-2 border border-gray-300 rounded-md text-sm font-mono resize-y"
                placeholder="Document content..."
              />
            ) : (
              <div className="w-full h-64 p-3 border border-gray-300 rounded-md bg-gray-50 overflow-y-auto">
                <div className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                  {document.content}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modal Actions */}
        <div className="flex justify-end space-x-3 mt-6">
          {isEditing && (
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              {t('common.save')}
            </button>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            {t('common.close')}
          </button>
        </div>
      </div>
    </div>
  );
};

const AdminDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<AdminStats>({ total_documents: 0, total_chats: 0, categories: [] });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);
  const [showDocumentModal, setShowDocumentModal] = useState<boolean>(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [notification, setNotification] = useState<Notification>({ message: '', type: 'info' });
  const [activeTab, setActiveTab] = useState<'documents' | 'scraper'>('documents');
  
  // Filter & Search states
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'category'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterDocuments();
  }, [documents, searchTerm, selectedCategory, sortBy, sortOrder]);

  const loadData = async (): Promise<void> => {
    setIsLoading(true);
    try {
      // Добавляем timestamp для избежания кэша
      const timestamp = new Date().getTime();
      const [documentsResponse, statsResponse] = await Promise.all([
        axios.get<DocumentsResponse>(`/api/admin/documents?_t=${timestamp}`),
        axios.get<AdminStats>(`/api/admin/stats?_t=${timestamp}`)
      ]);
      
      // Адаптируем ответ к нашему интерфейсу
      const docs = documentsResponse.data.documents || [];
      const formattedDocs = docs.map((doc: any, index: number) => ({
        id: doc.id || `doc_${index}_${Date.now()}`, // Используем реальный ID или создаем уникальный
        filename: doc.filename,
        content: doc.content,
        category: doc.category,
        size: doc.size,
        source: doc.source || 'Unknown',
        original_url: doc.original_url || 'N/A',
        word_count: doc.word_count || 0,
        chunks_count: doc.chunks_count || 0,
        added_at: doc.added_at,
        metadata: doc.metadata || {}
      }));
      
      console.log('Loaded documents:', formattedDocs); // Для отладки
      setDocuments(formattedDocs);
      setStats(statsResponse.data);
    } catch (error) {
      console.error('Error loading data:', error);
      showNotification(t('common.error'), 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const filterDocuments = (): void => {
    let filtered = [...documents];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(doc => 
        doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.content.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Category filter
    if (selectedCategory) {
      filtered = filtered.filter(doc => doc.category === selectedCategory);
    }

    // Sort
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

  const showNotification = (message: string, type: Notification['type']): void => {
    setNotification({ message, type });
    setTimeout(() => setNotification({ message: '', type: 'info' }), 3000);
  };

  const handleUpload = async (file: File, category: string): Promise<void> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', category);

      const response = await axios.post('/api/admin/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
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
      // In a real implementation, this would call an API endpoint
      // For now, we'll just update the local state
      setDocuments(prev => 
        prev.map(doc => doc.id === updatedDoc.id ? updatedDoc : doc)
      );
      showNotification('Document updated successfully', 'success');
    } catch (error) {
      console.error('Error updating document:', error);
      showNotification(t('common.error'), 'error');
      throw error;
    }
  };

  const deleteDocument = async (docId: number): Promise<void> => {
    if (!window.confirm(t('admin.documents.deleteConfirm'))) return;

    try {
      await axios.delete(`/api/admin/documents/${docId}`);
      showNotification(t('admin.documents.deleteSuccess'), 'success');
      await loadData();
    } catch (error) {
      console.error('Error deleting document:', error);
      showNotification(t('common.error'), 'error');
    }
  };

  const viewDocument = (doc: Document): void => {
    setSelectedDocument(doc);
    setShowDocumentModal(true);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getCategoryDisplayName = (category: string): string => {
    return t(`admin.categories.${category}`) || category;
  };

  const handleSort = (field: 'name' | 'size' | 'category'): void => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

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
      {/* Notification */}
      {notification.message && (
        <div className={`p-4 rounded-md flex items-center space-x-2 ${
          notification.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 
          notification.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
          notification.type === 'warning' ? 'bg-yellow-50 text-yellow-700 border border-yellow-200' :
          'bg-blue-50 text-blue-700 border border-blue-200'
        }`}>
          {notification.type === 'success' && <CheckCircle size={20} />}
          {notification.type === 'error' && <AlertCircle size={20} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Header with Tabs */}
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

        {/* Tab Navigation */}
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

      {/* Tab Content */}
      {activeTab === 'documents' ? (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">{t('admin.stats.documents')}</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_documents}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Users className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">{t('admin.stats.chats')}</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_chats}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <FolderOpen className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">{t('admin.stats.categories')}</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.categories.length}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Documents Management */}
          <div className="bg-white rounded-lg shadow-sm">
            <div className="p-6 border-b border-gray-200">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
                <h2 className="text-lg font-semibold text-gray-800">{t('admin.documents.title')}</h2>
                
                {/* Search and Filters */}
                <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
                  {/* Search */}
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

                  {/* Category Filter */}
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

                  {/* Upload Button */}
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
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th 
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort('name')}
                        >
                          <div className="flex items-center space-x-1">
                            <span>{t('admin.documents.filename')}</span>
                            {sortBy === 'name' && (
                              <span className="text-blue-500">
                                {sortOrder === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th 
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort('category')}
                        >
                          <div className="flex items-center space-x-1">
                            <span>{t('admin.documents.category')}</span>
                              <span className="text-blue-500">
                                {sortOrder === 'asc' ? '↑' : '↓'}
                              </span>
                            
                          </div>
                        </th>
                        <th 
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort('size')}
                        >
                          <div className="flex items-center space-x-1">
                            <span>{t('admin.documents.size')}</span>
                            {sortBy === 'size' && (
                              <span className="text-blue-500">
                                {sortOrder === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {t('admin.documents.actions')}
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredDocuments.map((doc) => (
                        <tr key={doc.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            <div className="flex items-center">
                              <FileText size={16} className="mr-2 text-gray-400" />
                              <span className="truncate max-w-xs" title={doc.filename}>
                                {doc.filename}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                              {getCategoryDisplayName(doc.category)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatFileSize(doc.size)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => viewDocument(doc)}
                                className="text-blue-600 hover:text-blue-900 hover:bg-blue-50 p-1 rounded"
                                title="View document"
                              >
                                <Eye size={16} />
                              </button>
                              <button
                                onClick={() => {
                                  // Download functionality - create a blob and download
                                  const blob = new Blob([doc.content], { type: 'text/plain' });
                                  const url = window.URL.createObjectURL(blob);
                                  const a = document.createElement('a');
                                  a.href = url;
                                  a.download = doc.filename;
                                  document.body.appendChild(a);
                                  a.click();
                                  document.body.removeChild(a);
                                  window.URL.revokeObjectURL(url);
                                }}
                                className="text-green-600 hover:text-green-900 hover:bg-green-50 p-1 rounded"
                                title="Download document"
                              >
                                <Download size={16} />
                              </button>
                              <button
                                onClick={() => deleteDocument(doc.id)}
                                className="text-red-600 hover:text-red-900 hover:bg-red-50 p-1 rounded"
                                title="Delete document"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Pagination info */}
              {filteredDocuments.length > 0 && (
                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    Showing {filteredDocuments.length} of {documents.length} documents
                    {searchTerm && (
                      <span className="ml-1">
                        matching "{searchTerm}"
                      </span>
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
        /* Website Scraper Tab */
        <URLScraper />
      )}

      {/* Upload Modal */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={handleUpload}
      />

      {/* Document View/Edit Modal */}
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