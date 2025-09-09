import { useState } from 'react'
import UploadPDF from '../components/UploadPDF'
import ChatBox from '../components/ChatBox'

export default function Home() {
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [chatError, setChatError] = useState<string | null>(null)

  const handleUploadSuccess = (filename: string) => {
    setUploadSuccess(filename)
    setUploadError(null)
    // Clear success message after 5 seconds
    setTimeout(() => setUploadSuccess(null), 5000)
  }

  const handleUploadError = (error: string) => {
    setUploadError(error)
    setUploadSuccess(null)
  }

  const handleChatError = (error: string) => {
    setChatError(error)
    // Clear chat error after 5 seconds
    setTimeout(() => setChatError(null), 5000)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">DocAI</h1>
              <p className="text-gray-600 mt-1">
                Upload documents and chat with them using AI
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Global Success/Error Messages */}
          {uploadSuccess && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <svg
                  className="w-5 h-5 text-green-400 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <p className="text-green-700">
                  Document uploaded successfully: {uploadSuccess}. You can now chat with it!
                </p>
              </div>
            </div>
          )}

          {(uploadError || chatError) && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <svg
                  className="w-5 h-5 text-red-400 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-red-700">
                  {uploadError || chatError}
                </p>
              </div>
            </div>
          )}

          {/* Upload Section */}
          <section>
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Upload Your Documents
              </h2>
              <p className="text-gray-600">
                Upload PDF, TXT, DOC, or DOCX files to get started
              </p>
            </div>
            <UploadPDF
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          </section>

          {/* Chat Section */}
          <section>
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Chat with Your Documents
              </h2>
              <p className="text-gray-600">
                Ask questions about your uploaded documents and get intelligent answers
              </p>
            </div>
            <ChatBox onChatError={handleChatError} />
          </section>

          {/* Instructions */}
          <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              How to Use DocAI
            </h3>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 font-bold text-lg">1</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Upload Documents</h4>
                <p className="text-gray-600 text-sm">
                  Upload your PDF, TXT, DOC, or DOCX files using the upload area above
                </p>
              </div>
              <div className="text-center">
                <div className="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 font-bold text-lg">2</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Processing</h4>
                <p className="text-gray-600 text-sm">
                  DocAI processes your documents and creates searchable embeddings
                </p>
              </div>
              <div className="text-center">
                <div className="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 font-bold text-lg">3</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Ask Questions</h4>
                <p className="text-gray-600 text-sm">
                  Use the chat interface to ask questions about your documents
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-500 text-sm">
            <p>DocAI - Document AI Chat Assistant</p>
          </div>
        </div>
      </footer>
    </div>
  )
}