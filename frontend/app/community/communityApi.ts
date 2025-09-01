// 基础API配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// 响应数据通用类型
interface ApiResponse<T> {
  status: 'success' | 'error';
  message?: string;
  data?: T;
  count?: number;
  // 新增错误代码，便于前端处理特定错误
  errorCode?: string;
}

// 用户信息类型
export interface UserProfile {
  id: number;
  name: string;
  avatar: string;
  bio: string;
  gender: string;
  age: number;
  mbti: string;
  hobbies: string[];
  travelDestination: string;
  schedule: string;
  budget: string;
}

// 匹配用户类型
export interface MatchUser extends UserProfile {
  matchingScore: number;
  isVerified?: boolean;
}

// 队伍类型
export interface Team {
  id: number;
  name: string;
  captainId: number;
  members: UserProfile[];
  memberCount?: number;
}

// 消息类型
export interface Message {
  id: number;
  teamId: number;
  senderId: number;
  senderName: string;
  content: string;
  timestamp: string;
}

// 字典数据类型
export interface Dictionaries {
  mbtiTypes: string[];
  hobbies: string[];
  destinations: string[];
  schedules: string[];
  budgets: string[];
}

// 新增：检查队伍名是否已存在
export const checkTeamNameExists = async (captainId: number, teamName: string) => {
  const response = await fetch(
    `${API_BASE_URL}/teams/check-name?captain_id=${captainId}&name=${encodeURIComponent(teamName)}`
  );
  
  const data: ApiResponse<{ exists: boolean }> = await response.json();
  return data;
};

// API服务类
export const communityApi = {
  // 初始化基础数据
  initBaseData: async () => {
    const response = await fetch(`${API_BASE_URL}/init-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    const data: ApiResponse<{}> = await response.json();
    return data;
  },
  
  // 初始化测试用户
  initTestUsers: async (count: number = 20) => {
    const response = await fetch(`${API_BASE_URL}/init-users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ count }),
    });
    
    const data: ApiResponse<{}> = await response.json();
    return data;
  },
  
  // 获取字典数据
  getDictionaries: async () => {
    const response = await fetch(`${API_BASE_URL}/dictionaries`);
    const data: ApiResponse<Dictionaries> = await response.json();
    return data;
  },
  
  // 获取用户信息
  getUserProfile: async (userId: number) => {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`);
    const data: ApiResponse<UserProfile> = await response.json();
    return data;
  },
  
  // 更新用户信息
  updateUserProfile: async (userId: number, profile: Partial<UserProfile>) => {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profile),
    });
    
    const data: ApiResponse<UserProfile> = await response.json();
    return data;
  },
  
  // 获取用户匹配结果
  getUserMatches: async (userId: number) => {
    const response = await fetch(`${API_BASE_URL}/users/${userId}/matches`);
    const data: ApiResponse<{user: MatchUser}[]> = await response.json();
    
    // 转换数据格式以适应前端需求
    if (data.status === 'success' && data.data) {
      return {
        ...data,
        data: data.data.map(item => item.user)
      };
    }
    
    return data;
  },
  
  // 为用户寻找匹配
  findMatchesForUser: async (userId: number) => {
    const response = await fetch(`${API_BASE_URL}/users/${userId}/matches`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    const data: ApiResponse<{user: MatchUser}[]> = await response.json();
    console.assert(data);
    
    // 转换数据格式以适应前端需求
    if (data.status === 'success' && data.data) {
      console.assert(data.data);
      return {
        ...data,
        data: data.data.map(item => item.user)
      };
    }
    
    return data;
  },
  
  // 获取用户的队伍
  getUserTeams: async (userId: number) => {
    const response = await fetch(`${API_BASE_URL}/teams?user_id=${userId}`);
    const data: ApiResponse<{
      captainTeams: Team[];
      memberTeams: Team[];
    }> = await response.json();
    return data;
  },
  
  // 创建队伍 - 增加防重复检查逻辑
  createTeam: async (name: string, captainId: number) => {
    // 前端先检查队伍名是否已存在
    const checkResponse = await checkTeamNameExists(captainId, name);
    if (checkResponse.status === 'success' && checkResponse.data?.exists) {
      return {
        status: 'error',
        message: '您已创建过同名队伍，请更换名称',
        errorCode: 'DUPLICATE_TEAM_NAME'
      } as ApiResponse<Team>;
    }
    
    // 后端再次验证并创建队伍
    const response = await fetch(`${API_BASE_URL}/teams`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, captainId }),
    });
    
    const data: ApiResponse<Team> = await response.json();
    return data;
  },
  
  // 删除队伍
  deleteTeam: async (teamId: number, userId: number) => {
    const response = await fetch(`${API_BASE_URL}/teams/${teamId}?user_id=${userId}`, {
      method: 'DELETE',
    });
    
    const data: ApiResponse<{}> = await response.json();
    return data;
  },
  
  // 添加队员 - 增加重复检查
  addTeamMember: async (teamId: number, userId: number) => {
    // 先获取当前队伍信息，检查用户是否已在队伍中
    const teamsResponse = await communityApi.getUserTeams(userId);
    if (teamsResponse.status === 'success' && teamsResponse.data) {
      const allTeams = [...teamsResponse.data.captainTeams, ...teamsResponse.data.memberTeams];
      const targetTeam = allTeams.find(team => team.id === teamId);
      
      if (targetTeam && targetTeam.members.some(member => member.id === userId)) {
        return {
          status: 'error',
          message: '该用户已在队伍中',
          errorCode: 'USER_ALREADY_IN_TEAM'
        } as ApiResponse<Team>;
      }
    }
    
    const response = await fetch(`${API_BASE_URL}/teams/${teamId}/members`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId }),
    });
    
    const data: ApiResponse<Team> = await response.json();
    return data;
  },
  
  // 移除队员
  removeTeamMember: async (teamId: number, memberId: number, requesterId: number) => {
    // 检查是否尝试移除自己
    if (memberId === requesterId) {
      // 是队长且是最后一个成员
      const teamsResponse = await communityApi.getUserTeams(requesterId);
      if (teamsResponse.status === 'success' && teamsResponse.data) {
        const captainTeam = teamsResponse.data.captainTeams.find(team => team.id === teamId);
        if (captainTeam && captainTeam.memberCount === 1) {
          return {
            status: 'error',
            message: '作为队长，您不能离开最后一个成员的队伍，请先删除队伍',
            errorCode: 'LAST_MEMBER_CANNOT_LEAVE'
          } as ApiResponse<Team>;
        }
      }
    }
    
    const response = await fetch(
      `${API_BASE_URL}/teams/${teamId}/members/${memberId}?requester_id=${requesterId}`,
      { method: 'DELETE' }
    );
    
    const data: ApiResponse<Team> = await response.json();
    return data;
  },
  
  // 获取队伍消息
  getTeamMessages: async (teamId: number) => {
    const response = await fetch(`${API_BASE_URL}/teams/${teamId}/messages`);
    const data: ApiResponse<Message[]> = await response.json();
    return data;
  },
  
  // 发送队伍消息 - 增加空消息检查
  sendTeamMessage: async (teamId: number, senderId: number, content: string) => {
    // 检查消息内容是否为空或只包含空格
    const trimmedContent = content.trim();
    if (!trimmedContent) {
      return {
        status: 'error',
        message: '消息内容不能为空',
        errorCode: 'EMPTY_MESSAGE'
      } as ApiResponse<Message>;
    }
    
    const response = await fetch(`${API_BASE_URL}/teams/${teamId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ senderId, content: trimmedContent }),
    });
    
    const data: ApiResponse<Message> = await response.json();
    return data;
  }
};
