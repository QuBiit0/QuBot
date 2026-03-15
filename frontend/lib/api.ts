import { Agent, Task, ApiResponse, TaskStatus } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public errors?: Record<string, string[]>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  const data = await response.json();
  
  if (!response.ok) {
    throw new ApiError(
      response.status,
      data.message || response.statusText,
      data.errors
    );
  }
  
  return data;
}

function getAuthHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

// Agents API
export const agentsApi = {
  getAll: async (): Promise<ApiResponse<Agent[]>> => {
    const response = await fetch(`${API_BASE_URL}/agents`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  getById: async (id: string): Promise<ApiResponse<Agent>> => {
    const response = await fetch(`${API_BASE_URL}/agents/${id}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  create: async (data: Partial<Agent>): Promise<ApiResponse<Agent>> => {
    const response = await fetch(`${API_BASE_URL}/agents`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  update: async (id: string, data: Partial<Agent>): Promise<ApiResponse<Agent>> => {
    const response = await fetch(`${API_BASE_URL}/agents/${id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  delete: async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/agents/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new ApiError(response.status, 'Failed to delete agent');
    }
  },
};

// Tasks API
export const tasksApi = {
  getAll: async (): Promise<ApiResponse<Task[]>> => {
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  getById: async (id: string): Promise<ApiResponse<Task>> => {
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(response);
  },

  create: async (data: Partial<Task>): Promise<ApiResponse<Task>> => {
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  update: async (id: string, data: Partial<Task>): Promise<ApiResponse<Task>> => {
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  updateStatus: async (id: string, status: TaskStatus): Promise<ApiResponse<Task>> => {
    const response = await fetch(`${API_BASE_URL}/tasks/${id}/status`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ status }),
    });
    return handleResponse(response);
  },

  delete: async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new ApiError(response.status, 'Failed to delete task');
    }
  },
};

// Generic API methods for any endpoint
async function get<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

async function post<T>(endpoint: string, data: any): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse(response);
}

async function patch<T>(endpoint: string, data: any): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse(response);
}

async function del(endpoint: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new ApiError(response.status, 'Request failed');
  }
}

// Legacy exports for backwards compatibility
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
