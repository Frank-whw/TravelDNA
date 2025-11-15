/**
 * 旅游行程规划页面
 * 美观、大气的行程展示和编辑界面
 */
"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { 
  Calendar, MapPin, Clock, Utensils, Hotel, Navigation, 
  Edit2, Save, X, Plus, Trash2, Sun, Cloud, CloudRain,
  Star, Heart, Share2, Download, ChevronRight, Sparkles,
  GripVertical, CheckCircle2, AlertCircle
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import agentApi from "@/lib/agentApi"

interface DayPlan {
  date: string
  dateLabel: string
  weather?: {
    condition: string
    temperature: string
    icon: string
  }
  items: PlanItem[]
}

interface PlanItem {
  id: string
  time: string
  type: 'attraction' | 'restaurant' | 'hotel' | 'transport' | 'activity'
  title: string
  location?: string
  description?: string
  duration?: string
  cost?: number
  rating?: number
  notes?: string
  editable?: boolean
}

export default function PlanningPage() {
  const params = useParams()
  const router = useRouter()
  const planId = params.planId as string
  
  const [plan, setPlan] = useState<DayPlan[]>([])
  const [isEditing, setIsEditing] = useState(false)
  const [editingItem, setEditingItem] = useState<PlanItem | null>(null)
  const [planTitle, setPlanTitle] = useState("我的上海之旅")
  const [planDescription, setPlanDescription] = useState("")
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadPlan()
  }, [planId])

  const loadPlan = async () => {
    try {
      // 从localStorage加载规划数据
      const savedPlan = localStorage.getItem(`plan_${planId}`)
      if (savedPlan) {
        const data = JSON.parse(savedPlan)
        setPlanTitle(data.title || "我的旅行计划")
        setPlanDescription(data.description || "")
        
        // 如果有已保存的days数据，使用它
        if (data.days && Array.isArray(data.days) && data.days.length > 0) {
          setPlan(data.days)
        } else {
          // 否则从extractedInfo和description中解析生成规划
          parsePlanFromData(data)
        }
      } else {
        // 如果没有保存的数据，创建默认规划
        createDefaultPlan()
      }
    } catch (error) {
      console.error("加载规划失败:", error)
      createDefaultPlan()
    } finally {
      setIsLoading(false)
    }
  }

  const parsePlanFromData = (data: any) => {
    // 从AI回复的文本中解析行程
    const content = data.description || ""
    const extractedInfo = data.extractedInfo || {}
    const travelDays = extractedInfo.travel_days || 3
    
    // 简单的文本解析（实际可以更智能）
    const days: DayPlan[] = []
    const today = new Date()
    
    for (let i = 0; i < travelDays; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      const dateStr = date.toISOString().split('T')[0]
      const dateLabel = `${date.getMonth() + 1}月${date.getDate()}日`
      
      days.push({
        date: dateStr,
        dateLabel,
        weather: {
          condition: i === 0 ? '晴' : i === 1 ? '多云' : '小雨',
          temperature: `${20 + i * 2}°C`,
          icon: i === 0 ? 'sun' : i === 1 ? 'cloud' : 'rain'
        },
        items: []
      })
    }
    
    // 尝试从content中提取行程项（简单示例）
    // 实际应该使用更智能的解析
    if (content.includes('第') && content.includes('天')) {
      // 解析多天行程
      const dayMatches = content.match(/第(\d+)天[：:]([\s\S]*?)(?=第\d+天|$)/g)
      if (dayMatches) {
        dayMatches.forEach((match, index) => {
          if (index < days.length) {
            // 简单提取时间和地点
            const timeMatches = match.match(/(\d{1,2}:\d{2})/g)
            const locationMatches = match.match(/([^\s，,。.]+(?:公园|广场|博物馆|景点|餐厅|酒店))/g)
            
            if (timeMatches && locationMatches) {
              timeMatches.forEach((time, timeIndex) => {
                if (timeIndex < locationMatches.length) {
                  days[index].items.push({
                    id: `item-${index}-${timeIndex}`,
                    time: time,
                    type: locationMatches[timeIndex].includes('餐厅') ? 'restaurant' : 
                          locationMatches[timeIndex].includes('酒店') ? 'hotel' : 'attraction',
                    title: locationMatches[timeIndex],
                    editable: true
                  })
                }
              })
            }
          }
        })
      }
    }
    
    // 如果没有解析到内容，使用默认示例
    if (days.every(d => d.items.length === 0)) {
      days.forEach((day, index) => {
        day.items = [
          {
            id: `item-${index}-1`,
            time: '09:00',
            type: 'attraction',
            title: extractedInfo.locations?.[0] || '待定景点',
            location: extractedInfo.locations?.[0] || '',
            description: '待添加详细描述',
            duration: '2小时',
            editable: true
          }
        ]
      })
    }
    
    setPlan(days)
  }

  const createDefaultPlan = () => {
    // 创建示例规划
    const today = new Date()
    const days: DayPlan[] = []
    
    for (let i = 0; i < 3; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      const dateStr = date.toISOString().split('T')[0]
      const dateLabel = `${date.getMonth() + 1}月${date.getDate()}日`
      
      days.push({
        date: dateStr,
        dateLabel,
        weather: {
          condition: i === 0 ? '晴' : i === 1 ? '多云' : '小雨',
          temperature: `${20 + i * 2}°C`,
          icon: i === 0 ? 'sun' : i === 1 ? 'cloud' : 'rain'
        },
        items: [
          {
            id: `item-${i}-1`,
            time: '09:00',
            type: 'attraction',
            title: '外滩',
            location: '黄浦区中山东一路',
            description: '上海标志性景点，欣赏黄浦江两岸风光',
            duration: '2小时',
            cost: 0,
            rating: 4.8,
            editable: true
          },
          {
            id: `item-${i}-2`,
            time: '12:00',
            type: 'restaurant',
            title: '老正兴菜馆',
            location: '黄浦区南京东路',
            description: '品尝正宗本帮菜',
            duration: '1.5小时',
            cost: 150,
            rating: 4.5,
            editable: true
          }
        ]
      })
    }
    
    setPlan(days)
  }

  const savePlan = () => {
    const planData = {
      id: planId,
      title: planTitle,
      description: planDescription,
      days: plan,
      updatedAt: new Date().toISOString()
    }
    localStorage.setItem(`plan_${planId}`, JSON.stringify(planData))
    setIsEditing(false)
  }

  const addItem = (dayIndex: number) => {
    const newItem: PlanItem = {
      id: `item-${Date.now()}`,
      time: '10:00',
      type: 'activity',
      title: '新活动',
      editable: true
    }
    
    const newPlan = [...plan]
    newPlan[dayIndex].items.push(newItem)
    setPlan(newPlan)
    setEditingItem(newItem)
    setIsEditing(true)
  }

  const deleteItem = (dayIndex: number, itemId: string) => {
    const newPlan = [...plan]
    newPlan[dayIndex].items = newPlan[dayIndex].items.filter(item => item.id !== itemId)
    setPlan(newPlan)
  }

  const updateItem = (dayIndex: number, itemId: string, updates: Partial<PlanItem>) => {
    const newPlan = [...plan]
    const itemIndex = newPlan[dayIndex].items.findIndex(item => item.id === itemId)
    if (itemIndex !== -1) {
      newPlan[dayIndex].items[itemIndex] = { ...newPlan[dayIndex].items[itemIndex], ...updates }
      setPlan(newPlan)
    }
  }

  const getTypeIcon = (type: PlanItem['type']) => {
    switch (type) {
      case 'attraction': return MapPin
      case 'restaurant': return Utensils
      case 'hotel': return Hotel
      case 'transport': return Navigation
      default: return Sparkles
    }
  }

  const getTypeColor = (type: PlanItem['type']) => {
    switch (type) {
      case 'attraction': return 'bg-blue-500'
      case 'restaurant': return 'bg-orange-500'
      case 'hotel': return 'bg-purple-500'
      case 'transport': return 'bg-green-500'
      default: return 'bg-pink-500'
    }
  }

  const getWeatherIcon = (icon: string) => {
    switch (icon) {
      case 'sun': return <Sun className="w-5 h-5 text-yellow-500" />
      case 'cloud': return <Cloud className="w-5 h-5 text-gray-400" />
      case 'rain': return <CloudRain className="w-5 h-5 text-blue-500" />
      default: return <Sun className="w-5 h-5 text-yellow-500" />
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载行程规划中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* 顶部导航栏 */}
      <div className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={() => router.back()}
                className="text-gray-600 hover:text-gray-900"
              >
                <X className="w-5 h-5 mr-2" />
                返回
              </Button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div>
                <Input
                  value={planTitle}
                  onChange={(e) => setPlanTitle(e.target.value)}
                  className="text-2xl font-bold border-0 bg-transparent p-0 focus-visible:ring-0"
                  placeholder="我的旅行计划"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Share2 className="w-4 h-4 mr-2" />
                分享
              </Button>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                导出
              </Button>
              {isEditing ? (
                <div className="flex items-center gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => {
                      if (confirm('确定要取消编辑吗？未保存的更改将丢失。')) {
                        setIsEditing(false)
                        loadPlan() // 重新加载原始数据
                      }
                    }}
                  >
                    <X className="w-4 h-4 mr-2" />
                    取消
                  </Button>
                  <Button 
                    onClick={savePlan} 
                    size="sm" 
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    保存更改
                  </Button>
                </div>
              ) : (
                <Button onClick={() => setIsEditing(true)} size="sm" variant="outline">
                  <Edit2 className="w-4 h-4 mr-2" />
                  编辑行程
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 编辑提示 */}
        {isEditing && (
          <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500 rounded-lg shadow-sm">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="flex-1">
                <div className="font-semibold text-blue-900 mb-1">编辑模式</div>
                <div className="text-sm text-blue-700">
                  你可以点击任意项目进行编辑，拖拽调整顺序，或使用删除按钮移除不需要的项目。
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 规划描述 */}
        <Card className="mb-8 border-2 border-blue-200 bg-gradient-to-r from-white to-blue-50/50 shadow-lg">
          <CardContent className="pt-6">
            <Textarea
              value={planDescription}
              onChange={(e) => setPlanDescription(e.target.value)}
              placeholder="添加行程描述..."
              disabled={!isEditing}
              className={`min-h-[80px] border-0 bg-transparent resize-none focus-visible:ring-0 text-gray-700 ${
                !isEditing ? 'cursor-default' : ''
              }`}
            />
          </CardContent>
        </Card>

        {/* 行程时间轴 */}
        <div className="space-y-8">
          {plan.map((day, dayIndex) => (
            <Card 
              key={day.date} 
              className="overflow-hidden border-2 border-gray-200 shadow-xl hover:shadow-2xl transition-all duration-300 bg-white"
            >
              {/* 日期头部 */}
              <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 p-6 text-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Calendar className="w-6 h-6" />
                    <div>
                      <h3 className="text-2xl font-bold">{day.dateLabel}</h3>
                      <p className="text-blue-100 text-sm">{day.date}</p>
                    </div>
                  </div>
                  {day.weather && (
                    <div className="flex items-center gap-3 bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
                      {getWeatherIcon(day.weather.icon)}
                      <div>
                        <div className="text-sm font-medium">{day.weather.condition}</div>
                        <div className="text-xs text-blue-100">{day.weather.temperature}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <CardContent className="p-6">
                {/* 行程项目 */}
                <div className="space-y-4">
                  {day.items.map((item, itemIndex) => {
                    const Icon = getTypeIcon(item.type)
                    const colorClass = getTypeColor(item.type)
                    
                    return (
                      <div
                        key={item.id}
                        className="relative flex gap-4 group"
                      >
                        {/* 时间轴 */}
                        <div className="flex flex-col items-center">
                          <div className={`w-12 h-12 rounded-full ${colorClass} flex items-center justify-center text-white shadow-lg`}>
                            <Icon className="w-6 h-6" />
                          </div>
                          {itemIndex < day.items.length - 1 && (
                            <div className="w-0.5 h-full bg-gradient-to-b from-gray-300 to-transparent mt-2"></div>
                          )}
                        </div>

                        {/* 内容卡片 */}
                        <div className={`flex-1 bg-gradient-to-r from-gray-50 to-white rounded-xl p-5 border-2 transition-all duration-300 shadow-md hover:shadow-lg ${
                          isEditing ? 'border-blue-400 ring-2 ring-blue-200' : 'border-gray-200 hover:border-blue-300'
                        }`}>
                          <div className="flex items-start justify-between gap-3">
                            {/* 拖拽手柄 - 仅在编辑模式显示 */}
                            {isEditing && (
                              <div className="cursor-move text-gray-400 hover:text-gray-600 mt-1">
                                <GripVertical className="w-5 h-5" />
                              </div>
                            )}
                            
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2 flex-wrap">
                                <Badge variant="outline" className="text-xs font-mono bg-white">
                                  <Clock className="w-3 h-3 mr-1" />
                                  {item.time}
                                </Badge>
                                {isEditing ? (
                                  <Input
                                    value={item.title}
                                    onChange={(e) => updateItem(dayIndex, item.id, { title: e.target.value })}
                                    className="flex-1 text-lg font-bold border-2 border-blue-300 rounded-lg px-3 py-1 focus:border-blue-500"
                                    placeholder="活动名称"
                                  />
                                ) : (
                                  <h4 className="text-lg font-bold text-gray-900">{item.title}</h4>
                                )}
                              </div>
                              
                              {item.location && (
                                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                                  <MapPin className="w-4 h-4 text-red-500" />
                                  {isEditing ? (
                                    <Input
                                      value={item.location}
                                      onChange={(e) => updateItem(dayIndex, item.id, { location: e.target.value })}
                                      className="flex-1 border-2 border-blue-300 rounded-lg px-2 py-1 text-sm focus:border-blue-500"
                                      placeholder="地点地址"
                                    />
                                  ) : (
                                    <span className="hover:text-blue-600 cursor-pointer" onClick={() => {
                                      // 可以在这里添加地图跳转功能
                                      window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(item.location)}`, '_blank')
                                    }}>{item.location}</span>
                                  )}
                                </div>
                              )}
                              
                              {/* 时间编辑 */}
                              {isEditing && (
                                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                                  <Clock className="w-4 h-4 text-blue-500" />
                                  <Input
                                    value={item.time}
                                    onChange={(e) => updateItem(dayIndex, item.id, { time: e.target.value })}
                                    className="w-32 border-2 border-blue-300 rounded-lg px-2 py-1 text-sm focus:border-blue-500"
                                    placeholder="09:00"
                                  />
                                </div>
                              )}

                              {item.description && (
                                <div className="mb-3">
                                  {isEditing ? (
                                    <Textarea
                                      value={item.description}
                                      onChange={(e) => updateItem(dayIndex, item.id, { description: e.target.value })}
                                      className="min-h-[60px] text-sm border-gray-200"
                                    />
                                  ) : (
                                    <p className="text-sm text-gray-700">{item.description}</p>
                                  )}
                                </div>
                              )}

                              <div className="flex items-center gap-4 flex-wrap">
                                {item.duration && (
                                  <Badge variant="secondary" className="text-xs">
                                    <Clock className="w-3 h-3 mr-1" />
                                    {item.duration}
                                  </Badge>
                                )}
                                {item.cost !== undefined && (
                                  <Badge variant="secondary" className="text-xs">
                                    <span className="mr-1">¥</span>
                                    {item.cost}
                                  </Badge>
                                )}
                                {item.rating && (
                                  <Badge variant="secondary" className="text-xs">
                                    <Star className="w-3 h-3 mr-1 fill-yellow-400 text-yellow-400" />
                                    {item.rating}
                                  </Badge>
                                )}
                              </div>
                            </div>

                            {isEditing && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => deleteItem(dayIndex, item.id)}
                                className="opacity-0 group-hover:opacity-100 transition-opacity text-red-500 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}

                  {/* 添加新项目按钮 */}
                  {isEditing && (
                    <Button
                      variant="outline"
                      className="w-full border-2 border-dashed border-gray-300 hover:border-blue-400 hover:bg-blue-50 transition-all"
                      onClick={() => addItem(dayIndex)}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      添加活动
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}

