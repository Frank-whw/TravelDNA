/**
 * 知旅主页组件 - 应用入口页面和功能展示
 * 
 * 功能概述：
 * - 展示应用品牌形象和核心价值主张
 * - 提供旅游目的地搜索入口
 * - 展示三大核心功能：智能推荐、实时优化、AI问答
 * - 实时数据展示（天气、客流、交通）
 * 
 * 设计思路：
 * - 采用渐变色和现代化设计语言，体现科技感
 * - 分区块展示，结构清晰易于用户理解
 * - 响应式设计，适配移动端和桌面端
 * - 交互式Tab组件展示实时数据
 * 
 * 技术架构：
 * - Next.js 13+ App Router客户端组件
 * - React Hooks状态管理
 * - Tailwind CSS响应式布局
 * - Lucide React图标库
 * - Shadcn/ui组件库
 * 
 * 数据流向：
 * - 搜索查询状态本地管理
 * - 实时数据展示为静态示例（待接入后端API）
 * - 导航链接为静态路由
 */

"use client"

import { useState } from "react"
import { MapPin, Cloud, Users, Navigation, MessageCircle, Sparkles, TrendingUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

/**
 * 主页组件 - 知旅应用的首页展示
 * 
 * 状态管理：
 * - searchQuery: 用户输入的搜索关键词
 * 
 * 组件结构：
 * 1. Header - 顶部导航栏（品牌、导航菜单、登录注册）
 * 2. Hero Section - 英雄区（标题、描述、搜索框、特色卡片）
 * 3. Real-time Data Section - 实时数据展示区（Tab切换展示）
 * 
 * @returns {JSX.Element} 主页完整布局
 */
export default function HomePage() {
  /**
   * 搜索查询状态 - 用户输入的目的地关键词
   * @type {string} 当前搜索输入值
   */
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Header - 顶部导航栏 */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* 品牌标识区域 */}
            <div className="flex items-center space-x-2">
              {/* 品牌图标 - 渐变色地图标志 */}
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                <MapPin className="w-5 h-5 text-white" />
              </div>
              {/* 品牌名称 - 渐变文字效果 */}
              <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                知旅
              </span>
            </div>
            
            {/* 主导航菜单 - 隐藏在移动端 */}
            <nav className="hidden md:flex items-center space-x-6">
              <a href="planning" className="text-gray-600 hover:text-blue-600 transition-colors">
                智能规划
              </a>
              <a href="chat" className="text-gray-600 hover:text-blue-600 transition-colors">
                AI问答
              </a>
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">
                社区
              </a>
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">
                我的
              </a>
            </nav>
            
            {/* 用户操作区域 */}
            <div className="flex items-center space-x-2">
              <Button variant="ghost">登录</Button>
              <Button>注册</Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section - 主要展示区域 */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          {/* 主标题区域 - 渐变文字和品牌宣传 */}
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
              智能旅游规划
            </span>
            <br />
            <span className="text-gray-800">让每次出行都完美</span>
          </h1>
          
          {/* 产品描述 - 简洁明了的价值主张 */}
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            融合实时天气、客流、交通数据，提供个性化旅游推荐。AI问答助手随时为您解答旅行疑问。
          </p>

          {/* Search Bar - 搜索功能入口 */}
          <div className="max-w-2xl mx-auto mb-12">
            <div className="relative">
              {/* 搜索输入框 - 支持键盘事件和状态同步 */}
              <Input
                placeholder="想去哪里？输入目的地开始规划..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-14 text-lg pl-6 pr-32 rounded-full border-2 border-blue-200 focus:border-blue-400"
              />
              {/* 搜索按钮 - 绝对定位在输入框右侧 */}
              <Button className="absolute right-2 top-2 h-10 px-6 rounded-full">开始规划</Button>
            </div>
          </div>

          {/* Feature Cards - 核心功能特色展示 */}
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {/* 智能推荐功能卡片 */}
            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader className="text-center">
                {/* 功能图标 - 圆形背景突出视觉效果 */}
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-6 h-6 text-blue-600" />
                </div>
                <CardTitle className="text-blue-600">智能推荐</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">基于个人喜好和实时数据，提供千人千面的个性化旅游方案</p>
              </CardContent>
            </Card>

            {/* 实时优化功能卡片 */}
            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                </div>
                <CardTitle className="text-green-600">实时优化</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">动态调整行程安排，考虑天气变化、景点客流和交通状况</p>
              </CardContent>
            </Card>

            {/* AI问答功能卡片 */}
            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MessageCircle className="w-6 h-6 text-purple-600" />
                </div>
                <CardTitle className="text-purple-600">AI问答</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">RAG技术驱动的智能助手，随时解答您的旅行疑问</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Real-time Data Section - 实时数据驱动决策展示 */}
      <section className="py-16 px-4 bg-white">
        <div className="container mx-auto">
          {/* 章节标题 */}
          <h2 className="text-3xl font-bold text-center mb-12">实时数据驱动的智能决策</h2>

          {/* Tab组件 - 切换展示不同类型的实时数据 */}
          <Tabs defaultValue="weather" className="max-w-4xl mx-auto">
            {/* Tab导航列表 - 三个数据类型选项 */}
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="weather" className="flex items-center gap-2">
                <Cloud className="w-4 h-4" />
                天气数据
              </TabsTrigger>
              <TabsTrigger value="crowd" className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                客流分析
              </TabsTrigger>
              <TabsTrigger value="traffic" className="flex items-center gap-2">
                <Navigation className="w-4 h-4" />
                交通状况
              </TabsTrigger>
            </TabsList>

            {/* 天气数据展示面板 */}
            <TabsContent value="weather" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cloud className="w-5 h-5 text-blue-500" />
                    实时天气监控
                  </CardTitle>
                  <CardDescription>通过API获取准确天气数据，智能调整户外活动安排</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* 多城市天气展示网格 */}
                  <div className="grid md:grid-cols-3 gap-4">
                    {/* 北京天气卡片 */}
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">22°C</div>
                      <div className="text-sm text-gray-600">北京 晴</div>
                    </div>
                    {/* 上海天气卡片 */}
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">26°C</div>
                      <div className="text-sm text-gray-600">上海 多云</div>
                    </div>
                    {/* 广州天气卡片 */}
                    <div className="text-center p-4 bg-orange-50 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">28°C</div>
                      <div className="text-sm text-gray-600">广州 小雨</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 客流分析展示面板 */}
            <TabsContent value="crowd" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-green-500" />
                    客流预测分析
                  </CardTitle>
                  <CardDescription>基于历史数据的时间序列分析，预测景点客流密度</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* 景点客流状态列表 */}
                  <div className="space-y-4">
                    {/* 故宫客流状态 - 较少 */}
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <span className="font-medium">故宫博物院</span>
                      <Badge variant="secondary" className="bg-green-100 text-green-700">
                        客流较少
                      </Badge>
                    </div>
                    {/* 天安门客流状态 - 适中 */}
                    <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                      <span className="font-medium">天安门广场</span>
                      <Badge variant="secondary" className="bg-yellow-100 text-yellow-700">
                        客流适中
                      </Badge>
                    </div>
                    {/* 颐和园客流状态 - 拥挤 */}
                    <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                      <span className="font-medium">颐和园</span>
                      <Badge variant="secondary" className="bg-red-100 text-red-700">
                        客流拥挤
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 交通状况展示面板 */}
            <TabsContent value="traffic" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Navigation className="w-5 h-5 text-purple-500" />
                    交通状况监控
                  </CardTitle>
                  <CardDescription>实时获取地图交通数据，优化出行路线</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* 交通线路状态列表 */}
                  <div className="space-y-4">
                    {/* 机场快线 - 畅通 */}
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <div>
                        <div className="font-medium">机场快线</div>
                        <div className="text-sm text-gray-600">预计25分钟</div>
                      </div>
                      <Badge className="bg-green-500">畅通</Badge>
                    </div>
                    {/* 地铁1号线 - 缓慢 */}
                    <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                      <div>
                        <div className="font-medium">地铁1号线</div>
                        <div className="text-sm text-gray-600">预计35分钟</div>
                      </div>
                      <Badge className="bg-yellow-500">缓慢</Badge>
                    </div>
                    {/* 三环路 - 拥堵 */}
                    <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                      <div>
                        <div className="font-medium">三环路</div>
                        <div className="text-sm text-gray-600">预计50分钟</div>
                      </div>
                      <Badge className="bg-red-500">拥堵</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </section>
    </div>
  )
}
