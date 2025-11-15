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
import { useRouter } from "next/navigation"
import { Send, MapPin, MessageCircle, Sparkles, Clock, Star, Navigation, Brain, Loader2, CheckCircle, Calendar } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import agentApi from "@/lib/agentApi"
import FloatingNodes from "@/components/FloatingNodes"
import PlanPreviewCard from "@/components/PlanPreviewCard"

// 类型定义
interface ThoughtProcess {
  step: number;
  thought: string;
  keywords: string[];
  reasoning: string;
  icon: string;
}

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
  const router = useRouter()
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<Array<{
    id: number;
    type: "user" | "assistant" | "thinking" | "action" | "response";
    content: string;
    timestamp: string;
    data?: {
      suggestions?: string[];
      thoughts?: ThoughtProcess[];
      extracted_info?: any;
      weather?: any;
      raw?: any;
    };
  }>>([
    {
      id: 1,
      type: "assistant",
      content: "你好！我是「知小旅」，你的智能旅游规划助手～\n\n我可以为你提供个性化的旅游建议和实时天气信息。你可以用文字描述，也可以用标签（如 #3天2晚 #2大1小 #预算1万）来快速表达需求。\n\n请告诉我你想去哪里旅游？",
      timestamp: "刚刚",
    },
  ])
  const [isConnected, setIsConnected] = useState(true) // 改为默认连接状态
  const [isLoading, setIsLoading] = useState(false)
  const [selectedTags, setSelectedTags] = useState<string[]>([])  // 选中的标签
  const [showTagInput, setShowTagInput] = useState(false)  // 是否显示标签输入
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const userId = "user_" + Math.random().toString(36).substr(2, 9)
  
  // 标签选项
  const tagOptions = {
    "基础标签": ["3天2晚", "2大1小", "预算1万", "上海", "5天4晚", "1大1小", "预算5千"],
    "偏好标签": ["亲子游", "不赶时间", "必吃本帮菜", "避开人群", "浪漫", "美食", "购物", "文化"],
    "特殊标签": ["带65岁老人", "儿童推车随行", "雨天备选", "轮椅", "无障碍"]
  }

  // 移除 WebSocket 连接，改为检查 API 连接状态
  useEffect(() => {
    const checkApiConnection = async () => {
      try {
        // 检查 Agent API 连接状态
        const response = await fetch('http://localhost:5001/api/v1/health')
        if (response.ok) {
          setIsConnected(true)
        } else {
          setIsConnected(false)
        }
      } catch (error) {
        console.warn('Agent API 连接检查失败，将使用离线模式:', error)
        setIsConnected(false)
      }
    }

    checkApiConnection()
    
    // 每30秒检查一次连接状态
    const interval = setInterval(checkApiConnection, 30000)
    
    return () => clearInterval(interval)
  }, [])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return

    // 合并消息和标签
    const fullMessage = message
    const tagsToSend = selectedTags.length > 0 ? selectedTags : undefined

    // 添加用户消息
    const userMessage = {
      id: Date.now(),
      type: "user" as const,
      content: fullMessage + (tagsToSend ? ` ${tagsToSend.map(t => `#${t}`).join(' ')}` : ''),
      timestamp: "刚刚",
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    const textToSend = fullMessage
    setMessage("")
    setSelectedTags([])  // 清空标签

    try {
      // 直接使用 HTTP API，传递标签
      const data = await agentApi.chat(textToSend, undefined, tagsToSend)
      
      // 处理响应数据
          const assistantMsg = {
            id: Date.now() + 1,
        type: (data.status === "thinking" ? "thinking" : "assistant") as const,
        content: data.message || (data.status === "thinking" ? "正在分析你的需求..." : "抱歉，我暂时无法处理您的请求。"),
            timestamp: data.timestamp || new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
            data: { 
              suggestions: data.suggestions || [],
              thoughts: data.thoughts || [],  // 添加思考过程
              extracted_info: data.extracted_info || {},  // 添加提取的信息
          status: data.status || '',  // 添加状态
              raw: data // 保留原始数据以便调试
            }
          }
      
      console.log('收到Agent回复:', assistantMsg)
      setMessages(prev => [...prev, assistantMsg])
      
      // 如果是思考阶段，继续等待最终回复
      if (data.status === "thinking") {
        // 等待一段时间后再次请求获取最终回复
        setTimeout(async () => {
          try {
            const finalData = await agentApi.chat(textToSend, undefined, tagsToSend)
            const finalMsg = {
              id: Date.now() + 2,
              type: "assistant" as const,
              content: finalData.message || "正在为您生成攻略...",
              timestamp: finalData.timestamp || new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
              data: {
                suggestions: finalData.suggestions || [],
                thoughts: [],  // 最终回复不显示思考过程
                extracted_info: finalData.extracted_info || {},
                status: finalData.status || 'completed',
                raw: finalData
              }
            }
            setMessages(prev => [...prev, finalMsg])
          } catch (err) {
            console.error('获取最终回复失败:', err)
          }
        }, 2000)  // 等待2秒后获取最终回复
      }
    } catch (err: any) {
      console.error('API 调用失败:', err)
      
      // 提供更友好的错误处理
      let errorMessage = "抱歉，服务暂时不可用。"
      
      if (err?.message?.includes('fetch')) {
        errorMessage = "网络连接异常，请检查网络连接后重试。"
      } else if (err?.message?.includes('timeout')) {
        errorMessage = "请求超时，请稍后重试。"
      } else if (err?.status === 500) {
        errorMessage = "服务器内部错误，我们正在修复中。"
      } else if (err?.status === 404) {
        errorMessage = "服务接口不存在，请联系技术支持。"
      }
      
      const errorMsg = {
        id: Date.now() + 2,
        type: "response" as const,
        content: errorMessage,
        timestamp: "刚刚",
      }
      setMessages(prev => [...prev, errorMsg])
      
      // 更新连接状态
      setIsConnected(false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFeedback = async (feedback: string, messageId: number) => {
    if (!feedback.trim() || isLoading) return
    
    setIsLoading(true)
    
    // 找到原始方案消息
    const originalMessage = messages.find(m => m.id === messageId)
    const originalPlan = originalMessage?.content || ""
    
    try {
      // 确保传递user_id
      const data = await agentApi.submitFeedback(feedback, undefined, userId || 'default', originalPlan)
      
      const feedbackMsg = {
        id: Date.now() + 1,
        type: "assistant" as const,
        content: data.message || "已根据你的反馈优化方案",
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        data: {
          thoughts: data.thoughts || [],
          extracted_info: data.extracted_info || {},
          iteration_count: data.iteration_count || 0
        }
      }
      
      setMessages(prev => [...prev, feedbackMsg])
    } catch (err: any) {
      console.error('反馈提交失败:', err)
      const errorMsg = {
        id: Date.now() + 2,
        type: "response" as const,
        content: "反馈提交失败，请稍后重试",
        timestamp: "刚刚",
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const handleStartPlanning = (message: any) => {
    // 生成规划ID
    const planId = `plan_${Date.now()}`
    
    // 解析消息内容，提取行程信息
    const planData = {
      id: planId,
      title: "我的旅行计划",
      description: message.content,
      extractedInfo: message.data?.extracted_info || {},
      thoughts: message.data?.thoughts || [],
      createdAt: new Date().toISOString()
    }
    
    // 保存到localStorage
    localStorage.setItem(`plan_${planId}`, JSON.stringify(planData))
    
    // 跳转到规划页面
    router.push(`/planning/${planId}`)
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
                    知小旅
                  </CardTitle>
                  <CardDescription>像真人顾问一样懂需求、会变通的智能旅游规划助手</CardDescription>
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
            <Card className="h-[700px] flex flex-col">
              {/* 聊天区域头部 */}
              <CardHeader className="border-b">
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="w-5 h-5 text-blue-500" />
                  知小旅
                  {isLoading && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
                </CardTitle>
                <CardDescription>告诉我你想去的地方，我会为你获取天气信息并提供个性化旅游建议。支持文字描述和标签组合输入～</CardDescription>
              </CardHeader>

              {/* Messages - 消息展示区域 */}
              <CardContent className="flex-1 overflow-y-auto p-4">
                <div className="space-y-4">
                  {messages.map((msg) => (
                    <div key={msg.id} className={`flex gap-3 ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
                      {/* Agent头像 - 仅在非用户消息时显示 */}
                      {msg.type !== "user" && (
                        <Avatar className="w-10 h-10 border-2 border-blue-200 shadow-md">
                          <AvatarImage src="/placeholder.svg?height=40&width=40" />
                          <AvatarFallback className={`text-white text-sm font-semibold ${
                            msg.type === "thinking" ? "bg-gradient-to-br from-purple-500 to-purple-600" :
                            msg.type === "action" ? "bg-gradient-to-br from-blue-500 to-blue-600" :
                            "bg-gradient-to-br from-blue-500 via-indigo-500 to-green-500"
                          }`}>
                            {msg.type === "thinking" ? <Brain className="w-5 h-5" /> :
                             msg.type === "action" ? <Loader2 className="w-5 h-5" /> :
                             "知"}
                          </AvatarFallback>
                        </Avatar>
                      )}

                      {/* 消息气泡 - 根据消息类型应用不同样式 */}
                      <div
                        className={`max-w-[85%] rounded-xl p-5 shadow-md ${
                          msg.type === "user" ? "bg-gradient-to-br from-blue-500 to-indigo-600 text-white" :
                          msg.type === "thinking" ? "bg-gradient-to-br from-purple-50 to-purple-100 text-purple-900 border-2 border-purple-300" :
                          msg.type === "action" ? "bg-gradient-to-br from-blue-50 to-indigo-100 text-blue-900 border-2 border-blue-300" :
                          "bg-gradient-to-br from-white to-gray-50 text-gray-900 border-2 border-gray-200"
                        }`}
                      >
                        {/* 消息类型标识 */}
                        {msg.type === "thinking" && (
                          <div className="flex items-center gap-2 text-sm font-medium text-purple-700 mb-2">
                            <Brain className="w-4 h-4 animate-pulse" />
                            <span>思考中...</span>
                          </div>
                        )}
                        {msg.type === "action" && (
                          <div className="flex items-center gap-2 text-sm font-medium text-blue-700 mb-2">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>执行中...</span>
                          </div>
                        )}
                        {msg.type === "response" && (
                          <div className="flex items-center gap-2 text-sm font-medium text-green-700 mb-2">
                            <CheckCircle className="w-4 h-4" />
                            <span>完成</span>
                          </div>
                        )}
                        
                        {/* 消息内容 - 支持Markdown样式的长文本 */}
                        <div className={`text-base whitespace-pre-wrap break-words leading-relaxed ${
                          msg.type === "user" ? "" : "space-y-3"
                        }`}>
                          {/* 美化攻略展示 */}
                          {msg.type === "assistant" && msg.data?.status === "completed" && msg.content.includes("行程主题") ? (
                            <div className="space-y-4">
                              {msg.content.split(/\n\n+/).map((section, sectionIdx) => {
                                // 行程主题
                                if (section.includes("**行程主题：**")) {
                                  const match = section.match(/\*\*行程主题：\*\*\s*(.+)/)
                                  return (
                                    <div key={sectionIdx} className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border-l-4 border-blue-500">
                                      <div className="text-sm font-semibold text-blue-700 mb-1">行程主题</div>
                                      <div className="text-lg font-bold text-gray-900">{match ? match[1] : section}</div>
                                    </div>
                                  )
                                }
                                
                                // 行程总览
                                if (section.includes("天数：") || section.includes("总预算：")) {
                                  return (
                                    <div key={sectionIdx} className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg border border-green-200">
                                      <div className="text-sm font-semibold text-green-700 mb-2">行程总览</div>
                                      <div className="space-y-1 text-sm text-gray-700">
                                        {section.split('\n').filter(line => line.trim()).map((line, lineIdx) => {
                                          if (line.includes('•')) {
                                            return (
                                              <div key={lineIdx} className="flex items-start gap-2">
                                                <span className="text-green-600 mt-1">•</span>
                                                <span>{line.replace(/^[•·\-\*]\s*/, '')}</span>
                                              </div>
                                            )
                                          }
                                          return <div key={lineIdx}>{line}</div>
                                        })}
                                      </div>
                                    </div>
                                  )
                                }
                                
                                // 每日行程
                                if (section.match(/^\*\*第\d+天/)) {
                                  const dayMatch = section.match(/\*\*第(\d+)天[：:](.+?)\*\*/)
                                  return (
                                    <div key={sectionIdx} className="bg-white p-4 rounded-lg border-2 border-purple-200 shadow-sm">
                                      {dayMatch && (
                                        <div className="text-lg font-bold text-purple-700 mb-3 flex items-center gap-2">
                                          <Calendar className="w-5 h-5" />
                                          第{dayMatch[1]}天：{dayMatch[2]}
                                        </div>
                                      )}
                                      <div className="space-y-3">
                                        {section.split(/\n(?=\*\*)/).map((item, itemIdx) => {
                                          const timeMatch = item.match(/\*\*(\d{2}:\d{2}-\d{2}:\d{2})\*\*\s*(.+?)(?:\n|$)/)
                                          if (timeMatch) {
                                            return (
                                              <div key={itemIdx} className="pl-4 border-l-2 border-blue-300 bg-blue-50/50 p-3 rounded-r-lg">
                                                <div className="flex items-center gap-2 mb-2">
                                                  <Badge className="bg-blue-600 text-white">{timeMatch[1]}</Badge>
                                                  <span className="font-semibold text-gray-900">{timeMatch[2]}</span>
                                                </div>
                                                <div className="text-sm text-gray-700 space-y-1 ml-2">
                                                  {item.split('\n').slice(1).filter(line => line.trim() && !line.match(/^\*\*/)).map((detail, detailIdx) => (
                                                    <div key={detailIdx} className="flex items-start gap-2">
                                                      {detail.includes('👶') && <span className="text-blue-500">👶</span>}
                                                      {detail.includes('👴') && <span className="text-green-500">👴</span>}
                                                      {detail.includes('💡') && <span className="text-yellow-500">💡</span>}
                                                      {detail.includes('💰') && <span className="text-orange-500">💰</span>}
                                                      <span>{detail.replace(/^[-•·]\s*/, '').replace(/^(👶|👴|💡|💰)\s*/, '')}</span>
                                                    </div>
                                                  ))}
                                                </div>
                                              </div>
                                            )
                                          }
                                          return null
                                        })}
                                      </div>
                                    </div>
                                  )
                                }
                                
                                // 其他内容
                                return (
                                  <div key={sectionIdx} className="text-gray-700">
                                    {section.split('\n').map((line, lineIdx) => (
                                      <div key={lineIdx} className={line.match(/^\*\*/) ? 'font-bold text-gray-900 my-2' : ''}>
                                        {line.replace(/\*\*/g, '')}
                                      </div>
                                    ))}
                                  </div>
                                )
                              })}
                            </div>
                          ) : (
                            // 普通消息展示
                            msg.content.split('\n\n').map((paragraph, idx) => (
                            <p key={idx} className="mb-2 last:mb-0">
                              {paragraph.split('\n').map((line, lineIdx) => (
                                <span key={lineIdx}>
                                    {line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')}
                                  {lineIdx < paragraph.split('\n').length - 1 && <br />}
                                </span>
                              ))}
                            </p>
                            ))
                          )}
                        </div>
                        
        {/* 游离节点可视化 - Agent思考过程 */}
        {msg.data && msg.data.extracted_info && msg.data.status === "thinking" && (
          <div className="mt-6 space-y-3">
            <div className="text-base font-bold text-gray-800 flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-600 animate-pulse" />
              <span>AI正在分析你的需求...</span>
                      </div>
            <FloatingNodes 
              extractedInfo={msg.data.extracted_info}
              keywords={msg.data.thoughts?.flatMap((t: ThoughtProcess) => t.keywords || []) || []}
              className="h-80"
            />
                </div>
              )}

        {/* 思考过程展示 - 优先显示完整景点信息，然后显示关键词标签 */}
        {msg.data && msg.data.extracted_info && (
          <div className="mt-4">
            <div className="flex flex-wrap gap-3">
              {/* 优先显示enhanced_locations中的完整景点信息 */}
              {msg.data.extracted_info.enhanced_locations && 
               Array.isArray(msg.data.extracted_info.enhanced_locations) &&
               msg.data.extracted_info.enhanced_locations.map((enhancedLoc: any, locIdx: number) => {
                 if (enhancedLoc.suggestions && Array.isArray(enhancedLoc.suggestions)) {
                   return enhancedLoc.suggestions.slice(0, 2).map((suggestion: any, sugIdx: number) => {
                     const name = suggestion.name || ''
                     const address = suggestion.address || suggestion.district || ''
                     const displayText = address ? `${name}（${address}）` : name
                     if (name && name.trim().length > 1 && !/^\d+$/.test(name.trim())) {
                       return (
                         <Badge
                           key={`loc-${locIdx}-${sugIdx}`}
                           variant="secondary"
                           className="bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-2 rounded-full text-sm font-semibold border-0 shadow-md hover:shadow-lg hover:scale-105 transition-all cursor-default"
                           title={address ? `地址：${address}` : name}
                         >
                           {displayText}
                         </Badge>
                       )
                     }
                     return null
                   })
                 }
                 return null
               })}
              
              {/* 然后显示有效的关键词标签（过滤掉已显示的景点） */}
              {msg.data.thoughts && msg.data.thoughts.length > 0 && 
               msg.data.thoughts.flatMap((thought: ThoughtProcess) => {
                 // 获取已显示的景点名称
                 const displayedPlaces = new Set(
                   msg.data.extracted_info.enhanced_locations
                     ?.flatMap((el: any) => el.suggestions?.map((s: any) => s.name) || []) || []
                 )
                 
                 return (thought.keywords || [])
                   .filter((kw: string) => {
                     // 过滤掉纯数字、单个字符、已显示的景点
                     return kw && 
                            kw.trim().length > 1 && 
                            !/^\d+$/.test(kw.trim()) &&
                            !displayedPlaces.has(kw.trim())
                   })
                   .slice(0, 10)
                   .map((keyword: string, kidx: number) => (
                     <Badge
                       key={`${thought.step}-${kidx}`}
                       variant="secondary"
                       className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-2 rounded-full text-sm font-semibold border-0 shadow-md hover:shadow-lg hover:scale-105 transition-all cursor-default"
                     >
                       {keyword}
                     </Badge>
                   ))
               })}
            </div>
          </div>
        )}

        {/* 方案预览卡片 - 当Agent生成完整攻略时显示 */}
        {msg.type === "assistant" && msg.data?.status === "completed" && (() => {
          // 从消息内容中提取方案信息
          const content = msg.content || ""
          const daysMatch = content.match(/(\d+)天/)
          const budgetMatch = content.match(/预算[：:]\s*[¥￥]?([\d,]+)/)
          const titleMatch = content.match(/\*\*行程主题[：:]\*\*\s*(.+)/)
          
          // 提取亮点
          const highlights: string[] = []
          const highlightMatch = content.match(/核心亮点[：:]([\s\S]*?)(?:\n\n|\*\*|$)/)
          if (highlightMatch) {
            highlightMatch[1].split(/[•·\-\*]/).forEach(item => {
              const trimmed = item.trim()
              if (trimmed && trimmed.length > 0 && trimmed.length < 20) {
                highlights.push(trimmed)
              }
            })
          }
          
          // 如果检测到是攻略内容，显示预览卡片
          if (content.includes("行程主题") || content.includes("第") && content.includes("天")) {
            return (
              <div className="mt-4">
                <PlanPreviewCard
                  title={titleMatch ? titleMatch[1].trim() : "我的旅行计划"}
                  days={daysMatch ? parseInt(daysMatch[1]) : undefined}
                  budget={budgetMatch ? `约¥${budgetMatch[1]}` : undefined}
                  highlights={highlights.length > 0 ? highlights : undefined}
                  description={content.substring(0, 100) + "..."}
                  onViewPlan={() => handleStartPlanning(msg)}
                  className="max-w-md"
                />
              </div>
            )
          }
          return null
        })()}

        {/* 智能建议标签 */}
        {msg.data && msg.data.suggestions && msg.data.suggestions.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-yellow-500" />
              <span>相关建议</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {msg.data.suggestions.map((suggestion: string, idx: number) => {
                // 检查是否是反馈相关的建议
                const isFeedback = suggestion.includes("满意") || suggestion.includes("不满意") || suggestion.includes("调整")
                return (
                <Badge
                  key={idx}
                    variant={isFeedback ? "default" : "secondary"}
                    className={`cursor-pointer transition-all transform hover:scale-105 text-sm px-4 py-2 rounded-full font-medium shadow-sm ${
                      isFeedback
                        ? "bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white border-0"
                        : "bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 text-blue-700 border border-blue-200"
                    }`}
                    onClick={() => {
                      if (isFeedback && suggestion.includes("不满意")) {
                        // 触发反馈输入
                        const feedback = prompt("请说明具体需要调整的地方（如：想减少步行、换一家餐厅等）：")
                        if (feedback) {
                          handleFeedback(feedback, msg.id)
                        }
                      } else if (suggestion.includes("满意") && suggestion.includes("规划")) {
                        // 跳转到规划页面
                        handleStartPlanning(msg)
                      } else {
                        setMessage(suggestion)
                      }
                    }}
                >
                  {suggestion}
                </Badge>
                )
              })}
            </div>
          </div>
        )}
                        
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
                        <p className={`text-xs mt-3 pt-2 border-t ${
                          msg.type === "user" ? "text-blue-100 border-blue-400/30" :
                          msg.type === "thinking" ? "text-purple-500 border-purple-300" :
                          msg.type === "action" ? "text-blue-500 border-blue-300" :
                          "text-gray-500 border-gray-200"
                        }`}>
                          {msg.timestamp}
                        </p>
                      </div>

                      {/* 用户头像 - 仅在用户消息时显示 */}
                      {msg.type === "user" && (
                        <Avatar className="w-10 h-10 border-2 border-gray-200 shadow-md">
                          <AvatarImage src="/placeholder.svg?height=40&width=40" />
                          <AvatarFallback className="bg-gradient-to-br from-gray-500 to-gray-600 text-white text-sm font-semibold">我</AvatarFallback>
                        </Avatar>
                      )}
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </CardContent>

              {/* Input Area - 消息输入区域 */}
              <div className="border-t p-4">
                    {/* 标签输入区域 */}
                {showTagInput && (
                  <div className="mb-4 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl space-y-4 border border-blue-200 shadow-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-base font-semibold text-gray-800 flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-blue-500" />
                        快速标签
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowTagInput(false)}
                        className="text-gray-600 hover:text-gray-800"
                      >
                        收起
                      </Button>
                    </div>
                    {Object.entries(tagOptions).map(([category, tags]) => (
                      <div key={category} className="space-y-3">
                        <div className="text-sm font-medium text-gray-700">{category}</div>
                        <div className="flex flex-wrap gap-2">
                          {tags.map((tag) => {
                            const isSelected = selectedTags.includes(tag)
                            return (
                              <Badge
                                key={tag}
                                variant={isSelected ? "default" : "outline"}
                                className={`cursor-pointer transition-all transform hover:scale-105 text-sm px-4 py-2 rounded-full font-medium ${
                                  isSelected
                                    ? "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md border-0"
                                    : "bg-white hover:bg-blue-50 text-gray-700 border-2 border-blue-200 hover:border-blue-400"
                                }`}
                                onClick={() => {
                                  if (isSelected) {
                                    setSelectedTags(selectedTags.filter((t) => t !== tag))
                                  } else {
                                    setSelectedTags([...selectedTags, tag])
                                  }
                                }}
                              >
                                #{tag}
                              </Badge>
                            )
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="flex gap-2">
                  {/* 标签按钮 */}
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setShowTagInput(!showTagInput)}
                    title="标签输入"
                    className="h-12 w-12 border-2 border-gray-300 hover:border-blue-500 rounded-xl text-xl font-bold hover:bg-blue-50 transition-all"
                  >
                    #
                  </Button>
                  
                  {/* 消息输入框 - 支持Enter键发送 */}
                  <Input
                    placeholder="输入你的旅行需求，或用标签快速表达..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                    className="flex-1 text-base h-12 px-4 border-2 border-gray-300 focus:border-blue-500 rounded-xl"
                  />
                  {/* 发送按钮 - 空消息时禁用 */}
                  <Button 
                    onClick={handleSendMessage} 
                    disabled={!message.trim() && selectedTags.length === 0}
                    className="h-12 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl shadow-md transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    <Send className="w-5 h-5 mr-2" />
                    <span className="text-base font-medium">发送</span>
                  </Button>
                </div>
                
                {/* 已选标签显示 */}
                {selectedTags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    <span className="text-sm font-medium text-gray-600 self-center">已选标签：</span>
                    {selectedTags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="default"
                        className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white cursor-pointer hover:from-blue-700 hover:to-indigo-700 text-sm px-3 py-1.5 rounded-full font-medium shadow-sm transition-all transform hover:scale-105"
                        onClick={() => setSelectedTags(selectedTags.filter((t) => t !== tag))}
                      >
                        #{tag} <span className="ml-1 text-xs">×</span>
                      </Badge>
                    ))}
                  </div>
                )}
                
                {/* 快速问题标签 - 提供便捷的问题入口 */}
                <div className="flex flex-wrap gap-2 mt-4">
                  <span className="text-sm font-medium text-gray-600 self-center">快速问题：</span>
                  {quickQuestions.slice(0, 3).map((question, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="cursor-pointer hover:bg-blue-50 text-sm px-4 py-2 rounded-full border-2 border-blue-200 hover:border-blue-400 text-gray-700 font-medium transition-all transform hover:scale-105"
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
