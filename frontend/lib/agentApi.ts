/**
 * Agent模块API服务
 * 处理与智能旅游Agent的交互
 */

const AGENT_API_BASE_URL = process.env.NEXT_PUBLIC_AGENT_API_URL || 'http://localhost:5001/api/v1';

// 数据类型定义
export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: string;
  type?: 'text' | 'plan' | 'suggestions';
}

export interface TravelPreference {
  weather_tolerance?: 'excellent' | 'good' | 'fair' | 'poor';
  traffic_tolerance?: 'smooth' | 'slow' | 'congested' | 'severe';
  crowd_tolerance?: 'low' | 'medium' | 'high' | 'very_high';
  time_conscious?: boolean;
  budget_conscious?: boolean;
  comfort_priority?: boolean;
  cultural_interest?: boolean;
  nature_preference?: boolean;
  food_lover?: boolean;
  photography_enthusiast?: boolean;
}

export interface POIInfo {
  name: string;
  address?: string;
  rating?: number;
  category?: string;
  description?: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
  opening_hours?: string;
  ticket_price?: number;
  visit_duration?: number;
  crowd_level?: 'low' | 'medium' | 'high' | 'very_high';
  weather_dependency?: boolean;
}

export interface RouteSegment {
  from_poi: string;
  to_poi: string;
  distance?: number;
  duration?: number;
  transport_mode?: string;
  traffic_condition?: 'smooth' | 'slow' | 'congested' | 'severe';
  cost?: number;
}

export interface TravelPlan {
  id: string;
  origin: string;
  destinations: string[];
  pois?: POIInfo[];
  route_segments?: RouteSegment[];
  total_distance?: number;
  total_duration?: number;
  total_cost?: number;
  weather_compatibility?: number;
  traffic_score?: number;
  crowd_score?: number;
  overall_score?: number;
  recommendations?: string[];
  adjustments?: string[];
  created_at?: string;
}

export interface PreferenceQuestion {
  id: string;
  question: string;
  type: string;
  options: string[];
}

export interface PreferenceQuestions {
  questions: PreferenceQuestion[];
}

// API请求函数
class AgentApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${AGENT_API_BASE_URL}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    const response = await fetch(url, {
      ...defaultOptions,
      ...options,
    });

    let json: any = null;
    try {
      json = await response.json();
    } catch (e) {
      // ignore parse error for empty body
    }

    if (!response.ok) {
      const message = json?.message || json?.error || `HTTP error! status: ${response.status}`;
      throw new Error(message);
    }

    // unwrap { status, data } pattern if present
    if (json && typeof json === 'object' && 'status' in json && 'data' in json) {
      return json.data as T;
    }

    return json as T;
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string; message: string; timestamp?: string; version?: string }> {
    return this.request('/health');
  }

  /**
   * AI聊天对话
   */
  async chat(message: string, context?: any): Promise<{ message: string; suggestions?: string[]; type?: string; timestamp?: string }> {
    return this.request('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        context,
      }),
    });
  }

  /**
   * 创建旅游计划
   */
  async createTravelPlan(
    origin: string,
    destinations: string[],
    preferences?: TravelPreference
  ): Promise<TravelPlan> {
    return this.request('/travel-plan', {
      method: 'POST',
      body: JSON.stringify({
        origin,
        destinations,
        preferences,
      }),
    });
  }

  /**
   * 获取用户偏好问题
   */
  async getUserPreferenceQuestions(): Promise<PreferenceQuestion[]> {
    return this.request('/travel/preferences/questions');
  }

  /**
   * 根据用户偏好调整计划
   */
  async adjustPlanByPreferences(
    planId: string,
    userAnswers: Record<string, any>
  ): Promise<TravelPlan> {
    return this.request(`/travel/plan/${planId}/adjust`, {
      method: 'POST',
      body: JSON.stringify({
        adjustments: userAnswers,
      }),
    });
  }

  /**
   * 搜索POI
   */
  async searchPOI(query: string, location?: string, category?: string): Promise<POIInfo[]> {
    const params = new URLSearchParams({ q: query });
    if (location) params.append('city', location);
    if (category) params.append('category', category);
    
    return this.request(`/poi/search?${params.toString()}`);
  }

  /**
   * 优化路线
   */
  async optimizeRoute(
    planId: string,
    optimizationType: 'time' | 'cost' | 'comfort' = 'time'
  ): Promise<TravelPlan> {
    return this.request(`/travel/plan/${planId}/optimize`, {
      method: 'POST',
      body: JSON.stringify({
        optimization_type: optimizationType,
      }),
    });
  }

  /**
   * 获取旅游计划详情
   */
  async getTravelPlan(planId: string): Promise<TravelPlan> {
    return this.request(`/travel/plan/${planId}`);
  }

  /**
   * 获取天气信息
   */
  async getWeatherInfo(location: string, date?: string): Promise<any> {
    const params = new URLSearchParams({ location });
    if (date) {
      params.append('date', date);
    }
    
    return this.request(`/travel/weather?${params.toString()}`);
  }

  /**
   * 获取交通信息
   */
  async getTrafficInfo(from: string, to: string): Promise<any> {
    const params = new URLSearchParams({ from, to });
    return this.request(`/travel/traffic?${params.toString()}`);
  }

  /**
   * 获取人流信息
   */
  async getCrowdInfo(location: string, date?: string): Promise<any> {
    const params = new URLSearchParams({ location });
    if (date) {
      params.append('date', date);
    }
    
    return this.request(`/travel/crowd?${params.toString()}`);
  }
}

// 创建单例实例
export const agentApi = new AgentApiService();

// 导出默认实例
export default agentApi;

// 辅助函数
export const formatChatMessage = (content: string, sender: 'user' | 'ai', type: 'text' | 'plan' | 'suggestions' = 'text'): ChatMessage => {
  return {
    id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    content,
    sender,
    timestamp: new Date().toISOString(),
    type,
  };
};

export const formatTravelPlan = (plan: TravelPlan): string => {
  let formatted = `🗺️ **旅游计划** (${plan.id})\n\n`;
  formatted += `📍 **出发地**: ${plan.origin}\n`;
  formatted += `🎯 **目的地**: ${plan.destinations.join(' → ')}\n\n`;
  
  if (plan.total_distance) {
    formatted += `📏 **总距离**: ${plan.total_distance}公里\n`;
  }
  if (plan.total_duration) {
    formatted += `⏱️ **总时长**: ${Math.floor(plan.total_duration / 60)}小时${plan.total_duration % 60}分钟\n`;
  }
  if (plan.total_cost) {
    formatted += `💰 **预估费用**: ¥${plan.total_cost}\n`;
  }
  
  if (plan.overall_score) {
    formatted += `\n⭐ **综合评分**: ${plan.overall_score}/100\n`;
  }
  
  if (plan.recommendations && plan.recommendations.length > 0) {
    formatted += `\n💡 **智能建议**:\n`;
    plan.recommendations.forEach((rec, index) => {
      formatted += `${index + 1}. ${rec}\n`;
    });
  }
  
  return formatted;
};

export const formatPOIInfo = (poi: POIInfo): string => {
  let formatted = `📍 **${poi.name}**\n`;
  
  if (poi.rating) {
    formatted += `⭐ 评分: ${poi.rating}/5\n`;
  }
  if (poi.category) {
    formatted += `🏷️ 类型: ${poi.category}\n`;
  }
  if (poi.description) {
    formatted += `📝 简介: ${poi.description}\n`;
  }
  if (poi.opening_hours) {
    formatted += `🕒 开放时间: ${poi.opening_hours}\n`;
  }
  if (poi.ticket_price && poi.ticket_price > 0) {
    formatted += `🎫 门票: ¥${poi.ticket_price}\n`;
  }
  if (poi.visit_duration) {
    formatted += `⏰ 建议游览时间: ${poi.visit_duration}分钟\n`;
  }
  
  return formatted;
};