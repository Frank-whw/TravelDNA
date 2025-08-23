/**
 * 主题提供者组件 - 深色/浅色模式管理
 * 
 * 功能概述：
 * - 封装next-themes的ThemeProvider，提供主题切换功能
 * - 支持系统主题自动检测和用户偏好记忆
 * - 为整个应用提供主题上下文
 * 
 * 设计思路：
 * - 采用Context模式向下传递主题状态
 * - 使用next-themes库处理主题持久化和SSR兼容
 * - 支持多种主题切换策略（手动、自动、系统）
 * 
 * 依赖要求：
 * - next-themes 包提供主题管理核心功能
 * - 需要在应用根部使用此Provider包裹
 * - CSS变量需要配合定义深色和浅色主题样式
 * 
 * 使用限制：
 * - 必须在客户端渲染环境下使用（'use client'）
 * - 避免服务端渲染时的主题状态不一致问题
 */

'use client'

import * as React from 'react'
import {
  ThemeProvider as NextThemesProvider,
  type ThemeProviderProps,
} from 'next-themes'

/**
 * 主题提供者包装组件
 * 
 * @param {ThemeProviderProps} props - 主题提供者配置属性
 * @param {React.ReactNode} props.children - 子组件，所有需要主题功能的组件都应包含在内
 * @param {...ThemeProviderProps} props - 其他next-themes配置选项：
 *   - attribute?: string - 主题属性名（默认'data-theme'）
 *   - defaultTheme?: string - 默认主题（'light' | 'dark' | 'system'）
 *   - enableSystem?: boolean - 是否启用系统主题检测
 *   - disableTransitionOnChange?: boolean - 是否禁用主题切换动画
 * 
 * @returns {JSX.Element} 主题上下文提供者
 * 
 * @example
 * // 在 layout.tsx 中使用
 * <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
 *   <App />
 * </ThemeProvider>
 * 
 * 注意事项：
 * - 建议在根布局组件中使用
 * - 主题切换通过useTheme hook在子组件中访问
 * - CSS需要配合定义对应的主题样式变量
 */
export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
