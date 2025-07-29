interface ChatMessage {
  message: string;
  language?: string;
}

interface ChatResponse {
  response: string;
  debabelized_text: string;
  response_language?: string;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8005';
  }

  async sendMessage(message: string, language?: string): Promise<ChatResponse> {
    const payload: ChatMessage = {
      message,
      language
    };

    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }
}

export const apiService = new ApiService();