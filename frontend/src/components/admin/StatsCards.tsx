import React from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, Users, FolderOpen } from 'lucide-react';
import { AdminStats } from '../../types/api';

interface StatsCardsProps {
  stats: AdminStats;
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => {
  const { t } = useTranslation();

  return (
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
  );
};

export default StatsCards;