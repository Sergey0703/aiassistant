import React from 'react';
import { CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { Notification as NotificationType } from '../../types/api';

interface NotificationProps {
  notification: NotificationType;
}

const Notification: React.FC<NotificationProps> = ({ notification }) => {
  if (!notification.message) return null;

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle size={20} className="text-green-600" />;
      case 'error':
        return <AlertCircle size={20} className="text-red-600" />;
      case 'warning':
        return <AlertTriangle size={20} className="text-yellow-600" />;
      default:
        return <Info size={20} className="text-blue-600" />;
    }
  };

  const getStyles = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-50 text-green-700 border border-green-200';
      case 'error':
        return 'bg-red-50 text-red-700 border border-red-200';
      case 'warning':
        return 'bg-yellow-50 text-yellow-700 border border-yellow-200';
      default:
        return 'bg-blue-50 text-blue-700 border border-blue-200';
    }
  };

  return (
    <div className={`p-4 rounded-md flex items-center space-x-2 ${getStyles()}`}>
      {getIcon()}
      <span>{notification.message}</span>
    </div>
  );
};

export default Notification;