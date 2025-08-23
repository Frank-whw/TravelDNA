/**
 * 移动端设备检测Hook - 响应式断点监听
 * 
 * 功能概述：
 * - 实时检测当前设备是否为移动端
 * - 监听窗口尺寸变化，动态更新移动端状态
 * - 提供统一的响应式断点判断逻辑
 * 
 * 设计思路：
 * - 基于窗口宽度判断设备类型（768px作为移动端断点）
 * - 使用MediaQueryList API监听尺寸变化，性能优于resize事件
 * - 处理服务端渲染时的初始状态问题
 * 
 * 算法逻辑：
 * 1. 初始化状态为undefined，避免SSR不一致
 * 2. 客户端挂载后立即检测当前窗口尺寸
 * 3. 监听媒体查询变化，实时更新移动端状态
 * 4. 组件卸载时清理事件监听器
 * 
 * 性能考虑：
 * - 使用matchMedia替代resize事件，减少回调频率
 * - 避免频繁的DOM查询，缓存窗口尺寸判断
 */

import * as React from "react"

/**
 * 移动端断点常量 - 基于常见UI框架的标准断点
 * 768px对应Tailwind CSS的md断点，小于此值视为移动端
 */
const MOBILE_BREAKPOINT = 768

/**
 * 移动端检测自定义Hook
 * 
 * 功能说明：
 * - 检测当前视口是否属于移动端尺寸
 * - 自动响应窗口尺寸变化
 * - 处理服务端渲染兼容性问题
 * 
 * @returns {boolean} 移动端状态
 *   - true: 当前为移动端设备（窗口宽度 < 768px）
 *   - false: 当前为桌面端设备（窗口宽度 >= 768px）
 * 
 * 实现细节：
 * - 初始状态为undefined，防止SSR水合不一致
 * - 使用MediaQueryList监听断点变化
 * - 自动清理事件监听器，避免内存泄漏
 * 
 * @example
 * function ResponsiveComponent() {
 *   const isMobile = useIsMobile()
 *   
 *   return (
 *     <div>
 *       {isMobile ? <MobileView /> : <DesktopView />}
 *     </div>
 *   )
 * }
 * 
 * 注意事项：
 * - 仅在客户端环境下可用
 * - 初次渲染可能返回undefined，建议有fallback处理
 * - 断点变化时会触发组件重新渲染
 */
export function useIsMobile() {
  // 移动端状态：undefined（SSR）| true（移动端）| false（桌面端）
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(undefined)

  React.useEffect(() => {
    // 创建媒体查询对象，监听移动端断点
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    
    // 断点变化时的回调函数
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }
    
    // 监听媒体查询变化
    mql.addEventListener("change", onChange)
    
    // 立即设置初始状态
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    
    // 清理函数：移除事件监听器
    return () => mql.removeEventListener("change", onChange)
  }, [])

  // 返回布尔值，将undefined转换为false
  return !!isMobile
}
