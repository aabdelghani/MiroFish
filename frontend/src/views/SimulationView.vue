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
          <span class="step-num">Step 2/5</span>
          <span class="step-name">{{ $t('steps.envSetup') }}</span>
          <span class="step-name">Environment Setup</span>
          <span class="step-name">{{ $t('home.step2Title') }}</span>
          <span class="step-name">{{ t.step2Title }}</span>
          <span class="step-name">{{ t('mainView.stepEnv') }}</span>
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
          :currentPhase="2"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step 2 Environment Setup -->
      <!-- Right Panel: Step2 Environment Setup -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step2EnvSetup
          :simulationId="currentSimulationId"
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import GraphPanel from '../components/GraphPanel.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import LanguageSelector from '../components/LanguageSelector.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, stopSimulation, getEnvStatus, closeSimulationEnv } from '../api/simulation'

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
  if (currentStatus.value === 'completed') return 'Ready'
  return 'Preparing'
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 100) {
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

const handleGoBack = () => {
  // Return to the process page.
  if (projectData.value?.project_id) {
    router.push({ name: 'Process', params: { projectId: projectData.value.project_id } })
  } else {
    router.push('/')
  }
}

const handleNextStep = (params = {}) => {
  addLog(t('simulation.enterStep3'))
  if (params.maxRounds) {
    addLog(t('simulation.customRounds', { n: params.maxRounds }))
  } else {
    addLog(t('simulation.autoRounds'))
  }
  addLog('Entered Step 3: Run Simulation')
  
  // Record the round configuration.
  if (params.maxRounds) {
    addLog(`Custom simulation rounds: ${params.maxRounds}`)
  } else {
    addLog('Using the auto-generated round count')
  addLog('Entering Step 3: Simulation')
  
  // 记录模拟轮数配置
  if (params.maxRounds) {
    addLog(`Custom rounds: ${params.maxRounds}`)
  } else {
    addLog('Using auto-configured rounds')
  addLog(t('logs.enterStep', { step: 3, name: t('mainView.stepSim') }))
  
  // 记录模拟轮数配置
  if (params.maxRounds) {
    addLog(t('logs.customRounds', { rounds: params.maxRounds }))
  } else {
    addLog(t('logs.sv_autoRounds'))
  }
  
  // Build route params.
  addLog(t('simView.enterStep3'))

  if (params.maxRounds) {
    addLog(t('simView.customRounds', { rounds: params.maxRounds }))
  } else {
    addLog(t('simView.autoRounds'))
  }

  const routeParams = {
    name: 'SimulationRun',
    params: { simulationId: currentSimulationId.value }
  }
  if (params.maxRounds) {
    routeParams.query = { maxRounds: params.maxRounds }
  }
  
  // Pass custom rounds through the query string when provided.
  if (params.maxRounds) {
    routeParams.query = { maxRounds: params.maxRounds }
  }
  
  // Navigate to Step 3.

  if (params.maxRounds) {
    routeParams.query = { maxRounds: params.maxRounds }
  }

  router.push(routeParams)
}

// --- Data Logic ---

/** When user returns from Step 3 to Step 2, close any running simulation. */
/**
 * Check for a running simulation and shut it down.
 * Returning from Step 3 to Step 2 implies the user wants to exit the run.
 */
const checkAndStopRunningSimulation = async () => {
  if (!currentSimulationId.value) return
  try {
    // Check whether the simulation environment is still alive first.
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog(t('simulation.simRunningClosing'))
      addLog('Detected a running simulation environment. Closing it...')
      addLog('Simulation environment running, closing...')
      addLog(t('logs.sv_envRunningClosing'))
      
      // Try a graceful shutdown first.
const checkAndStopRunningSimulation = async () => {
  if (!currentSimulationId.value) return

  try {
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })

    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog(t('simView.envRunningClosing'))

      try {
        const closeRes = await closeSimulationEnv({
          simulation_id: currentSimulationId.value,
          timeout: 10
        })
        if (closeRes.success) {
          addLog(t('simulation.simEnvClosed'))
        } else {
          addLog(t('simulation.closeEnvFailed', { msg: closeRes.error || t('common.unknownError') }))
          await forceStopSimulation()
        }
      } catch (closeErr) {
        addLog(t('simulation.closeEnvError', { msg: closeErr.message }))

        if (closeRes.success) {
          addLog(t('simView.envClosed'))
        } else {
          addLog(t('simView.closeEnvFailed', { error: closeRes.error || t('common.unknownError') }))
          await forceStopSimulation()
        }
      } catch (closeErr) {
        addLog(t('simView.closeEnvError', { error: closeErr.message }))
          addLog('✓ Simulation environment closed')
        } else {
          addLog(`Failed to close simulation: ${closeRes.error || 'Unknown error'}`)
          addLog(t('logs.sv_envClosed'))
        } else {
          addLog(t('logs.sv_closeEnvFailed', { error: closeRes.error || t('errors.unknown') }))
          // 如果优雅关闭失败，尝试强制停止
          await forceStopSimulation()
        }
      } catch (closeErr) {
        addLog(`Exception closing simulation: ${closeErr.message}`)
        addLog(t('logs.sv_closeEnvException', { error: closeErr.message }))
        // 如果优雅关闭异常，尝试强制停止
        await forceStopSimulation()
      }
    } else {
      const simRes = await getSimulation(currentSimulationId.value)
      if (simRes.success && simRes.data?.status === 'running') {
        addLog(t('simulation.simRunningStopping'))
          addLog('✓ Simulation environment closed')
        } else {
          addLog(`Failed to close the simulation environment: ${closeRes.error || 'Unknown error'}`)
          // Fall back to a forced stop if graceful shutdown fails.
          await forceStopSimulation()
        }
      } catch (closeErr) {
        addLog(`Error while closing the simulation environment: ${closeErr.message}`)
        // Fall back to a forced stop if graceful shutdown errors.
        await forceStopSimulation()
      }
    } else {
      // The environment is not alive, but a process may still be running.
      const simRes = await getSimulation(currentSimulationId.value)
      if (simRes.success && simRes.data?.status === 'running') {
        addLog('Detected a running simulation state. Stopping it...')
        addLog(t('simView.simRunningStopping'))
        addLog('Simulation running, stopping...')
        addLog(t('logs.sv_simRunningStopping'))
        await forceStopSimulation()
      }
    }
  } catch (err) {
    console.warn('Check env status failed:', err)
  }
}

    // Failure to inspect environment status should not block navigation.
    console.warn('Failed to inspect simulation status:', err)
  }
}

/**
 * Force stop the simulation.
 */
    console.warn('Check simulation status failed:', err)
  }
}

const forceStopSimulation = async () => {
  try {
    const stopRes = await stopSimulation({ simulation_id: currentSimulationId.value })
    if (stopRes.success) {
      addLog(t('simulation.forceStopDone'))
    } else {
      addLog(t('simulation.forceStopFailed', { msg: stopRes.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('simulation.forceStopError', { msg: err.message }))
      addLog('✓ Simulation force-stopped')
    } else {
      addLog(`Failed to force-stop the simulation: ${stopRes.error || 'Unknown error'}`)
    }
  } catch (err) {
    addLog(`Error while force-stopping the simulation: ${err.message}`)
      addLog(t('simView.simForceStopped'))
    } else {
      addLog(t('simView.forceStopFailed', { error: stopRes.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('simView.forceStopError', { error: err.message }))
      addLog('✓ Simulation force-stopped')
    } else {
      addLog(`Force stop failed: ${stopRes.error || 'Unknown error'}`)
    }
  } catch (err) {
    addLog(`Force stop exception: ${err.message}`)
      addLog(t('logs.sv_simForceStoppedOk'))
    } else {
      addLog(t('logs.sv_forceStopFailed', { error: stopRes.error || t('errors.unknown') }))
    }
  } catch (err) {
    addLog(t('logs.sv_forceStopException', { error: err.message }))
  }
}

const loadSimulationData = async () => {
  try {
    addLog(t('simulation.loadingSimData', { id: currentSimulationId.value }))
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
    addLog(`Loading simulation data: ${currentSimulationId.value}`)
    addLog(t('logs.sv_loadingSimData', { id: currentSimulationId.value }))
    
    // Fetch simulation data.
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
      
      // Fetch project data.
    addLog(t('simView.loadingSimData', { id: currentSimulationId.value }))

    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data

      if (simData.project_id) {
        const projRes = await getProject(simData.project_id)
        if (projRes.success && projRes.data) {
          projectData.value = projRes.data
          addLog(t('simulation.projectLoaded', { id: projRes.data.project_id }))
          addLog(`Project loaded: ${projRes.data.project_id}`)
          
          // Fetch graph data.
          addLog(t('simView.projectLoaded', { id: projRes.data.project_id }))

          addLog(t('logs.sv_projectLoaded', { id: projRes.data.project_id }))

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
    addLog(`Load exception: ${err.message}`)
      addLog(t('simView.loadSimDataFailed', { error: simRes.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('simView.loadException', { error: err.message }))
      addLog(`Failed to load simulation data: ${simRes.error || 'Unknown error'}`)
    }
  } catch (err) {
    addLog(`Load exception: ${err.message}`)
      addLog(t('logs.sv_loadSimFailed', { error: simRes.error || t('errors.unknown') }))
    }
  } catch (err) {
    addLog(t('logs.sv_loadException', { error: err.message }))
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog(t('simulation.graphDataLoaded'))
    }
  } catch (err) {
    addLog(t('simulation.graphLoadFailed', { msg: err.message }))
      addLog('Graph data loaded successfully')
    }
  } catch (err) {
    addLog(`Failed to load graph: ${err.message}`)
      addLog(t('simView.graphDataLoaded'))
    }
  } catch (err) {
    addLog(t('simView.graphLoadFailed', { error: err.message }))
      addLog('Graph data loaded successfully')
    }
  } catch (err) {
    addLog(`Graph load failed: ${err.message}`)
      addLog(t('logs.graphDataLoaded'))
    }
  } catch (err) {
    addLog(t('logs.sv_graphLoadFailed', { error: err.message }))
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

onMounted(async () => {
  addLog(t('simulation.simViewInit'))
  await checkAndStopRunningSimulation()
  addLog('SimulationView initialized')
  addLog(t('logs.sv_init'))
  
  // Check for and close any running simulation when the user returns from Step 3
  await checkAndStopRunningSimulation()
  
  // Load simulation data
  addLog(t('simView.viewInit'))

  await checkAndStopRunningSimulation()

  loadSimulationData()
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

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
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
