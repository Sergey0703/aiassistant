import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Translation resources
const resources = {
  en: {
    translation: {
      app: {
        title: "Legal Assistant"
      },
      nav: {
        home: "Home",
        chat: "Chat",
        admin: "Admin"
      },
      home: {
        welcome: "Welcome to Legal Assistant",
        subtitle: "Get legal advice and assistance powered by AI",
        startChat: "Start Consultation",
        features: {
          title: "Features",
          consultation: {
            title: "AI Legal Consultation",
            description: "Get instant answers to your legal questions"
          },
          documents: {
            title: "Document Templates",
            description: "Access legal document templates and forms"
          },
          search: {
            title: "Legal Search",
            description: "Search through legal documents and cases"
          }
        }
      },
      chat: {
        title: "Legal Consultation",
        placeholder: "Ask your legal question...",
        send: "Send",
        clear: "Clear Chat",
        history: "Chat History",
        sources: "Sources",
        thinking: "Thinking...",
        error: "Something went wrong. Please try again.",
        empty: "Start by asking a legal question"
      },
      admin: {
        title: "Admin Dashboard",
        stats: {
          title: "Statistics",
          documents: "Total Documents",
          chats: "Total Chats",
          categories: "Categories"
        },
        documents: {
          title: "Document Management",
          upload: "Upload Document",
          filename: "Filename",
          category: "Category",
          size: "Size",
          actions: "Actions",
          delete: "Delete",
          noDocuments: "No documents uploaded yet",
          uploadSuccess: "Document uploaded successfully",
          uploadError: "Error uploading document",
          deleteSuccess: "Document deleted successfully",
          deleteConfirm: "Are you sure you want to delete this document?"
        },
        upload: {
          title: "Upload New Document",
          selectFile: "Select File",
          dragDrop: "or drag and drop files here",
          category: "Category",
          categoryPlaceholder: "Select category",
          upload: "Upload",
          cancel: "Cancel",
          supportedFormats: "Supported formats: TXT, PDF, DOCX, MD"
        },
        categories: {
          general: "General",
          civil: "Civil Law",
          criminal: "Criminal Law",
          tax: "Tax Law",
          corporate: "Corporate Law",
          family: "Family Law",
          labor: "Labor Law",
          real_estate: "Real Estate"
        }
      },
      footer: {
        copyright: "© 2025 Legal Assistant. All rights reserved."
      },
      common: {
        loading: "Loading...",
        error: "Error",
        success: "Success",
        cancel: "Cancel",
        save: "Save",
        delete: "Delete",
        edit: "Edit",
        close: "Close",
        yes: "Yes",
        no: "No"
      }
    }
  },
  uk: {
    translation: {
      app: {
        title: "Юридичний Асистент"
      },
      nav: {
        home: "Головна",
        chat: "Чат",
        admin: "Адмін"
      },
      home: {
        welcome: "Ласкаво просимо до Юридичного Асистента",
        subtitle: "Отримайте юридичну консультацію та допомогу за допомогою ШІ",
        startChat: "Почати Консультацію",
        features: {
          title: "Можливості",
          consultation: {
            title: "ШІ Юридична Консультація",
            description: "Отримайте миттєві відповіді на ваші юридичні питання"
          },
          documents: {
            title: "Шаблони Документів",
            description: "Доступ до шаблонів юридичних документів та форм"
          },
          search: {
            title: "Юридичний Пошук",
            description: "Пошук у юридичних документах та справах"
          }
        }
      },
      chat: {
        title: "Юридична Консультація",
        placeholder: "Задайте ваше юридичне питання...",
        send: "Відправити",
        clear: "Очистити Чат",
        history: "Історія Чату",
        sources: "Джерела",
        thinking: "Думаю...",
        error: "Щось пішло не так. Спробуйте ще раз.",
        empty: "Почніть із юридичного питання"
      },
      admin: {
        title: "Панель Адміністратора",
        stats: {
          title: "Статистика",
          documents: "Всього Документів",
          chats: "Всього Чатів",
          categories: "Категорії"
        },
        documents: {
          title: "Управління Документами",
          upload: "Завантажити Документ",
          filename: "Ім'я файлу",
          category: "Категорія",
          size: "Розмір",
          actions: "Дії",
          delete: "Видалити",
          noDocuments: "Документи ще не завантажені",
          uploadSuccess: "Документ успішно завантажено",
          uploadError: "Помилка завантаження документа",
          deleteSuccess: "Документ успішно видалено",
          deleteConfirm: "Ви впевнені, що хочете видалити цей документ?"
        },
        upload: {
          title: "Завантажити Новий Документ",
          selectFile: "Обрати Файл",
          dragDrop: "або перетягніть файли сюди",
          category: "Категорія",
          categoryPlaceholder: "Оберіть категорію",
          upload: "Завантажити",
          cancel: "Скасувати",
          supportedFormats: "Підтримувані формати: TXT, PDF, DOCX, MD"
        },
        categories: {
          general: "Загальне",
          civil: "Цивільне право",
          criminal: "Кримінальне право",
          tax: "Податкове право",
          corporate: "Корпоративне право",
          family: "Сімейне право",
          labor: "Трудове право",
          real_estate: "Нерухомість"
        }
      },
      footer: {
        copyright: "© 2025 Юридичний Асистент. Всі права захищені."
      },
      common: {
        loading: "Завантаження...",
        error: "Помилка",
        success: "Успіх",
        cancel: "Скасувати",
        save: "Зберегти",
        delete: "Видалити",
        edit: "Редагувати",
        close: "Закрити",
        yes: "Так",
        no: "Ні"
      }
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en', // default language
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false // React already does escaping
    },
    debug: process.env.NODE_ENV === 'development'
  });

export default i18n;