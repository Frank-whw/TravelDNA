/**
 * 智能旅游规划页面组件 - 个性化行程定制界面
 * 
 * 功能概述：
 * - 提供详细的旅游偏好设置表单
 * - 实时显示天气、客流、交通等影响因素
 * - 生成基于AI算法的个性化旅游行程
 * - 支持实时优化和备选方案推荐
 * 
 * 设计思路：
 * - 左侧配置表单，右侧结果展示的经典布局
 * - 分步骤引导用户完成偏好设置
 * - 可视化的滑块组件提升交互体验
 * - Tab组件展示多日行程安排
 * 
 * 技术架构：
 * - React客户端组件with多状态管理
 * - 受控表单组件（预算、天数、偏好等）
 * - Shadcn/ui高级组件（Select、Slider、Switch）
 * - 响应式栅格布局适配不同屏幕
 * 
 * 核心算法：
 * - 基于用户偏好的权重计算
 * - 实时数据融合的行程优化
 * - 多目标约束的路线规划
 * - 动态调整的备选方案生成
 * 
 * 待接入功能：
 * - 后端AI规划算法API
 * - 实时天气/客流/交通数据接口
 * - 地图可视化集成
 * - 行程导出和分享功能
 */

"use client"

import { useEffect, useMemo, useState } from "react"
import {
  MapPin,
  Users,
  Clock,
  Cloud,
  Navigation,
  Star,
  Plus,
  Settings,
  Loader2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import agentApi, {
  BudgetLevelKey,
  ShanghaiDatasetSummary,
  ShanghaiRecommendationPayload,
  ShanghaiRecommendationResponse,
} from "@/lib/agentApi"
import { cn } from "@/lib/utils"

const INTEREST_OPTIONS = [
  "历史文化",
  "自然风光",
  "美食",
  "购物",
  "夜生活",
  "博物馆",
  "户外运动",
  "温泉",
  "亲子互动",
  "艺术设计",
  "潮流打卡",
]

const DEFAULT_CITY = "上海"

const LEVEL_LABEL: Record<BudgetLevelKey, string> = {
  low: "经济型",
  medium: "舒适型",
  medium_high: "品质型",
  high: "高端型",
}

const TRAVEL_STYLE_LABEL: Record<string, string> = {
  relaxed: "休闲放松",
  adventure: "探险刺激",
  cultural: "文化体验",
  food: "美食之旅",
  photography: "摄影采风",
}

function resolveBudgetLevel(value: number): BudgetLevelKey {
  if (value <= 1500) return "low"
  if (value <= 3000) return "medium"
  if (value <= 5000) return "medium_high"
  return "high"
}

export default function PlanningPage() {
  const [budget, setBudget] = useState([3000])
  const [duration, setDuration] = useState([3])
  const [destination, setDestination] = useState(DEFAULT_CITY)
  const [travelStyle, setTravelStyle] = useState<string | undefined>()
  const [selectedInterests, setSelectedInterests] = useState<string[]>([])
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [weatherAdaptive, setWeatherAdaptive] = useState(true)
  const [avoidCrowd, setAvoidCrowd] = useState(true)
  const [trafficOptimization, setTrafficOptimization] = useState(true)

  const [datasetSummary, setDatasetSummary] = useState<ShanghaiDatasetSummary | null>(null)
  const [plan, setPlan] = useState<ShanghaiRecommendationResponse | null>(null)
  const [activeTab, setActiveTab] = useState<string>("day1")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    agentApi
      .getShanghaiDataset()
      .then((data) => setDatasetSummary(data))
      .catch((err) => {
        console.error(err)
        setError("上海旅游数据预览获取失败，稍后重试或直接生成方案。")
      })
  }, [])

  const budgetLevel = useMemo(() => resolveBudgetLevel(budget[0]), [budget])

  useEffect(() => {
    if (plan?.itinerary?.length) {
      setActiveTab(`day${plan.itinerary[0].day}`)
    }
  }, [plan])

  const handleInterestToggle = (tag: string) => {
    setSelectedInterests((prev) =>
      prev.includes(tag) ? prev.filter((item) => item !== tag) : [...prev, tag],
    )
  }

  const handleGeneratePlan = async (event?: React.FormEvent) => {
    event?.preventDefault()
    setLoading(true)
    setError(null)

    const payload: ShanghaiRecommendationPayload = {
      city: destination || DEFAULT_CITY,
      travel_days: duration[0],
      budget: budget[0],
      budget_level: budgetLevel,
      travel_style: travelStyle,
      interests: selectedInterests,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      weather_adaptive: weatherAdaptive,
      avoid_crowd: avoidCrowd,
      traffic_optimization: trafficOptimization,
    }

    try {
      const response = await agentApi.getShanghaiRecommendations(payload)
      setPlan(response)
    } catch (err: any) {
      console.error(err)
      setError(err?.message || "生成智能方案失败，请稍后再试。")
    } finally {
      setLoading(false)
    }
  }

  const weatherHighlight =
    plan?.analytics.weather_advice?.[0] ??
    datasetSummary?.seasonal_notes?.spring ??
    "等待生成，稍后将给出天气与出行建议"
  const crowdHighlight = plan?.analytics.crowd_strategy ?? "生成方案后将智能避开人流高峰"
  const trafficHighlight = plan?.analytics.traffic_tip ?? "开启交通优化后，将给出更顺畅的出行建议"
  const indoorRatio =
    plan?.analytics.indoor_ratio !== undefined ? `${Math.round(plan.analytics.indoor_ratio * 100)}%` : "—"

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                <MapPin className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                知小旅
              </span>
            </div>
            <nav className="hidden md:flex items-center space-x-6">
              <a href="/" className="text-gray-600 hover:text-blue-600 transition-colors">
                首页
              </a>
              <a href="/planning" className="text-blue-600 font-medium">
                智能规划
              </a>
              <a href="/chat" className="text-gray-600 hover:text-blue-600 transition-colors">
                AI问答
              </a>
              <a href="/community" className="text-gray-600 hover:text-blue-600 transition-colors">
                社区
              </a>
            </nav>
            <Button variant="outline">我的行程</Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  规划设置
                </CardTitle>
                <CardDescription>像真人顾问一样懂需求、会变通。支持标签组合输入，快速生成个性化行程。</CardDescription>
              </CardHeader>
              <CardContent>
                <form className="space-y-6" onSubmit={handleGeneratePlan}>
                  <div className="space-y-2">
                    <Label htmlFor="destination">目的地</Label>
                    <Input
                      id="destination"
                      value={destination}
                      onChange={(event) => setDestination(event.target.value)}
                      placeholder="当前预留为上海，可继续细化区域"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="start-date">出发日期</Label>
                      <Input
                        id="start-date"
                        type="date"
                        value={startDate}
                        onChange={(event) => setStartDate(event.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="end-date">返回日期</Label>
                      <Input
                        id="end-date"
                        type="date"
                        value={endDate}
                        onChange={(event) => setEndDate(event.target.value)}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>旅行天数: {duration[0]} 天</Label>
                    <Slider value={duration} onValueChange={setDuration} max={14} min={1} step={1} className="w-full" />
                  </div>

                  <div className="space-y-2">
                    <Label>
                      预算范围: ¥{budget[0]}（{LEVEL_LABEL[budgetLevel]}）
                    </Label>
                    <Slider
                      value={budget}
                      onValueChange={setBudget}
                      max={10000}
                      min={500}
                      step={100}
                      className="w-full"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="travel-style">旅行风格</Label>
                    <Select value={travelStyle} onValueChange={setTravelStyle}>
                      <SelectTrigger>
                        <SelectValue placeholder="请选择" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="relaxed">休闲放松</SelectItem>
                        <SelectItem value="adventure">探险刺激</SelectItem>
                        <SelectItem value="cultural">文化体验</SelectItem>
                        <SelectItem value="food">美食之旅</SelectItem>
                        <SelectItem value="photography">摄影采风</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>兴趣标签</Label>
                    <div className="flex flex-wrap gap-2">
                      {INTEREST_OPTIONS.map((tag) => {
                        const active = selectedInterests.includes(tag)
                        return (
                          <button
                            key={tag}
                            type="button"
                            onClick={() => handleInterestToggle(tag)}
                            className="outline-none"
                          >
                            <Badge
                              variant={active ? "default" : "outline"}
                              className={cn(
                                "cursor-pointer transition-colors",
                                active ? "bg-blue-600 hover:bg-blue-700" : "hover:bg-blue-50",
                              )}
                            >
                              {tag}
                            </Badge>
                          </button>
                        )
                      })}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <Label>实时优化</Label>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">天气自适应</span>
                        <Switch checked={weatherAdaptive} onCheckedChange={setWeatherAdaptive} />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">避开拥挤景点</span>
                        <Switch checked={avoidCrowd} onCheckedChange={setAvoidCrowd} />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">交通优化</span>
                        <Switch checked={trafficOptimization} onCheckedChange={setTrafficOptimization} />
                      </div>
                    </div>
                  </div>

                  {error && (
                    <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
                      {error}
                    </div>
                  )}

                  <Button className="w-full" size="lg" type="submit" disabled={loading}>
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        正在生成...
                      </span>
                    ) : (
                      "生成智能方案"
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-blue-500" />
                  实时状况洞察
                </CardTitle>
                <CardDescription>
                  无论数据是否齐备，都提前为上海预留好天气、客流与交通的反馈结构。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                    <Cloud className="w-8 h-8 text-blue-500" />
                    <div>
                      <div className="font-medium">天气建议</div>
                      <div className="text-sm text-gray-600">{weatherHighlight}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                    <Users className="w-8 h-8 text-green-500" />
                    <div>
                      <div className="font-medium">人流策略</div>
                      <div className="text-sm text-gray-600">{crowdHighlight}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                    <Navigation className="w-8 h-8 text-purple-500" />
                    <div>
                      <div className="font-medium">交通提示</div>
                      <div className="text-sm text-gray-600">{trafficHighlight}</div>
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border border-dashed border-slate-200 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <p className="text-sm text-slate-500">室内/室外平衡度</p>
                      <p className="text-2xl font-semibold text-slate-800">{indoorRatio}</p>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-slate-500 mb-2">上海精选参考（占位数据）</p>
                      <div className="flex flex-wrap gap-2">
                        {(datasetSummary?.sample_pois ?? []).map((poi) => (
                          <Badge key={poi.id} variant="outline">
                            {poi.name}
                          </Badge>
                        ))}
                        {!datasetSummary?.sample_pois?.length && (
                          <span className="text-xs text-slate-400">
                            数据集准备中，可先使用推荐算法生成方案。
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-yellow-500" />
                  推荐行程
                </CardTitle>
                <CardDescription>结合用户画像与协同过滤得分生成的上海个性化行程。</CardDescription>
              </CardHeader>
              <CardContent>
                {plan?.itinerary?.length ? (
                  <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsList className="flex flex-wrap gap-2">
                      {plan.itinerary.map((day) => (
                        <TabsTrigger key={day.day} value={`day${day.day}`} className="flex-1 min-w-[100px]">
                          第{day.day}天
                        </TabsTrigger>
                      ))}
                    </TabsList>

                    {plan.itinerary.map((day) => (
                      <TabsContent key={day.day} value={`day${day.day}`} className="space-y-4 mt-4">
                        <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                          <div className="flex flex-wrap items-center justify-between">
                            <div>
                              <span className="font-medium text-slate-800">
                                {day.focus || "主题：城市探索"}
                              </span>
                              {day.date && <span className="ml-2 text-xs text-slate-500">日期：{day.date}</span>}
                            </div>
                            {day.weather_note && (
                              <span className="text-xs text-blue-600">{day.weather_note}</span>
                            )}
                          </div>
                        </div>

                        {day.spots.map((spot) => (
                          <div key={spot.id} className="flex items-start gap-4 p-4 border rounded-lg bg-white">
                            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                              <Clock className="w-6 h-6 text-blue-600" />
                            </div>
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center justify-between gap-2">
                                <h3 className="font-medium text-slate-800">{spot.name}</h3>
                                <Badge variant="secondary">{spot.schedule}</Badge>
                              </div>
                              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                                <Badge variant="outline">匹配度 {spot.score}</Badge>
                                <Badge variant="outline">{spot.district}</Badge>
                                {spot.price_level && <Badge variant="outline">消费 {spot.price_level}</Badge>}
                                {spot.crowd_level && <Badge variant="outline">客流 {spot.crowd_level}</Badge>}
                                <Badge variant="outline">{spot.indoor ? "室内" : "户外"}</Badge>
                              </div>
                              <div className="space-y-1">
                                {spot.reasons.slice(0, 3).map((reason, index) => (
                                  <p key={index} className="text-sm text-slate-600 leading-snug">
                                    • {reason}
                                  </p>
                                ))}
                              </div>
                            </div>
                          </div>
                        ))}
                      </TabsContent>
                    ))}
                  </Tabs>
                ) : (
                  <div className="rounded-lg border border-dashed border-slate-200 py-12 text-center text-slate-500">
                    尚未生成行程，请填写左侧偏好并点击“生成智能方案”。
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-emerald-500" />
                  用户画像洞察
                </CardTitle>
                <CardDescription>根据旅行风格、预算与兴趣自动绘制的标签画像。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {plan ? (
                  <>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                        <p className="text-xs text-slate-500">预算定位</p>
                        <p className="text-sm font-medium text-slate-800">
                          {plan.user_profile.budget_level.label ?? LEVEL_LABEL[plan.user_profile.budget_level.key]}
                        </p>
                        {plan.user_profile.budget_level.range && (
                          <p className="text-xs text-slate-500">{plan.user_profile.budget_level.range}</p>
                        )}
                      </div>
                      <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                        <p className="text-xs text-slate-500">旅行风格</p>
                        <p className="text-sm font-medium text-slate-800">
                          {plan.user_profile.travel_style
                            ? TRAVEL_STYLE_LABEL[plan.user_profile.travel_style] ?? plan.user_profile.travel_style
                            : "未指定"}
                        </p>
                        <p className="text-xs text-slate-500">
                          {plan.user_profile.preferences.weather_adaptive ? "天气自适应·" : ""}
                          {plan.user_profile.preferences.avoid_crowd ? "避开人群·" : ""}
                          {plan.user_profile.preferences.traffic_optimization ? "交通优化" : ""}
                        </p>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 mb-2">核心画像标签</p>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(plan.user_profile.tags)
                          .slice(0, 8)
                          .map(([tag, weight]) => (
                            <Badge key={tag} variant="outline" className="bg-slate-50">
                              {tag} {Math.round(weight * 100)}%
                            </Badge>
                          ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-slate-500">
                    生成方案后，会自动呈现用户画像标签，方便后续个性化调整。
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="w-5 h-5 text-green-500" />
                  备选方案
                </CardTitle>
                <CardDescription>
                  为天气、人流或预算变化预留的备用景点，可随时替换。
                </CardDescription>
              </CardHeader>
              <CardContent>
                {plan?.backup_options?.length ? (
                  <div className="space-y-3">
                    {plan.backup_options.map((option) => (
                      <div key={option.id} className="flex items-start justify-between gap-3 p-3 border rounded-lg">
                        <div>
                          <div className="font-medium text-slate-800">{option.name}</div>
                          <div className="text-xs text-slate-500 mb-1">
                            {option.district} · {option.category}
                          </div>
                          {option.reason.slice(0, 2).map((reason, index) => (
                            <p key={index} className="text-xs text-slate-500">
                              • {reason}
                            </p>
                          ))}
                        </div>
                        <Badge variant="secondary">匹配度 {option.score}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed border-slate-200 py-10 text-center text-sm text-slate-500">
                    智能备选将在生成主行程后自动提供，也可以后续接入更丰富的上海数据集。
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
