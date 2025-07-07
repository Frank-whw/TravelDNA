/**
 * Card UI组件库 - 卡片容器组件系统
 * 
 * 功能概述：
 * - 提供结构化的卡片布局容器
 * - 支持头部、内容、底部的语义化分区
 * - 统一的阴影、边框、圆角设计规范
 * - 响应式和可访问的内容组织
 * 
 * 设计思路：
 * - 基于语义化HTML结构的组件拆分
 * - 灵活的组合模式，支持任意组件组合
 * - 一致的间距和视觉层次系统
 * - 与设计系统色彩和字体规范集成
 * 
 * 技术架构：
 * - React.forwardRef支持ref传递和组合
 * - TypeScript类型安全的属性继承
 * - Tailwind CSS实用类的语义化封装
 * - cn工具函数支持样式扩展和覆盖
 * 
 * 组件组合：
 * - Card: 主容器，提供边框、阴影、背景
 * - CardHeader: 头部区域，通常包含标题和描述
 * - CardTitle: 卡片标题，语义化h3级别标题
 * - CardDescription: 卡片描述，次要信息展示
 * - CardContent: 主要内容区域，支持任意内容
 * - CardFooter: 底部区域，通常包含操作按钮
 * 
 * 使用场景：
 * - 产品/服务展示卡片
 * - 统计数据面板
 * - 表单分组容器
 * - 文章预览卡片
 * - 用户信息展示
 */

import * as React from "react"

import { cn } from "@/lib/utils"

/**
 * Card主容器组件 - 卡片的根容器元素
 * 
 * 样式特性：
 * - rounded-lg: 大圆角符合现代设计趋势
 * - border: 细边框提供视觉边界
 * - bg-card: 使用设计系统的卡片背景色
 * - text-card-foreground: 卡片专用文字色，确保对比度
 * - shadow-sm: 小阴影提供层次感，不干扰内容
 * 
 * @param {React.HTMLAttributes<HTMLDivElement>} props - 标准div属性
 * @param {string} props.className - 自定义样式类名
 * @param {React.Ref<HTMLDivElement>} ref - DOM元素引用
 * 
 * @returns {JSX.Element} 卡片容器元素
 * 
 * @example
 * <Card className="w-full max-w-md">
 *   <CardContent>
 *     <p>基础卡片内容</p>
 *   </CardContent>
 * </Card>
 */
const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

/**
 * CardHeader头部组件 - 卡片头部内容容器
 * 
 * 布局特性：
 * - flex flex-col: 垂直弹性布局，标题描述垂直排列
 * - space-y-1.5: 子元素间垂直间距，保持紧凑但可读
 * - p-6: 标准内边距，与卡片整体间距系统一致
 * 
 * 语义化：
 * - 作为header角色，包含卡片的标题和元信息
 * - 通常包含CardTitle和CardDescription组件
 * 
 * @param {React.HTMLAttributes<HTMLDivElement>} props - 标准div属性
 * @param {React.Ref<HTMLDivElement>} ref - DOM元素引用
 * 
 * @example
 * <CardHeader>
 *   <CardTitle>卡片标题</CardTitle>
 *   <CardDescription>卡片描述信息</CardDescription>
 * </CardHeader>
 */
const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

/**
 * CardTitle标题组件 - 卡片主标题元素
 * 
 * 字体样式：
 * - text-2xl: 大字号突出标题重要性
 * - font-semibold: 半粗字体，既突出又不过重
 * - leading-none: 紧凑行高，避免标题过高
 * - tracking-tight: 微调字母间距，提升视觉紧凑度
 * 
 * 语义化：
 * - 使用div而非h标签，避免SEO层级混乱
 * - 在卡片上下文中提供标题语义
 * 
 * @param {React.HTMLAttributes<HTMLDivElement>} props - 标准div属性
 * @param {React.Ref<HTMLDivElement>} ref - DOM元素引用
 * 
 * @example
 * <CardTitle>产品名称</CardTitle>
 */
const CardTitle = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

/**
 * CardDescription描述组件 - 卡片描述文本
 * 
 * 样式特点：
 * - text-sm: 小字号，次要信息的视觉层次
 * - text-muted-foreground: 静音文字色，降低视觉权重
 * 
 * 用途：
 * - 提供卡片内容的简短描述
 * - 显示次要信息如时间、作者、分类等
 * - 补充标题信息，增强内容理解
 * 
 * @param {React.HTMLAttributes<HTMLDivElement>} props - 标准div属性
 * @param {React.Ref<HTMLDivElement>} ref - DOM元素引用
 * 
 * @example
 * <CardDescription>
 *   这是一个产品的详细描述信息，提供更多背景内容。
 * </CardDescription>
 */
const CardDescription = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

/**
 * CardContent内容组件 - 卡片主要内容区域
 * 
 * 布局特点：
 * - p-6: 与header一致的内边距，保持视觉连续性
 * - pt-0: 顶部无内边距，避免与header重复间距
 * 
 * 功能：
 * - 承载卡片的主要内容，如文本、图片、表单等
 * - 提供标准的内容间距，确保内容可读性
 * - 支持任意子组件和内容类型
 * 
 * @param {React.HTMLAttributes<HTMLDivElement>} props - 标准div属性
 * @param {React.Ref<HTMLDivElement>} ref - DOM元素引用
 * 
 * @example
 * <CardContent>
 *   <p>这里是卡片的主要内容...</p>
 *   <img src="image.jpg" alt="描述" />
 * </CardContent>
 */
const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

/**
 * CardFooter底部组件 - 卡片底部操作区域
 * 
 * 布局特性：
 * - flex items-center: 水平弹性布局，内容垂直居中
 * - p-6 pt-0: 与content一致的边距处理
 * 
 * 使用场景：
 * - 放置操作按钮（确认、取消、更多等）
 * - 显示状态信息或标签
 * - 提供额外的元数据或链接
 * 
 * @param {React.HTMLAttributes<HTMLDivElement>} props - 标准div属性
 * @param {React.Ref<HTMLDivElement>} ref - DOM元素引用
 * 
 * @example
 * <CardFooter>
 *   <Button variant="outline" className="mr-2">取消</Button>
 *   <Button>确认</Button>
 * </CardFooter>
 */
const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

/**
 * 导出所有Card相关组件
 * 
 * 组合使用示例：
 * 
 * @example
 * // 完整的卡片结构
 * <Card className="w-[350px]">
 *   <CardHeader>
 *     <CardTitle>创建项目</CardTitle>
 *     <CardDescription>
 *       一键部署新项目，快速开始开发工作。
 *     </CardDescription>
 *   </CardHeader>
 *   <CardContent>
 *     <form>
 *       <div className="grid w-full items-center gap-4">
 *         <Label htmlFor="name">项目名称</Label>
 *         <Input id="name" placeholder="输入项目名称" />
 *       </div>
 *     </form>
 *   </CardContent>
 *   <CardFooter className="flex justify-between">
 *     <Button variant="outline">取消</Button>
 *     <Button>创建</Button>
 *   </CardFooter>
 * </Card>
 * 
 * @example
 * // 简化的信息卡片
 * <Card>
 *   <CardHeader>
 *     <CardTitle>统计数据</CardTitle>
 *   </CardHeader>
 *   <CardContent>
 *     <div className="text-2xl font-bold">1,234</div>
 *     <p className="text-xs text-muted-foreground">
 *       比上月增长 +20.1%
 *     </p>
 *   </CardContent>
 * </Card>
 */
export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
