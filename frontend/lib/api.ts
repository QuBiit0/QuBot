import { Agent, Task, ApiResponse, TaskStatus } from '@/types';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === 'development' ? 'http://localhost:8000/api/v1' : '/api/v1');

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
    public errors?: Record<string, string[]>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// --- Token management ---

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

function clearToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('token');
}

// --- Core fetch wrapper with retry + 401 handling ---

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

async function refreshAccessToken(): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // send refresh_token cookie
    });

    if (!res.ok) return null;

    const data = await res.json();
    const newToken = data.access_token as string;
    localStorage.setItem('token', newToken);
    return newToken;
  } catch {
    return null;
  }
}

async function fetchWithAuth<T>(
  url: string,
  options: RequestInit = {},
  retries = 2
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, { ...options, headers });

      // Handle 401 — try token refresh once
      if (response.status === 401 && token) {
        if (!isRefreshing) {
          isRefreshing = true;
          const newToken = await refreshAccessToken();
          isRefreshing = false;

          if (newToken) {
            onTokenRefreshed(newToken);
            // Retry request with new token
            headers.Authorization = `Bearer ${newToken}`;
            const retryResponse = await fetch(url, { ...options, headers });
            return handleResponse<T>(retryResponse);
          } else {
            // Refresh failed — clear auth and redirect
            clearToken();
            if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
              window.location.href = '/login';
            }
            throw new ApiError(401, 'Session expired. Please log in again.', 'SESSION_EXPIRED');
          }
        } else {
          // Another request is already refreshing — wait for it
          return new Promise<T>((resolve, reject) => {
            addRefreshSubscriber(async (newToken: string) => {
              try {
                headers.Authorization = `Bearer ${newToken}`;
                const retryResponse = await fetch(url, { ...options, headers });
                resolve(await handleResponse<T>(retryResponse));
              } catch (err) {
                reject(err);
              }
            });
          });
        }
      }

      return await handleResponse<T>(response);
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));

      // Don't retry on client errors (4xx) except network failures
      if (err instanceof ApiError && err.status >= 400 && err.status < 500) {
        throw err;
      }

      // Last attempt — throw
      if (attempt === retries) {
        throw lastError;
      }

      // Exponential backoff before retry
      await new Promise((r) => setTimeout(r, Math.pow(2, attempt) * 500));
    }
  }

  throw lastError ?? new Error('Request failed');
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    if (!response.ok) {
      throw new ApiError(response.status, response.statusText);
    }
    return undefined as T;
  }

  if (!response.ok) {
    const errorData = data as { error?: { code?: string; message?: string }; detail?: string };
    const message =
      errorData.error?.message ?? errorData.detail ?? response.statusText;
    const code = errorData.error?.code ?? `HTTP_${response.status}`;
    throw new ApiError(response.status, message, code);
  }

  return data as T;
}

// --- Auth API ---

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  avatar_url?: string;
  created_at: string;
}

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    return fetchWithAuth<TokenResponse>(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      body: JSON.stringify(data),
      credentials: 'include', // needed for cross-origin Set-Cookie (refresh_token)
    });
  },

  register: async (data: RegisterRequest): Promise<UserResponse> => {
    return fetchWithAuth<UserResponse>(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  logout: async (): Promise<void> => {
    await fetchWithAuth<void>(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    clearToken();
  },

  me: async (): Promise<UserResponse> => {
    return fetchWithAuth<UserResponse>(`${API_BASE_URL}/auth/me`);
  },
};

// --- Agents API ---

export const agentsApi = {
  getAll: async (page = 1, limit = 50): Promise<ApiResponse<Agent[]>> => {
    return fetchWithAuth<ApiResponse<Agent[]>>(
      `${API_BASE_URL}/agents?skip=${(page-1)*limit}&limit=${limit}`
    );
  },

  getById: async (id: string): Promise<ApiResponse<Agent>> => {
    return fetchWithAuth<ApiResponse<Agent>>(`${API_BASE_URL}/agents/${id}`);
  },

  create: async (data: Partial<Agent>): Promise<ApiResponse<Agent>> => {
    return fetchWithAuth<ApiResponse<Agent>>(`${API_BASE_URL}/agents`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: string, data: Partial<Agent>): Promise<ApiResponse<Agent>> => {
    return fetchWithAuth<ApiResponse<Agent>>(`${API_BASE_URL}/agents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<void> => {
    return fetchWithAuth<void>(`${API_BASE_URL}/agents/${id}`, {
      method: 'DELETE',
    });
  },
};

// --- Tasks API ---

export const tasksApi = {
  getAll: async (page = 1, limit = 50): Promise<ApiResponse<Task[]>> => {
    return fetchWithAuth<ApiResponse<Task[]>>(
      `${API_BASE_URL}/tasks?skip=${(page-1)*limit}&limit=${limit}`
    );
  },

  getById: async (id: string): Promise<ApiResponse<Task>> => {
    return fetchWithAuth<ApiResponse<Task>>(`${API_BASE_URL}/tasks/${id}`);
  },

  getKanban: async (): Promise<ApiResponse<Record<TaskStatus, Task[]>>> => {
    return fetchWithAuth<ApiResponse<Record<TaskStatus, Task[]>>>(
      `${API_BASE_URL}/tasks/kanban/board`
    );
  },

  create: async (data: Partial<Task>): Promise<ApiResponse<Task>> => {
    return fetchWithAuth<ApiResponse<Task>>(`${API_BASE_URL}/tasks`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: string, data: Partial<Task>): Promise<ApiResponse<Task>> => {
    return fetchWithAuth<ApiResponse<Task>>(`${API_BASE_URL}/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  updateStatus: async (id: string, status: TaskStatus): Promise<ApiResponse<Task>> => {
    return fetchWithAuth<ApiResponse<Task>>(`${API_BASE_URL}/tasks/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },

  delete: async (id: string): Promise<void> => {
    return fetchWithAuth<void>(`${API_BASE_URL}/tasks/${id}`, {
      method: 'DELETE',
    });
  },
};

// --- Generic API helpers ---

async function get<T>(endpoint: string): Promise<T> {
  return fetchWithAuth<T>(`${API_BASE_URL}${endpoint}`);
}

async function post<T>(endpoint: string, data: unknown): Promise<T> {
  return fetchWithAuth<T>(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

async function patch<T>(endpoint: string, data: unknown): Promise<T> {
  return fetchWithAuth<T>(`${API_BASE_URL}${endpoint}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

async function del(endpoint: string): Promise<void> {
  return fetchWithAuth<void>(`${API_BASE_URL}${endpoint}`, {
    method: 'DELETE',
  });
}

// --- Unified export ---

export const api = {
  ...agentsApi,
  ...tasksApi,
  getAgents: agentsApi.getAll,
  getAgent: agentsApi.getById,
  createAgent: agentsApi.create,
  updateAgent: agentsApi.update,
  deleteAgent: agentsApi.delete,
  getTasks: tasksApi.getAll,
  getTask: tasksApi.getById,
  createTask: tasksApi.create,
  updateTask: tasksApi.update,
  updateTaskStatus: tasksApi.updateStatus,
  deleteTask: tasksApi.delete,
  get,
  post,
  patch,
  delete: del,
};

export { ApiError };
