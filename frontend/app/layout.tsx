/**
 * 知旅应用根布局组件 - Next.js 13+ App Router架构
 * 
 * 功能概述：
 * - 定义整个应用的HTML结构和全局样式
 * - 配置SEO元数据和字体加载
 * - 提供统一的页面布局容器
 * 
 * 设计思路：
 * - 采用Next.js App Router的布局嵌套机制
 * - 使用Google Fonts的Inter字体提升用户体验
 * - 设置中文语言环境优化搜索引擎收录
 * 
 * 关键依赖：
 * - Next.js 13+ App Router
 * - Google Fonts Inter字体
 * - 全局CSS样式（globals.css）
 */

import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

/**
 * Inter字体配置 - Google Fonts优化加载
 * subsets: ["latin"] - 仅加载拉丁字符集，减少字体文件大小
 */
const inter = Inter({ subsets: ["latin"] })

/**
 * 应用元数据配置 - SEO优化设置
 * @type {Metadata} Next.js元数据对象
 */
export const metadata: Metadata = {
  title: "知旅 - 智能旅游规划平台",
  description: "融合多源数据的动态旅游推荐平台，提供个性化旅游方案、AI问答和实时优化服务",
    generator: 'v0.dev'
}

/**
 * 根布局组件 - 应用最外层的布局容器
 * 
 * @param {Object} props - 组件属性
 * @param {React.ReactNode} props.children - 子组件内容（所有页面都会渲染在此处）
 * @returns {JSX.Element} 根HTML结构
 * 
 * 注意事项：
 * - lang="zh-CN" 设置中文语言环境，有助于SEO和屏幕阅读器
 * - Inter字体通过className应用到body元素
 * - 所有页面组件都会作为children渲染
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
