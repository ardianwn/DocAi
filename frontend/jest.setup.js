import '@testing-library/jest-dom'

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {
    return null
  }
  disconnect() {
    return null
  }
  unobserve() {
    return null
  }
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() {
    return null
  }
  disconnect() {
    return null
  }
  unobserve() {
    return null
  }
}

// Mock AbortSignal.timeout for Node.js environments
if (typeof AbortSignal.timeout === 'undefined') {
  AbortSignal.timeout = function(milliseconds) {
    const controller = new AbortController()
    setTimeout(() => controller.abort(), milliseconds)
    return controller.signal
  }
}

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_APP_NAME = 'DocAI'
process.env.NEXT_PUBLIC_APP_VERSION = '1.0.0'
process.env.NEXT_PUBLIC_MAX_FILE_SIZE = '10485760'
process.env.NEXT_PUBLIC_ENABLE_MULTI_UPLOAD = 'true'