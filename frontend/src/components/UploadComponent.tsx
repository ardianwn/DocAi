'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

interface UploadResult {
  filename: string
  fileId: string
  success: boolean
  error?: string
  chunksProcessed?: number
  chunksEmbedded?: number
}

interface UploadComponentProps {
  onUploadSuccess?: (filename: string, result: UploadResult) => void
  onUploadError?: (error: string) => void
}

interface UploadProgress {
  [key: string]: {
    filename: string
    status: 'uploading' | 'processing' | 'success' | 'error'
    progress: number
    error?: string
    result?: UploadResult
  }
}

export default function UploadComponent({ onUploadSuccess, onUploadError }: UploadComponentProps) {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({})
  const [globalError, setGlobalError] = useState<string | null>(null)
  const [isMultipleEnabled] = useState(
    process.env.NEXT_PUBLIC_ENABLE_MULTI_UPLOAD === 'true'
  )

  const processFile = async (file: File): Promise<UploadResult> => {
    const fileId = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    // Update progress
    setUploadProgress(prev => ({
      ...prev,
      [fileId]: {
        filename: file.name,
        status: 'uploading',
        progress: 0
      }
    }))

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/upload`, {
        method: 'POST',
        body: formData,
      })

      // Update to processing
      setUploadProgress(prev => ({
        ...prev,
        [fileId]: {
          ...prev[fileId],
          status: 'processing',
          progress: 50
        }
      }))

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data = await response.json()
      
      const result: UploadResult = {
        filename: data.filename,
        fileId: data.file_id || fileId,
        success: true,
        chunksProcessed: data.chunks_processed,
        chunksEmbedded: data.chunks_embedded
      }

      // Update to success
      setUploadProgress(prev => ({
        ...prev,
        [fileId]: {
          ...prev[fileId],
          status: 'success',
          progress: 100,
          result
        }
      }))

      return result

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      
      const result: UploadResult = {
        filename: file.name,
        fileId,
        success: false,
        error: errorMessage
      }

      // Update to error
      setUploadProgress(prev => ({
        ...prev,
        [fileId]: {
          ...prev[fileId],
          status: 'error',
          progress: 0,
          error: errorMessage,
          result
        }
      }))

      return result
    }
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    setGlobalError(null)

    // If multiple uploads are disabled, only take the first file
    const filesToProcess = isMultipleEnabled ? acceptedFiles : [acceptedFiles[0]]

    // Process files
    const results = await Promise.all(filesToProcess.map(processFile))

    // Notify about results
    results.forEach(result => {
      if (result.success) {
        onUploadSuccess?.(result.filename, result)
      } else {
        onUploadError?.(result.error || 'Upload failed')
      }
    })

    // Clear completed uploads after delay
    setTimeout(() => {
      setUploadProgress(prev => {
        const newProgress = { ...prev }
        Object.keys(newProgress).forEach(key => {
          if (newProgress[key].status === 'success' || newProgress[key].status === 'error') {
            delete newProgress[key]
          }
        })
        return newProgress
      })
    }, 5000)

  }, [onUploadSuccess, onUploadError, isMultipleEnabled])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: parseInt(process.env.NEXT_PUBLIC_MAX_FILE_SIZE || '10485760'), // 10MB
    multiple: isMultipleEnabled,
  })

  const hasActiveUploads = Object.values(uploadProgress).some(
    progress => progress.status === 'uploading' || progress.status === 'processing'
  )

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return (
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
        )
      case 'success':
        return (
          <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        )
      case 'error':
        return (
          <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )
      default:
        return null
    }
  }

  const getStatusText = (progress: UploadProgress[string]) => {
    switch (progress.status) {
      case 'uploading':
        return 'Uploading...'
      case 'processing':
        return 'Processing document...'
      case 'success':
        return `Processed ${progress.result?.chunksEmbedded || 0} chunks`
      case 'error':
        return progress.error || 'Upload failed'
      default:
        return ''
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${hasActiveUploads ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} disabled={hasActiveUploads} />
        
        <div className="flex flex-col items-center gap-4">
          <svg
            className="w-12 h-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          
          {hasActiveUploads ? (
            <p className="text-blue-600">Processing uploads...</p>
          ) : isDragActive ? (
            <p className="text-blue-600">Drop the file{isMultipleEnabled ? 's' : ''} here...</p>
          ) : (
            <div>
              <p className="text-gray-600 mb-2">
                Drag & drop document{isMultipleEnabled ? 's' : ''} here, or click to select
              </p>
              <p className="text-sm text-gray-400">
                Supports PDF, TXT, DOC, DOCX (max 10MB{isMultipleEnabled ? ' each' : ''})
              </p>
              {isMultipleEnabled && (
                <p className="text-xs text-gray-400 mt-1">
                  Multiple file upload enabled
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Upload Progress */}
      {Object.keys(uploadProgress).length > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-sm font-medium text-gray-700">Upload Progress</h3>
          {Object.entries(uploadProgress).map(([fileId, progress]) => (
            <div key={fileId} className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(progress.status)}
                  <span className="text-sm font-medium text-gray-700 truncate max-w-xs">
                    {progress.filename}
                  </span>
                </div>
                <span className={`text-xs font-medium ${
                  progress.status === 'success' ? 'text-green-600' :
                  progress.status === 'error' ? 'text-red-600' :
                  'text-blue-600'
                }`}>
                  {getStatusText(progress)}
                </span>
              </div>
              
              {(progress.status === 'uploading' || progress.status === 'processing') && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress.progress}%` }}
                  ></div>
                </div>
              )}

              {progress.status === 'success' && progress.result && (
                <div className="mt-2 text-xs text-gray-600">
                  <div className="flex justify-between">
                    <span>Chunks processed: {progress.result.chunksProcessed}</span>
                    <span>Chunks embedded: {progress.result.chunksEmbedded}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Global Error */}
      {globalError && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
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
            <p className="text-red-700">Upload Error: {globalError}</p>
          </div>
        </div>
      )}
    </div>
  )
}