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

import { useState } from "react"
import { MapPin, Users, Clock, Cloud, Navigation, Star, Plus, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

/**
 * 智能规划页面主组件 - 旅游行程定制和生成
 * 
 * 状态管理：
 * - budget: 用户预算范围（数组格式适配Slider组件）
 * - duration: 旅行天数（数组格式）
 * 
 * 组件结构：
 * 1. Header - 顶部导航（品牌、导航菜单、我的行程）
 * 2. Planning Form - 左侧规划设置表单
 * 3. Results Panel - 右侧结果展示区域
 * 
 * @returns {JSX.Element} 完整的规划页面布局
 */
export default function PlanningPage() {
  /**
   * 预算状态 - 用户设定的旅行预算范围
   * @type {number[]} Slider组件要求的数组格式，[3000]表示默认3000元
   */
  const [budget, setBudget] = useState([3000])
  
  /**
   * 旅行天数状态 - 用户选择的行程总天数
   * @type {number[]} Slider组件格式，[3]表示默认3天
   */
  const [duration, setDuration] = useState([3])

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
            
            {/* 我的行程入口 */}
            <Button variant="outline">我的行程</Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Planning Form - 左侧规划设置表单 */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  规划设置
                </CardTitle>
                <CardDescription>告诉我们您的偏好，我们为您量身定制旅行方案</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Destination - 目的地输入 */}
                <div className="space-y-2">
                  <Label htmlFor="destination">目的地</Label>
                  <Input id="destination" placeholder="输入城市或景点名称" />
                </div>

                {/* Date Range - 日期范围选择 */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="start-date">出发日期</Label>
                    <Input id="start-date" type="date" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="end-date">返回日期</Label>
                    <Input id="end-date" type="date" />
                  </div>
                </div>

                {/* Duration - 旅行天数滑块 */}
                <div className="space-y-2">
                  <Label>旅行天数: {duration[0]} 天</Label>
                  {/* 滑块组件 - 1-14天范围选择 */}
                  <Slider value={duration} onValueChange={setDuration} max={14} min={1} step={1} className="w-full" />
                </div>

                {/* Budget - 预算范围滑块 */}
                <div className="space-y-2">
                  <Label>预算范围: ¥{budget[0]}</Label>
                  {/* 滑块组件 - 500-10000元范围选择 */}
                  <Slider
                    value={budget}
                    onValueChange={setBudget}
                    max={10000}
                    min={500}
                    step={100}
                    className="w-full"
                  />
                </div>

                {/* Travel Style - 旅行风格下拉选择 */}
                <div className="space-y-2">
                  <Label htmlFor="travel-style">旅行风格</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="选择您的旅行风格" />
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

                {/* Interests - 兴趣标签选择 */}
                <div className="space-y-2">
                  <Label>兴趣标签</Label>
                  {/* 标签网格 - 支持多选兴趣点 */}
                  <div className="flex flex-wrap gap-2">
                    {["历史文化", "自然风光", "美食", "购物", "夜生活", "博物馆", "户外运动", "温泉"].map((tag) => (
                      <Badge key={tag} variant="outline" className="cursor-pointer hover:bg-blue-50">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Real-time Options - 实时优化开关 */}
                <div className="space-y-4">
                  <Label>实时优化选项</Label>
                  <div className="space-y-3">
                    {/* 天气自适应开关 */}
                    <div className="flex items-center justify-between">
                      <span className="text-sm">天气自适应</span>
                      <Switch defaultChecked />
                    </div>
                    {/* 避开拥挤景点开关 */}
                    <div className="flex items-center justify-between">
                      <span className="text-sm">避开拥挤景点</span>
                      <Switch defaultChecked />
                    </div>
                    {/* 交通优化开关 */}
                    <div className="flex items-center justify-between">
                      <span className="text-sm">交通优化</span>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>

                {/* 生成方案按钮 - 触发AI规划算法 */}
                <Button className="w-full" size="lg">
                  生成智能方案
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results - 右侧结果展示区域 */}
          <div className="lg:col-span-2">
            <div className="space-y-6">
              {/* Real-time Status - 实时状况监控卡片 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-blue-500" />
                    实时状况
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {/* 状况指标网格 */}
                  <div className="grid md:grid-cols-3 gap-4">
                    {/* 天气状况 */}
                    <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                      <Cloud className="w-8 h-8 text-blue-500" />
                      <div>
                        <div className="font-medium">天气</div>
                        <div className="text-sm text-gray-600">晴 22°C</div>
                      </div>
                    </div>
                    {/* 客流状况 */}
                    <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                      <Users className="w-8 h-8 text-green-500" />
                      <div>
                        <div className="font-medium">客流</div>
                        <div className="text-sm text-gray-600">适中</div>
                      </div>
                    </div>
                    {/* 交通状况 */}
                    <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                      <Navigation className="w-8 h-8 text-purple-500" />
                      <div>
                        <div className="font-medium">交通</div>
                        <div className="text-sm text-gray-600">畅通</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recommended Itinerary - 推荐行程主要展示区 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Star className="w-5 h-5 text-yellow-500" />
                    推荐行程
                  </CardTitle>
                  <CardDescription>基于您的偏好和实时数据生成的个性化方案</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Tab组件 - 多日行程切换展示 */}
                  <Tabs defaultValue="day1" className="w-full">
                    {/* Tab导航 - 支持扩展更多天数 */}
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="day1">第1天</TabsTrigger>
                      <TabsTrigger value="day2">第2天</TabsTrigger>
                      <TabsTrigger value="day3">第3天</TabsTrigger>
                    </TabsList>

                    {/* 第1天行程内容 */}
                    <TabsContent value="day1" className="space-y-4 mt-4">
                      <div className="space-y-4">
                        {/* 天安门广场行程项 */}
                        <div className="flex items-start gap-4 p-4 border rounded-lg">
                          {/* 时间图标 */}
                          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <Clock className="w-6 h-6 text-blue-600" />
                          </div>
                          <div className="flex-1">
                            {/* 景点名称和时间 */}
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="font-medium">天安门广场</h3>
                              <Badge variant="secondary">09:00-11:00</Badge>
                            </div>
                            {/* 景点描述 */}
                            <p className="text-sm text-gray-600 mb-2">参观天安门广场，感受首都的庄严与历史厚重感</p>
                            {/* 实时状态标签 */}
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <Badge variant="outline" className="text-green-600">
                                客流适中
                              </Badge>
                              <Badge variant="outline" className="text-blue-600">
                                天气适宜
                              </Badge>
                            </div>
                          </div>
                        </div>

                        {/* 故宫博物院行程项 */}
                        <div className="flex items-start gap-4 p-4 border rounded-lg">
                          <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <MapPin className="w-6 h-6 text-green-600" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="font-medium">故宫博物院</h3>
                              <Badge variant="secondary">11:30-15:30</Badge>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">深度游览紫禁城，探索明清两代皇家宫殿的建筑艺术</p>
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <Badge variant="outline" className="text-green-600">
                                客流较少
                              </Badge>
                              <Badge variant="outline" className="text-blue-600">
                                推荐时段
                              </Badge>
                            </div>
                          </div>
                        </div>

                        {/* 王府井步行街行程项 */}
                        <div className="flex items-start gap-4 p-4 border rounded-lg">
                          <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <Star className="w-6 h-6 text-orange-600" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="font-medium">王府井步行街</h3>
                              <Badge variant="secondary">16:00-19:00</Badge>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">品尝北京小吃，购买特色纪念品，体验老北京文化</p>
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <Badge variant="outline" className="text-yellow-600">
                                美食推荐
                              </Badge>
                              <Badge variant="outline" className="text-purple-600">
                                购物
                              </Badge>
                            </div>
                          </div>
                        </div>
                      </div>
                    </TabsContent>

                    {/* 第2天和第3天占位内容 */}
                    <TabsContent value="day2" className="space-y-4 mt-4">
                      <div className="text-center py-8 text-gray-500">第2天行程规划中...</div>
                    </TabsContent>

                    <TabsContent value="day3" className="space-y-4 mt-4">
                      <div className="text-center py-8 text-gray-500">第3天行程规划中...</div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>

              {/* Alternative Suggestions - 备选方案推荐 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Plus className="w-5 h-5 text-green-500" />
                    备选方案
                  </CardTitle>
                  <CardDescription>根据实时情况的其他推荐</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* 备选建议列表 */}
                  <div className="space-y-3">
                    {/* 颐和园替换方案 */}
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">颐和园</div>
                        <div className="text-sm text-gray-600">如果故宫客流过多，推荐游览颐和园</div>
                      </div>
                      <Button variant="outline" size="sm">
                        替换
                      </Button>
                    </div>
                    {/* 室内博物馆替换方案 */}
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">室内博物馆</div>
                        <div className="text-sm text-gray-600">如果天气转雨，推荐国家博物馆</div>
                      </div>
                      <Button variant="outline" size="sm">
                        替换
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
