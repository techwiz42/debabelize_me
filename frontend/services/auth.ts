// Authentication service for debabelizer frontend

export interface User {
  id: number;
  email: string;
  is_confirmed: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginResponse {
  user: User;
  session_token: string;
  message: string;
}

export interface MessageResponse {
  message: string;
  success: boolean;
}

export interface AuthStatus {
  authenticated: boolean;
  user?: User;
}

class AuthService {
  private currentUser: User | null = null;
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL!;
  }

  // Registration
  async register(email: string, password: string): Promise<MessageResponse> {
    const response = await fetch(`${this.baseUrl}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
  }

  // Login
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const loginResponse: LoginResponse = await response.json();
    this.currentUser = loginResponse.user;
    return loginResponse;
  }

  // Logout
  async logout(): Promise<MessageResponse> {
    const response = await fetch(`${this.baseUrl}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Logout failed');
    }

    this.currentUser = null;
    return response.json();
  }

  // Confirm email
  async confirmEmail(token: string): Promise<MessageResponse> {
    const response = await fetch(`${this.baseUrl}/auth/confirm-email`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ token }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Email confirmation failed');
    }

    return response.json();
  }

  // Get current user info
  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/me`, {
        credentials: 'include',
      });

      if (!response.ok) {
        return null;
      }

      const user: User = await response.json();
      this.currentUser = user;
      return user;
    } catch (error) {
      console.error('Error fetching current user:', error);
      return null;
    }
  }

  // Check authentication status
  async checkAuthStatus(): Promise<AuthStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/status`, {
        credentials: 'include',
      });

      if (!response.ok) {
        return { authenticated: false };
      }

      const status: AuthStatus = await response.json();
      if (status.user) {
        this.currentUser = status.user;
      }
      return status;
    } catch (error) {
      console.error('Error checking auth status:', error);
      return { authenticated: false };
    }
  }

  // Get cached current user (doesn't make API call)
  getCachedUser(): User | null {
    return this.currentUser;
  }

  // Clear cached user data
  clearCache(): void {
    this.currentUser = null;
  }
}

// Export singleton instance
export const authService = new AuthService();

// Export individual methods for convenience
export const register = authService.register.bind(authService);
export const login = authService.login.bind(authService);
export const logout = authService.logout.bind(authService);
export const confirmEmail = authService.confirmEmail.bind(authService);
export const getCurrentUser = authService.getCurrentUser.bind(authService);
export const checkAuthStatus = authService.checkAuthStatus.bind(authService);