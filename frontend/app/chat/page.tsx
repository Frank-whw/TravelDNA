/**
 * AI聊天页面组件 - 旅游智能问答界面
 * 
 * 功能概述：
 * - 提供AI驱动的旅游问答服务
 * - 支持实时消息对话和历史记录
 * - 快速问题模板和侧边栏功能导航
 * - 响应式聊天界面适配移动端和桌面端
 * 
 * 设计思路：
 * - 经典的聊天应用布局（侧边栏+主聊天区）
 * - 区分用户消息和AI回复的视觉样式
 * - 提供快速问题入口降低用户使用门槛
 * - 展示AI能力和在线状态增强用户信任
 * 
 * 技术架构：
 * - React客户端组件with hooks状态管理
 * - 消息数据结构化管理（id、类型、内容、时间）
 * - 模拟AI回复机制（实际项目中对接RAG后端）
 * - Lucide图标和Shadcn/ui组件
 * 
 * 交互流程：
 * 1. 用户输入消息或点击快速问题
 * 2. 消息添加到消息列表并清空输入框
 * 3. 模拟AI思考延迟后显示回复
 * 4. 支持Enter键快捷发送
 * 
 * 待扩展功能：
 * - 接入真实的RAG AI后端API
 * - 消息持久化和历史对话管理
 * - 富文本消息（图片、链接、地图等）
 * - 语音输入和语音播放
 */

"use client"

import { useState, useRef, useEffect } from "react"
import { Send, MapPin, MessageCircle, Sparkles, Clock, Star, Navigation, Bot, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { agentApi, formatChatMessage, formatTravelPlan, type ChatMessage, type TravelPlan } from "@/lib/agentApi"

/**
 * 聊天页面主组件 - AI旅游助手对话界面
 * 
 * 状态管理：
 * - message: 当前输入框的消息内容
 * - messages: 对话历史记录数组
 * 
 * 组件结构：
 * 1. Header - 顶部导航（品牌、导航菜单、历史对话）
 * 2. Sidebar - 左侧功能面板（AI信息、快速问题、功能特色）
 * 3. Chat Area - 主聊天区域（消息列表、输入框、快速问题）
 * 
 * @returns {JSX.Element} 完整的聊天页面布局
 */
export default function ChatPage() {
  /**
   * 当前输入消息状态 - 用户正在输入的消息内容
   * @type {string} 输入框绑定的消息文本
   */
  const [message, setMessage] = useState("")
  
  /**
   * 消息历史状态 - 用户和AI的对话记录
   * @type {Array<ChatMessage>} 消息对象数组，使用从agentApi导入的ChatMessage类型
   */
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  /**
   * 发送消息处理函数 - 处理用户消息发送和AI回复
   * 
   * 功能流程：
   * 1. 验证消息内容非空
   * 2. 创建用户消息对象并添加到消息列表
   * 3. 清空输入框
   * 4. 调用真实的AI API
   * 5. 处理AI回复和错误
   * 
   * 性能考虑：
   * - 使用函数式更新避免状态竞争
   * - 真实API调用替换模拟延迟
   */
  const handleSendMessage = async () => {
    // 验证消息内容，空消息不发送
    if (!message.trim() || isLoading) return

    const userMessage = formatChatMessage(message, 'user')
    setMessages(prev => [...prev, userMessage])
    setMessage("")
    setIsLoading(true)
    setError(null)

    try {
      // 检查是否是旅游规划请求
      const isPlanningRequest = message.includes('规划') || message.includes('计划') || 
                               message.includes('路线') || message.includes('行程')
      
      if (isPlanningRequest) {
        // 尝试解析目的地信息
        const destinations = extractDestinations(message)
        const origin = extractOrigin(message) || '上海'
        
        if (destinations.length > 0) {
          // 创建旅游计划
          const plan = await agentApi.createTravelPlan(origin, destinations)
          const planMessage = formatChatMessage(
            formatTravelPlan(plan),
            'ai',
            'plan'
          )
          setMessages(prev => [...prev, planMessage])
        } else {
          // 普通聊天
          const response = await agentApi.chat(message)
          const aiMessage = formatChatMessage(response.response, 'ai')
          setMessages(prev => [...prev, aiMessage])
          
          // 如果有建议，添加建议消息
          if (response.suggestions && response.suggestions.length > 0) {
            const suggestionsMessage = formatChatMessage(
              `💡 **相关建议**:\n${response.suggestions.map((s, i) => `${i + 1}. ${s}`).join('\n')}`,
              'ai',
              'suggestions'
            )
            setMessages(prev => [...prev, suggestionsMessage])
          }
        }
      } else {
        // 普通聊天
        const response = await agentApi.chat(message)
        const aiMessage = formatChatMessage(response.response, 'ai')
        setMessages(prev => [...prev, aiMessage])
        
        // 如果有建议，添加建议消息
        if (response.suggestions && response.suggestions.length > 0) {
          const suggestionsMessage = formatChatMessage(
            `💡 **相关建议**:\n${response.suggestions.map((s, i) => `${i + 1}. ${s}`).join('\n')}`,
            'ai',
            'suggestions'
          )
          setMessages(prev => [...prev, suggestionsMessage])
        }
      }
    } catch (err) {
      console.error('Chat error:', err)
      const errorMessage = err instanceof Error ? err.message : '发生未知错误'
      setError(errorMessage)
      
      const errorResponse = formatChatMessage(
        `抱歉，我遇到了一些问题：${errorMessage}。请稍后再试，或者检查网络连接。`,
        'ai'
      )
      setMessages(prev => [...prev, errorResponse])
    } finally {
      setIsLoading(false)
    }
  }

  // 辅助函数：从用户输入中提取目的地
  const extractDestinations = (input: string): string[] => {
    const destinations: string[] = []
    const commonDestinations = ['外滩', '东方明珠', '豫园', '南京路步行街', '人民广场', '田子坊', '新天地', '朱家角']
    
    commonDestinations.forEach(dest => {
      if (input.includes(dest)) {
        destinations.push(dest)
      }
    })
    
    return destinations
  }

  // 辅助函数：从用户输入中提取出发地
  const extractOrigin = (input: string): string | null => {
    const originKeywords = ['从', '出发', '起点']
    const commonOrigins = ['上海', '北京', '广州', '深圳', '杭州', '南京']
    
    for (const origin of commonOrigins) {
      if (input.includes(origin)) {
        return origin
      }
    }
    
    return null
  }

  /**
   * 快速问题模板 - 降低用户使用门槛的预设问题
   * @type {string[]} 常见旅游问题列表
   */
  const quickQuestions = [
    "北京三日游推荐路线",
    "上海必吃美食有哪些",
    "西湖周边住宿推荐",
    "成都到九寨沟怎么去",
    "三亚最佳旅游季节",
    "青岛海边景点推荐",
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header - 顶部导航栏 */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* 品牌标识 */}
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                <MapPin className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                知旅
              </span>
            </div>
            
            {/* 导航菜单 - 突出当前页面 */}
            <nav className="hidden md:flex items-center space-x-6">
              <a href="/" className="text-gray-600 hover:text-blue-600 transition-colors">
                首页
              </a>
              <a href="/planning" className="text-gray-600 hover:text-blue-600 transition-colors">
                智能规划
              </a>
              <a href="/chat" className="text-blue-600 font-medium">
                AI问答
              </a>
              <a href="/community" className="text-gray-600 hover:text-blue-600 transition-colors">
                社区
              </a>
            </nav>
            
            {/* 历史对话入口 */}
            <Button variant="outline">历史对话</Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Sidebar - 左侧功能面板 */}
          <div className="lg:col-span-1">
            <div className="space-y-6">
              {/* AI Assistant Info - AI助手信息卡片 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-500" />
                    AI助手
                  </CardTitle>
                  <CardDescription>基于RAG技术的智能旅游问答</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* 在线状态指示器 */}
                    <div className="flex items-center gap-2 text-sm">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>在线服务</span>
                    </div>
                    {/* AI能力描述 */}
                    <div className="text-sm text-gray-600">融合多源旅游数据，提供准确、实时的旅行建议</div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Questions - 快速问题模板 */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">热门问题</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {quickQuestions.map((question, index) => (
                      <Button
                        key={index}
                        variant="ghost"
                        className="w-full justify-start text-left h-auto p-3 text-sm"
                        onClick={() => setMessage(question)}
                      >
                        {question}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Features - 功能特色展示 */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">功能特色</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* 景点推荐 */}
                    <div className="flex items-center gap-2 text-sm">
                      <Star className="w-4 h-4 text-yellow-500" />
                      <span>景点推荐</span>
                    </div>
                    {/* 路线规划 */}
                    <div className="flex items-center gap-2 text-sm">
                      <Navigation className="w-4 h-4 text-blue-500" />
                      <span>路线规划</span>
                    </div>
                    {/* 实时信息 */}
                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="w-4 h-4 text-green-500" />
                      <span>实时信息</span>
                    </div>
                    {/* 24/7在线 */}
                    <div className="flex items-center gap-2 text-sm">
                      <MessageCircle className="w-4 h-4 text-purple-500" />
                      <span>24/7在线</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Chat Area - 主聊天区域 */}
          <div className="lg:col-span-3">
            <Card className="h-[600px] flex flex-col">
              {/* 聊天区域头部 */}
              <CardHeader className="border-b">
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="w-5 h-5 text-blue-500" />
                  AI旅游助手
                </CardTitle>
                <CardDescription>有任何旅行问题都可以问我，我会基于最新的旅游数据为您解答</CardDescription>
              </CardHeader>

              {/* Messages - 消息展示区域 */}
              <CardContent className="flex-1 overflow-y-auto p-4">
                {error && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-600 text-sm">⚠️ {error}</p>
                  </div>
                )}
                
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>开始与AI助手对话吧！</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((msg) => (
                      <div key={msg.id} className={`flex gap-3 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                        <div className={`flex items-start space-x-3 max-w-[80%] ${
                          msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                        }`}>
                          {/* 头像 */}
                          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                            msg.sender === 'user' 
                              ? 'bg-blue-500 text-white' 
                              : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                          }`}>
                            {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                          </div>
                          
                          {/* 消息内容 */}
                          <div
                            className={`p-4 rounded-lg ${
                              msg.sender === 'user'
                                ? 'bg-blue-500 text-white'
                                : msg.type === 'plan'
                                ? 'bg-gradient-to-r from-green-50 to-blue-50 text-gray-800 border border-green-200'
                                : msg.type === 'suggestions'
                                ? 'bg-gradient-to-r from-yellow-50 to-orange-50 text-gray-800 border border-yellow-200'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            <div className="whitespace-pre-wrap">
                              {msg.content.split('\n').map((line, index) => {
                                // 处理Markdown样式的粗体文本
                                if (line.includes('**')) {
                                  const parts = line.split('**')
                                  return (
                                    <p key={index} className="mb-1">
                                      {parts.map((part, partIndex) => 
                                        partIndex % 2 === 1 ? 
                                          <strong key={partIndex}>{part}</strong> : 
                                          part
                                      )}
                                    </p>
                                  )
                                }
                                return <p key={index} className="mb-1">{line}</p>
                              })}
                            </div>
                            <p className="text-xs mt-2 opacity-70">
                              {new Date(msg.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    {/* 加载指示器 */}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="flex items-start space-x-3 max-w-[80%]">
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white flex items-center justify-center">
                            <Bot size={16} />
                          </div>
                          <div className="bg-gray-100 text-gray-800 p-4 rounded-lg">
                            <div className="flex items-center space-x-2">
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500"></div>
                              <span className="text-sm">AI正在思考中...</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* 滚动到底部的引用 */}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </CardContent>

              {/* Input Area - 消息输入区域 */}
              <div className="border-t p-4">
                <div className="flex gap-2">
                  {/* 消息输入框 - 支持Enter键发送 */}
                  <Input
                    placeholder="输入您的旅行问题..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                    className="flex-1"
                  />
                  {/* 发送按钮 - 空消息时禁用 */}
                  <Button onClick={handleSendMessage} disabled={!message.trim() || isLoading}>
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
                
                {/* 快速问题标签 - 提供便捷的问题入口 */}
                <div className="flex flex-wrap gap-2 mt-3">
                  {quickQuestions.slice(0, 3).map((question, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="cursor-pointer hover:bg-blue-50"
                      onClick={() => setMessage(question)}
                    >
                      {question}
                    </Badge>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
