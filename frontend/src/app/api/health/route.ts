import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Check if we can connect to the backend
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    let backendHealth = false
    let backendError = null
    
    try {
      const response = await fetch(`${backendUrl}/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        // Short timeout for health check
        signal: AbortSignal.timeout(5000)
      })
      
      backendHealth = response.ok
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        backendError = errorData.detail || `Backend returned ${response.status}`
      }
    } catch (error) {
      backendHealth = false
      backendError = error instanceof Error ? error.message : 'Unknown error'
    }
    
    const healthStatus = {
      status: backendHealth ? 'healthy' : 'unhealthy',
      service: 'docai-frontend',
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      timestamp: new Date().toISOString(),
      backend_connection: backendHealth,
      backend_url: backendUrl,
      environment: process.env.NODE_ENV || 'development',
      app_name: process.env.NEXT_PUBLIC_APP_NAME || 'DocAI'
    }
    
    if (backendError) {
      healthStatus.backend_error = backendError
    }
    
    const statusCode = backendHealth ? 200 : 503
    
    return NextResponse.json(healthStatus, { status: statusCode })
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    
    return NextResponse.json({
      status: 'unhealthy',
      service: 'docai-frontend',
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      timestamp: new Date().toISOString(),
      error: errorMessage,
      backend_connection: false
    }, { status: 503 })
  }
}