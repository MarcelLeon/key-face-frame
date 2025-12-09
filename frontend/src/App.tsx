/**
 * App Component - Root Application
 *
 * 应用根组件，配置路由和全局样式
 *
 * 路由结构：
 * - / - 首页（上传和配置）
 * - /processing/:videoId - 处理中页面
 * - /result/:videoId - 结果展示页面
 *
 * @module App
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

// Pages
import HomePage from '@/pages/Home';
import ProcessingPage from '@/pages/Processing';
import ResultPage from '@/pages/Result';

/**
 * App Component
 *
 * @component
 * @description
 * 应用入口组件
 * - 配置 Ant Design 中文语言包
 * - 配置 React Router 路由
 */
function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 4,
        },
      }}
    >
      <Routes>
        {/* 首页：上传和配置 */}
        <Route path="/" element={<HomePage />} />

        {/* 处理页：实时显示进度 */}
        <Route path="/processing/:videoId" element={<ProcessingPage />} />

        {/* 结果页：关键帧展示 */}
        <Route path="/result/:videoId" element={<ResultPage />} />

        {/* 404重定向到首页 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ConfigProvider>
  );
}

export default App;
