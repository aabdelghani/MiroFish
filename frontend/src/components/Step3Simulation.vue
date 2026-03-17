<template>
  <div class="simulation-panel">
    <!-- Top control bar -->
    <div class="control-bar">
      <div class="status-group">
        <!-- Twitter platform progress -->
    <div class="control-bar">
      <div class="status-group">
        <div class="platform-status twitter" :class="{ active: runStatus.twitter_running, completed: runStatus.twitter_completed }">
          <div class="platform-header">
            <span class="platform-name">INFO PLAZA</span>
            <span class="status-chip">{{ runStatus.twitter_completed ? 'DONE' : (runStatus.twitter_running ? 'LIVE' : 'IDLE') }}</span>
          </div>
          <div class="platform-stats">
            <span class="stat">
              <span class="stat-label">ROUND</span>
              <span class="stat-value mono">{{ runStatus.twitter_current_round || 0 }}<span class="stat-total">/{{ runStatus.total_rounds || maxRounds || '-' }}</span></span>
            </span>
            <span class="stat">
              <span class="stat-label">Elapsed Time</span>
              <span class="stat-value mono">{{ twitterElapsedTime }}</span>
            </span>
            <span class="stat">
              <span class="stat-label">ACTS</span>
              <span class="stat-value mono">{{ runStatus.twitter_actions_count || 0 }}</span>
            </span>
          </div>
          <!-- Available actions tooltip -->
          <div class="actions-tooltip">
            <div class="tooltip-title">Available Actions</div>
            <div class="tooltip-actions">
              <span class="tooltip-action">POST</span>
              <span class="tooltip-action">LIKE</span>
              <span class="tooltip-action">REPOST</span>
              <span class="tooltip-action">QUOTE</span>
              <span class="tooltip-action">FOLLOW</span>
              <span class="tooltip-action">IDLE</span>
            </div>
          </div>
        </div>
        
        <!-- Reddit platform progress -->
            <span>ROUND {{ runStatus.twitter_current_round || 0 }}/{{ runStatus.total_rounds || maxRounds || '-' }}</span>
            <span>TIME {{ twitterElapsedTime }}</span>
            <span>ACTS {{ runStatus.twitter_actions_count || 0 }}</span>
          </div>
        </div>

        <div class="platform-status reddit" :class="{ active: runStatus.reddit_running, completed: runStatus.reddit_completed }">
          <div class="platform-header">
            <span class="platform-name">TOPIC COMMUNITY</span>
            <span class="status-chip">{{ runStatus.reddit_completed ? 'DONE' : (runStatus.reddit_running ? 'LIVE' : 'IDLE') }}</span>
          </div>
          <div class="platform-stats">
            <span class="stat">
              <span class="stat-label">ROUND</span>
              <span class="stat-value mono">{{ runStatus.reddit_current_round || 0 }}<span class="stat-total">/{{ runStatus.total_rounds || maxRounds || '-' }}</span></span>
            </span>
            <span class="stat">
              <span class="stat-label">Elapsed Time</span>
              <span class="stat-value mono">{{ redditElapsedTime }}</span>
            </span>
            <span class="stat">
              <span class="stat-label">ACTS</span>
              <span class="stat-value mono">{{ runStatus.reddit_actions_count || 0 }}</span>
            </span>
          </div>
          <!-- Available actions tooltip -->
          <div class="actions-tooltip">
            <div class="tooltip-title">Available Actions</div>
            <div class="tooltip-actions">
              <span class="tooltip-action">POST</span>
              <span class="tooltip-action">COMMENT</span>
              <span class="tooltip-action">LIKE</span>
              <span class="tooltip-action">DISLIKE</span>
              <span class="tooltip-action">SEARCH</span>
              <span class="tooltip-action">TREND</span>
              <span class="tooltip-action">FOLLOW</span>
              <span class="tooltip-action">MUTE</span>
              <span class="tooltip-action">REFRESH</span>
              <span class="tooltip-action">IDLE</span>
            </div>
            <span>ROUND {{ runStatus.reddit_current_round || 0 }}/{{ runStatus.total_rounds || maxRounds || '-' }}</span>
            <span>TIME {{ redditElapsedTime }}</span>
            <span>ACTS {{ runStatus.reddit_actions_count || 0 }}</span>
          </div>
        </div>
      </div>

      <div class="action-controls">
        <button class="action-btn primary" :disabled="phase !== 2 || isGeneratingReport" @click="handleNextStep">
          <span v-if="isGeneratingReport" class="loading-spinner-small"></span>
          {{ isGeneratingReport ? 'Starting...' : 'Generate result report' }} 
          {{ isGeneratingReport ? $t('step3.launching') : $t('step3.generateReport') }} 
          {{ isGeneratingReport ? t.s3_starting : t.s3_gen_report }} 
          {{ isGeneratingReport ? $t('step3.starting') : $t('step3.startReport') }} 
          <span v-if="!isGeneratingReport" class="arrow-icon">→</span>
          {{ isGeneratingReport ? 'REPORT LINKING...' : 'GENERATE REPORT' }}
        </button>
      </div>
    </div>

    <!-- Main Content: Dual Timeline -->
    <div class="main-content-area" ref="scrollContainer">
      <!-- Timeline Header -->
      <div class="timeline-header" v-if="allActions.length > 0">
        <div class="timeline-stats">
          <span class="total-count">TOTAL EVENTS: <span class="mono">{{ allActions.length }}</span></span>
          <span class="platform-breakdown">
            <span class="breakdown-item twitter">
              <svg class="mini-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
              <span class="mono">{{ twitterActionsCount }}</span>
            </span>
            <span class="breakdown-divider">/</span>
            <span class="breakdown-item reddit">
              <svg class="mini-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
              <span class="mono">{{ redditActionsCount }}</span>
            </span>
          </span>
        </div>
      </div>
      
      <!-- Timeline Feed -->
      <div class="timeline-feed">
        <div class="timeline-axis"></div>
        
        <TransitionGroup name="timeline-item">
          <div 
            v-for="action in chronologicalActions" 
            :key="action._uniqueId || action.id || `${action.timestamp}-${action.agent_id}`" 
            class="timeline-item"
            :class="action.platform"
          >
            <div class="timeline-marker">
              <div class="marker-dot"></div>
            </div>
            
            <div class="timeline-card">
              <div class="card-header">
                <div class="agent-info">
                  <div class="avatar-placeholder">{{ (action.agent_name || 'A')[0] }}</div>
                  <span class="agent-name">{{ action.agent_name }}</span>
                </div>
                
                <div class="header-meta">
                  <div class="platform-indicator">
                    <svg v-if="action.platform === 'twitter'" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                    <svg v-else viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                  </div>
                  <div class="action-badge" :class="getActionTypeClass(action.action_type)">
                    {{ getActionTypeLabel(action.action_type) }}
                  </div>
                </div>
              </div>
              
              <div class="card-body">
                <!-- CREATE_POST: Publish post -->
                <div v-if="action.action_type === 'CREATE_POST' && action.action_args?.content" class="content-text main-text">
                  {{ action.action_args.content }}
                </div>

                <!-- QUOTE_POST: Quote post -->
                <template v-if="action.action_type === 'QUOTE_POST'">
                  <div v-if="action.action_args?.quote_content" class="content-text">
                    {{ action.action_args.quote_content }}
                  </div>
                  <div v-if="action.action_args?.original_content" class="quoted-block">
                    <div class="quote-header">
                      <svg class="icon-small" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                      <span class="quote-label">@{{ action.action_args.original_author_name || 'User' }}</span>
                    </div>
                    <div class="quote-text">
                      {{ truncateContent(action.action_args.original_content, 150) }}
                    </div>
                  </div>
                </template>

                <!-- REPOST: Repost -->
                <template v-if="action.action_type === 'REPOST'">
                  <div class="repost-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"></polyline><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><polyline points="7 23 3 19 7 15"></polyline><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg>
                    <span class="repost-label">Reposted from @{{ action.action_args?.original_author_name || 'User' }}</span>
                  </div>
                  <div v-if="action.action_args?.original_content" class="repost-content">
                    {{ truncateContent(action.action_args.original_content, 200) }}
                  </div>
                </template>

                <!-- LIKE_POST: Like post -->
                <template v-if="action.action_type === 'LIKE_POST'">
                  <div class="like-info">
                    <svg class="icon-small filled" viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                    <span class="like-label">Liked @{{ action.action_args?.post_author_name || 'User' }}'s post</span>
                  </div>
                  <div v-if="action.action_args?.post_content" class="liked-content">
                    "{{ truncateContent(action.action_args.post_content, 120) }}"
                  </div>
                </template>

                <!-- CREATE_COMMENT: Create comment -->
                <template v-if="action.action_type === 'CREATE_COMMENT'">
                  <div v-if="action.action_args?.content" class="content-text">
                    {{ action.action_args.content }}
                  </div>
                  <div v-if="action.action_args?.post_id" class="comment-context">
                    <svg class="icon-small" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                    <span>Reply to post #{{ action.action_args.post_id }}</span>
                  </div>
                </template>

                <!-- SEARCH_POSTS: Search posts -->
                <template v-if="action.action_type === 'SEARCH_POSTS'">
                  <div class="search-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    <span class="search-label">Search Query:</span>
                    <span class="search-query">"{{ action.action_args?.query || '' }}"</span>
                  </div>
                </template>

                <!-- FOLLOW: Follow user -->
                <template v-if="action.action_type === 'FOLLOW'">
                  <div class="follow-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
                    <span class="follow-label">Followed @{{ action.action_args?.target_user || action.action_args?.user_id || 'User' }}</span>
                  </div>
                </template>

                <!-- UPVOTE / DOWNVOTE -->
                <template v-if="action.action_type === 'UPVOTE_POST' || action.action_type === 'DOWNVOTE_POST'">
                  <div class="vote-info">
                    <svg v-if="action.action_type === 'UPVOTE_POST'" class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"></polyline></svg>
                    <svg v-else class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                    <span class="vote-label">{{ action.action_type === 'UPVOTE_POST' ? 'Upvoted' : 'Downvoted' }} Post</span>
                  </div>
                  <div v-if="action.action_args?.post_content" class="voted-content">
                    "{{ truncateContent(action.action_args.post_content, 120) }}"
                  </div>
                </template>

                <!-- DO_NOTHING: No action (idle) -->
                <template v-if="action.action_type === 'DO_NOTHING'">
                  <div class="idle-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    <span class="idle-label">Action Skipped</span>
                  </div>
                </template>

                <!-- Generic fallback: unknown type or content not handled above -->
                <div v-if="!['CREATE_POST', 'QUOTE_POST', 'REPOST', 'LIKE_POST', 'CREATE_COMMENT', 'SEARCH_POSTS', 'FOLLOW', 'UPVOTE_POST', 'DOWNVOTE_POST', 'DO_NOTHING'].includes(action.action_type) && action.action_args?.content" class="content-text">
                  {{ action.action_args.content }}
                </div>
              </div>

              <div class="card-footer">
                <span class="time-tag">R{{ action.round_num }} • {{ formatActionTime(action.timestamp) }}</span>
                <!-- Platform tag removed as it is in header now -->
              </div>
    <div class="main-content-area">
      <div class="intel-layout">
        <section class="timeline-shell full">
          <div class="timeline-header" v-if="allActions.length > 0">
            <div class="timeline-statline">
              <span>[ TOTAL {{ allActions.length }} ]</span>
              <span>[ TW {{ twitterActionsCount }} ]</span>
              <span>[ RD {{ redditActionsCount }} ]</span>
              <span>[ STATUS {{ runStatus.runner_status || 'running' }} ]</span>
            </div>
          </div>

        <div v-if="allActions.length === 0" class="waiting-state">
          <div class="pulse-ring"></div>
          <span>{{ t.s3_waiting }}</span>
        </div>
          <div class="timeline-feed">
            <div class="timeline-axis"></div>
            <TransitionGroup name="timeline-item">
              <article
                v-for="action in chronologicalActions"
                :key="action._uniqueId || action.id || `${action.timestamp}-${action.agent_id}`"
                class="timeline-item"
                :class="action.platform"
              >
                <div class="timeline-marker">
                  <div class="marker-core"></div>
                </div>

                <div class="timeline-card">
                  <div class="card-header">
                    <div>
                      <div class="agent-name">{{ action.agent_name || 'Unknown agent' }}</div>
                      <div class="agent-meta">{{ action.platform || 'stream' }} :: {{ getActionTypeLabel(action.action_type) }}</div>
                    </div>
                    <div class="round-pill">R{{ action.round_num || action.round || 0 }}</div>
                  </div>

                  <div class="card-body">
                    <div v-if="getPrimaryContent(action)" class="content-text main-text">
                      {{ getPrimaryContent(action) }}
                    </div>
                    <div v-if="getSecondaryContent(action)" class="support-block">
                      {{ getSecondaryContent(action) }}
                    </div>
                    <div v-if="getContextLabel(action)" class="context-line">
                      {{ getContextLabel(action) }}
                    </div>
                  </div>

                  <div class="card-footer">
                    <span>{{ formatActionTime(action.timestamp) }}</span>
                    <span>{{ getPlatformLabel(action.platform) }}</span>
                  </div>
                </div>
              </article>
            </TransitionGroup>

            <div v-if="allActions.length === 0" class="waiting-state">
              <div class="waiting-title">[ AGENT SOCIETIES BOOTING ]</div>
              <div class="waiting-copy">Awaiting first live actions from the simulation bus.</div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <div class="system-logs">
      <div class="log-header">
        <span>SIMULATION MONITOR</span>
        <span>{{ simulationId || 'NO_SIMULATION' }}</span>
      </div>
      <div class="log-content" ref="logContent">
        <div v-for="(log, idx) in systemLogs" :key="idx" class="log-line">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { t, currentLang, toggleLang } from '../i18n'
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { 
  startSimulation, 
  stopSimulation,
  getRunStatus, 
  getRunStatusDetail
} from '../api/simulation'
import { generateReport } from '../api/report'
import { getRunStatus, getRunStatusDetail, startSimulation, stopSimulation } from '../api/simulation'

const props = defineProps({
  simulationId: String,
  maxRounds: Number, // Max rounds passed from Step 2
  minutesPerRound: {
    type: Number,
    default: 30 // Default: 30 minutes per round
  maxRounds: Number, // Max rounds passed from Step2
  minutesPerRound: {
    type: Number,
    default: 30 // Default 30 minutes per round
  maxRounds: Number,
  minutesPerRound: {
    type: Number,
    default: 30
  },
  projectData: Object,
  graphData: Object,
  systemLogs: Array
})

const emit = defineEmits(['go-back', 'next-step', 'add-log', 'update-status'])

const router = useRouter()
const { t } = useI18n()

// State
const isGeneratingReport = ref(false)
const phase = ref(0) // 0: not started, 1: running, 2: completed
const isGeneratingReport = ref(false)
const phase = ref(0)
const isStarting = ref(false)
const runStatus = ref({})
const allActions = ref([]) // All actions (incrementally accumulated)
const actionIds = ref(new Set()) // For deduplicating actions
const scrollContainer = ref(null)

// Computed
// Show actions in chronological order (latest at the bottom)
const actionIds = ref(new Set()) // Action ID set for deduplication
const scrollContainer = ref(null)

// Computed
// Display actions in chronological order (latest at the bottom)
const allActions = ref([])
const actionIds = ref(new Set())
const prevTwitterRound = ref(0)
const prevRedditRound = ref(0)
const logContent = ref(null)
let statusTimer = null
let detailTimer = null

const chronologicalActions = computed(() => {
  return [...allActions.value].sort((a, b) => {
    const first = new Date(a.timestamp || 0).getTime()
    const second = new Date(b.timestamp || 0).getTime()
    return first - second
  })
})

// Per-platform action counts
const twitterActionsCount = computed(() => {
  return allActions.value.filter(a => a.platform === 'twitter').length
})
const twitterActionsCount = computed(() => allActions.value.filter(action => action.platform === 'twitter').length)
const redditActionsCount = computed(() => allActions.value.filter(action => action.platform === 'reddit').length)

function addLog(message) {
  emit('add-log', message)
}

// Format simulated elapsed time (based on rounds and minutes per round)
// Format simulated elapsed time (calculated from rounds and minutes per round)
const formatElapsedTime = (currentRound) => {
function formatElapsedTime(currentRound) {
  if (!currentRound || currentRound <= 0) return '0h 0m'
  const totalMinutes = currentRound * props.minutesPerRound
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours}h ${minutes}m`
}

// Simulated elapsed time on Twitter-like platform
// Twitter platform simulated elapsed time
const twitterElapsedTime = computed(() => {
  return formatElapsedTime(runStatus.value.twitter_current_round || 0)
})

// Simulated elapsed time on Reddit-like platform
// Reddit platform simulated elapsed time
const redditElapsedTime = computed(() => {
  return formatElapsedTime(runStatus.value.reddit_current_round || 0)
})

// Methods
const addLog = (msg) => {
  emit('add-log', msg)
}

// Reset all state (for restarting simulation)
const resetAllState = () => {
const twitterElapsedTime = computed(() => formatElapsedTime(runStatus.value.twitter_current_round || 0))
const redditElapsedTime = computed(() => formatElapsedTime(runStatus.value.reddit_current_round || 0))

function resetAllState() {
  phase.value = 0
  runStatus.value = {}
  allActions.value = []
  actionIds.value = new Set()
  prevTwitterRound.value = 0
  prevRedditRound.value = 0
  startError.value = null
  isStarting.value = false
  isStopping.value = false
  stopPolling()  // Stop any previous polling
  stopPolling()  // Stop any existing polling
}

// Start simulation
const doStartSimulation = async () => {
  stopPolling()
}

async function doStartSimulation() {
  if (!props.simulationId) {
    addLog('Error: missing simulationId')
    addLog(t('errors.missingSimulationId'))
    return
  }
  
  // Reset all state first to avoid interference from previous runs
    addLog(t('step3.missingSimId'))
    return
  }

  // Reset all state first to avoid interference from previous simulation

  resetAllState()
  isStarting.value = true
  startError.value = null
  addLog(t('step3.startingParallel'))
  addLog('Initializing dual-platform simulation workbench...')
  addLog(t('logs.s3_startingParallelSim'))
  emit('update-status', 'processing')

  try {
    const params = {
      simulation_id: props.simulationId,
      platform: 'parallel',
      force: true,  // Force restart
      enable_graph_memory_update: true  // Enable dynamic graph memory updates
      enable_graph_memory_update: true  // Enable dynamic graph memory update
      force: true,
      enable_graph_memory_update: true
    }

    if (props.maxRounds) {
      params.max_rounds = props.maxRounds
      addLog(`Set max simulation rounds: ${props.maxRounds}`)
    }
    
    addLog('Graph memory update mode enabled')
      addLog(t('step3.setMaxRounds', { rounds: props.maxRounds }))
    }
    
    addLog(t('step3.graphMemoryEnabled'))
      addLog(t('logs.s3_setMaxRounds', { rounds: props.maxRounds }))
    }
    
    addLog(t('logs.s3_graphUpdateEnabled'))
    
    const res = await startSimulation(params)
    
    if (res.success && res.data) {
      if (res.data.force_restarted) {
        addLog('✓ Cleaned old logs and restarted simulation')
      }
      addLog('✓ Simulation engine started')
        addLog('✓ ' + t('step3.oldLogsCleared'))
      }
      addLog('✓ ' + t('step3.engineStarted'))
        addLog(t('logs.s3_oldLogsCleared'))
      }
      addLog(t('logs.s3_engineStarted'))
      addLog(`  ├─ PID: ${res.data.process_pid || '-'}`)
      
      addLog(`Max rounds pinned to ${props.maxRounds}`)
    }

    const response = await startSimulation(params)
    if (response.success && response.data) {
      addLog('Simulation engine online')
      phase.value = 1
      runStatus.value = response.data
      startStatusPolling()
      startDetailPolling()
    } else {
      startError.value = res.error || '启动失败'
      addLog(`✗ Failed to start: ${res.error || 'Unknown error'}`)
      startError.value = res.error || t('step3.startFailed', { error: '' })
      addLog('✗ ' + t('step3.startFailed', { error: res.error || t('common.unknownError') }))
      startError.value = res.error || t('errors.startFailed')
      addLog(`✗ ${t('errors.startFailed')}: ${res.error || t('errors.unknown')}`)
      emit('update-status', 'error')
    }
  } catch (err) {
    startError.value = err.message
    addLog(`✗ Start exception: ${err.message}`)
    addLog('✗ ' + t('step3.startError', { error: err.message }))
      addLog(`启动失败: ${response.error || '未知错误'}`)
      emit('update-status', 'error')
    }
  } catch (error) {
    addLog(`启动异常: ${error.message}`)
    addLog(t('logs.s3_startException', { error: err.message }))
    emit('update-status', 'error')
  } finally {
    isStarting.value = false
  }
}

// Stop simulation
const handleStopSimulation = async () => {
  if (!props.simulationId) return
  
  isStopping.value = true
  addLog('Stopping simulation...')
  addLog(t('step3.stoppingSim'))
  addLog(t('logs.s3_stoppingSim'))
  
  try {
    const res = await stopSimulation({ simulation_id: props.simulationId })
    
    if (res.success) {
      addLog('✓ Simulation stopped')
      addLog('✓ ' + t('step3.simStopped'))
      addLog(t('logs.s3_simStopped'))
      phase.value = 2
      stopPolling()
      emit('update-status', 'completed')
    } else {
      addLog(`Failed to stop simulation: ${res.error || 'Unknown error'}`)
    }
  } catch (err) {
    addLog(`Stop exception: ${err.message}`)
      addLog(t('step3.stopFailed', { error: res.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('step3.stopError', { error: err.message }))
      addLog(`${t('errors.stopFailed')}: ${res.error || t('errors.unknown')}`)
    }
  } catch (err) {
    addLog(t('logs.s3_stopException', { error: err.message }))
  } finally {
    isStopping.value = false
  }
}

// Polling
// Poll status
let statusTimer = null
let detailTimer = null

const startStatusPolling = () => {
async function handleStopSimulation() {
  if (!props.simulationId) return

  addLog('Stopping simulation...')
  try {
    const response = await stopSimulation({ simulation_id: props.simulationId })
    if (response.success) {
      addLog('Simulation stopped')
      phase.value = 2
      stopPolling()
      emit('update-status', 'completed')
    }
  } catch (error) {
    addLog(`停止异常: ${error.message}`)
  }
}

function startStatusPolling() {
  statusTimer = setInterval(fetchRunStatus, 2000)
}

function startDetailPolling() {
  if (statusTimer) clearInterval(statusTimer)
  statusTimer = setInterval(fetchRunStatus, 2000)
}

const startDetailPolling = () => {
  if (detailTimer) clearInterval(detailTimer)
  detailTimer = setInterval(fetchRunStatusDetail, 3000)
}

function stopPolling() {
  if (statusTimer) clearInterval(statusTimer)
  if (detailTimer) clearInterval(detailTimer)
  statusTimer = null
  detailTimer = null
}

// Track last round per platform to log changes
// Track previous round per platform for detecting changes and logging
const prevTwitterRound = ref(0)
const prevRedditRound = ref(0)

const fetchRunStatus = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getRunStatus(props.simulationId)
    
    if (res.success && res.data) {
      const data = res.data
      
      runStatus.value = data
      
      // Detect per-platform round changes and log them
      // Detect round changes per platform and output logs
      if (data.twitter_current_round > prevTwitterRound.value) {
        addLog(`[Plaza] R${data.twitter_current_round}/${data.total_rounds} | T:${data.twitter_simulated_hours || 0}h | A:${data.twitter_actions_count}`)
        prevTwitterRound.value = data.twitter_current_round
      }
      
      if (data.reddit_current_round > prevRedditRound.value) {
        addLog(`[Community] R${data.reddit_current_round}/${data.total_rounds} | T:${data.reddit_simulated_hours || 0}h | A:${data.reddit_actions_count}`)
        prevRedditRound.value = data.reddit_current_round
      }
      
      // Check if the simulation has completed (via runner_status or per-platform completion)
      const isCompleted = data.runner_status === 'completed' || data.runner_status === 'stopped'
      
      // Extra check: if runner_status is not yet updated but platforms report completion
      // Detect if simulation completed (via runner_status or platform completion status)
      const isCompleted = data.runner_status === 'completed' || data.runner_status === 'stopped'
      
      // Additional check: if backend hasn't updated runner_status yet but platforms report completion
      // Detect via twitter_completed and reddit_completed status
      const platformsCompleted = checkPlatformsCompleted(data)
      
      if (isCompleted || platformsCompleted) {
        if (platformsCompleted && !isCompleted) {
          addLog('✓ ' + t('step3.allPlatformsDone'))
        }
        addLog('✓ ' + t('step3.simCompleted'))
          addLog(t('logs.s3_allPlatformsCompleted'))
        }
        addLog(t('logs.s3_simCompleted'))
        phase.value = 2
        stopPolling()
        emit('update-status', 'completed')
      }
    }
  } catch (err) {
    console.warn('Run status fetch failed:', err)
  }
}

// Check whether all enabled platforms have completed
const checkPlatformsCompleted = (data) => {
  // If no platform data, treat as not completed
  if (!data) return false
  
  // Per-platform completion flags
  const twitterCompleted = data.twitter_completed === true
  const redditCompleted = data.reddit_completed === true
  
  // If at least one platform is complete, ensure all enabled platforms are complete
  // Use actions_count / running flags to detect enabled platforms
  const twitterEnabled = (data.twitter_actions_count > 0) || data.twitter_running || twitterCompleted
  const redditEnabled = (data.reddit_actions_count > 0) || data.reddit_running || redditCompleted
  
  // If no platform is enabled, treat as not completed
  if (!twitterEnabled && !redditEnabled) return false
  
  // All enabled platforms must be completed
// Check if all enabled platforms have completed
const checkPlatformsCompleted = (data) => {
  // If no platform data, return false
  if (!data) return false
  
  // Check each platform's completion status
  const twitterCompleted = data.twitter_completed === true
  const redditCompleted = data.reddit_completed === true
  
  // If at least one platform completed, check if all enabled platforms completed
  // Determine if platform is enabled by actions_count (count > 0 or was running)
  const twitterEnabled = (data.twitter_actions_count > 0) || data.twitter_running || twitterCompleted
  const redditEnabled = (data.reddit_actions_count > 0) || data.reddit_running || redditCompleted
  
  // If no platform is enabled, return false
  if (!twitterEnabled && !redditEnabled) return false
  
  // Check if all enabled platforms have completed
function checkPlatformsCompleted(data) {
  if (!data) return false
  const twitterCompleted = data.twitter_completed === true
  const redditCompleted = data.reddit_completed === true
  const twitterEnabled = (data.twitter_actions_count > 0) || data.twitter_running || twitterCompleted
  const redditEnabled = (data.reddit_actions_count > 0) || data.reddit_running || redditCompleted
  if (!twitterEnabled && !redditEnabled) return false
  if (twitterEnabled && !twitterCompleted) return false
  if (redditEnabled && !redditCompleted) return false
  return true
}

async function fetchRunStatus() {
  if (!props.simulationId) return
  try {
    const res = await getRunStatusDetail(props.simulationId)
    
    if (res.success && res.data) {
      // Use all_actions for the full action list
      const serverActions = res.data.all_actions || []
      
      // Incrementally append new actions (deduplicated)
      let newActionsAdded = 0
      serverActions.forEach(action => {
        // Generate a unique ID
      // Use all_actions to get the complete action list
      const serverActions = res.data.all_actions || []
      
      // Incrementally add new actions (deduplication)
      let newActionsAdded = 0
      serverActions.forEach(action => {
        // Generate unique ID
        const actionId = action.id || `${action.timestamp}-${action.platform}-${action.agent_id}-${action.action_type}`
        
        if (!actionIds.value.has(actionId)) {
          actionIds.value.add(actionId)
          allActions.value.push({
            ...action,
            _uniqueId: actionId
          })
          newActionsAdded++
        }
      })
      
      // Don't auto-scroll, let user freely browse the timeline
      // New actions are appended at the bottom
    }
  } catch (err) {
    console.warn('Detail status fetch failed:', err)
    const response = await getRunStatus(props.simulationId)
    if (!(response.success && response.data)) return

    const data = response.data
    runStatus.value = data

    if (data.twitter_current_round > prevTwitterRound.value) {
      addLog(`[Plaza] R${data.twitter_current_round}/${data.total_rounds} | T:${data.twitter_simulated_hours || 0}h | A:${data.twitter_actions_count}`)
      prevTwitterRound.value = data.twitter_current_round
    }

    if (data.reddit_current_round > prevRedditRound.value) {
      addLog(`[Community] R${data.reddit_current_round}/${data.total_rounds} | T:${data.reddit_simulated_hours || 0}h | A:${data.reddit_actions_count}`)
      prevRedditRound.value = data.reddit_current_round
    }

    const completed = data.runner_status === 'completed' || data.runner_status === 'stopped' || checkPlatformsCompleted(data)
    if (completed) {
      addLog('Simulation complete')
      phase.value = 2
      stopPolling()
      emit('update-status', 'completed')
    }
  } catch (error) {
    console.warn('获取运行状态失败:', error)
  }
}

async function fetchRunStatusDetail() {
  if (!props.simulationId) return

  try {
    const response = await getRunStatusDetail(props.simulationId)
    if (!(response.success && response.data)) return

    const serverActions = response.data.all_actions || []
    serverActions.forEach(action => {
      const actionId = action.id || `${action.timestamp}-${action.platform}-${action.agent_id}-${action.action_type}`
      if (actionIds.value.has(actionId)) return
      actionIds.value.add(actionId)
      allActions.value.push({ ...action, _uniqueId: actionId })
    })
  } catch (error) {
    console.warn('获取详细状态失败:', error)
  }
}

function getActionTypeLabel(type) {
  const labels = {
    CREATE_POST: 'POST',
    REPOST: 'REPOST',
    LIKE_POST: 'LIKE',
    CREATE_COMMENT: 'COMMENT',
    LIKE_COMMENT: 'LIKE',
    DO_NOTHING: 'IDLE',
    FOLLOW: 'FOLLOW',
    SEARCH_POSTS: 'SEARCH',
    QUOTE_POST: 'QUOTE',
    UPVOTE_POST: 'UPVOTE',
    DOWNVOTE_POST: 'DOWNVOTE',
    TREND: 'TREND',
    REFRESH: 'REFRESH'
  }
  return labels[type] || type || 'UNKNOWN'
}

function getPrimaryContent(action) {
  const args = action.action_args || {}
  return args.content || args.quote_content || args.query || args.post_content || ''
}

function getSecondaryContent(action) {
  const args = action.action_args || {}
  if (args.original_content) return args.original_content
  if (args.post_content && args.post_content !== args.content) return args.post_content
  return ''
}

function getContextLabel(action) {
  const args = action.action_args || {}
  if (action.action_type === 'FOLLOW') return `target :: ${args.target_user || args.user_id || 'user'}`
  if (action.action_type === 'SEARCH_POSTS') return `query :: ${args.query || 'n/a'}`
  if (action.action_type === 'CREATE_COMMENT') return `reply :: post #${args.post_id || 'n/a'}`
  if (args.original_author_name) return `source :: @${args.original_author_name}`
  if (args.post_author_name) return `source :: @${args.post_author_name}`
  return ''
}

function getPlatformLabel(platform) {
  if (platform === 'twitter') return 'PLAZA'
  if (platform === 'reddit') return 'COMMUNITY'
  return (platform || 'STREAM').toUpperCase()
}

function formatActionTime(timestamp) {
  if (!timestamp) return ''
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return ''
  }
}

const handleNextStep = async () => {
  if (!props.simulationId) {
    addLog('Error: missing simulationId')
    addLog(t('step3.missingSimId'))
    addLog(t('errors.missingSimulationId'))
    return
  }

  if (isGeneratingReport.value) {
    addLog('Report generation has already been requested, please wait...')
    addLog(t('step3.reportStarting'))
    addLog(t('logs.s3_reportRequestSent'))
    return
  }

  isGeneratingReport.value = true
  addLog('Starting report generation...')
  addLog(t('step3.reportStarting'))
  addLog(t('logs.s3_startingReportGen'))
  
async function handleNextStep() {
  if (!props.simulationId || isGeneratingReport.value) return
  isGeneratingReport.value = true
  addLog('Starting report generation...')

  try {
    const response = await generateReport({
      simulation_id: props.simulationId,
      force_regenerate: true
    })
    
    if (res.success && res.data) {
      const reportId = res.data.report_id
      addLog(`✓ Report generation task started: ${reportId}`)
      addLog(t('logs.s3_reportTaskStarted', { id: reportId }))
      
      // Navigate to the report page
      router.push({ name: 'Report', params: { reportId } })
    } else {
      addLog(`✗ Failed to start report generation: ${res.error || 'Unknown error'}`)
      isGeneratingReport.value = false
    }
  } catch (err) {
    addLog(`✗ Report generation exception: ${err.message}`)
      addLog('✓ ' + t('step3.reportTaskStarted', { id: reportId }))
      
      // Navigate to report page
      router.push({ name: 'Report', params: { reportId } })
    } else {
      addLog('✗ ' + t('step3.reportStartFailed', { error: res.error || t('common.unknownError') }))
      isGeneratingReport.value = false
    }
  } catch (err) {
    addLog('✗ ' + t('step3.reportStartError', { error: err.message }))

    if (response.success && response.data) {
      addLog(`Report task online: ${response.data.report_id}`)
      router.push({ name: 'Report', params: { reportId: response.data.report_id } })
      return
    }

    addLog(`报告生成失败: ${response.error || '未知错误'}`)
  } catch (error) {
    addLog(`报告生成异常: ${error.message}`)
  } finally {
      addLog(`✗ ${t('errors.reportGenFailed')}: ${res.error || t('errors.unknown')}`)
      isGeneratingReport.value = false
    }
  } catch (err) {
    addLog(t('logs.s3_reportGenException', { error: err.message }))
    isGeneratingReport.value = false
  }
}

watch(() => props.systemLogs?.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})

onMounted(() => {
  addLog('Step 3 simulation run initialized')
  addLog(t('step3.simRunInit'))
  addLog(t('logs.s3_init'))
  if (props.simulationId) {
    doStartSimulation()
  }
  addLog('Simulation workbench armed')
  if (props.simulationId) doStartSimulation()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.simulation-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: radial-gradient(circle at top, rgba(17, 40, 30, 0.95), #050908 48%);
  color: #dbffed;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
  overflow: hidden;
}

.control-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(122, 240, 181, 0.12);
  background: rgba(4, 9, 8, 0.85);
  backdrop-filter: blur(18px);
}

.status-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.platform-status {
  min-width: 220px;
  padding: 12px 14px;
  border: 1px solid rgba(122, 240, 181, 0.12);
  background: rgba(255, 255, 255, 0.02);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.platform-status.active {
  border-color: rgba(122, 240, 181, 0.34);
  background: rgba(122, 240, 181, 0.06);
}

.platform-status.completed {
  border-color: rgba(255, 211, 106, 0.34);
}

.platform-header,
.platform-stats,
.action-controls,
.timeline-statline,
.card-header,
.card-footer,
.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.platform-name,
.action-btn,
.timeline-statline,
.round-pill,
.log-header,
.agent-meta,
.context-line,
.card-footer {
  font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
}

.platform-name,
.timeline-statline,
.log-header {
  letter-spacing: 0.14em;
  font-size: 10px;
}

.platform-name {
  color: #8cf6c2;
}

.platform-stats {
  margin-top: 8px;
  flex-wrap: wrap;
  font-size: 11px;
  color: rgba(219, 255, 237, 0.76);
}

.status-chip,
.round-pill {
  padding: 3px 7px;
  border: 1px solid rgba(122, 240, 181, 0.16);
  font-size: 10px;
  color: rgba(219, 255, 237, 0.72);
}

.action-controls {
  flex-shrink: 0;
}

.action-btn {
  padding: 11px 14px;
  border: 1px solid rgba(122, 240, 181, 0.16);
  background: rgba(255, 255, 255, 0.02);
  color: #dbffed;
  letter-spacing: 0.12em;
  font-size: 11px;
  cursor: pointer;
}

.action-btn.primary {
  background: linear-gradient(90deg, rgba(77, 226, 165, 0.16), rgba(255, 211, 106, 0.12));
}

.action-btn:hover:not(:disabled) {
  border-color: rgba(122, 240, 181, 0.34);
}

.action-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.main-content-area {
  flex: 1;
  overflow-y: auto;
}

.intel-layout {
  display: block;
  padding: 20px 24px 24px;
}

.timeline-shell {
  min-width: 0;
}

.timeline-header {
  position: sticky;
  top: 0;
  z-index: 4;
  padding-bottom: 12px;
  background: linear-gradient(180deg, rgba(5, 9, 8, 0.92), rgba(5, 9, 8, 0.32));
  backdrop-filter: blur(12px);
}

.timeline-statline {
  justify-content: flex-start;
  flex-wrap: wrap;
  padding: 10px 12px;
  border: 1px solid rgba(122, 240, 181, 0.12);
  background: rgba(255, 255, 255, 0.03);
  color: rgba(219, 255, 237, 0.72);
}

.timeline-feed {
  position: relative;
  min-height: 100%;
  padding: 12px 0 24px;
}

.timeline-axis {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(180deg, rgba(122, 240, 181, 0.16), rgba(122, 240, 181, 0.02));
  transform: translateX(-50%);
}

.timeline-item {
  position: relative;
  width: 100%;
  display: flex;
  margin-bottom: 24px;
}

.timeline-item.twitter {
  justify-content: flex-start;
  padding-right: 50%;
}

.timeline-item.reddit {
  justify-content: flex-end;
  padding-left: 50%;
}

.timeline-marker {
  position: absolute;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  width: 14px;
  height: 14px;
  border: 1px solid rgba(122, 240, 181, 0.2);
  background: #06100d;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.marker-core {
  width: 6px;
  height: 6px;
  background: #82f7bf;
}

.timeline-card {
  width: calc(100% - 44px);
  padding: 16px 18px;
  border: 1px solid rgba(122, 240, 181, 0.12);
  background:
    linear-gradient(180deg, rgba(12, 23, 18, 0.96), rgba(5, 10, 8, 0.98)),
    repeating-linear-gradient(0deg, rgba(122, 240, 181, 0.03), rgba(122, 240, 181, 0.03) 1px, transparent 1px, transparent 20px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.18);
}

.timeline-item.twitter .timeline-card {
  margin-right: 32px;
}

.timeline-item.reddit .timeline-card {
  margin-left: 32px;
}

.card-header {
  align-items: flex-start;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(122, 240, 181, 0.08);
}

.agent-name {
  font-size: 14px;
  font-weight: 700;
  color: #f2fff8;
}

.agent-meta,
.context-line,
.card-footer {
  font-size: 10px;
  letter-spacing: 0.1em;
  color: rgba(219, 255, 237, 0.56);
  text-transform: uppercase;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.content-text {
  font-size: 13px;
  line-height: 1.7;
  color: rgba(219, 255, 237, 0.85);
}

.main-text {
  color: #f6fff9;
}

.support-block {
  padding: 10px 12px;
  border: 1px solid rgba(122, 240, 181, 0.08);
  background: rgba(255, 255, 255, 0.03);
  font-size: 12px;
  line-height: 1.6;
  color: rgba(219, 255, 237, 0.72);
}

.waiting-state {
  min-height: 380px;
  display: grid;
  place-items: center;
  text-align: center;
  border: 1px dashed rgba(122, 240, 181, 0.16);
  color: rgba(219, 255, 237, 0.55);
}

.waiting-title {
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.16em;
  margin-bottom: 10px;
  color: #8cf6c2;
}

.system-logs {
  flex-shrink: 0;
  padding: 14px 18px 16px;
  border-top: 1px solid rgba(122, 240, 181, 0.1);
  background: rgba(2, 5, 4, 0.98);
  font-family: 'JetBrains Mono', monospace;
}

.log-header {
  font-size: 10px;
  letter-spacing: 0.14em;
  color: #8cf6c2;
  margin-bottom: 10px;
}

.log-content {
  max-height: 132px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.log-line {
  display: grid;
  grid-template-columns: 112px 1fr;
  gap: 12px;
  font-size: 11px;
  line-height: 1.5;
}

.log-time {
  color: rgba(219, 255, 237, 0.44);
}

.log-msg {
  color: rgba(219, 255, 237, 0.8);
}

.loading-spinner-small {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.timeline-item-enter-active {
  transition: all 0.35s ease;
}

.timeline-item-enter-from {
  opacity: 0;
  transform: translateY(14px);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 1440px) {
  .intel-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .control-bar {
    flex-direction: column;
  }

  .timeline-axis,
  .timeline-marker {
    left: 14px;
    transform: none;
  }

  .timeline-item,
  .timeline-item.twitter,
  .timeline-item.reddit {
    padding: 0 0 0 34px;
    justify-content: flex-start;
  }

  .timeline-item.twitter .timeline-card,
  .timeline-item.reddit .timeline-card {
    margin: 0;
    width: 100%;
  }

  .log-line {
    grid-template-columns: 1fr;
    gap: 3px;
  }
}
</style>
