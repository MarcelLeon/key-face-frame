/**
 * Result Page
 *
 * 处理结果展示页面
 *
 * 功能：
 * 1. 展示处理结果摘要
 * 2. 关键帧画廊展示
 * 3. 下载功能
 * 4. 返回首页继续处理
 *
 * @module pages/Result
 */

import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Layout, Space, Button, Result, Card, Divider } from 'antd';
import {
  DownloadOutlined,
  ReloadOutlined,
  HomeOutlined,
} from '@ant-design/icons';
import ProcessingStatus from '@/components/ProcessingStatus';
import KeyframeGallery from '@/components/KeyframeGallery';
import { useProcessingStatus } from '@/hooks/useProcessingStatus';
import { downloadKeyframes } from '@/api/video';
import { message } from 'antd';

const { Content } = Layout;

/**
 * Result Page Component
 *
 * @component
 * @description
 * 结果页面，展示处理完成的视频和提取的关键帧
 */
export const ResultPage: React.FC = () => {
  const navigate = useNavigate();
  const { videoId } = useParams<{ videoId: string }>();

  // 获取视频状态（虽然已完成，但需要获取完整数据）
  const { status, loading, error, refresh } = useProcessingStatus(videoId || null);

  /**
   * 返回首页
   */
  const handleBackHome = () => {
    navigate('/', { replace: true });
  };

  /**
   * 下载关键帧（ZIP）
   */
  const handleDownload = async () => {
    if (!videoId) return;

    try {
      message.loading({ content: '正在打包下载...', key: 'download' });

      const response = await downloadKeyframes(videoId);

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `keyframes-${videoId}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      message.success({ content: '下载成功！', key: 'download' });
    } catch (err: any) {
      console.error('[Download] Error:', err);
      message.error({
        content: err.message || '下载失败，请重试',
        key: 'download',
      });
    }
  };

  // ========== 错误状态 ==========
  if (error) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ padding: '40px 24px' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            <Result
              status="error"
              title="加载失败"
              subTitle={error}
              extra={[
                <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={refresh}>
                  重新加载
                </Button>,
                <Button key="home" icon={<HomeOutlined />} onClick={handleBackHome}>
                  返回首页
                </Button>,
              ]}
            />
          </div>
        </Content>
      </Layout>
    );
  }

  // ========== 未完成状态（重定向到处理页） ==========
  if (status && status.status !== 'completed') {
    navigate(`/processing/${videoId}`, { replace: true });
    return null;
  }

  // ========== 结果展示 ==========
  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ padding: '40px 24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {/* 顶部操作栏 */}
          <div style={{ marginBottom: 24 }}>
            <Space>
              <Button icon={<HomeOutlined />} onClick={handleBackHome}>
                返回首页
              </Button>
              <Button icon={<ReloadOutlined />} onClick={refresh} disabled={loading}>
                刷新数据
              </Button>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={handleDownload}
                disabled={!status || !status.keyframes || status.keyframes.length === 0}
              >
                下载所有关键帧
              </Button>
            </Space>
          </div>

          {/* 处理结果摘要 */}
          <Card style={{ marginBottom: 24 }}>
            <ProcessingStatus status={status} loading={loading} error={error} />
          </Card>

          {/* 分隔线 */}
          <Divider orientation="left" style={{ fontSize: 18, fontWeight: 500 }}>
            关键帧画廊
          </Divider>

          {/* 关键帧展示 */}
          {status && status.keyframes && status.keyframes.length > 0 ? (
            <KeyframeGallery
              keyframes={status.keyframes}
              videoId={videoId!}
              loading={loading}
            />
          ) : (
            <Card>
              <Result
                status="warning"
                title="未提取到关键帧"
                subTitle="视频中可能没有检测到人物，或检测阈值设置过高"
                extra={
                  <Button type="primary" icon={<HomeOutlined />} onClick={handleBackHome}>
                    返回首页重新处理
                  </Button>
                }
              />
            </Card>
          )}

          {/* 底部提示 */}
          {status && status.keyframes && status.keyframes.length > 0 && (
            <Card
              style={{ marginTop: 24 }}
              bodyStyle={{ background: '#fafafa', padding: '16px 24px' }}
            >
              <Space direction="vertical" size="small">
                <span style={{ fontWeight: 500 }}>使用提示：</span>
                <span style={{ color: '#595959' }}>
                  • 点击任意关键帧可放大查看
                </span>
                <span style={{ color: '#595959' }}>
                  • 可以按评分或时间戳排序
                </span>
                <span style={{ color: '#595959' }}>
                  • 点击"下载所有关键帧"按钮可打包下载为ZIP文件
                </span>
              </Space>
            </Card>
          )}
        </div>
      </Content>
    </Layout>
  );
};

export default ResultPage;
