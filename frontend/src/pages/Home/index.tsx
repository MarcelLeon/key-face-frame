/**
 * Home Page
 *
 * 首页 - 视频上传和配置页面
 *
 * 功能：
 * 1. 展示应用介绍
 * 2. 视频上传组件
 * 3. 处理参数配置
 * 4. 上传成功后跳转到处理页
 *
 * @module pages/Home
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Typography, Space, Row, Col, Card } from 'antd';
import {
  VideoCameraOutlined,
  RobotOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import VideoUploader from '@/components/VideoUploader';
import ConfigPanel from '@/components/ConfigPanel';
import { useConfig, useVideoActions } from '@/stores/videoStore';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;

/**
 * 功能特性卡片
 */
const FeatureCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
}> = ({ icon, title, description }) => (
  <Card hoverable style={{ height: '100%' }}>
    <Space direction="vertical" align="center" style={{ width: '100%' }}>
      <div style={{ fontSize: 48, color: '#1890ff' }}>{icon}</div>
      <Title level={4}>{title}</Title>
      <Text type="secondary" style={{ textAlign: 'center' }}>
        {description}
      </Text>
    </Space>
  </Card>
);

/**
 * Home Page Component
 *
 * @component
 * @description
 * 主页面，包含上传区域和配置面板
 * 上传成功后自动跳转到处理页面
 */
export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const config = useConfig();
  const { updateConfig, setCurrentVideo } = useVideoActions();

  /**
   * 上传成功回调
   * @param videoId - 返回的视频ID
   */
  const handleUploadSuccess = (videoId: string) => {
    // 保存到Store
    setCurrentVideo(videoId);

    // 跳转到处理页
    navigate(`/processing/${videoId}`);
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ padding: '40px 24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {/* 页面标题 */}
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <Title level={1} style={{ fontSize: 48, marginBottom: 16 }}>
              Key-Face-Frame
            </Title>
            <Paragraph style={{ fontSize: 18, color: '#8c8c8c' }}>
              视频人物关键帧提取工具 - 智能检测人物，自动提取高质量关键帧
            </Paragraph>
          </div>

          {/* 功能特性 */}
          <Row gutter={[24, 24]} style={{ marginBottom: 48 }}>
            <Col xs={24} md={8}>
              <FeatureCard
                icon={<VideoCameraOutlined />}
                title="智能检测"
                description="基于YOLOv8的人物检测，精准识别视频中的人物"
              />
            </Col>
            <Col xs={24} md={8}>
              <FeatureCard
                icon={<RobotOutlined />}
                title="多维评分"
                description="综合人物大小、置信度、居中程度和稳定性的智能评分"
              />
            </Col>
            <Col xs={24} md={8}>
              <FeatureCard
                icon={<ThunderboltOutlined />}
                title="高效处理"
                description="支持Apple Silicon MPS加速，处理速度快"
              />
            </Col>
          </Row>

          {/* 上传和配置区域 */}
          <Row gutter={[24, 24]}>
            {/* 左侧：上传 */}
            <Col xs={24} md={14}>
              <Card
                title={
                  <Space>
                    <VideoCameraOutlined />
                    <Text strong>上传视频</Text>
                  </Space>
                }
              >
                <VideoUploader config={config} onSuccess={handleUploadSuccess} />
              </Card>
            </Col>

            {/* 右侧：配置 */}
            <Col xs={24} md={10}>
              <ConfigPanel value={config} onChange={updateConfig} />
            </Col>
          </Row>

          {/* 使用提示 */}
          <Card
            style={{ marginTop: 24 }}
            bodyStyle={{ background: '#fafafa', padding: '16px 24px' }}
          >
            <Space direction="vertical" size="small">
              <Text strong>使用说明：</Text>
              <Text type="secondary">
                1. 选择处理模式或自定义参数配置
              </Text>
              <Text type="secondary">
                2. 拖拽或点击上传视频文件（支持 MP4、MOV、AVI、MKV 格式）
              </Text>
              <Text type="secondary">
                3. 等待视频处理完成，系统会自动提取关键帧
              </Text>
              <Text type="secondary">
                4. 查看和下载提取的关键帧
              </Text>
            </Space>
          </Card>
        </div>
      </Content>
    </Layout>
  );
};

export default HomePage;
