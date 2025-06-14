// API Response Types
export interface ApiResponse<T = any> {
  message?: string;
  data?: T;
  error?: string;
}

// Chat Types
export interface ChatMessage {
  message: string;
  language: string;
}

export interface ChatResponse {
  response: string;
  sources?: string[];
}

export interface ChatHistoryItem {
  message: string;
  response: string;
  language: string;
  sources?: string[];
}

export interface ChatHistory {
  history: ChatHistoryItem[];
}

// Message Types for UI
export interface Message {
  type: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp?: Date;
}

// Document Types
export interface DocumentUpload {
  filename: string;
  content: string;
  category?: string;
}

export interface Document {
  id: number;
  filename: string;
  content: string;
  category: string;
  size: number;
  source?: string;
  original_url?: string;
  word_count?: number;
  chunks_count?: number;
  added_at: number; // Unix timestamp
  metadata?: any;
  uploadDate?: string; // Deprecated, use added_at instead
}

export interface DocumentsResponse {
  documents: Document[];
  total: number;
}

// Admin Stats Types
export interface AdminStats {
  total_documents: number;
  total_chats: number;
  categories: string[];
}

// Upload Form Types
export interface UploadFormData {
  file: File | null;
  category: string;
}

// Notification Types
export interface Notification {
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

// Language Types
export type SupportedLanguage = 'en' | 'uk';

// API Endpoints enum
export enum ApiEndpoints {
  HEALTH = '/api/health',
  CHAT = '/api/user/chat',
  CHAT_HISTORY = '/api/user/chat/history',
  DOCUMENTS_UPLOAD = '/api/admin/documents/upload',
  DOCUMENTS_LIST = '/api/admin/documents',
  DOCUMENTS_DELETE = '/api/admin/documents',
  ADMIN_STATS = '/api/admin/stats'
}

// HTTP Methods
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

// Form validation types
export interface FormErrors {
  [key: string]: string;
}

// Categories for documents
export const DOCUMENT_CATEGORIES = [
  'general',
  'legislation', 
  'jurisprudence',
  'government',
  'civil_rights',
  'scraped',
  'ukraine_legal',
  'ireland_legal',
  'civil',
  'criminal',
  'tax',
  'corporate',
  'family',
  'labor',
  'real_estate'
] as const;

export type DocumentCategory = typeof DOCUMENT_CATEGORIES[number];