"use client"

import { useState } from "react"
import { MapPin, Cloud, Users, Navigation, MessageCircle, Sparkles, TrendingUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                <MapPin className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                知旅
              </span>
            </div>
            <nav className="hidden md:flex items-center space-x-6">
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">
                智能规划
              </a>
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">
                AI问答
              </a>
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">
                社区
              </a>
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">
                我的
              </a>
            </nav>
            <div className="flex items-center space-x-2">
              <Button variant="ghost">登录</Button>
              <Button>注册</Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
              智能旅游规划
            </span>
            <br />
            <span className="text-gray-800">让每次出行都完美</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            融合实时天气、客流、交通数据，提供个性化旅游推荐。AI问答助手随时为您解答旅行疑问。
          </p>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto mb-12">
            <div className="relative">
              <Input
                placeholder="想去哪里？输入目的地开始规划..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-14 text-lg pl-6 pr-32 rounded-full border-2 border-blue-200 focus:border-blue-400"
              />
              <Button className="absolute right-2 top-2 h-10 px-6 rounded-full">开始规划</Button>
            </div>
          </div>

          {/* Feature Cards */}
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-6 h-6 text-blue-600" />
                </div>
                <CardTitle className="text-blue-600">智能推荐</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">基于个人喜好和实时数据，提供千人千面的个性化旅游方案</p>
              </CardContent>
            </Card>

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

      {/* Real-time Data Section */}
      <section className="py-16 px-4 bg-white">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">实时数据驱动的智能决策</h2>

          <Tabs defaultValue="weather" className="max-w-4xl mx-auto">
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
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">22°C</div>
                      <div className="text-sm text-gray-600">北京 晴</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">26°C</div>
                      <div className="text-sm text-gray-600">上海 多云</div>
                    </div>
                    <div className="text-center p-4 bg-orange-50 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">28°C</div>
                      <div className="text-sm text-gray-600">广州 小雨</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

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
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <span className="font-medium">故宫博物院</span>
                      <Badge variant="secondary" className="bg-green-100 text-green-700">
                        客流较少
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                      <span className="font-medium">天安门广场</span>
                      <Badge variant="secondary" className="bg-yellow-100 text-yellow-700">
                        客流适中
                      </Badge>
                    </div>
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
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <div>
                        <div className="font-medium">机场快线</div>
                        <div className="text-sm text-gray-600">预计25分钟</div>
                      </div>
                      <Badge className="bg-green-500">畅通</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                      <div>
                        <div className="font-medium">地铁1号线</div>
                        <div className="text-sm text-gray-600">预计35分钟</div>
                      </div>
                      <Badge className="bg-yellow-500">缓慢</Badge>
                    </div>
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
