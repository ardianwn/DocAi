'use client'

import { useState } from 'react'
import UploadComponent from '@/components/UploadComponent'
import ChatComponent from '@/components/ChatComponent'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'upload' | 'chat'>('upload')
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])

  const handleUploadSuccess = (filename: string) => {
    setUploadedFiles(prev => [...prev, filename])
    // Auto-switch to chat after successful upload
    setTimeout(() => setActiveTab('chat'), 1000)
  }

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error)
  }

  const handleChatError = (error: string) => {
    console.error('Chat error:', error)
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                {process.env.NEXT_PUBLIC_APP_NAME || 'DocAI'}
              </h1>
              <span className="ml-2 text-sm text-gray-500">
                v{process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'}
              </span>
            </div>
            <div className="flex items-center space-x-4">
              {uploadedFiles.length > 0 && (
                <span className="text-sm text-gray-600">
                  {uploadedFiles.length} document{uploadedFiles.length > 1 ? 's' : ''} uploaded
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('upload')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'upload'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Upload Documents
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Chat with Documents
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {activeTab === 'upload' && (
          <div>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Upload Your Documents
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Upload your documents to start chatting with them. Supported formats include PDF, TXT, DOC, and DOCX files.
              </p>
            </div>
            <UploadComponent
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          </div>
        )}

        {activeTab === 'chat' && (
          <div>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Chat with Your Documents
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Ask questions about your uploaded documents and get instant answers powered by AI.
              </p>
            </div>
            {uploadedFiles.length === 0 ? (
              <div className="text-center py-12">
                <svg
                  className="w-12 h-12 text-gray-400 mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No documents uploaded yet
                </h3>
                <p className="text-gray-600 mb-4">
                  Upload some documents first to start chatting with them.
                </p>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Upload Documents
                </button>
              </div>
            ) : (
              <ChatComponent onChatError={handleChatError} />
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500">
            <p>&copy; 2024 DocAI. Powered by AI for intelligent document processing.</p>
          </div>
        </div>
      </footer>
    </main>
  )
}
