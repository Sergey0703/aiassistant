import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Edit3, X } from 'lucide-react';
import { Document, DOCUMENT_CATEGORIES } from '../../types/api';

interface DocumentModalProps {
  document: Document | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (updatedDoc: Document) => Promise<void>;
}

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

export default DocumentModal;