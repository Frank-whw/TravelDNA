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

import { useState } from "react"
import { Send, MapPin, MessageCircle, Sparkles, Clock, Star, Navigation } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

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
   * @type {Array<Object>} 消息对象数组，每个消息包含：
   *   - id: 唯一标识符
   *   - type: 消息类型（'user' | 'assistant'）
   *   - content: 消息内容文本
   *   - timestamp: 发送时间戳
   */
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "assistant",
      content:
        "您好！我是知旅AI助手，可以为您解答任何旅行相关的问题。比如景点推荐、交通路线、美食攻略等。请问有什么可以帮助您的吗？",
      timestamp: "刚刚",
    },
  ])

  /**
   * 发送消息处理函数 - 处理用户消息发送和AI回复
   * 
   * 功能流程：
   * 1. 验证消息内容非空
   * 2. 创建用户消息对象并添加到消息列表
   * 3. 清空输入框
   * 4. 模拟AI处理延迟
   * 5. 生成AI回复消息
   * 
   * 性能考虑：
   * - 使用函数式更新避免状态竞争
   * - setTimeout模拟网络延迟，实际使用时替换为API调用
   */
  const handleSendMessage = () => {
    // 验证消息内容，空消息不发送
    if (!message.trim()) return

    // 创建新的用户消息对象
    const newMessage = {
      id: messages.length + 1,
      type: "user",
      content: message,
      timestamp: "刚刚",
    }

    // 更新消息列表，添加用户消息
    setMessages([...messages, newMessage])
    // 清空输入框
    setMessage("")

    // 模拟AI回复延迟（实际项目中替换为API调用）
    setTimeout(() => {
      const aiResponse = {
        id: messages.length + 2,
        type: "assistant",
        content: "我正在为您查询相关信息，请稍等...",
        timestamp: "刚刚",
      }
      // 使用函数式更新确保状态正确
      setMessages((prev) => [...prev, aiResponse])
    }, 1000)
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
                <div className="space-y-4">
                  {messages.map((msg) => (
                    <div key={msg.id} className={`flex gap-3 ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
                      {/* AI头像 - 仅在助手消息时显示 */}
                      {msg.type === "assistant" && (
                        <Avatar className="w-8 h-8">
                          <AvatarImage src="/placeholder.svg?height=32&width=32" />
                          <AvatarFallback className="bg-gradient-to-r from-blue-500 to-green-500 text-white text-xs">
                            AI
                          </AvatarFallback>
                        </Avatar>
                      )}

                      {/* 消息气泡 - 根据消息类型应用不同样式 */}
                      <div
                        className={`max-w-[70%] rounded-lg p-3 ${
                          msg.type === "user" ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-900"
                        }`}
                      >
                        {/* 消息内容 */}
                        <p className="text-sm">{msg.content}</p>
                        {/* 时间戳 */}
                        <p className={`text-xs mt-1 ${msg.type === "user" ? "text-blue-100" : "text-gray-500"}`}>
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
