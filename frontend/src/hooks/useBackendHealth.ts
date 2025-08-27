// Travel Agent Pro - Backend Health Check Hook
// 管理后端服务健康状态检查

import { useEffect } from 'react'
import { checkBackendHealth } from '../lib/api'
import { useUIStore } from '../stores/uiStore'

export function useBackendHealth() {
  const setBackendHealthy = useUIStore(state => state.setBackendHealthy)
  const backendHealthy = useUIStore(state => state.backendHealthy)
  
  useEffect(() => {
    const checkHealth = async () => {
      const isHealthy = await checkBackendHealth()
      setBackendHealthy(isHealthy)
    }
    
    checkHealth()
  }, []) // 移除setBackendHealthy依赖，因为它是稳定的Zustand函数
  
  return {
    backendHealthy,
    recheckHealth: async () => {
      const isHealthy = await checkBackendHealth()
      setBackendHealthy(isHealthy)
      return isHealthy
    }
  }
}
