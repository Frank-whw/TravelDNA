/**
 * Tailwind CSS 配置文件 - 知旅应用样式系统配置
 * 
 * 功能概述：
 * - 定义应用的设计令牌系统（颜色、字体、间距等）
 * - 配置深色模式支持和主题切换
 * - 扩展Tailwind默认功能，添加自定义动画和组件样式
 * 
 * 设计系统：
 * - 基于CSS变量的主题系统，支持动态主题切换
 * - 语义化颜色命名（primary、secondary、destructive等）
 * - 统一的圆角、阴影、动画规范
 * 
 * 兼容性说明：
 * - 支持Tailwind CSS v3.x
 * - 深色模式采用class策略（.dark类名切换）
 * - 使用HSL颜色空间便于主题调色
 * 
 * 性能优化：
 * - 精确的content配置减少CSS产出体积
 * - 按需生成样式类，避免冗余代码
 */

import type { Config } from "tailwindcss";

// 临时解决方案说明：当前所有配置项都设置为Tailwind v3兼容模式
// all in fixtures is set to tailwind v3 as interims solutions

/**
 * Tailwind CSS 主配置对象
 * @type {Config} Tailwind配置类型定义
 */
const config: Config = {
    /**
     * 深色模式配置 - 基于CSS类名的主题切换
     * 策略：["class"] - 通过.dark类名启用深色模式
     * 优势：可编程控制，支持用户偏好设置
     */
    darkMode: ["class"],
    
    /**
     * 内容扫描路径 - 指定需要分析的文件范围
     * 用途：Tailwind扫描这些文件中的类名，按需生成CSS
     * 性能优化：精确匹配减少CSS包大小
     */
    content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",    // Pages Router页面
    "./components/**/*.{js,ts,jsx,tsx,mdx}", // 组件目录
    "./app/**/*.{js,ts,jsx,tsx,mdx}",      // App Router页面
    "*.{js,ts,jsx,tsx,mdx}"                // 根目录文件
  ],
  
  /**
   * 主题配置扩展 - 在默认主题基础上添加自定义设计令牌
   */
  theme: {
  	extend: {
  		/**
         * 颜色系统 - 基于CSS变量的语义化颜色定义
         * 设计理念：使用HSL颜色空间和CSS变量，支持主题切换
         * 命名规范：语义化命名而非具体颜色值
         */
  		colors: {
  			// 基础背景和前景色
  			background: 'hsl(var(--background))',       // 页面背景色
  			foreground: 'hsl(var(--foreground))',       // 主要文本色
  			
  			// 卡片组件配色
  			card: {
  				DEFAULT: 'hsl(var(--card))',            // 卡片背景
  				foreground: 'hsl(var(--card-foreground))' // 卡片文本
  			},
  			
  			// 弹出层配色
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',         // 弹出层背景
  				foreground: 'hsl(var(--popover-foreground))' // 弹出层文本
  			},
  			
  			// 主色调系统
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',         // 主色调
  				foreground: 'hsl(var(--primary-foreground))' // 主色调文本
  			},
  			
  			// 次要色调系统
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',       // 次要色
  				foreground: 'hsl(var(--secondary-foreground))' // 次要色文本
  			},
  			
  			// 静音色调系统（低对比度）
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',           // 静音背景
  				foreground: 'hsl(var(--muted-foreground))' // 静音文本
  			},
  			
  			// 强调色系统
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',          // 强调色背景
  				foreground: 'hsl(var(--accent-foreground))' // 强调色文本
  			},
  			
  			// 警告/危险色系统
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',     // 危险操作背景
  				foreground: 'hsl(var(--destructive-foreground))' // 危险操作文本
  			},
  			
  			// 边框和输入框配色
  			border: 'hsl(var(--border))',              // 边框色
  			input: 'hsl(var(--input))',                // 输入框边框
  			ring: 'hsl(var(--ring))',                  // 焦点环颜色
  			
  			// 图表配色系统（数据可视化）
  			chart: {
  				'1': 'hsl(var(--chart-1))',            // 图表色1
  				'2': 'hsl(var(--chart-2))',            // 图表色2  
  				'3': 'hsl(var(--chart-3))',            // 图表色3
  				'4': 'hsl(var(--chart-4))',            // 图表色4
  				'5': 'hsl(var(--chart-5))'             // 图表色5
  			},
  			
  			// 侧边栏专用配色系统
  			sidebar: {
  				DEFAULT: 'hsl(var(--sidebar-background))',           // 侧边栏背景
  				foreground: 'hsl(var(--sidebar-foreground))',        // 侧边栏文本
  				primary: 'hsl(var(--sidebar-primary))',              // 侧边栏主色
  				'primary-foreground': 'hsl(var(--sidebar-primary-foreground))', // 侧边栏主色文本
  				accent: 'hsl(var(--sidebar-accent))',                // 侧边栏强调色
  				'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',   // 侧边栏强调色文本
  				border: 'hsl(var(--sidebar-border))',                // 侧边栏边框
  				ring: 'hsl(var(--sidebar-ring))'                     // 侧边栏焦点环
  			}
  		},
  		
  		/**
         * 圆角系统 - 基于CSS变量的统一圆角规范
         * 设计理念：三级圆角系统，保持视觉一致性
         */
  		borderRadius: {
  			lg: 'var(--radius)',                       // 大圆角
  			md: 'calc(var(--radius) - 2px)',           // 中圆角
  			sm: 'calc(var(--radius) - 4px)'            // 小圆角
  		},
  		
  		/**
         * 关键帧动画定义 - 自定义动画效果
         * 用途：为手风琴等交互组件提供流畅的展开/收起动画
         */
  		keyframes: {
  			// 手风琴展开动画
  			'accordion-down': {
  				from: {
  					height: '0'                         // 起始高度为0
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)' // 目标高度为内容高度
  				}
  			},
  			// 手风琴收起动画
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)' // 起始高度为内容高度
  				},
  				to: {
  					height: '0'                         // 目标高度为0
  				}
  			}
  		},
  		
  		/**
         * 动画配置 - 将关键帧动画映射为可用的CSS类
         * 性能优化：使用ease-out缓动函数，提供自然的动画体验
         */
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',  // 0.2秒展开动画
  			'accordion-up': 'accordion-up 0.2s ease-out'       // 0.2秒收起动画
  		}
  	}
  },
  
  /**
   * 插件配置 - 扩展Tailwind功能
   * tailwindcss-animate: 提供预定义的动画工具类
   */
  plugins: [require("tailwindcss-animate")],
};

export default config;
