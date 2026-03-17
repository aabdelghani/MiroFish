<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">MIROFISH</div>
      </div>
      
      <div class="header-center">
        <div class="view-switcher">
          <button 
            v-for="mode in ['graph', 'split', 'workbench']" 
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ $t('common.modes.' + mode) }}
            {{ { graph: 'Graph', split: 'Split', workbench: 'Workbench' }[mode] }}
            {{ { graph: $t('nav.graph'), split: $t('nav.split'), workbench: $t('nav.workbench') }[mode] }}
            {{ { graph: t.view_graph, split: t.view_split, workbench: t.view_workbench }[mode] }}
            {{ { graph: t('mainView.graph'), split: t('mainView.split'), workbench: t('mainView.workbench') }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <LanguageSelector light />
        <div class="workflow-step">
          <span class="step-num">Step 3/5</span>
          <span class="step-name">{{ $t('steps.startSimulation') }}</span>
          <span class="step-name">Run Simulation</span>
          <span class="step-name">{{ $t('home.step3Title') }}</span>
          <span class="step-name">{{ t.step3Title }}</span>
          <span class="step-name">{{ t('mainView.stepSim') }}</span>
        </div>
        <div class="step-divider"></div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="content-area">
      <!-- Left Panel: Graph -->
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <GraphPanel 
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="3"
          :isSimulating="isSimulating"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step 3 Start Simulation -->
      <!-- Right Panel: Step 3 Run Simulation -->
      <!-- Right Panel: Step3 Start Simulation -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step3Simulation
          :simulationId="currentSimulationId"
          :maxRounds="maxRounds"
          :minutesPerRound="minutesPerRound"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { t, currentLang } from '../i18n'
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import GraphPanel from '../components/GraphPanel.vue'
import Step3Simulation from '../components/Step3Simulation.vue'
import LanguageSelector from '../components/LanguageSelector.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, getSimulationConfig, stopSimulation, closeSimulationEnv, getEnvStatus } from '../api/simulation'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// Props
const props = defineProps({
  simulationId: String
})

// Layout State
const viewMode = ref('split')

// Data State
const currentSimulationId = ref(route.params.simulationId)
const maxRounds = ref(route.query.maxRounds ? parseInt(route.query.maxRounds) : null)
const minutesPerRound = ref(30)
// Read maxRounds from the query on init so the child component gets it immediately.
const maxRounds = ref(route.query.maxRounds ? parseInt(route.query.maxRounds) : null)
const minutesPerRound = ref(30) // Default to 30 minutes per round.
// Get maxRounds from query params at init time to ensure child components receive the value immediately
const maxRounds = ref(route.query.maxRounds ? parseInt(route.query.maxRounds) : null)
const minutesPerRound = ref(30) // Default 30 minutes per round
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing') // processing | completed | error

// --- Computed Layout Styles ---
const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

// --- Status Computed ---
const statusClass = computed(() => {
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Completed'
  return 'Running'
})

const isSimulating = computed(() => currentStatus.value === 'processing')

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}

// --- Layout Methods ---
const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = 'split'
  } else {
    viewMode.value = target
  }
}

const handleGoBack = async () => {
  addLog(t('simulation.preparingReturnStep2'))
  // Close any running simulation before returning to Step 2.
  addLog('Preparing to return to Step 2. Closing the simulation...')
  // 在返回 Step 2 之前，先关闭正在运行的模拟
  addLog('Returning to Step 2, closing simulation...')
  addLog(t('logs.srv_goingBackStep2'))
  
  // Stop polling.
  // Before returning to Step 2, close any running simulation
  addLog(t('simRun.preparingGoBack'))
  
  // Stop polling
  stopGraphRefresh()
  try {
    // Attempt a graceful shutdown first.
    // First try to gracefully close the simulation environment
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog(t('simulation.closingEnv'))
      addLog('Closing the simulation environment...')
      addLog(t('simRun.closingEnv'))
      addLog('Closing simulation environment...')
      addLog(t('logs.srv_closingEnv'))
      try {
        await closeSimulationEnv({
          simulation_id: currentSimulationId.value,
          timeout: 10
        })
        addLog(t('simulation.simEnvClosed'))
      } catch (closeErr) {
        addLog(t('simulation.closeEnvFailedRetry'))
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog(t('simulation.forceStopDone'))
        } catch (stopErr) {
          addLog(t('simulation.forceStopFailedErr', { msg: stopErr.message }))
        addLog('✓ Simulation environment closed')
      } catch (closeErr) {
        addLog('Close failed, force-stopping...')
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog('✓ Simulation force-stopped')
        } catch (stopErr) {
          addLog(`Force stop failed: ${stopErr.message}`)
        addLog(t('logs.srv_envClosed'))
      } catch (closeErr) {
        addLog(t('logs.srv_closeFailedForceStop'))
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog(t('logs.srv_simForceStopped'))
        } catch (stopErr) {
          addLog(t('logs.srv_forceStopFailed', { error: stopErr.message }))
        }
      }
    } else {
      if (isSimulating.value) {
        addLog(t('simulation.stoppingProcess'))
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog(t('simulation.simStopped'))
        } catch (err) {
          addLog(t('simulation.stopSimFailed', { msg: err.message }))
          addLog('✓ Simulation environment closed')
      } catch (closeErr) {
        addLog('Failed to close the environment. Attempting a forced stop...')
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog('✓ Simulation force-stopped')
        } catch (stopErr) {
          addLog(`Forced stop failed: ${stopErr.message}`)
        }
      }
    } else {
      // The environment is not running. Check whether a process still needs to be stopped.
      if (isSimulating.value) {
        addLog('Stopping simulation process...')
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog('✓ Simulation stopped')
        } catch (err) {
          addLog(`Failed to stop simulation: ${err.message}`)
        addLog(t('simRun.envClosed'))
      } catch (closeErr) {
        addLog(t('simRun.closeEnvFailedForceStop'))
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog(t('simRun.simForceStopped'))
        } catch (stopErr) {
          addLog(t('simRun.forceStopFailed', { error: stopErr.message }))
        }
      }
    } else {
      // Environment not running, check if process needs to be stopped
      if (isSimulating.value) {
        addLog(t('simRun.stoppingSimProcess'))
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog(t('simRun.simStopped'))
        } catch (err) {
          addLog(t('simRun.stopSimFailed', { error: err.message }))
        addLog('Stopping simulation process...')
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog('✓ Simulation stopped')
        } catch (err) {
          addLog(`Stop failed: ${err.message}`)
        addLog(t('logs.srv_stoppingSimProcess'))
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog(t('logs.srv_simStopped'))
        } catch (err) {
          addLog(t('logs.srv_stopSimFailed', { error: err.message }))
        }
      }
    }
  } catch (err) {
    addLog(t('simulation.checkStatusFailed', { msg: err.message }))
  }
    addLog(`Failed to inspect simulation status: ${err.message}`)
    addLog(`Check simulation status failed: ${err.message}`)
    addLog(t('logs.srv_checkStatusFailed', { error: err.message }))
  }
  
  // Return to Step 2 (environment setup).
    addLog(t('simRun.checkStatusFailed', { error: err.message }))
  }
  
  // Return to Step 2 (environment setup)
  router.push({ name: 'Simulation', params: { simulationId: currentSimulationId.value } })
}

const handleNextStep = () => {
  addLog(t('simulation.enterStep4'))
  // Step3Simulation handles report generation and routing directly.
  // This method remains as a fallback.
  addLog('Entered Step 4: Generate Report')
  // Step3Simulation component handles report generation and routing directly
  // This method is only a fallback
  addLog(t('simRun.enterStep4'))
  // Step3Simulation 组件会直接处理报告生成和路由跳转
  // 这个方法仅作为备用
  addLog('Entering Step 4: Report Generation')
  addLog(t('logs.enterStep', { step: 4, name: t('mainView.stepReport') }))
}

// --- Data Logic ---
const loadSimulationData = async () => {
  try {
    addLog(t('simulation.loadingSimData', { id: currentSimulationId.value }))
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
    addLog(`Loading simulation data: ${currentSimulationId.value}`)
    addLog(t('logs.srv_loadingSimData', { id: currentSimulationId.value }))
    
    // Fetch simulation data.
    addLog(t('simRun.loadingSimData', { id: currentSimulationId.value }))
    
    // Get simulation info
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
      
      // Fetch simulation config to read minutes_per_round.
      // Get simulation config to obtain minutes_per_round
      try {
        const configRes = await getSimulationConfig(currentSimulationId.value)
        if (configRes.success && configRes.data?.time_config?.minutes_per_round) {
          minutesPerRound.value = configRes.data.time_config.minutes_per_round
          addLog(t('simulation.timeConfig', { n: minutesPerRound.value }))
        }
      } catch (configErr) {
        addLog(t('simulation.timeConfigFallback', { n: minutesPerRound.value }))
      }
          addLog(`Time config: ${minutesPerRound.value} minutes per round`)
        }
      } catch (configErr) {
        addLog(`Failed to load time config. Using default: ${minutesPerRound.value} minutes per round`)
          addLog(`Time config: ${minutesPerRound.value} min/round`)
        }
      } catch (configErr) {
        addLog(`Time config failed, defaulting to ${minutesPerRound.value} min/round`)
          addLog(t('logs.srv_timeConfig', { mins: minutesPerRound.value }))
        }
      } catch (configErr) {
        addLog(t('logs.srv_timeConfigFallback', { mins: minutesPerRound.value }))
      }
      
      // Fetch project data.
          addLog(t('simRun.timeConfig', { minutes: minutesPerRound.value }))
        }
      } catch (configErr) {
        addLog(t('simRun.timeConfigFallback', { minutes: minutesPerRound.value }))
      }
      
      // Get project info
      if (simData.project_id) {
        const projRes = await getProject(simData.project_id)
        if (projRes.success && projRes.data) {
          projectData.value = projRes.data
          addLog(t('simulation.projectLoaded', { id: projRes.data.project_id }))
          addLog(`Project loaded: ${projRes.data.project_id}`)
          
          // Fetch graph data.
          addLog(t('simRun.projectLoaded', { id: projRes.data.project_id }))
          
          // Get graph data
          addLog(t('logs.srv_projectLoaded', { id: projRes.data.project_id }))

          // 获取 graph 数据
          if (projRes.data.graph_id) {
            await loadGraph(projRes.data.graph_id)
          }
        }
      }
    } else {
      addLog(t('simulation.loadSimDataFailed', { msg: simRes.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('simulation.loadError', { msg: err.message }))
      addLog(`Failed to load simulation data: ${simRes.error || 'Unknown error'}`)
    }
  } catch (err) {
    addLog(`Load error: ${err.message}`)
      addLog(t('simRun.loadSimDataFailed', { error: simRes.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('simRun.loadException', { error: err.message }))
      addLog(`Failed to load simulation: ${simRes.error || 'Unknown error'}`)
    }
  } catch (err) {
    addLog(`Load exception: ${err.message}`)
      addLog(t('logs.srv_loadSimFailed', { error: simRes.error || t('errors.unknown') }))
    }
  } catch (err) {
    addLog(t('logs.srv_loadException', { error: err.message }))
  }
}

const loadGraph = async (graphId) => {
  if (!isSimulating.value) graphLoading.value = true
  // Avoid full-screen loading flashes during active simulation refreshes.
  // Keep loading visible for manual refreshes and the initial load.
  // When simulating, auto-refresh doesn't show fullscreen loading to avoid flickering
  // Show loading for manual refresh or initial load
  if (!isSimulating.value) {
    graphLoading.value = true
  }
  
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      if (!isSimulating.value) addLog(t('simulation.graphDataLoaded'))
    }
  } catch (err) {
    addLog(t('simulation.graphLoadFailed', { msg: err.message }))
      if (!isSimulating.value) {
        addLog('Graph data loaded')
      }
    }
  } catch (err) {
    addLog(`Failed to load graph data: ${err.message}`)
        addLog(t('simRun.graphDataLoaded'))
      }
    }
  } catch (err) {
    addLog(t('simRun.graphLoadFailed', { error: err.message }))
    addLog(`Graph load failed: ${err.message}`)
        addLog(t('logs.graphDataLoaded'))
      }
    }
  } catch (err) {
    addLog(t('logs.srv_graphLoadFailed', { error: err.message }))
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

// --- Auto Refresh Logic ---
let graphRefreshTimer = null

const startGraphRefresh = () => {
  if (graphRefreshTimer) return
  addLog(t('simulation.graphRefreshOn'))
  addLog('Enabled live graph refresh (30s)')
  // Refresh immediately, then every 30 seconds
  addLog(t('simRun.startGraphRefresh'))
  // Refresh once immediately, then every 30 seconds
  addLog('Started real-time graph refresh (30s)')
  addLog(t('logs.srv_graphRefreshStart'))
  // 立即刷新一次，然后每30秒刷新
  graphRefreshTimer = setInterval(refreshGraph, 30000)
}

const stopGraphRefresh = () => {
  if (graphRefreshTimer) {
    clearInterval(graphRefreshTimer)
    graphRefreshTimer = null
    addLog(t('simulation.graphRefreshOff'))
    addLog('Stopped live graph refresh')
    addLog(t('simRun.stopGraphRefresh'))
    addLog('Stopped real-time graph refresh')
    addLog(t('logs.srv_graphRefreshStop'))
  }
}

watch(isSimulating, (newValue) => {
  if (newValue) {
    startGraphRefresh()
  } else {
    stopGraphRefresh()
  }
}, { immediate: true })

onMounted(() => {
  addLog(t('simulation.simRunViewInit'))
  if (maxRounds.value) {
    addLog(t('simulation.customRoundsValue', { n: maxRounds.value }))
  addLog('SimulationRunView initialized')
  addLog(t('simRun.viewInit'))
  
  // Log maxRounds config (value already obtained from query params at init)
  if (maxRounds.value) {
    addLog(t('simRun.customRounds', { rounds: maxRounds.value }))
  addLog('SimulationRunView initialized')
  
  // 记录 maxRounds 配置（值已在初始化时从 query 参数获取）
  if (maxRounds.value) {
    addLog(`Custom simulation rounds: ${maxRounds.value}`)
  addLog(t('logs.srv_init'))
  
  // 记录 maxRounds 配置（值已在初始化时从 query 参数获取）
  if (maxRounds.value) {
    addLog(t('logs.customRounds', { rounds: maxRounds.value }))
  }
  
  // Log maxRounds configuration (value is already read from query on init)
  if (maxRounds.value) {
    addLog(`Custom simulation rounds: ${maxRounds.value}`)
  }
  loadSimulationData()
})

onUnmounted(() => {
  stopGraphRefresh()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #FFF;
  overflow: hidden;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

/* Header */
.app-header {
  height: 60px;
  border-bottom: 1px solid #EAEAEA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #FFF;
  z-index: 100;
  position: relative;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.view-switcher {
  display: flex;
  background: #F5F5F5;
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: #FFF;
  color: #000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #999;
}

.step-name {
  font-weight: 700;
  color: #000;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: #E0E0E0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.processing .dot { background: #FF5722; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

/* Content */
.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left {
  border-right: 1px solid #EAEAEA;
}
</style>
