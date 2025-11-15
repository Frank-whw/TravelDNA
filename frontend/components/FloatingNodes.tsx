/**
 * 游离节点可视化组件 - 重新设计，更大气美观
 * 展示Agent思考过程中的关键信息
 */
"use client"

import { useEffect, useRef, useState } from "react"
import { MapPin, Users, Calendar, DollarSign, Heart, Sparkles, Tag } from "lucide-react"

interface Node {
  id: string
  text: string
  type: 'keyword' | 'location' | 'activity' | 'budget' | 'date' | 'preference' | 'person'
  x: number
  y: number
  vx: number
  vy: number
  size: number
  opacity: number
}

interface FloatingNodesProps {
  extractedInfo?: any
  keywords?: string[]
  className?: string
}

const nodeIcons = {
  keyword: Tag,
  location: MapPin,
  activity: Sparkles,
  budget: DollarSign,
  date: Calendar,
  preference: Heart,
  person: Users
}

const nodeGradients = {
  keyword: 'from-blue-500 to-cyan-500',
  location: 'from-green-500 to-emerald-500',
  activity: 'from-purple-500 to-pink-500',
  budget: 'from-yellow-500 to-orange-500',
  date: 'from-pink-500 to-rose-500',
  preference: 'from-red-500 to-rose-500',
  person: 'from-indigo-500 to-blue-500'
}

export default function FloatingNodes({ extractedInfo, keywords = [], className = "" }: FloatingNodesProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const animationFrameRef = useRef<number>()
  const nodesRef = useRef<Node[]>([])
  const [nodes, setNodes] = useState<Node[]>([])

  // 从extractedInfo中提取节点数据，只显示有效地点
  useEffect(() => {
    const newNodes: Node[] = []
    let nodeId = 0

    // 优先从enhanced_locations提取完整景点信息
    if (extractedInfo?.enhanced_locations && Array.isArray(extractedInfo.enhanced_locations)) {
      extractedInfo.enhanced_locations.forEach((enhancedLoc: any) => {
        if (enhancedLoc.suggestions && Array.isArray(enhancedLoc.suggestions)) {
          enhancedLoc.suggestions.slice(0, 3).forEach((suggestion: any) => {
            const name = suggestion.name || suggestion
            if (name && name.trim().length > 1 && !/^\d+$/.test(name.trim())) {
              // 使用完整的景点名称
              const displayText = suggestion.address 
                ? `${name}（${suggestion.address}）` 
                : name
              newNodes.push(createNode(nodeId++, displayText.trim(), 'location'))
            }
          })
        }
      })
    }

    // 如果没有enhanced_locations，则从locations提取
    if (newNodes.filter(n => n.type === 'location').length === 0 && 
        extractedInfo?.locations && Array.isArray(extractedInfo.locations)) {
      extractedInfo.locations
        .filter((loc: any) => {
          const locText = typeof loc === 'string' ? loc : loc.name || loc
          // 过滤掉纯数字、单个字符、无效地点
          return locText && 
                 locText.trim().length > 1 && 
                 !/^\d+$/.test(locText.trim()) &&
                 !locText.includes('%') &&
                 !locText.includes('会议中心')
        })
        .slice(0, 8)
        .forEach((location: any) => {
          const locText = typeof location === 'string' ? location : location.name || location
          if (locText && locText.trim()) {
            newNodes.push(createNode(nodeId++, locText.trim(), 'location'))
          }
        })
    }

    // 提取关键词（过滤无效关键词）
    if (keywords && keywords.length > 0) {
      keywords
        .filter((kw: string) => kw && kw.trim().length > 1 && !/^\d+$/.test(kw.trim()))
        .slice(0, 12)
        .forEach((keyword: string) => {
          newNodes.push(createNode(nodeId++, keyword.trim(), 'keyword'))
        })
    }

    // 提取活动类型
    if (extractedInfo?.activity_types && Array.isArray(extractedInfo.activity_types)) {
      extractedInfo.activity_types.slice(0, 4).forEach((activity: string) => {
        if (activity && activity.trim()) {
          newNodes.push(createNode(nodeId++, activity.trim(), 'activity'))
        }
      })
    }

    // 提取预算信息
    if (extractedInfo?.budget_info) {
      const budget = extractedInfo.budget_info
      if (budget.amount) {
        newNodes.push(createNode(nodeId++, `预算${budget.amount}元`, 'budget'))
      }
    }

    // 提取旅行天数
    if (extractedInfo?.travel_days) {
      newNodes.push(createNode(nodeId++, `${extractedInfo.travel_days}天行程`, 'date'))
    }

    nodesRef.current = newNodes
    setNodes(newNodes)
  }, [extractedInfo, keywords])

  // 创建节点
  function createNode(id: number, text: string, type: Node['type']): Node {
    const container = containerRef.current
    const width = container?.clientWidth || 600
    const height = container?.clientHeight || 400

    return {
      id: `node-${id}`,
      text: text.length > 15 ? text.substring(0, 15) + '...' : text,
      type,
      x: Math.random() * (width - 150) + 75,
      y: Math.random() * (height - 80) + 40,
      vx: (Math.random() - 0.5) * 0.8,
      vy: (Math.random() - 0.5) * 0.8,
      size: Math.max(80, Math.min(140, text.length * 7 + 60)),
      opacity: 0.9 + Math.random() * 0.1
    }
  }

  // 动画循环
  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return

    const animate = () => {
      const container = containerRef.current
      if (!container) return

      const width = container.clientWidth
      const height = container.clientHeight

      setNodes((prevNodes) => {
        return prevNodes.map((node) => {
          let { x, y, vx, vy } = node

          // 更新位置
          x += vx
          y += vy

          // 边界碰撞检测
          if (x <= 0 || x >= width - node.size) {
            vx = -vx * 0.9
            x = Math.max(0, Math.min(width - node.size, x))
          }
          if (y <= 0 || y >= height - 60) {
            vy = -vy * 0.9
            y = Math.max(0, Math.min(height - 60, y))
          }

          // 添加轻微的随机扰动
          vx += (Math.random() - 0.5) * 0.03
          vy += (Math.random() - 0.5) * 0.03

          // 限制速度
          vx = Math.max(-1.2, Math.min(1.2, vx))
          vy = Math.max(-1.2, Math.min(1.2, vy))

          return { ...node, x, y, vx, vy }
        })
      })

      animationFrameRef.current = requestAnimationFrame(animate)
    }

    animationFrameRef.current = requestAnimationFrame(animate)

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [nodes.length])

  if (nodes.length === 0) return null

  return (
    <div 
      ref={containerRef}
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/30 border-2 border-blue-200/50 shadow-2xl backdrop-blur-sm ${className}`}
      style={{ minHeight: '300px', height: '100%' }}
    >
      {/* 背景装饰 - 更大气 */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-0 left-0 w-64 h-64 bg-blue-400 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-0 w-80 h-80 bg-purple-400 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 w-48 h-48 bg-pink-400 rounded-full blur-2xl animate-pulse delay-500"></div>
      </div>

      {/* 节点 */}
      {nodes.map((node) => {
        const Icon = nodeIcons[node.type]
        const gradient = nodeGradients[node.type]
        
        return (
          <div
            key={node.id}
            className="absolute flex items-center gap-3 px-5 py-3 rounded-2xl border-2 backdrop-blur-md transition-all duration-500 hover:scale-110 hover:shadow-2xl cursor-pointer group"
            style={{
              left: `${node.x}px`,
              top: `${node.y}px`,
              minWidth: `${node.size}px`,
              opacity: node.opacity,
              transform: 'translateZ(0)',
              background: `linear-gradient(135deg, var(--tw-gradient-stops))`,
              borderColor: 'rgba(255, 255, 255, 0.3)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
            }}
            title={node.text}
          >
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform`}>
              <Icon className="w-5 h-5" />
            </div>
            <span className="text-base font-bold text-gray-800 whitespace-nowrap drop-shadow-sm">
              {node.text}
            </span>
          </div>
        )
      })}
    </div>
  )
}
