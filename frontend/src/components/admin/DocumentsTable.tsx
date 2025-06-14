import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  FileText, 
  Eye, 
  Download, 
  Trash2, 
  Search 
} from 'lucide-react';
import { Document } from '../../types/api';

interface DocumentsTableProps {
  documents: Document[];
  onView: (doc: Document) => void;
  onDelete: (docId: number) => void;
  sortBy: 'name' | 'size' | 'category' | 'date';
  sortOrder: 'asc' | 'desc';
  onSort: (field: 'name' | 'size' | 'category' | 'date') => void;
}

const DocumentsTable: React.FC<DocumentsTableProps> = ({
  documents,
  onView,
  onDelete,
  sortBy,
  sortOrder,
  onSort
}) => {
  const { t } = useTranslation();

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp: number): string => {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp * 1000); // Конвертируем Unix timestamp в миллисекунды
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getCategoryDisplayName = (category: string): string => {
    return t(`admin.categories.${category}`) || category;
  };

  const handleDownload = (doc: Document): void => {
    const blob = new Blob([doc.content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = doc.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Search size={48} className="mx-auto mb-4 text-gray-300" />
        <p>No documents match your search criteria</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => onSort('name')}
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
              onClick={() => onSort('category')}
            >
              <div className="flex items-center space-x-1">
                <span>{t('admin.documents.category')}</span>
                {sortBy === 'category' && (
                  <span className="text-blue-500">
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </div>
            </th>
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => onSort('size')}
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
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => onSort('date')}
            >
              <div className="flex items-center space-x-1">
                <span>Date Added</span>
                {sortBy === 'date' && (
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
          {documents.map((doc) => (
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
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <div className="flex flex-col">
                  <span>{formatDate(doc.added_at)}</span>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onView(doc)}
                    className="text-blue-600 hover:text-blue-900 hover:bg-blue-50 p-1 rounded"
                    title="View document"
                  >
                    <Eye size={16} />
                  </button>
                  <button
                    onClick={() => handleDownload(doc)}
                    className="text-green-600 hover:text-green-900 hover:bg-green-50 p-1 rounded"
                    title="Download document"
                  >
                    <Download size={16} />
                  </button>
                  <button
                    onClick={() => onDelete(doc.id)}
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
  );
};

export default DocumentsTable;