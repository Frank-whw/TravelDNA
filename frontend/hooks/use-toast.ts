/**
 * Toast通知Hook - 全局消息提示管理系统
 * 
 * 功能概述：
 * - 提供全局的Toast消息显示和管理功能
 * - 支持多种消息类型（成功、错误、警告、信息）
 * - 自动移除机制和手动控制选项
 * - 无限制并发Toast支持（限制1个同时显示）
 * 
 * 设计思路：
 * - 基于React外部状态管理，避免Context性能问题
 * - 使用Reducer模式管理复杂的Toast状态变化
 * - 全局监听器模式，支持跨组件调用
 * - 自动超时和手动控制的混合机制
 * 
 * 技术架构：
 * - 外部状态存储（非React状态）
 * - Reducer模式的动作分发
 * - 自定义Hook封装API
 * - TypeScript类型安全保障
 * 
 * 性能优化：
 * - 限制同时显示Toast数量（TOAST_LIMIT = 1）
 * - 延迟移除机制避免闪烁
 * - 内存清理和监听器管理
 * 
 * 灵感来源：
 * - 基于react-hot-toast库的设计理念
 * - 适配Shadcn/ui组件系统
 */

"use client"

// 基于react-hot-toast库设计理念
// Inspired by react-hot-toast library
import * as React from "react"

import type {
  ToastActionElement,
  ToastProps,
} from "@/components/ui/toast"

/**
 * Toast系统配置常量
 */
// 同时显示的Toast最大数量限制
const TOAST_LIMIT = 1
// Toast移除延迟时间（毫秒）- 设置很长避免自动移除
const TOAST_REMOVE_DELAY = 1000000

/**
 * Toast数据类型定义 - 扩展基础Props增加业务字段
 * 
 * @interface ToasterToast
 * @extends {ToastProps} 继承基础Toast组件属性
 */
type ToasterToast = ToastProps & {
  id: string                          // 唯一标识符
  title?: React.ReactNode             // 标题内容
  description?: React.ReactNode       // 描述内容  
  action?: ToastActionElement         // 操作按钮元素
}

/**
 * 动作类型枚举 - 定义所有可能的Toast操作
 */
const actionTypes = {
  ADD_TOAST: "ADD_TOAST",             // 添加新Toast
  UPDATE_TOAST: "UPDATE_TOAST",       // 更新现有Toast
  DISMISS_TOAST: "DISMISS_TOAST",     // 关闭Toast（开始动画）
  REMOVE_TOAST: "REMOVE_TOAST",       // 移除Toast（从列表删除）
} as const

/**
 * ID生成器计数器 - 确保每个Toast有唯一标识
 */
let count = 0

/**
 * 生成唯一ID函数 - 循环计数避免溢出
 * 
 * @returns {string} 唯一的字符串ID
 */
function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

/**
 * 动作类型定义
 */
type ActionType = typeof actionTypes

/**
 * 动作对象联合类型 - 支持TypeScript类型检查
 */
type Action =
  | {
      type: ActionType["ADD_TOAST"]
      toast: ToasterToast
    }
  | {
      type: ActionType["UPDATE_TOAST"]  
      toast: Partial<ToasterToast>
    }
  | {
      type: ActionType["DISMISS_TOAST"]
      toastId?: ToasterToast["id"]
    }
  | {
      type: ActionType["REMOVE_TOAST"]
      toastId?: ToasterToast["id"]
    }

/**
 * Toast状态接口定义
 */
interface State {
  toasts: ToasterToast[]              // Toast列表数组
}

/**
 * 超时定时器管理Map - 追踪每个Toast的移除定时器
 * Key: toastId, Value: setTimeout返回的定时器ID
 */
const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

/**
 * 添加Toast到移除队列 - 设置延迟移除定时器
 * 
 * @param {string} toastId - 要移除的Toast ID
 * 
 * 功能说明：
 * - 检查是否已有定时器，避免重复设置
 * - 延迟后自动分发REMOVE_TOAST动作
 * - 清理定时器引用避免内存泄漏
 */
const addToRemoveQueue = (toastId: string) => {
  // 防止重复添加定时器
  if (toastTimeouts.has(toastId)) {
    return
  }

  // 设置延迟移除定时器
  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId)
    dispatch({
      type: "REMOVE_TOAST",
      toastId: toastId,
    })
  }, TOAST_REMOVE_DELAY)

  toastTimeouts.set(toastId, timeout)
}

/**
 * Toast状态reducer - 处理所有Toast状态变化
 * 
 * @param {State} state - 当前状态
 * @param {Action} action - 动作对象
 * @returns {State} 新的状态
 * 
 * 状态变化逻辑：
 * - ADD_TOAST: 添加新Toast到列表头部，限制总数量
 * - UPDATE_TOAST: 根据ID更新特定Toast属性
 * - DISMISS_TOAST: 设置Toast为关闭状态，触发关闭动画
 * - REMOVE_TOAST: 从列表中完全移除Toast
 */
export const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case "ADD_TOAST":
      return {
        ...state,
        // 新Toast添加到头部，slice限制总数量
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
      }

    case "UPDATE_TOAST":
      return {
        ...state,
        // 更新匹配ID的Toast，保持其他不变
        toasts: state.toasts.map((t) =>
          t.id === action.toast.id ? { ...t, ...action.toast } : t
        ),
      }

    case "DISMISS_TOAST": {
      const { toastId } = action

      // ! 副作用处理 ! - 可以提取为独立动作，但为简化保留在此
      // 设置移除定时器
      if (toastId) {
        addToRemoveQueue(toastId)
      } else {
        // 关闭所有Toast
        state.toasts.forEach((toast) => {
          addToRemoveQueue(toast.id)
        })
      }

      return {
        ...state,
        // 设置Toast为关闭状态，触发CSS动画
        toasts: state.toasts.map((t) =>
          t.id === toastId || toastId === undefined
            ? {
                ...t,
                open: false,
              }
            : t
        ),
      }
    }
    
    case "REMOVE_TOAST":
      // 未指定ID则清空所有Toast
      if (action.toastId === undefined) {
        return {
          ...state,
          toasts: [],
        }
      }
      // 过滤移除指定ID的Toast
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.toastId),
      }
  }
}

/**
 * 状态监听器数组 - 存储所有订阅状态变化的回调函数
 */
const listeners: Array<(state: State) => void> = []

/**
 * 外部状态存储 - 独立于React组件的全局状态
 */
let memoryState: State = { toasts: [] }

/**
 * 状态分发器 - 触发状态更新和监听器通知
 * 
 * @param {Action} action - 要执行的动作
 * 
 * 执行流程：
 * 1. 通过reducer计算新状态
 * 2. 更新内存状态
 * 3. 通知所有监听器状态变化
 */
function dispatch(action: Action) {
  memoryState = reducer(memoryState, action)
  listeners.forEach((listener) => {
    listener(memoryState)
  })
}

/**
 * Toast输入类型 - 排除id字段的ToasterToast
 */
type Toast = Omit<ToasterToast, "id">

/**
 * 创建Toast函数 - 主要的外部API
 * 
 * @param {Toast} props - Toast配置属性
 * @returns {Object} Toast控制对象，包含id、dismiss、update方法
 * 
 * 功能特性：
 * - 自动生成唯一ID
 * - 返回控制方法便于后续操作
 * - 自动设置open状态和onOpenChange回调
 * 
 * @example
 * const { id, dismiss, update } = toast({
 *   title: "操作成功",
 *   description: "数据已保存",
 *   variant: "default"
 * })
 * 
 * // 2秒后自动关闭
 * setTimeout(dismiss, 2000)
 */
function toast({ ...props }: Toast) {
  const id = genId()

  /**
   * 更新Toast内容
   * @param {ToasterToast} props - 新的Toast属性
   */
  const update = (props: ToasterToast) =>
    dispatch({
      type: "UPDATE_TOAST",
      toast: { ...props, id },
    })
    
  /**
   * 关闭Toast
   */
  const dismiss = () => dispatch({ type: "DISMISS_TOAST", toastId: id })

  // 分发添加Toast动作
  dispatch({
    type: "ADD_TOAST",
    toast: {
      ...props,
      id,
      open: true,
      onOpenChange: (open) => {
        if (!open) dismiss()
      },
    },
  })

  return {
    id: id,
    dismiss,
    update,
  }
}

/**
 * useToast Hook - React组件中使用Toast的主要接口
 * 
 * @returns {Object} Toast状态和控制方法
 *   - toasts: 当前Toast列表
 *   - toast: 创建新Toast的函数
 *   - dismiss: 关闭指定Toast的函数
 * 
 * 实现原理：
 * - 订阅外部状态变化
 * - 自动清理监听器避免内存泄漏
 * - 提供统一的API接口
 * 
 * @example
 * function MyComponent() {
 *   const { toast, dismiss } = useToast()
 *   
 *   const showSuccess = () => {
 *     toast({
 *       title: "成功",
 *       description: "操作完成",
 *       variant: "default"
 *     })
 *   }
 *   
 *   return <button onClick={showSuccess}>显示Toast</button>
 * }
 * 
 * 注意事项：
 * - 确保在组件挂载后调用
 * - 避免在循环或条件语句中使用
 * - 支持在任何React组件中调用
 */
function useToast() {
  const [state, setState] = React.useState<State>(memoryState)

  React.useEffect(() => {
    // 添加状态监听器
    listeners.push(setState)
    
    // 清理函数：移除监听器
    return () => {
      const index = listeners.indexOf(setState)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }, [state])

  return {
    ...state,
    toast,
    dismiss: (toastId?: string) => dispatch({ type: "DISMISS_TOAST", toastId }),
  }
}

export { useToast, toast }
