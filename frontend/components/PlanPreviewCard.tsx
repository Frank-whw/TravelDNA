/**
 * 方案预览卡片组件
 * 在聊天界面中展示可点击的攻略卡片
 */
"use client"

import { useState } from "react"
import { Calendar, MapPin, Clock, Users, DollarSign, Sparkles, ChevronRight, Edit2, Heart, Share2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

interface PlanPreviewCardProps {
  title?: string
  days?: number
  budget?: string
  highlights?: string[]
  description?: string
  onViewPlan?: () => void
  onEditPlan?: () => void
  className?: string
}

export default function PlanPreviewCard({
  title = "我的旅行计划",
  days = 3,
  budget,
  highlights = [],
  description,
  onViewPlan,
  onEditPlan,
  className = ""
}: PlanPreviewCardProps) {
  const [isLiked, setIsLiked] = useState(false)

  return (
    <Card className={`bg-gradient-to-br from-white via-blue-50/30 to-indigo-50/30 border-2 border-blue-200 shadow-lg hover:shadow-xl transition-all duration-300 ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-500" />
              {title}
            </CardTitle>
            <CardDescription className="text-sm text-gray-600">
              {description || "精心为你定制的旅行方案"}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full hover:bg-red-50"
              onClick={() => setIsLiked(!isLiked)}
            >
              <Heart className={`w-4 h-4 ${isLiked ? 'fill-red-500 text-red-500' : 'text-gray-400'}`} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full hover:bg-blue-50"
            >
              <Share2 className="w-4 h-4 text-gray-400" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* 关键信息 */}
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="w-4 h-4 text-blue-500" />
            <span className="text-gray-700 font-medium">{days}天行程</span>
          </div>
          {budget && (
            <div className="flex items-center gap-2 text-sm">
              <DollarSign className="w-4 h-4 text-green-500" />
              <span className="text-gray-700 font-medium">{budget}</span>
            </div>
          )}
        </div>

        {/* 核心亮点 */}
        {highlights.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-gray-600 uppercase tracking-wide">核心亮点</div>
            <div className="flex flex-wrap gap-2">
              {highlights.slice(0, 4).map((highlight, idx) => (
                <Badge
                  key={idx}
                  variant="secondary"
                  className="bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 border border-blue-200 text-xs px-3 py-1 rounded-full"
                >
                  {highlight}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex gap-2 pt-2 border-t border-gray-200">
          <Button
            onClick={onViewPlan}
            className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg shadow-md transition-all transform hover:scale-105"
          >
            <span className="text-sm font-medium">查看完整方案</span>
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
          {onEditPlan && (
            <Button
              variant="outline"
              onClick={onEditPlan}
              className="px-4 border-2 border-blue-300 hover:bg-blue-50 rounded-lg"
            >
              <Edit2 className="w-4 h-4 text-blue-600" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

