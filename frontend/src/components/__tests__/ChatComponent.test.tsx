import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import ChatComponent from '@/components/ChatComponent'

// Mock the environment variable
const originalEnv = process.env
beforeEach(() => {
  process.env = {
    ...originalEnv,
    NEXT_PUBLIC_API_URL: 'http://localhost:8000'
  }
})

afterEach(() => {
  process.env = originalEnv
})

// Setup MSW server for API mocking
const server = setupServer(
  rest.post('http://localhost:8000/chat', (req, res, ctx) => {
    return res(
      ctx.json({
        question: 'What is this about?',
        answer: 'This is a test response from the AI assistant.',
        sources: [
          {
            source: 'test.pdf',
            page: 1,
            score: 0.95,
            content_preview: 'This is a preview of the relevant content...'
          }
        ],
        session_id: 'test-session',
        error: false
      })
    )
  }),
  rest.get('http://localhost:8000/sessions/*/history', (req, res, ctx) => {
    return res(
      ctx.json({
        session_id: 'test-session',
        history: [
          {
            question: 'Previous question?',
            answer: 'Previous answer.',
            timestamp: 1640995200
          }
        ],
        total_turns: 1
      })
    )
  }),
  rest.delete('http://localhost:8000/sessions/*/history', (req, res, ctx) => {
    return res(
      ctx.json({
        message: 'Chat history cleared',
        session_id: 'test-session'
      })
    )
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('ChatComponent', () => {
  test('renders chat interface correctly', () => {
    render(<ChatComponent />)
    
    expect(screen.getByText('Chat with Documents')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ask a question about your documents...')).toBeInTheDocument()
    expect(screen.getByText('Send')).toBeInTheDocument()
    expect(screen.getByText('Clear Chat')).toBeInTheDocument()
  })

  test('displays empty state message', () => {
    render(<ChatComponent />)
    
    expect(screen.getByText('Start a conversation by asking a question about your documents.')).toBeInTheDocument()
    expect(screen.getByText('Your chat history will be saved for this session.')).toBeInTheDocument()
  })

  test('sends message successfully', async () => {
    render(<ChatComponent />)
    
    const input = screen.getByPlaceholderText('Ask a question about your documents...')
    const sendButton = screen.getByText('Send')
    
    fireEvent.change(input, { target: { value: 'What is this about?' } })
    fireEvent.click(sendButton)
    
    // Check that user message appears
    expect(screen.getByText('What is this about?')).toBeInTheDocument()
    
    // Check loading state
    expect(screen.getByText('Thinking...')).toBeInTheDocument()
    
    // Wait for AI response
    await waitFor(() => {
      expect(screen.getByText('This is a test response from the AI assistant.')).toBeInTheDocument()
    })
    
    // Check that sources are available
    expect(screen.getByText('1 source')).toBeInTheDocument()
  })

  test('handles send with Enter key', async () => {
    render(<ChatComponent />)
    
    const input = screen.getByPlaceholderText('Ask a question about your documents...')
    
    fireEvent.change(input, { target: { value: 'Test question' } })
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 })
    
    expect(screen.getByText('Test question')).toBeInTheDocument()
    
    await waitFor(() => {
      expect(screen.getByText('This is a test response from the AI assistant.')).toBeInTheDocument()
    })
  })

  test('prevents send with Shift+Enter', () => {
    render(<ChatComponent />)
    
    const input = screen.getByPlaceholderText('Ask a question about your documents...')
    
    fireEvent.change(input, { target: { value: 'Test question' } })
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13, shiftKey: true })
    
    // Message should not be sent
    expect(screen.queryByText('Test question')).not.toBeInTheDocument()
  })

  test('toggles source visibility', async () => {
    render(<ChatComponent />)
    
    const input = screen.getByPlaceholderText('Ask a question about your documents...')
    const sendButton = screen.getByText('Send')
    
    fireEvent.change(input, { target: { value: 'What is this about?' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('This is a test response from the AI assistant.')).toBeInTheDocument()
    })
    
    // Click on sources toggle
    const sourcesToggle = screen.getByText('1 source')
    fireEvent.click(sourcesToggle)
    
    // Sources details should now be visible
    expect(screen.getByText('test.pdf (Page 1)')).toBeInTheDocument()
    expect(screen.getByText('Relevance: 95.0%')).toBeInTheDocument()
    expect(screen.getByText('This is a preview of the relevant content...')).toBeInTheDocument()
  })

  test('clears chat successfully', async () => {
    render(<ChatComponent />)
    
    // First send a message
    const input = screen.getByPlaceholderText('Ask a question about your documents...')
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(screen.getByText('Send'))
    
    expect(screen.getByText('Test message')).toBeInTheDocument()
    
    // Clear chat
    fireEvent.click(screen.getByText('Clear Chat'))
    
    await waitFor(() => {
      expect(screen.queryByText('Test message')).not.toBeInTheDocument()
    })
    
    // Should show empty state again
    expect(screen.getByText('Start a conversation by asking a question about your documents.')).toBeInTheDocument()
  })

  test('exports chat history', async () => {
    // Mock URL.createObjectURL
    const mockCreateObjectURL = jest.fn(() => 'mock-url')
    const mockRevokeObjectURL = jest.fn()
    Object.assign(global.URL, {
      createObjectURL: mockCreateObjectURL,
      revokeObjectURL: mockRevokeObjectURL
    })
    
    // Mock document.createElement and appendChild
    const mockAnchor = {
      href: '',
      download: '',
      click: jest.fn()
    }
    const mockAppendChild = jest.fn()
    const mockRemoveChild = jest.fn()
    
    jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any)
    jest.spyOn(document.body, 'appendChild').mockImplementation(mockAppendChild)
    jest.spyOn(document.body, 'removeChild').mockImplementation(mockRemoveChild)
    
    render(<ChatComponent />)
    
    // First send a message to have something to export
    const input = screen.getByPlaceholderText('Ask a question about your documents...')
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(screen.getByText('Send'))
    
    await waitFor(() => {
      expect(screen.getByText('This is a test response from the AI assistant.')).toBeInTheDocument()
    })
    
    // Export chat
    fireEvent.click(screen.getByText('Export'))
    
    expect(mockCreateObjectURL).toHaveBeenCalled()
    expect(mockAnchor.click).toHaveBeenCalled()
    expect(mockRevokeObjectURL).toHaveBeenCalled()
  })

  test('handles API error gracefully', async () => {
    // Override the default handler to return an error
    server.use(
      rest.post('http://localhost:8000/chat', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({
            detail: 'Internal server error'
          })
        )
      })
    )
    
    render(<ChatComponent />)
    
    const input = screen.getByPlaceholderText('Ask a question about your documents...')
    const sendButton = screen.getByText('Send')
    
    fireEvent.change(input, { target: { value: 'What is this about?' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText('Sorry, I encountered an error: Internal server error')).toBeInTheDocument()
    })
    
    // Error should also be displayed in error section
    expect(screen.getByText('Chat Error: Internal server error')).toBeInTheDocument()
  })

  test('prevents sending empty messages', () => {
    render(<ChatComponent />)
    
    const sendButton = screen.getByText('Send')
    
    // Button should be disabled when input is empty
    expect(sendButton).toBeDisabled()
    
    // Try clicking anyway
    fireEvent.click(sendButton)
    
    // No message should be sent
    expect(screen.queryByText('Thinking...')).not.toBeInTheDocument()
  })

  test('shows character limit', () => {
    render(<ChatComponent />)
    
    const input = screen.getByPlaceholderText('Ask a question about your documents...')
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    
    expect(screen.getByText('12/1000')).toBeInTheDocument()
  })

  test('calls onChatError when error occurs', async () => {
    const mockOnChatError = jest.fn()
    
    server.use(
      rest.post('http://localhost:8000/chat', (req, res, ctx) => {
        return res(
          ctx.status(400),
          ctx.json({
            detail: 'Bad request'
          })
        )
      })
    )
    
    render(<ChatComponent onChatError={mockOnChatError} />)
    
    const input = screen.getByPlaceholderText('Ask a question about your documents...')
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(screen.getByText('Send'))
    
    await waitFor(() => {
      expect(mockOnChatError).toHaveBeenCalledWith('Bad request')
    })
  })
})