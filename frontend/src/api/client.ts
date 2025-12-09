/**
 * Axios HTTP 客户端配置
 */
import axios, { AxiosError } from 'axios';

// 获取API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 创建Axios实例
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    // config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // 统一错误处理
    if (error.response) {
      // 服务器返回错误状态码
      const status = error.response.status;
      const data: any = error.response.data;

      switch (status) {
        case 400:
          console.error('请求参数错误:', data.detail || error.message);
          break;
        case 404:
          console.error('资源不存在:', data.detail || error.message);
          break;
        case 422:
          console.error('验证失败:', data.detail || error.message);
          break;
        case 500:
          console.error('服务器错误:', data.detail || error.message);
          break;
        default:
          console.error('未知错误:', error.message);
      }

      // 返回更友好的错误信息
      const errorMessage = data.detail || data.message || error.message || '请求失败';
      throw new Error(errorMessage);
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('网络错误，请检查连接');
      throw new Error('网络错误，请检查连接');
    } else {
      // 其他错误
      console.error('请求配置错误:', error.message);
      throw new Error(error.message);
    }
  }
);

export default apiClient;
