import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { MessageSquare, FileText, Search, ArrowRight } from 'lucide-react';

interface Feature {
  icon: React.ReactNode;
  title: string;
  description: string;
}

const HomePage: React.FC = () => {
  const { t } = useTranslation();

  const features: Feature[] = [
    {
      icon: <MessageSquare className="h-8 w-8 text-blue-600" />,
      title: t('home.features.consultation.title'),
      description: t('home.features.consultation.description')
    },
    {
      icon: <FileText className="h-8 w-8 text-green-600" />,
      title: t('home.features.documents.title'),
      description: t('home.features.documents.description')
    },
    {
      icon: <Search className="h-8 w-8 text-purple-600" />,
      title: t('home.features.search.title'),
      description: t('home.features.search.description')
    }
  ];

  const quickStartSteps = {
    users: [
      { step: 1, text: 'Click on "Chat" to start a legal consultation' },
      { step: 2, text: 'Ask your legal question in plain language' },
      { step: 3, text: 'Receive AI-powered legal guidance with relevant sources' }
    ],
    admins: [
      { step: 1, text: 'Access the Admin panel to manage documents' },
      { step: 2, text: 'Upload legal documents and templates' },
      { step: 3, text: 'Monitor system usage and performance' }
    ]
  };

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center bg-white rounded-lg shadow-sm p-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          {t('home.welcome')}
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          {t('home.subtitle')}
        </p>
        <Link
          to="/chat"
          className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white text-lg font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          <MessageSquare size={20} />
          <span>{t('home.startChat')}</span>
          <ArrowRight size={20} />
        </Link>
      </div>

      {/* Features Section */}
      <div className="bg-white rounded-lg shadow-sm p-8">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
          {t('home.features.title')}
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div 
              key={index} 
              className="text-center p-6 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="flex justify-center mb-4">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Start Guide */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Getting Started
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              For Users
            </h3>
            <ul className="space-y-2 text-gray-700">
              {quickStartSteps.users.map((item, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <span className="text-blue-600 font-bold">{item.step}.</span>
                  <span>{item.text}</span>
                </li>
              ))}
            </ul>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              For Administrators
            </h3>
            <ul className="space-y-2 text-gray-700">
              {quickStartSteps.admins.map((item, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <span className="text-purple-600 font-bold">{item.step}.</span>
                  <span>{item.text}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Stats Preview */}
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div className="group hover:transform hover:scale-105 transition-transform">
            <div className="text-3xl font-bold text-blue-600 mb-2">24/7</div>
            <div className="text-gray-600">Available Support</div>
          </div>
          <div className="group hover:transform hover:scale-105 transition-transform">
            <div className="text-3xl font-bold text-green-600 mb-2">AI</div>
            <div className="text-gray-600">Powered Assistance</div>
          </div>
          <div className="group hover:transform hover:scale-105 transition-transform">
            <div className="text-3xl font-bold text-purple-600 mb-2">∞</div>
            <div className="text-gray-600">Legal Documents</div>
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white text-center">
        <h2 className="text-2xl font-bold mb-4">
          Ready to Get Started?
        </h2>
        <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
          Join thousands of users who are already getting reliable legal assistance powered by artificial intelligence.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/chat"
            className="inline-flex items-center justify-center px-6 py-3 bg-white text-blue-600 font-medium rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-blue-600 transition-colors"
          >
            <MessageSquare size={20} className="mr-2" />
            Start Consultation
          </Link>
          <Link
            to="/admin"
            className="inline-flex items-center justify-center px-6 py-3 border-2 border-white text-white font-medium rounded-md hover:bg-white hover:text-blue-600 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-blue-600 transition-colors"
          >
            Admin Panel
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;