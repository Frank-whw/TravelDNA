/**
 * 通用工具函数库 - Tailwind CSS类名合并工具
 * 
 * 功能概述：
 * - 提供类名合并和冲突解决功能
 * - 优化Tailwind CSS动态类名处理
 * - 支持条件类名和变体组合
 * 
 * 设计思路：
 * - 使用clsx处理条件类名逻辑
 * - 通过tailwind-merge解决Tailwind类名冲突
 * - 提供统一的类名处理接口
 * 
 * 性能考虑：
 * - tailwind-merge会缓存类名解析结果
 * - 避免重复计算相同的类名组合
 */

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * 智能合并类名函数 - 解决Tailwind CSS类名冲突
 * 
 * 功能说明：
 * - 合并多个类名输入
 * - 自动解决Tailwind类名冲突（如 px-2 px-4 只保留后者）
 * - 支持条件类名、数组、对象等多种输入格式
 * 
 * @param {...ClassValue[]} inputs - 类名输入数组，支持多种格式：
 *   - 字符串: "text-red-500 bg-blue-100"
 *   - 条件对象: { "active": isActive, "disabled": isDisabled }
 *   - 数组: ["base-class", { "conditional": condition }]
 *   - 嵌套组合: ["class1", ["class2", { "class3": true }]]
 * 
 * @returns {string} 合并后的类名字符串，已去重和解决冲突
 * 
 * @example
 * cn("px-2 py-1", "px-4", { "text-red-500": isError })
 * // 返回: "py-1 px-4 text-red-500" (如果isError为true)
 * 
 * @example
 * cn("text-sm", condition && "text-lg", { "font-bold": isBold })
 * // 根据条件动态组合类名
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
