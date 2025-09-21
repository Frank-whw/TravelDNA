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

import { useState, useEffect, useRef } from "react"
import { Send, MapPin, MessageCircle, Sparkles, Clock, Star, Navigation, Brain, Loader2, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import agentApi from "@/lib/agentApi"

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
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "assistant",
      content: "您好！我是TravelDNA智能旅游Agent，可以为您提供个性化的旅游建议和实时天气信息。请告诉我您想去哪里旅游？",
      timestamp: "刚刚",
    },
  ])
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const wsRef = useRef(null)
  const messagesEndRef = useRef(null)
  const userId = "user_" + Math.random().toString(36).substr(2, 9)

  // WebSocket连接管理
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(`ws://localhost:8000/ws/${userId}`)
        wsRef.current = ws

        ws.onopen = () => {
          console.log('WebSocket连接已建立')
          setIsConnected(true)
        }

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data)
          console.log('收到消息:', data)
          
          // 添加Agent响应到消息列表
          const newMessage = {
            id: Date.now(),
            type: data.type || "assistant",
            content: data.content,
            timestamp: "刚刚",
            data: data.data || null
          }
          
          setMessages(prev => [...prev, newMessage])
          
          // 如果是最后一条响应，停止加载状态
          if (data.type === "response") {
            setIsLoading(false)
          }
        }

        ws.onclose = () => {
          console.log('WebSocket连接已关闭')
          setIsConnected(false)
          // 3秒后尝试重连
          setTimeout(connectWebSocket, 3000)
        }

        ws.onerror = (error) => {
          console.error('WebSocket错误:', error)
          setIsConnected(false)
        }
      } catch (error) {
        console.error('WebSocket连接失败:', error)
        setIsConnected(false)
      }
    }

    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return

    // 添加用户消息
    const userMessage = {
      id: Date.now(),
      type: "user" as const,
      content: message,
      timestamp: "刚刚",
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    const textToSend = message
    setMessage("")

    try {
      // 优先通过WebSocket发送
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          message: textToSend,
          user_id: userId
        }))
        // 由后端推送消息来结束loading
        return
      }

      // WebSocket不可用时，回退至HTTP接口
      const data = await agentApi.chat(textToSend)
      const assistantMsg = {
        id: Date.now() + 1,
        type: (data.type as any) || "response",
        content: data.message || "",
        timestamp: data.timestamp || "刚刚",
        data: { suggestions: data.suggestions }
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err: any) {
      const errorMsg = {
        id: Date.now() + 2,
        type: "response" as const,
        content: `抱歉，服务暂时不可用。错误信息：${err?.message || '未知错误'}`,
        timestamp: "刚刚",
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const quickQuestions = [
    "我想去北京旅游",
    "上海的天气怎么样",
    "推荐杭州的景点",
    "成都有什么好玩的",
    "三亚适合什么时候去",
    "青岛的海边怎么样",
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
                    <Brain className="w-5 h-5 text-purple-500" />
                    TravelDNA Agent
                  </CardTitle>
                  <CardDescription>智能旅游助手，实时天气 + 个性化建议</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* 连接状态指示器 */}
                    <div className="flex items-center gap-2 text-sm">
                      <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      <span>{isConnected ? '已连接' : '连接中...'}</span>
                    </div>
                    {/* Agent状态 */}
                    {isLoading && (
                      <div className="flex items-center gap-2 text-sm text-blue-600">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>Agent思考中...</span>
                      </div>
                    )}
                    {/* AI能力描述 */}
                    <div className="text-sm text-gray-600">集成实时天气API，提供基于天气的旅游建议</div>
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
                  TravelDNA智能Agent
                  {isLoading && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
                </CardTitle>
                <CardDescription>告诉我您想去的地方，我会为您获取天气信息并提供个性化旅游建议</CardDescription>
              </CardHeader>

              {/* Messages - 消息展示区域 */}
              <CardContent className="flex-1 overflow-y-auto p-4">
                <div className="space-y-4">
                  {messages.map((msg) => (
                    <div key={msg.id} className={`flex gap-3 ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
                      {/* Agent头像 - 仅在非用户消息时显示 */}
                      {msg.type !== "user" && (
                        <Avatar className="w-8 h-8">
                          <AvatarImage src="/placeholder.svg?height=32&width=32" />
                          <AvatarFallback className={`text-white text-xs ${
                            msg.type === "thinking" ? "bg-purple-500" :
                            msg.type === "action" ? "bg-blue-500" :
                            "bg-gradient-to-r from-blue-500 to-green-500"
                          }`}>
                            {msg.type === "thinking" ? <Brain className="w-4 h-4" /> :
                             msg.type === "action" ? <Loader2 className="w-4 h-4" /> :
                             "AI"}
                          </AvatarFallback>
                        </Avatar>
                      )}

                      {/* 消息气泡 - 根据消息类型应用不同样式 */}
                      <div
                        className={`max-w-[70%] rounded-lg p-3 ${
                          msg.type === "user" ? "bg-blue-500 text-white" :
                          msg.type === "thinking" ? "bg-purple-50 text-purple-900 border border-purple-200" :
                          msg.type === "action" ? "bg-blue-50 text-blue-900 border border-blue-200" :
                          "bg-gray-100 text-gray-900"
                        }`}
                      >
                        {/* 消息类型标识 */}
                        {msg.type === "thinking" && (
                          <div className="flex items-center gap-1 text-xs text-purple-600 mb-1">
                            <Brain className="w-3 h-3" />
                            <span>思考中</span>
                          </div>
                        )}
                        {msg.type === "action" && (
                          <div className="flex items-center gap-1 text-xs text-blue-600 mb-1">
                            <Loader2 className="w-3 h-3 animate-spin" />
                            <span>执行中</span>
                          </div>
                        )}
                        {msg.type === "response" && (
                          <div className="flex items-center gap-1 text-xs text-green-600 mb-1">
                            <CheckCircle className="w-3 h-3" />
                            <span>完成</span>
                          </div>
                        )}
                        
                        {/* 消息内容 */}
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                        
                        {/* 天气数据展示 */}
                        {msg.data && msg.data.weather && msg.data.weather.results && msg.data.weather.results.length > 0 && (
                          <div className="mt-2 p-2 bg-white rounded border">
                            <div className="text-xs text-gray-500 mb-1">天气数据</div>
                            <div className="text-sm">
                              📍 {msg.data.weather.results[0].location.name}<br/>
                              🌡️ {msg.data.weather.results[0].now.temperature}°C<br/>
                              ☁️ {msg.data.weather.results[0].now.text}
                            </div>
                          </div>
                        )}
                        
                        {/* 时间戳 */}
                        <p className={`text-xs mt-1 ${
                          msg.type === "user" ? "text-blue-100" :
                          msg.type === "thinking" ? "text-purple-400" :
                          msg.type === "action" ? "text-blue-400" :
                          "text-gray-500"
                        }`}>
                          {msg.timestamp}
                        </p>
                      </div>

                      {/* 用户头像 - 仅在用户消息时显示 */}
                      {msg.type === "user" && (
                        <Avatar className="w-8 h-8">
                          <AvatarImage src="/placeholder.svg?height=32&width=32" />
                          <AvatarFallback className="bg-gray-500 text-white text-xs">我</AvatarFallback>
                        </Avatar>
                      )}
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
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
                  <Button onClick={handleSendMessage} disabled={!message.trim()}>
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
