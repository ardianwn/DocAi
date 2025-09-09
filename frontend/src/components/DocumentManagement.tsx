'use client'

import { useState, useEffect } from 'react'

interface DocumentStats {
  total_documents: number
  indexed_documents: number
  collection_status: string
  vector_store_health: boolean
  error?: string
}

interface DocumentManagementProps {
  onError?: (error: string) => void
}

export default function DocumentManagement({ onError }: DocumentManagementProps) {
  const [stats, setStats] = useState<DocumentStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [clearing, setClearing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/documents`)
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to fetch document statistics')
      }
      
      const data = await response.json()
      setStats(data)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(errorMessage)
      onError?.(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const clearAllDocuments = async () => {
    if (!confirm('Are you sure you want to clear all documents? This action cannot be undone.')) {
      return
    }

    try {
      setClearing(true)
      setError(null)
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/documents`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to clear documents')
      }
      
      // Refresh stats after clearing
      await fetchStats()
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(errorMessage)
      onError?.(errorMessage)
    } finally {
      setClearing(false)
    }
  }

  const refreshStats = () => {
    fetchStats()
  }

  useEffect(() => {
    fetchStats()
  }, [])

  const getHealthBadge = (healthy: boolean) => (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
      healthy 
        ? 'bg-green-100 text-green-800' 
        : 'bg-red-100 text-red-800'
    }`}>
      {healthy ? 'Healthy' : 'Unhealthy'}
    </span>
  )

  const getStatusBadge = (status: string) => {
    const colorMap: Record<string, string> = {
      'green': 'bg-green-100 text-green-800',
      'yellow': 'bg-yellow-100 text-yellow-800',
      'red': 'bg-red-100 text-red-800',
      'available': 'bg-green-100 text-green-800',
      'unavailable': 'bg-red-100 text-red-800',
      'error': 'bg-red-100 text-red-800'
    }
    
    const colorClass = colorMap[status.toLowerCase()] || 'bg-gray-100 text-gray-800'
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colorClass}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800">
            Document Management
          </h2>
          <div className="flex space-x-2">
            <button
              onClick={refreshStats}
              disabled={loading}
              className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-md transition-colors disabled:opacity-50"
              title="Refresh statistics"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            {stats && stats.total_documents > 0 && (
              <button
                onClick={clearAllDocuments}
                disabled={clearing}
                className="px-3 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded-md transition-colors disabled:opacity-50"
              >
                {clearing ? 'Clearing...' : 'Clear All'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-700">Error: {error}</p>
            </div>
          </div>
        )}

        {stats ? (
          <div className="space-y-4">
            {/* Statistics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-gray-900">
                  {stats.total_documents.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Total Documents</div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-gray-900">
                  {stats.indexed_documents.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Indexed Chunks</div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-gray-900">
                  {stats.total_documents > 0 ? 
                    Math.round((stats.indexed_documents / stats.total_documents) * 100) + '%' : 
                    '0%'
                  }
                </div>
                <div className="text-sm text-gray-600">Index Ratio</div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  {getHealthBadge(stats.vector_store_health)}
                </div>
                <div className="text-sm text-gray-600 mt-1">Vector Store</div>
              </div>
            </div>

            {/* Status Information */}
            <div className="border-t border-gray-200 pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">System Status</h3>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Collection Status:</span>
                  {getStatusBadge(stats.collection_status)}
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Vector Store Health:</span>
                  {getHealthBadge(stats.vector_store_health)}
                </div>
              </div>
            </div>

            {/* Actions */}
            {stats.total_documents === 0 && (
              <div className="text-center py-8">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No documents uploaded yet
                </h3>
                <p className="text-gray-600">
                  Upload some documents to see statistics and manage your document collection.
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Unable to load document statistics
            </h3>
            <p className="text-gray-600 mb-4">
              There was an error loading the document statistics.
            </p>
            <button
              onClick={refreshStats}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry
            </button>
          </div>
        )}
      </div>
    </div>
  )
}