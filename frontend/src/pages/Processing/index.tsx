/**
 * Processing Page
 *
 * 视频处理中页面
 *
 * 功能：
 * 1. 实时显示处理进度
 * 2. 显示当前处理阶段
 * 3. 自动轮询状态
 * 4. 处理完成后自动跳转到结果页
 *
 * @module pages/Processing
 */

import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Layout, Space, Button, Result, Spin } from 'antd';
import {
  LeftOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import ProcessingStatus from '@/components/ProcessingStatus';
import { useProcessingStatus } from '@/hooks/useProcessingStatus';

const { Content } = Layout;

/**
 * Processing Page Component
 *
 * @component
 * @description
 * 处理页面，使用useProcessingStatus Hook实时轮询状态
 * 处理完成后自动跳转到结果页
 */
export const ProcessingPage: React.FC = () => {
  const navigate = useNavigate();
  const { videoId } = useParams<{ videoId: string }>();

  // 使用自定义Hook获取处理状态
  const { status, loading, error, refresh } = useProcessingStatus(videoId || null);

  /**
   * 自动跳转逻辑
   * 当状态变为completed时，自动跳转到结果页
   */
  useEffect(() => {
    if (status?.status === 'completed') {
      // 延迟1秒跳转，让用户看到完成状态
      const timer = setTimeout(() => {
        navigate(`/result/${videoId}`, { replace: true });
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [status?.status, videoId, navigate]);

  /**
   * 返回首页
   */
  const handleBackHome = () => {
    navigate('/', { replace: true });
  };

  // ========== 错误状态 ==========
  if (error) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ padding: '40px 24px' }}>
          <div style={{ maxWidth: 800, margin: '0 auto' }}>
            <Result
              status="error"
              title="获取状态失败"
              subTitle={error}
              extra={[
                <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={refresh}>
                  重新加载
                </Button>,
                <Button key="home" icon={<LeftOutlined />} onClick={handleBackHome}>
                  返回首页
                </Button>,
              ]}
            />
          </div>
        </Content>
      </Layout>
    );
  }

  // ========== 处理失败状态 ==========
  if (status?.status === 'failed') {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ padding: '40px 24px' }}>
          <div style={{ maxWidth: 800, margin: '0 auto' }}>
            <Result
              status="error"
              icon={<CloseCircleOutlined />}
              title="处理失败"
              subTitle={status.error_message || '视频处理过程中出现错误'}
              extra={[
                <Button key="home" type="primary" icon={<LeftOutlined />} onClick={handleBackHome}>
                  返回首页重试
                </Button>,
              ]}
            />
          </div>
        </Content>
      </Layout>
    );
  }

  // ========== 处理完成状态（即将跳转） ==========
  if (status?.status === 'completed') {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ padding: '40px 24px' }}>
          <div style={{ maxWidth: 800, margin: '0 auto' }}>
            <Result
              status="success"
              icon={<CheckCircleOutlined />}
              title="处理完成！"
              subTitle="正在跳转到结果页面..."
              extra={
                <Spin size="large" />
              }
            />
          </div>
        </Content>
      </Layout>
    );
  }

  // ========== 处理中状态 ==========
  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ padding: '40px 24px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {/* 顶部操作栏 */}
          <div style={{ marginBottom: 24 }}>
            <Space>
              <Button icon={<LeftOutlined />} onClick={handleBackHome}>
                返回首页
              </Button>
              <Button icon={<ReloadOutlined />} onClick={refresh} disabled={loading}>
                刷新状态
              </Button>
            </Space>
          </div>

          {/* 处理状态组件 */}
          <ProcessingStatus status={status} loading={loading} error={error} />

          {/* 提示信息 */}
          {status && (status.status === 'pending' || status.status === 'processing') && (
            <div
              style={{
                marginTop: 24,
                padding: '16px',
                background: '#e6f7ff',
                borderRadius: 4,
                border: '1px solid #91d5ff',
              }}
            >
              <Space direction="vertical" size="small">
                <span style={{ color: '#1890ff', fontWeight: 500 }}>
                  处理中，请稍候...
                </span>
                <span style={{ color: '#595959', fontSize: 12 }}>
                  • 页面会自动刷新状态，无需手动操作
                </span>
                <span style={{ color: '#595959', fontSize: 12 }}>
                  • 处理时间取决于视频长度和配置参数
                </span>
                <span style={{ color: '#595959', fontSize: 12 }}>
                  • 完成后会自动跳转到结果页面
                </span>
              </Space>
            </div>
          )}
        </div>
      </Content>
    </Layout>
  );
};

export default ProcessingPage;
