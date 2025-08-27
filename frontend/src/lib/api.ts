// Travel Agent Pro Frontend API Client
// 与后端 FastAPI 服务通信

// 基础配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 类型定义（与后端 schemas.py 保持一致）
export interface TripRequest {
  destination: string;
  duration_days: number;
  theme?: string;
  budget?: number;
  interests?: string[];
  start_date?: string;
  include_accommodation?: boolean;
}

export interface Activity {
  name: string;
  type: string;
  location: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  description: string;
  estimated_cost?: number;
  tips?: string;
  distance_km_from_prev?: number;
  drive_time_min_from_prev?: number;
  category?: string;
  open_ok?: boolean;
  open_hours_raw?: string;
  closed_reason?: string;
  replaced_from?: string;
  open_hours_explain?: string;
  replaced_from_open_hours_raw?: string;
  replacement_reason?: string;
  replacement_commute_delta_min?: number;
  replacement_candidates?: Array<{
    name: string;
    summary: string;
    [key: string]: any;
  }>;
}

export interface DayPlan {
  date: string;
  day_title: string;
  activities: Activity[];
  daily_summary: string;
  estimated_daily_cost: number;
}

export interface TripPlan {
  destination: string;
  duration_days: number;
  theme: string;
  start_date: string;
  end_date: string;
  daily_plans: DayPlan[];
  total_estimated_cost: number;
  general_tips: string[];
  plan_rationale?: string;
}

export interface DailyForecast {
  date: string;
  text_day: string;
  icon_day: string;
  temp_max_c: number;
  temp_min_c: number;
  precip_mm: number;
  advice: string;
}

export interface WeatherForecast {
  location: string;
  location_id?: string;
  days: number;
  updated_at: string;
  daily: DailyForecast[];
}

// API 错误类
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// 通用请求函数
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  console.log(`🌐 API Request: ${options.method || 'GET'} ${url}`);
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

    const responseData = await response.json();

    if (!response.ok) {
      console.error(`❌ API Error: ${response.status} ${response.statusText}`, responseData);
      throw new APIError(
        responseData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        responseData
      );
    }

    console.log(`✅ API Success: ${url}`, responseData);
    return responseData;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    
    console.error(`❌ Network Error:`, error);
    throw new APIError(
      error instanceof Error ? error.message : 'Network request failed',
      0
    );
  }
}

// API 客户端方法
export const api = {
  // 健康检查
  async health(): Promise<{ status: string }> {
    return apiRequest('/health');
  },

  // 生成行程计划（使用标准接口）
  async generateTrip(request: TripRequest): Promise<TripPlan> {
    return apiRequest('/generate-trip', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // 使用 LangGraph 生成行程计划（推荐）
  async planWithGraph(request: TripRequest): Promise<TripPlan> {
    return apiRequest('/plan', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // 获取组合结果（行程 + 天气）
  async planBundle(request: TripRequest): Promise<{
    plan: TripPlan;
    weather: WeatherForecast;
  }> {
    return apiRequest('/plan-bundle', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // 获取目的地天气
  async getWeather(location: string): Promise<WeatherForecast> {
    return apiRequest('/destination-weather', {
      method: 'POST',
      body: JSON.stringify({ location }),
    });
  },

  // 获取POI统计信息
  async getPOIStats(): Promise<{
    total_count: number;
    sample_pois: Array<{ name: string; type: string; address: string }>;
  }> {
    return apiRequest('/poi-stats');
  },
};

// 工具函数：格式化错误信息
export function formatAPIError(error: unknown): string {
  if (error instanceof APIError) {
    if (error.status === 0) {
      return '网络连接失败，请检查后端服务是否正常运行';
    }
    return `服务器错误 (${error.status}): ${error.message}`;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return '发生未知错误';
}

// 工具函数：检查后端服务状态
export async function checkBackendHealth(): Promise<boolean> {
  try {
    await api.health();
    console.log('✅ 后端服务连接正常');
    return true;
  } catch (error) {
    console.error('❌ 后端服务连接失败:', error);
    return false;
  }
}

