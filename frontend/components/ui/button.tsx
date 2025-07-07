/**
 * Button UI组件 - 通用按钮组件系统
 * 
 * 功能概述：
 * - 提供统一的按钮样式和交互行为
 * - 支持多种视觉变体（默认、危险、轮廓、次要等）
 * - 灵活的尺寸系统（小、默认、大、图标）
 * - 完整的可访问性支持和键盘导航
 * 
 * 设计系统：
 * - 基于CVA（Class Variance Authority）的变体管理
 * - 支持asChild模式实现多态组件
 * - 遵循Radix UI的可访问性标准
 * - 集成Tailwind CSS响应式和状态样式
 * 
 * 技术架构：
 * - React.forwardRef支持ref传递
 * - TypeScript严格类型检查
 * - Radix UI Slot组件支持组合模式
 * - CVA变体配置系统
 * 
 * 可访问性特性：
 * - 焦点环显示和键盘导航
 * - 禁用状态的正确ARIA属性
 * - 屏幕阅读器友好的语义标记
 * - 触摸设备友好的点击区域
 */

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * 按钮变体配置 - 使用CVA定义所有样式变体
 * 
 * 基础样式：
 * - inline-flex: 内联弹性布局，支持图标文字组合
 * - items-center justify-center: 内容垂直水平居中
 * - gap-2: 图标与文字间距
 * - whitespace-nowrap: 防止文字换行
 * - rounded-md: 中等圆角符合设计系统
 * - ring-offset-background: 焦点环偏移背景色
 * - transition-colors: 颜色过渡动画
 * - focus-visible: 仅键盘导航显示焦点环
 * - disabled: 禁用状态样式
 * - [&_svg]: SVG图标专用样式
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      /**
       * 视觉变体定义 - 不同的按钮样式类型
       */
      variant: {
        // 默认主要按钮 - 品牌色背景，高对比度
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        
        // 危险操作按钮 - 警告色，用于删除等危险操作
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
          
        // 轮廓按钮 - 边框样式，次要操作
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
          
        // 次要按钮 - 低对比度背景
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
          
        // 幽灵按钮 - 透明背景，悬停显示
        ghost: "hover:bg-accent hover:text-accent-foreground",
        
        // 链接样式按钮 - 文字链接外观
        link: "text-primary underline-offset-4 hover:underline",
      },
      
      /**
       * 尺寸变体定义 - 不同的按钮大小
       */
      size: {
        // 默认尺寸 - 标准按钮高度和内边距
        default: "h-10 px-4 py-2",
        
        // 小尺寸 - 紧凑布局使用
        sm: "h-9 rounded-md px-3",
        
        // 大尺寸 - 重要操作或移动端友好
        lg: "h-11 rounded-md px-8",
        
        // 图标按钮 - 正方形，仅包含图标
        icon: "h-10 w-10",
      },
    },
    
    /**
     * 默认变体值 - 未指定时的fallback选项
     */
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

/**
 * Button组件属性接口 - 扩展HTML button属性
 * 
 * @interface ButtonProps
 * @extends {React.ButtonHTMLAttributes<HTMLButtonElement>} 继承原生button属性
 * @extends {VariantProps<typeof buttonVariants>} 继承CVA变体属性
 */
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /**
   * asChild模式 - 将样式应用到子元素而非button元素
   * @type {boolean} 默认false，启用时需要子元素支持所有button属性
   * 
   * 使用场景：
   * - <Button asChild><Link href="/path">链接按钮</Link></Button>
   * - 将按钮样式应用到其他可交互元素
   */
  asChild?: boolean
}

/**
 * Button组件 - 可复用的按钮组件
 * 
 * @param {ButtonProps} props - 组件属性
 * @param {string} props.className - 自定义CSS类名，会与变体样式合并
 * @param {string} props.variant - 按钮变体类型
 * @param {string} props.size - 按钮尺寸
 * @param {boolean} props.asChild - 是否为子元素模式
 * @param {React.Ref<HTMLButtonElement>} ref - 按钮元素引用
 * 
 * @returns {JSX.Element} 渲染的按钮组件
 * 
 * 实现特点：
 * - 使用forwardRef支持ref传递，便于表单集成
 * - Slot组件实现多态，asChild模式下渲染子元素
 * - cn函数智能合并类名，支持自定义样式覆盖
 * - 完整的TypeScript类型支持
 * 
 * @example
 * // 基础用法
 * <Button>点击我</Button>
 * 
 * @example  
 * // 危险操作按钮
 * <Button variant="destructive" size="sm">删除</Button>
 * 
 * @example
 * // 图标按钮
 * <Button variant="outline" size="icon">
 *   <Icon />
 * </Button>
 * 
 * @example
 * // asChild模式 - 链接按钮
 * <Button asChild>
 *   <Link href="/profile">个人资料</Link>
 * </Button>
 * 
 * 注意事项：
 * - asChild模式下子元素必须支持button的所有属性
 * - 自定义className会与变体样式合并，遵循Tailwind优先级
 * - 禁用状态会自动禁用pointer-events和降低透明度
 */
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    // 根据asChild决定渲染元素类型
    const Comp = asChild ? Slot : "button"
    
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)

// 设置displayName便于React开发工具调试
Button.displayName = "Button"

export { Button, buttonVariants }
