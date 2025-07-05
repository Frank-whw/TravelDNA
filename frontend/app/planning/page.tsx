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

export default function PlanningPage() {
  const [budget, setBudget] = useState([3000])
  const [duration, setDuration] = useState([3])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-50">
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
          {/* Planning Form */}
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
                {/* Destination */}
                <div className="space-y-2">
                  <Label htmlFor="destination">目的地</Label>
                  <Input id="destination" placeholder="输入城市或景点名称" />
                </div>

                {/* Date Range */}
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

                {/* Duration */}
                <div className="space-y-2">
                  <Label>旅行天数: {duration[0]} 天</Label>
                  <Slider value={duration} onValueChange={setDuration} max={14} min={1} step={1} className="w-full" />
                </div>

                {/* Budget */}
                <div className="space-y-2">
                  <Label>预算范围: ¥{budget[0]}</Label>
                  <Slider
                    value={budget}
                    onValueChange={setBudget}
                    max={10000}
                    min={500}
                    step={100}
                    className="w-full"
                  />
                </div>

                {/* Travel Style */}
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

                {/* Interests */}
                <div className="space-y-2">
                  <Label>兴趣标签</Label>
                  <div className="flex flex-wrap gap-2">
                    {["历史文化", "自然风光", "美食", "购物", "夜生活", "博物馆", "户外运动", "温泉"].map((tag) => (
                      <Badge key={tag} variant="outline" className="cursor-pointer hover:bg-blue-50">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Real-time Options */}
                <div className="space-y-4">
                  <Label>实时优化选项</Label>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">天气自适应</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">避开拥挤景点</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">交通优化</span>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>

                <Button className="w-full" size="lg">
                  生成智能方案
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results */}
          <div className="lg:col-span-2">
            <div className="space-y-6">
              {/* Real-time Status */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-blue-500" />
                    实时状况
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                      <Cloud className="w-8 h-8 text-blue-500" />
                      <div>
                        <div className="font-medium">天气</div>
                        <div className="text-sm text-gray-600">晴 22°C</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                      <Users className="w-8 h-8 text-green-500" />
                      <div>
                        <div className="font-medium">客流</div>
                        <div className="text-sm text-gray-600">适中</div>
                      </div>
                    </div>
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

              {/* Recommended Itinerary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Star className="w-5 h-5 text-yellow-500" />
                    推荐行程
                  </CardTitle>
                  <CardDescription>基于您的偏好和实时数据生成的个性化方案</CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="day1" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="day1">第1天</TabsTrigger>
                      <TabsTrigger value="day2">第2天</TabsTrigger>
                      <TabsTrigger value="day3">第3天</TabsTrigger>
                    </TabsList>

                    <TabsContent value="day1" className="space-y-4 mt-4">
                      <div className="space-y-4">
                        <div className="flex items-start gap-4 p-4 border rounded-lg">
                          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <Clock className="w-6 h-6 text-blue-600" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="font-medium">天安门广场</h3>
                              <Badge variant="secondary">09:00-11:00</Badge>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">参观天安门广场，感受首都的庄严与历史厚重感</p>
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

                    <TabsContent value="day2" className="space-y-4 mt-4">
                      <div className="text-center py-8 text-gray-500">第2天行程规划中...</div>
                    </TabsContent>

                    <TabsContent value="day3" className="space-y-4 mt-4">
                      <div className="text-center py-8 text-gray-500">第3天行程规划中...</div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>

              {/* Alternative Suggestions */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Plus className="w-5 h-5 text-green-500" />
                    备选方案
                  </CardTitle>
                  <CardDescription>根据实时情况的其他推荐</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">颐和园</div>
                        <div className="text-sm text-gray-600">如果故宫客流过多，推荐游览颐和园</div>
                      </div>
                      <Button variant="outline" size="sm">
                        替换
                      </Button>
                    </div>
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
