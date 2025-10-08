/**
 * Next.js 配置文件 - 知旅应用构建和运行时配置
 * 
 * 功能概述：
 * - 配置开发环境的构建优化选项
 * - 禁用严格的类型检查和ESLint，提升开发效率
 * - 优化图片处理，适配各种部署环境
 * - 修复 webpack 热更新问题
 * 
 * 配置策略：
 * - 开发阶段优先考虑构建速度和开发体验
 * - 生产环境部署时可重新启用严格检查
 * - 图片未优化处理适用于静态导出场景
 * 
 * 注意事项：
 * - 当前配置适用于开发阶段，生产环境建议调整
 * - ESLint和TypeScript检查被禁用，需要IDE辅助检查
 * - 图片优化被禁用，可能影响SEO和加载性能
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  /**
   * ESLint 配置 - 代码质量检查设置
   * 
   * ignoreDuringBuilds: true - 构建时跳过ESLint检查
   * 
   * 优势：
   * - 显著提升构建速度，特别是大型项目
   * - 避免因代码风格问题阻断开发流程
   * 
   * 风险：
   * - 可能遗漏潜在的代码质量问题
   * - 需要依靠IDE的ESLint插件进行实时检查
   * 
   * 建议：
   * - 开发环境可以启用，生产环境建议开启检查
   * - 配合pre-commit hooks确保代码质量
   */
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  /**
   * TypeScript 配置 - 类型检查设置
   * 
   * ignoreBuildErrors: true - 构建时忽略TypeScript错误
   * 
   * 优势：
   * - 允许渐进式TypeScript迁移
   * - 避免类型错误阻断原型开发
   * - 提升初期开发效率
   * 
   * 风险：
   * - 可能隐藏重要的类型安全问题
   * - 运行时错误风险增加
   * 
   * 建议：
   * - 开发后期应该开启严格类型检查
   * - 使用TypeScript IDE插件提供实时类型提示
   */
  typescript: {
    ignoreBuildErrors: true,
  },
  
  /**
   * Webpack 配置 - 修复热更新问题
   */
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // 修复 webpack 热更新的 ERR_ABORTED 错误
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
        ignored: ['**/node_modules/**', '**/.git/**', '**/.next/**'],
      }
      
      // 优化热更新性能和稳定性
      config.optimization = {
        ...config.optimization,
        removeAvailableModules: false,
        removeEmptyChunks: false,
        splitChunks: false,
      }
      
      // 添加更稳定的热更新配置
      config.infrastructureLogging = {
        level: 'error',
      }
      
      // 减少热更新文件的生成频率
      config.snapshot = {
        managedPaths: [/^(.+?[\\/]node_modules[\\/])/],
        immutablePaths: [],
        buildDependencies: {
          hash: true,
          timestamp: true,
        },
        module: {
          timestamp: true,
        },
        resolve: {
          timestamp: true,
        },
        resolveBuildDependencies: {
          hash: true,
          timestamp: true,
        },
      }
    }
    
    return config
  },
  
  /**
   * 图片优化配置 - Next.js Image组件设置
   * 
   * unoptimized: true - 禁用图片自动优化
   * 
   * 适用场景：
   * - 静态站点生成（SSG）部署
   * - CDN图片资源托管
   * - 开发环境快速预览
   * 
   * 影响：
   * - 图片不会自动压缩和格式转换
   * - 失去响应式图片和懒加载优化
   * - 可能影响页面加载性能和SEO评分
   * 
   * 替代方案：
   * - 生产环境建议启用优化，配置合适的loader
   * - 考虑使用第三方图片CDN服务
   */
  images: {
    unoptimized: true,
  },
}

export default nextConfig