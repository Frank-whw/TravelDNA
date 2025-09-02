/**
 * 社区页面组件 - 社交搭子匹配界面
 * 
 * 功能概述：
 * - 三栏式布局设计，支持独立滚动
 * - 左侧：用户信息编辑与匹配结果展示
 * - 中间：用户详情查看与队伍邀请
 * - 右侧：队伍管理功能
 * - 社交搭子匹配与团队协作功能
 * 
 * 设计思路：
 * - 采用现代卡片式UI设计，清晰分隔不同功能区域
 * - 使用柔和渐变与阴影创造层次感
 * - 交互元素有明确的视觉反馈
 * - 响应式设计适配不同屏幕尺寸
 */

"use client"

import { useState, useEffect, useRef } from "react"
import { 
  Users, MapPin, Calendar, Coffee, Moon, Sun, Wallet, 
  Filter, UserPlus, PlusCircle, Trash2, CheckCircle2, 
  XCircle, Send, ChevronRight, Menu, ArrowRight, RefreshCw, 
  MessageSquare, Heart, Edit3, MoreHorizontal, LogOut, Star
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Switch } from "@/components/ui/switch"
import { toast } from "sonner"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { communityApi, Message, Dictionaries,UserProfile,Team, MatchUser} from "./communityApi"
import { set } from "date-fns"

//当前用户id
const currentUserId = 1;

// MBTI类型列表
const mbtiTypes = [
  "ISTJ", "ISFJ", "INFJ", "INTJ",
  "ISTP", "ISFP", "INFP", "INTP",
  "ESTP", "ESFP", "ENFP", "ENTP",
  "ESTJ", "ESFJ", "ENFJ", "ENTJ"
];

// 兴趣爱好列表
const hobbiesList = [
  "美食", "摄影", "徒步", "文化", "购物", 
  "自然风光", "历史古迹", "城市观光", "户外探险",
  "博物馆", "艺术展览", "音乐", "夜生活", "美食探索"
];

// 旅行目的地列表
const destinations = [
  "北京", "上海", "广州", "成都", "杭州", "西安", 
  "三亚", "青岛", "厦门", "重庆", "拉萨", "乌鲁木齐",
  "南京", "苏州", "桂林", "张家界", "九寨沟", "丽江"
];

// 作息类型
const schedules = [
  "早睡早起", "晚睡晚起", "弹性作息", "跟随行程安排"
];

// 预算范围
const budgets = [
  "经济型", "舒适型", "轻奢型", "豪华型"
];

// 生成模拟匹配用户数据
const generateMockMatches = (): MatchUser[] => {
  return Array.from({ length: 8 }, (_, i) => ({
    id: i + 1,
    name: `旅行者${i + 1}`,
    avatar: `https://space.coze.cn/api/coze_space/gen_image?image_size=square&prompt=Traveler%20avatar%2C%20person%20portrait%2C%20cartoon%20style&sign=c78c870568801b5b3a239395ecc9a66d`,
    age: Math.floor(Math.random() * 30) + 20,
    gender: Math.random() > 0.5 ? "男" : "女",
    mbti: mbtiTypes[Math.floor(Math.random() * mbtiTypes.length)],
    hobbies: Array.from({ length: Math.floor(Math.random() * 3) + 2 }, () => 
      hobbiesList[Math.floor(Math.random() * hobbiesList.length)]
    ),
    travelDestination: destinations[Math.floor(Math.random() * destinations.length)],
    schedule: schedules[Math.floor(Math.random() * schedules.length)],
    budget: budgets[Math.floor(Math.random() * budgets.length)],
    matchingScore: Math.floor(Math.random() * 30) + 70,
    isVerified: Math.random() > 0.3,
    bio: "热爱旅行，希望找到志同道合的旅伴一起探索世界的美好。喜欢体验当地文化和美食，期待与你同行！"
  }));
};

// 生成初始队伍数据
const generateInitialTeams = (): Team[] => {
  return [
    {
      id: 1,
      name: "山水探索队",
      members: [
        {
          id: 999,
          name: "我自己",
          avatar: `https://space.coze.cn/api/coze_space/gen_image?image_size=square&prompt=User%20avatar%2C%20person%20portrait%2C%20cartoon%20style&sign=a9b44dd75e1d6cd26a8cf0935243421c`,
          age: 28,
          gender: "男",
          mbti: "ENFP",
          hobbies: ["摄影", "徒步", "自然风光"],
          travelDestination: "张家界",
          schedule: "弹性作息",
          budget: "舒适型",
          bio: "旅行爱好者，喜欢探索自然景观和人文历史。"
        }
      ],
      captainId: 999 // 当前用户ID
    }
  ];
};

export default function Community() {
    // 状态管理
    const [userProfile, setUserProfile] = useState<UserProfile>({
      id: currentUserId,
      name: "",
      avatar: "https://picsum.photos/seed/user/200/200",
      bio: "旅行爱好者，喜欢探索自然景观和人文历史。",
      mbti: "",
      hobbies: [],
      travelDestination: "",
      schedule: "",
      budget: "",
      gender: "",
      age: 0,
    });
    
    // 字典数据
    const [dictionaries, setDictionaries] = useState<Dictionaries>({
      mbtiTypes: [],
      hobbies: [],
      destinations: [],
      schedules: [],
      budgets: []
    });
    
    // 匹配结果状态
    const [matchResults, setMatchResults] = useState<MatchUser[]>([]);
    
    // 选中用户状态
    const [selectedUser, setSelectedUser] = useState<MatchUser | null>(null);
    
    // 队伍列表状态
    const [teams, setTeams] = useState<Team[]>([]);
    const [captainTeams, setCaptainTeams] = useState<Team[]>([]);
    const [memberTeams, setMemberTeams] = useState<Team[]>([]);
    
    // 新队伍名称状态
    const [newTeamName, setNewTeamName] = useState("");
    
    // 群聊状态
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [currentChatTeamId, setCurrentChatTeamId] = useState<number | null>(null);
    const [chatMessages, setChatMessages] = useState<Message[]>([]);
    const [newMessage, setNewMessage] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);
    
    // 加载状态
    const [isLoading, setIsLoading] = useState({
      profile: false,
      matches: false,
      teams: false,
      messages: false,
      init: false
    });
    
    // 初始化数据
    useEffect(() => {
      const initData = async () => {
        setIsLoading(prev => ({ ...prev, init: true }));
        try {
          // 加载字典数据
          const dictResponse = await communityApi.getDictionaries();
          if (dictResponse.status === 'success' && dictResponse.data) {
            setDictionaries(dictResponse.data);
          }
          
          // 加载用户信息
          setIsLoading(prev => ({ ...prev, profile: true }));
          const userResponse = await communityApi.getUserProfile(currentUserId);
          if (userResponse.status === 'success' && userResponse.data) {
            setUserProfile(userResponse.data);
          } else {
            // 如果用户不存在，可能需要引导注册流程
            toast.info("首次使用，请完善您的个人资料");
          }
          setIsLoading(prev => ({ ...prev, profile: false }));
          
          // 加载队伍信息
          loadTeams();
          
          // 加载匹配结果
          loadMatches();
        } catch (error) {
          console.error("初始化数据失败:", error);
          toast.error("初始化数据失败，请刷新页面重试");
        } finally {
          setIsLoading(prev => ({ ...prev, init: false }));
        }
      };
      
      initData();
      //console.log("OKOK\n");
    }, []);
  
  
  // 打开群聊模态框
  const openChatModal = (teamId: number) => {
    setCurrentChatTeamId(teamId);
    setIsChatOpen(true);
    
    // 模拟聊天历史记录
    const team = teams.find(t => t.id === teamId);
    if (team) {
      setChatMessages([
        {
          id: 1,
          teamId: 1,
          senderId: team.captainId,
          senderName: team.members.find(m => m.id === team.captainId)?.name || "队长",
          content: `欢迎来到${team.name}的群聊！`,
          timestamp: "10:00"
        },
        {
          id: 2,
          teamId: 2,
          senderId: 999,
          senderName: "我自己",
          content: "大家好！",
          timestamp: "10:05"
        }
      ]);
    }
  };

  // 加载队伍信息
  const loadTeams = async () => {
    try {
      setIsLoading(prev => ({ ...prev, teams: true }));
      const response = await communityApi.getUserTeams(currentUserId);
      if (response.status === 'success' && response) {
        setTeams([...response.data.captainTeams, ...response.data.memberTeams]);
        setCaptainTeams(response.data.captainTeams);
        setMemberTeams(response.data.memberTeams);
      }
    } catch (error) {
      console.error("加载队伍失败:", error);
      toast.error("加载队伍失败");
    } finally {
      setIsLoading(prev => ({ ...prev, teams: false }));
    }
  };
  
  // 加载匹配结果
  const loadMatches = async () => {
    try {
      setIsLoading(prev => ({ ...prev, matches: true }));
      const response = await communityApi.getUserMatches(currentUserId);
      //console.log(response.data);
      if (response.status === 'success' && response.data) {
        setMatchResults(response.data);
        if (response.data.length > 0 && !selectedUser) {
          setSelectedUser(response.data[0]);
        }
      }
    } catch (error) {
      console.error("加载匹配结果失败:", error);
      toast.error("加载匹配结果失败");
    } finally {
      setIsLoading(prev => ({ ...prev, matches: false }));
    }
  };
  
  // 关闭群聊模态框
  const closeChatModal = () => {
    setIsChatOpen(false);
    setCurrentChatTeamId(null);
    setNewMessage("");
  };
  
  // 发送消息
  const sendMessage = () => {
    if (!newMessage.trim() || !currentChatTeamId) return;
    
    const newMsg = {
      id: Date.now().toString(),
      senderId: 999,
      senderName: "我自己",
      content: newMessage,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    
    setChatMessages(prev => [...prev, newMsg]);
    setNewMessage("");
    
    // 模拟对方回复
    const team = teams.find(t => t.id === currentChatTeamId);
    if (team) {
      const otherMembers = team.members.filter(m => m.id !== 999);
      if (otherMembers.length > 0) {
        const randomMember = otherMembers[Math.floor(Math.random() * otherMembers.length)];
        
        setTimeout(() => {
          const replyMsg = {
            id: Date.now().toString(),
            senderId: randomMember.id,
            senderName: randomMember.name,
            content: "收到，我们稍后讨论一下具体行程吧！",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };
          setChatMessages(prev => [...prev, replyMsg]);
        }, 1500);
      }
    }
  };
  
  // 是否显示匹配结果状态
  const [showMatchResults, setShowMatchResults] = useState(true);
  
  // 加载状态
  const [isMatching, setIsMatching] = useState(false);
  
  // 处理用户资料变更
  const handleProfileChange = (field: keyof UserProfile, value: any) => {
    setUserProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  // 处理兴趣爱好变更
  const toggleHobby = (hobby: string) => {
    setUserProfile(prev => {
      const hobbies = prev.hobbies.includes(hobby)
        ? prev.hobbies.filter(h => h !== hobby)
        : [...prev.hobbies, hobby];
      
      return { ...prev, hobbies };
    });
  };
  
  // 创建新队伍
  const createTeam = async () => {
    if (!newTeamName.trim()) {
      toast.error("请输入队伍名称");
      return;
    }
    

    await communityApi.createTeam(newTeamName,userProfile.id);
    
    loadTeams();
    setNewTeamName("");
    toast.success(`成功创建队伍: ${newTeamName}`);
  };
  
  // 删除队伍
  const deleteTeam = async (teamId: number) => {
    await communityApi.deleteTeam(teamId,userProfile.id);

    loadTeams();//删除后重新加载队伍
    toast.success("队伍已删除");
  };
  
  // 邀请用户加入队伍
  const inviteToTeam = async (teamId: number) => {
    if (!selectedUser) return;
    
    await communityApi.addTeamMember(teamId,selectedUser.id);
    
    loadMatches();
    loadTeams();
    toast.success(`已邀请${selectedUser.name}加入队伍`);
  };
  
  // 队员离开队伍
  const leaveTeam = async (teamId: number) => {
    
    await communityApi.removeTeamMember(teamId,userProfile.id,userProfile.id);
    loadTeams();
    toast.success("成功离开队伍");
  };
  
  // 队长踢出成员
  const removeMember = async (teamId: number, memberId: number) => {
    await communityApi.removeTeamMember(teamId,memberId,userProfile.id);
    loadTeams();
    toast.success("已将成员踢出队伍");
  };
  
  // 开始匹配
  const handleStartMatching = () => {
    setIsMatching(true);

    //首先更新用户信息
    const aa = communityApi.updateUserProfile(currentUserId,userProfile);
    
    //更新匹配在获取匹配
    setTimeout(async ()=>{
      const results = await communityApi.findMatchesForUser(currentUserId);
      
      const response = await communityApi.getUserMatches(currentUserId);
      if (response.status === 'success' && response.data) {
        setMatchResults(response.data);
        if (response.data.length > 0 && !selectedUser) {
          setSelectedUser(response.data[0]);
        }
      }
      setShowMatchResults(true);
      setIsMatching(false);
    }, 1000);

    
    /*// 模拟匹配过程
    setTimeout(() => {
      const results = generateMockMatches();
      setMatchResults(results);
      setShowMatchResults(true);
      setIsMatching(false);
      
      // 自动选择第一个匹配结果
      if (results.length > 0) {
        setSelectedUser(results[0]);
      }
    }, 2000);*/
  };
  
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 顶部导航栏 */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* 品牌标识 */}
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                <Users className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                知旅 - 社区
              </span>
            </div>
            
            {/* 导航菜单 */}
            <nav className="hidden md:flex items-center space-x-6">
              <a href="/" className="text-gray-600 hover:text-blue-600 transition-colors">首页</a>
              <a href="/planning" className="text-gray-600 hover:text-blue-600 transition-colors">智能规划</a>
              <a href="/chat" className="text-gray-600 hover:text-blue-600 transition-colors">AI问答</a>
              <a href="/community" className="text-blue-600 font-medium">社区</a>
            </nav>
            
            {/* 移动端菜单按钮 */}
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* 主内容区 - 三栏布局 */}
      <div className="flex-1 container mx-auto px-4 py-6 flex flex-col lg:flex-row gap-6">
        {/* 左侧面板 - 用户信息和匹配结果 */}
        <div className="w-full lg:w-1/4 flex flex-col gap-6">
          {/* 用户信息编辑卡片 */}
          <Card className="shadow-sm">
            <CardHeader className="bg-gray-50">
              <CardTitle className="text-lg">个人资料</CardTitle>
              <CardDescription>完善信息以获得更精准的匹配</CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-4">
                  {/* 基本信息 */}
                  <div className="space-y-2">
                    <Label htmlFor="gender">性别</Label>
                    <select
                      id="gender"
                      value={userProfile.gender}
                      onChange={(e) => handleProfileChange('gender', e.target.value)}
                      className="w-full rounded-md border border-gray-300 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">选择性别</option>
                      <option value="男">男</option>
                      <option value="女">女</option>
                      <option value="其他">其他</option>
                    </select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="age">年龄</Label>
                    <Input
                      id="age"
                      type="number"
                      placeholder="输入年龄"
                      value={userProfile.age || ""}
                      onChange={(e) => handleProfileChange('age', parseInt(e.target.value))}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="mbti">MBTI类型</Label>
                    <select
                      id="mbti"
                      value={userProfile.mbti}
                      onChange={(e) => handleProfileChange('mbti', e.target.value)}
                      className="w-full rounded-md border border-gray-300 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">选择MBTI类型</option>
                      {mbtiTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>兴趣爱好</Label>
                    <div className="flex flex-wrap gap-2">
                      {hobbiesList.map(hobby => (
                        <Badge
                          key={hobby}
                          variant={userProfile.hobbies.includes(hobby) ? "default" : "outline"}
                          className="cursor-pointer"
                          onClick={() => toggleHobby(hobby)}
                        >
                          {hobby}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="destination">旅行目的地</Label>
                    <select
                      id="destination"
                      value={userProfile.travelDestination}
                      onChange={(e) => handleProfileChange('travelDestination', e.target.value)}
                      className="w-full rounded-md border border-gray-300 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">选择目的地</option>
                      {destinations.map(dest => (
                        <option key={dest} value={dest}>{dest}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="schedule">作息习惯</Label>
                    <select
                      id="schedule"
                      value={userProfile.schedule}
                      onChange={(e) => handleProfileChange('schedule', e.target.value)}
                      className="w-full rounded-md border border-gray-300 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">选择作息习惯</option>
                      {schedules.map(schedule => (
                        <option key={schedule} value={schedule}>{schedule}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="budget">预算范围</Label>
                    <select
                      id="budget"
                      value={userProfile.budget}
                      onChange={(e) => handleProfileChange('budget', e.target.value)}
                      className="w-full rounded-md border border-gray-300 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">选择预算范围</option>
                      {budgets.map(budget => (
                        <option key={budget} value={budget}>{budget}</option>
                      ))}
                    </select>
                  </div>
                  
                  <Button 
                    className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700"
                    onClick={handleStartMatching}
                    disabled={isMatching}
                  >
                    {isMatching ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        匹配中...
                      </>
                    ) : (
                      <>
                        开始匹配
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </>
                    )}
                  </Button>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
          
          {/* 匹配结果卡片 */}
          <Card className="shadow-sm flex-grow">
            <CardHeader className="bg-gray-50">
              <CardTitle className="text-lg flex items-center justify-between">
                <span>匹配结果</span>
                <Badge variant="outline">{matchResults.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {showMatchResults ? (
                <ScrollArea className="h-[400px]">
                  <div className="p-4 space-y-3">
                    {matchResults.length > 0 ? (
                      matchResults.map(user => (
                        <div 
                          key={user.id}
                          className={`p-3 rounded-lg cursor-pointer transition-all ${
                            selectedUser?.id === user.id 
                              ? 'bg-blue-50 border border-blue-200' 
                              : 'hover:bg-gray-50 border border-transparent'
                          }`}
                          onClick={() => setSelectedUser(user)}
                        >
                          <div className="flex items-center gap-3">
                            <Avatar className="w-10 h-10">
                              <AvatarImage src={user.avatar} alt={user.name} />
                              <AvatarFallback className="bg-gradient-to-r from-blue-500 to-indigo-500">
                                {user.name.charAt(0)}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1">
                              <div className="flex items-center gap-1">
                                <p className="font-medium text-sm">{user.name}, {user.age}</p>
                                {user.isVerified && (
                                  <i className="fa-solid fa-check-circle text-blue-500 text-xs"></i>
                                )}
                              </div>
                              <p className="text-xs text-gray-500">{user.travelDestination}</p>
                              <div className="flex items-center gap-1 mt-1">
                                <Badge variant="secondary" className="text-xs">
                                  {user.mbti}
                                </Badge>
                                <Badge className="text-xs bg-green-100 text-green-700">
                                  {user.matchingScore}% 匹配
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="flex flex-col items-center justify-center py-12 text-center">
                        <Users className="w-12 h-12 text-gray-300 mb-2" />
                        <h3 className="text-sm font-medium text-gray-900">暂无匹配结果</h3>
                        <p className="text-xs text-gray-500 mt-1">点击上方"开始匹配"按钮寻找旅行搭子</p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              ) : (
                <div className="flex flex-col items-center justify-center h-[400px] text-center p-6">
                  <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mb-4">
                    <Users className="w-8 h-8 text-blue-400" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">寻找旅行搭子</h3>
                  <p className="text-sm text-gray-500 mb-4 max-w-xs">
                    完善您的个人资料并点击"开始匹配"按钮，系统将为您推荐合适的旅行搭子
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        
        {/* 中间面板 - 用户详情 */}
        <div className="w-full lg:w-2/4">
          <Card className="shadow-sm h-full flex flex-col">
            {selectedUser ? (
              <>
                <CardHeader className="bg-gray-50 pb-2">
                  <CardTitle className="text-xl">用户详情</CardTitle>
                  <CardDescription>查看搭子详细信息并邀请加入队伍</CardDescription>
                </CardHeader>
                <CardContent className="flex-grow">
                  <ScrollArea className="h-[calc(100vh)] pr-4">
                    <div className="space-y-6">
                      {/* 用户基本信息 */}
                      <div className="flex flex-col items-center text-center">
                        <Avatar className="w-24 h-24 border-4 border-white shadow-md">
                          <AvatarImage src={selectedUser.avatar} alt={selectedUser.name} />
                          <AvatarFallback className="bg-gradient-to-r from-blue-500 to-indigo-500 text-2xl">
                            {selectedUser.name.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="mt-4">
                          <div className="flex items-center justify-center gap-1">
                            <h2 className="text-2xl font-bold">{selectedUser.name}</h2>
                            {selectedUser.isVerified && (
                              <i className="fa-solid fa-check-circle text-blue-500"></i>
                            )}
                          </div>
                          <p className="text-gray-500">{selectedUser.age}岁 · {selectedUser.gender}</p>
                          <div className="flex items-center justify-center gap-2 mt-2">
                            <Badge className="bg-blue-100 text-blue-700">{selectedUser.mbti}</Badge>
                            <Badge className="bg-green-100 text-green-700">{selectedUser.matchingScore}% 匹配</Badge>
                          </div>
                        </div>
                      </div>
                      
                      <Separator />
                      
                      {/* 旅行信息 */}
                      <div>
                        <h3 className="text-sm font-medium text-gray-500 mb-3">旅行信息</h3>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-gray-50 p-3 rounded-lg">
                            <p className="text-xs text-gray-500 mb-1">目的地</p>
                            <p className="font-medium flex items-center gap-1">
                              <MapPin className="w-4 h-4 text-blue-500" />
                              {selectedUser.travelDestination}
                            </p>
                          </div>
                          <div className="bg-gray-50 p-3 rounded-lg">
                            <p className="text-xs text-gray-500 mb-1">作息习惯</p>
                            <p className="font-medium flex items-center gap-1">
                              {selectedUser.schedule === "早睡早起" ? (
                                <Sun className="w-4 h-4 text-yellow-500" />
                              ) : selectedUser.schedule === "晚睡晚起" ? (
                                <Moon className="w-4 h-4 text-indigo-500" />
                              ) : (
                                <RefreshCw className="w-4 h-4 text-green-500" />
                              )}
                              {selectedUser.schedule}
                            </p>
                          </div>
                          <div className="bg-gray-50 p-3 rounded-lg">
                            <p className="text-xs text-gray-500 mb-1">预算范围</p>
                            <p className="font-medium flex items-center gap-1">
                              <Wallet className="w-4 h-4 text-purple-500" />
                              {selectedUser.budget}
                            </p>
                          </div>
                          <div className="bg-gray-50 p-3 rounded-lg">
                            <p className="text-xs text-gray-500 mb-1">兴趣爱好</p>
                            <div className="flex flex-wrap gap-1">
                              {selectedUser.hobbies.map(hobby => (
                                <Badge key={hobby} variant="secondary" className="text-xs">
                                  {hobby}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <Separator />
                      
                      {/* 个人简介 */}
                      <div>
                        <h3 className="text-sm font-medium text-gray-500 mb-2">个人简介</h3>
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <p className="text-gray-700">{selectedUser.bio}</p>
                        </div>
                      </div>
                      
                      <Separator />
                      
                      {/* 邀请加入队伍 */}
                      <div>
                        <h3 className="text-sm font-medium text-gray-500 mb-3">邀请加入队伍</h3>
                        {teams.length > 0 ? (
                          <div className="space-y-2">
                            {teams.map(team => (
                              <div key={team.id} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                                <div>
                                  <p className="font-medium">{team.name}</p>
                                  <p className="text-xs text-gray-500">{team.members.length}名成员</p>
                                </div>
                                <Button 
                                  size="sm"
                                  onClick={() => inviteToTeam(team.id)}
                                  disabled={team.members.some(m => m.id === selectedUser!.id)}
                                >
                                  {team.members.some(m => m.id === selectedUser!.id) 
                                    ? "已在队伍中" 
                                    : "邀请加入"
                                  }
                                </Button>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="bg-gray-50 p-6 rounded-lg text-center">
                            <p className="text-gray-500 mb-3">暂无队伍可邀请</p>
                            <Button size="sm" onClick={() => {
                              // 滚动到右侧队伍管理面板
                              document.querySelector('.team-management-panel')?.scrollIntoView({ behavior: 'smooth' });
                            }}>
                              创建队伍
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  </ScrollArea>
                </CardContent>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full py-12 text-center">
                <Users className="w-16 h-16 text-gray-300 mb-4" />
                <h3 className="text-xl font-medium mb-2">选择一位搭子查看详情</h3>
                <p className="text-gray-500 max-w-md">
                  从左侧匹配结果中选择一位旅行搭子，查看详细信息并邀请加入您的队伍
                </p>
              </div>
            )}
          </Card>
        </div>
        
        {/* 右侧面板 - 队伍管理 */}
        <div className="w-full lg:w-1/4">
          <Card className="shadow-sm team-management-panel">
            <CardHeader className="bg-gray-50">
              <CardTitle className="text-lg">队伍管理</CardTitle>
              <CardDescription>创建和管理您的旅行队伍</CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
               <div className="space-y-6">
                   {/* 创建队伍 */}
                   <div>
                     <div className="flex gap-2">
                       <Input
                         placeholder="输入队伍名称"
                         value={newTeamName}
                         onChange={(e) => setNewTeamName(e.target.value)}
                       />
                       <Button onClick={createTeam}>
                         <PlusCircle className="w-4 h-4" />
                       </Button>
                     </div>
                   </div>
                   
                   {/* 我创建的队伍 - 独立滚动区域 */}
                   <div className="mb-6">
                     <h3 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
                       <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                       我创建的队伍
                     </h3>
                     <ScrollArea className="h-[400px] pr-4">
                       <div className="space-y-4">
                         {captainTeams.length > 0 ? (
                           captainTeams.map(team => (
                             <div key={team.id} className="border rounded-lg overflow-hidden">
                               <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
                                 <div>
                                   <h3 className="font-medium">{team.name}</h3>
                                   <p className="text-xs text-gray-500">{team.members.length}名成员</p>
                                 </div>
                                <div className="flex gap-1">
                                  <Button 
                                    variant="ghost" 
                                    size="icon" 
                                    className="h-8 w-8 text-blue-500 hover:text-blue-700 hover:bg-blue-50"
                                    onClick={() => openChatModal(team.id)}
                                  >
                                    <MessageSquare className="w-4 h-4" />
                                  </Button>
                                  <Button 
                                    variant="ghost" 
                                    size="icon" 
                                    className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                                    onClick={() => deleteTeam(team.id)}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                               </div>
                               <div className="p-3 space-y-2 max-h-48 overflow-y-auto">
                                 {team.members.map(member => (
                                   <div key={member.id} className="flex items-center gap-2">
                                     <Avatar className="w-8 h-8">
                                       <AvatarImage src={member.avatar} alt={member.name} />
                                       <AvatarFallback className="bg-gradient-to-r from-blue-500 to-indigo-500">
                                         {member.name.charAt(0)}
                                       </AvatarFallback>
                                     </Avatar>
                                     <div className="flex-1 min-w-0">
                                       <p className="text-sm font-medium truncate">{member.name}</p>
                                       <div className="flex items-center gap-1">
                                         <Badge variant="secondary" className="text-xs">
                                           {member.mbti}
                                         </Badge>
                                         {member.id === team.captainId && (
                                           <Badge className="bg-yellow-100 text-yellow-700 text-xs">队长</Badge>
                                         )}
                                       </div>
                                     </div>
                                     {/* 队长可以踢出其他成员 */}
                                     {member.id !== team.captainId && (
                                       <Button 
                                         variant="ghost" 
                                         size="icon" 
                                         className="h-6 w-6 text-red-500 hover:text-red-700 hover:bg-red-50"
                                         onClick={() => removeMember(team.id, member.id)}
                                       >
                                         <Trash2 className="w-3 h-3" />
                                       </Button>
                                     )}
                                   </div>
                                 ))}
                               </div>
                             </div>
                           ))
                         ) : (
                           <div className="bg-gray-50 p-4 rounded-lg text-center">
                             <p className="text-gray-500 text-sm">暂无创建的队伍</p>
                           </div>
                         )}
                       </div>
                     </ScrollArea>
                   </div>
                   
                   {/* 我加入的队伍 - 独立滚动区域 */}
                   <div>
                     <h3 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
                       <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                       我加入的队伍
                     </h3>
                     <ScrollArea className="h-[400px] pr-4">
                       <div className="space-y-4">
                         {memberTeams.length > 0 ? (
                           memberTeams.map(team => (
                             <div key={team.id} className="border rounded-lg overflow-hidden">
                               <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
                                 <div>
                                   <h3 className="font-medium">{team.name}</h3>
                                   <p className="text-xs text-gray-500">{team.members.length}名成员</p>
                                 </div>
                                <div className="flex gap-1">
                                  <Button 
                                    variant="ghost" 
                                    size="icon" 
                                    className="h-8 w-8 text-blue-500 hover:text-blue-700 hover:bg-blue-50"
                                    onClick={() => openChatModal(team.id)}
                                  >
                                    <MessageSquare className="w-4 h-4" />
                                  </Button>
                                </div>
                               </div>
                               <div className="p-3 space-y-2 max-h-48 overflow-y-auto">
                                  {team.members.map(member => (
                                    <div key={member.id} className="flex items-center gap-2">
                                      <Avatar className="w-8 h-8">
                                        <AvatarImage src={member.avatar} alt={member.name} />
                                        <AvatarFallback className="bg-gradient-to-r from-blue-500 to-indigo-500">
                                          {member.name.charAt(0)}
                                        </AvatarFallback>
                                      </Avatar>
                                      <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">{member.name}</p>
                                        <div className="flex items-center gap-1">
                                          <Badge variant="secondary" className="text-xs">
                                            {member.mbti}
                                          </Badge>
                                          {member.id === team.captainId && (
                                            <Badge className="bg-yellow-100 text-yellow-700 text-xs">队长</Badge>
                                          )}
                                        </div>
                                      </div>
                                      {/* 自己可以离开队伍 */}
                                      {member.id === 999 && (
                                        <Button 
                                          variant="ghost" 
                                          size="icon" 
                                          className="h-6 w-6 text-red-500 hover:text-red-700 hover:bg-red-50"
                                          onClick={() => leaveTeam(team.id)}
                                        >
                                          <XCircle className="w-3 h-3" />
                                        </Button>
                                      )}
                                    </div>
                                  ))}
                               </div>
                             </div>
                           ))
                         ) : (
                           <div className="bg-gray-50 p-4 rounded-lg text-center">
                             <p className="text-gray-500 text-sm">暂无加入的队伍</p>
                           </div>
                         )}
                       </div>
                     </ScrollArea>
                   </div>
                 </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* 群聊模态框 */}
      {isChatOpen && currentChatTeamId && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md max-h-[90vh] flex flex-col">
            <CardHeader className="bg-gray-50 py-3 px-4 border-b">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">
                  {teams.find(t => t.id === currentChatTeamId)?.name || "群聊"}
                </CardTitle>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8"
                  onClick={closeChatModal}
                >
                  <XCircle className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMessages.map(msg => (
                <div key={msg.id} className={`flex gap-2 ${msg.senderId === 999 ? 'justify-end' : 'justify-start'}`}>
                  {msg.senderId !== 999 && (
                    <Avatar className="w-8 h-8 mt-1">
                      <AvatarFallback className="bg-gradient-to-r from-blue-500 to-indigo-500">
                        {msg.senderName.charAt(0)}
                      </AvatarFallback>
                    </Avatar>
                  )}
                  <div className={`max-w-[70%] ${msg.senderId === 999 ? 'items-end' : 'items-start'} flex flex-col`}>
                    {msg.senderId !== 999 && (
                      <span className="text-xs text-gray-500 mb-1">{msg.senderName}</span>
                    )}
                    <div className={`rounded-lg p-3 ${
                      msg.senderId === 999 
                        ? 'bg-blue-500 text-white rounded-br-none' 
                        : 'bg-gray-100 text-gray-900 rounded-bl-none'
                    }`}>
                      <p className="text-sm">{msg.content}</p>
                    </div>
                    <span className={`text-xs mt-1 ${msg.senderId === 999 ? 'text-blue-200' : 'text-gray-400'}`}>
                      {msg.timestamp}
                    </span>
                  </div>
                </div>
              ))}
            </CardContent>
            <div className="border-t p-4">
              <div className="flex gap-2">
                <Input
                  placeholder="输入消息..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                  className="flex-1"
                />
                <Button onClick={sendMessage} disabled={!newMessage.trim()}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}