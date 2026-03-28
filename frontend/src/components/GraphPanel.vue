<template>
  <div class="graph-panel">
    <div class="panel-header">
      <span class="panel-title">Starry Story Layer</span>
      <div class="header-tools">
        <button class="tool-btn" @click="$emit('refresh')" :disabled="loading" title="刷新星层">
          <span class="icon-refresh" :class="{ spinning: loading }">↻</span>
          <span class="btn-text">Refresh</span>
        </button>
        <button class="tool-btn" @click="$emit('toggle-maximize')" title="最大化/还原">
          <span class="icon-maximize">⛶</span>
        </button>
      </div>
    </div>

    <div class="graph-container">
      <div
        v-if="graphData"
        ref="sceneRef"
        class="starfield-scene"
        :class="sceneClasses"
        @click="handleSceneBackgroundClick"
      >
        <!-- required structure: ambient far-star layer / trace layer / node layer / story-card layer / subtle HUD controls / close affordance -->
        <div class="starfield-vignette"></div>
        <div class="starfield-depth starfield-depth--far">
          <span
            v-for="particle in farParticles"
            :key="particle.id"
            class="ambient-particle"
            :style="particleStyle(particle)"
          ></span>
        </div>

        <svg class="starfield-traces" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <path
            v-for="trace in traces"
            :key="trace.uuid || `${trace.source_node_uuid}-${trace.target_node_uuid}`"
            class="trace-path"
            :class="{ 'trace-path--active': isTraceActive(trace) }"
            :d="trace.path"
          />
        </svg>

        <div class="starfield-depth starfield-depth--mid">
          <span
            v-for="particle in midParticles"
            :key="particle.id"
            class="ambient-particle"
            :style="particleStyle(particle)"
          ></span>
        </div>

        <div class="starfield-nodes">
          <button
            v-for="node in starfieldNodes"
            :key="node.uuid"
            class="star-node"
            :class="[
              `star-node--${node.depthBand}`,
              { 'star-node--active': node.uuid === activeNodeId, 'star-node--muted': activeNodeId && node.uuid !== activeNodeId }
            ]"
            :style="nodeStyle(node)"
            type="button"
            @click.stop="activateNode(node)"
          >
            <span class="star-node__halo"></span>
            <span class="star-node__core"></span>
            <span class="star-node__label">{{ node.story_card?.title || node.name || 'Untitled memory' }}</span>
          </button>
        </div>

        <div class="starfield-depth starfield-depth--near">
          <span
            v-for="particle in nearParticles"
            :key="particle.id"
            class="ambient-particle"
            :style="particleStyle(particle)"
          ></span>
        </div>

        <transition name="story-card-fade">
          <article
            v-if="showStoryCard && activeStoryCard"
            ref="storyCardRef"
            class="story-card"
            @click.stop
          >
            <button class="story-card__close" type="button" @click="closeStoryCard" aria-label="Close story card">
              ✕
            </button>
            <div class="story-card__eyebrow">Summoned Memory</div>
            <h3 class="story-card__title">{{ activeStoryCard.title }}</h3>
            <p class="story-card__body">{{ activeStoryCard.description }}</p>
          </article>
        </transition>

        <div class="starfield-hud">
          <div v-if="entityTypes.length" class="hud-chip hud-chip--legend">
            <span class="hud-label">Constellations</span>
            <div class="legend-items">
              <span v-for="type in entityTypes" :key="type.name" class="legend-item">
                <span class="legend-dot" :style="{ background: type.color }"></span>
                {{ type.name }}
              </span>
            </div>
          </div>
          <div v-if="activeNodeLabel" class="hud-chip hud-chip--focus">
            <span class="hud-label">Awakened star</span>
            <strong>{{ activeNodeLabel }}</strong>
          </div>
        </div>

        <div v-if="currentPhase === 1 || isSimulating" class="graph-building-hint">
          <div class="memory-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="memory-icon">
              <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-4.04z" />
              <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-4.04z" />
            </svg>
          </div>
          {{ isSimulating ? 'GraphRAG长短期记忆实时更新中' : '星层正在缓慢刷新…' }}
        </div>

        <div v-if="showSimulationFinishedHint" class="graph-building-hint finished-hint">
          <div class="hint-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="hint-icon">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </div>
          <span class="hint-text">还有少量内容处理中，建议稍后手动刷新星层</span>
          <button class="hint-close-btn" @click="dismissFinishedHint" title="关闭提示">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>

      <div v-else-if="loading" class="graph-state">
        <div class="loading-spinner"></div>
        <p>星层数据加载中...</p>
      </div>

      <div v-else class="graph-state">
        <div class="empty-icon">✦</div>
        <p class="empty-text">等待故事星层生成...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { buildAmbientParticles, mapEdgesToTraces, mapNodesToStarfield } from '../utils/starfieldPresentation'

const props = defineProps({
  graphData: Object,
  loading: Boolean,
  currentPhase: Number,
  isSimulating: Boolean,
})

defineEmits(['refresh', 'toggle-maximize'])

const sceneRef = ref(null)
const storyCardRef = ref(null)
const activeNodeId = ref(null)
const focusStage = ref('idle')
const prefersReducedMotion = ref(false)
const showSimulationFinishedHint = ref(false)
const wasSimulating = ref(false)
const timers = []

const defaultScene = {
  motion: {
    reduced_motion_supported: true,
    focus_sequence: ['node-activate', 'trace-flow', 'camera-push', 'card-reveal'],
  },
  limits: { max_particles: 24 },
  contrast: { card_text_min_ratio: 4.5 },
}

const sceneConfig = computed(() => ({
  ...defaultScene,
  ...(props.graphData?.scene || {}),
  motion: {
    ...defaultScene.motion,
    ...(props.graphData?.scene?.motion || {}),
  },
  limits: {
    ...defaultScene.limits,
    ...(props.graphData?.scene?.limits || {}),
  },
  contrast: {
    ...defaultScene.contrast,
    ...(props.graphData?.scene?.contrast || {}),
  },
}))

const entityTypes = computed(() => {
  if (!props.graphData?.nodes) return []

  const palette = ['#8ab4ff', '#7be0cb', '#c9a3ff', '#ffd28f', '#ff9bc6', '#a6f3ff']
  const typeMap = new Map()

  props.graphData.nodes.forEach((node) => {
    const type = node.labels?.find((label) => label !== 'Entity') || 'Memory'
    if (!typeMap.has(type)) {
      typeMap.set(type, {
        name: type,
        color: palette[typeMap.size % palette.length],
      })
    }
  })

  return Array.from(typeMap.values())
})

const starfieldNodes = computed(() => mapNodesToStarfield(props.graphData?.nodes || [], props.graphData?.edges || []))
const traces = computed(() => mapEdgesToTraces(starfieldNodes.value, props.graphData?.edges || []))
const particles = computed(() => buildAmbientParticles(sceneConfig.value.limits.max_particles))
const farParticles = computed(() => particles.value.filter((particle) => particle.band === 'far'))
const midParticles = computed(() => particles.value.filter((particle) => particle.band === 'mid'))
const nearParticles = computed(() => particles.value.filter((particle) => particle.band === 'near'))

const activeNode = computed(() => starfieldNodes.value.find((node) => node.uuid === activeNodeId.value) || null)
const activeNodeLabel = computed(() => activeNode.value?.story_card?.title || activeNode.value?.name || '')
const activeStoryCard = computed(() => activeNode.value?.story_card || null)
const showStoryCard = computed(() => Boolean(activeNode.value) && (prefersReducedMotion.value || focusStage.value === 'card'))

const sceneClasses = computed(() => ({
  'starfield-scene--has-focus': Boolean(activeNode.value),
  'starfield-scene--trace': ['trace', 'camera', 'card'].includes(focusStage.value),
  'starfield-scene--camera': ['camera', 'card'].includes(focusStage.value) && !prefersReducedMotion.value,
  'starfield-scene--settled': showStoryCard.value,
  'starfield-scene--reduced-motion': prefersReducedMotion.value || !sceneConfig.value.motion.reduced_motion_supported,
}))

const dismissFinishedHint = () => {
  showSimulationFinishedHint.value = false
}

watch(
  () => props.isSimulating,
  (newValue) => {
    if (wasSimulating.value && !newValue) {
      showSimulationFinishedHint.value = true
    }
    wasSimulating.value = newValue
  },
  { immediate: true },
)

watch(
  () => props.graphData,
  () => {
    activeNodeId.value = null
    focusStage.value = 'idle'
    clearFocusTimers()
  },
  { deep: true },
)

function clearFocusTimers() {
  while (timers.length) {
    window.clearTimeout(timers.pop())
  }
}

function runFocusSequence() {
  clearFocusTimers()

  if (!activeNode.value) {
    focusStage.value = 'idle'
    return
  }

  if (prefersReducedMotion.value || !sceneConfig.value.motion.reduced_motion_supported) {
    focusStage.value = 'card'
    return
  }

  focusStage.value = 'node'
  timers.push(window.setTimeout(() => { focusStage.value = 'trace' }, 110))
  timers.push(window.setTimeout(() => { focusStage.value = 'camera' }, 240))
  timers.push(window.setTimeout(() => { focusStage.value = 'card' }, 420))
}

function activateNode(node) {
  activeNodeId.value = node.uuid
  runFocusSequence()
}

function closeStoryCard() {
  activeNodeId.value = null
  focusStage.value = 'idle'
  clearFocusTimers()
}

function handleSceneBackgroundClick(event) {
  if (!activeNode.value) return
  if (event.target.closest('.story-card') || event.target.closest('.star-node')) return
  closeStoryCard()
}

function handleKeydown(event) {
  if (event.key === 'Escape') {
    closeStoryCard()
  }
}

function handleReducedMotionChange(event) {
  prefersReducedMotion.value = event.matches
}

function isTraceActive(trace) {
  if (!activeNodeId.value) return false
  return trace.source_node_uuid === activeNodeId.value || trace.target_node_uuid === activeNodeId.value
}

function nodeStyle(node) {
  return {
    left: `${node.orbitX}%`,
    top: `${node.orbitY}%`,
    '--star-size': `${node.starSize}rem`,
    '--star-glow-scale': node.glowScale,
    '--star-delay': node.pulseDelay,
    '--star-hue': `${node.accentHue}`,
  }
}

function particleStyle(particle) {
  return {
    left: `${particle.x}%`,
    top: `${particle.y}%`,
    '--particle-size': `${particle.size}rem`,
    '--particle-opacity': particle.opacity,
    '--particle-duration': particle.duration,
    '--particle-delay': particle.delay,
  }
}

let mediaQuery

onMounted(() => {
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  prefersReducedMotion.value = mediaQuery.matches

  if (typeof mediaQuery.addEventListener === 'function') {
    mediaQuery.addEventListener('change', handleReducedMotionChange)
  } else if (typeof mediaQuery.addListener === 'function') {
    mediaQuery.addListener(handleReducedMotionChange)
  }

  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  clearFocusTimers()
  window.removeEventListener('keydown', handleKeydown)

  if (!mediaQuery) return

  if (typeof mediaQuery.removeEventListener === 'function') {
    mediaQuery.removeEventListener('change', handleReducedMotionChange)
  } else if (typeof mediaQuery.removeListener === 'function') {
    mediaQuery.removeListener(handleReducedMotionChange)
  }
})
</script>

<style scoped>
.graph-panel {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background:
    radial-gradient(circle at 20% 20%, rgba(80, 104, 181, 0.35), transparent 32%),
    radial-gradient(circle at 80% 10%, rgba(92, 52, 155, 0.32), transparent 24%),
    linear-gradient(180deg, #08111f 0%, #0b1427 45%, #070d18 100%);
  color: #edf6ff;
}

.panel-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 16px 20px;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(to bottom, rgba(7, 14, 27, 0.9), rgba(7, 14, 27, 0));
  pointer-events: none;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(236, 245, 255, 0.86);
  pointer-events: auto;
}

.header-tools {
  pointer-events: auto;
  display: flex;
  gap: 10px;
  align-items: center;
}

.tool-btn {
  height: 32px;
  padding: 0 12px;
  border: 1px solid rgba(186, 207, 255, 0.18);
  background: rgba(10, 18, 35, 0.6);
  backdrop-filter: blur(14px);
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  color: rgba(237, 246, 255, 0.8);
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
  font-size: 13px;
}

.tool-btn:hover {
  transform: translateY(-1px);
  border-color: rgba(186, 207, 255, 0.4);
  background: rgba(20, 32, 58, 0.72);
}

.tool-btn:disabled {
  opacity: 0.6;
  cursor: progress;
}

.tool-btn .btn-text {
  font-size: 12px;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.graph-container {
  width: 100%;
  height: 100%;
}

.starfield-scene {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  transition: transform 0.6s ease, filter 0.45s ease, background 0.45s ease;
}

.starfield-scene--camera {
  transform: scale(1.035);
}

.starfield-scene--has-focus {
  filter: saturate(1.08);
}

.starfield-scene--settled::after {
  opacity: 1;
}

.starfield-scene--reduced-motion,
.starfield-scene--reduced-motion * {
  animation-duration: 0.01ms !important;
  animation-iteration-count: 1 !important;
  transition-duration: 0.01ms !important;
  scroll-behavior: auto !important;
}

.starfield-vignette,
.starfield-scene::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.starfield-vignette {
  background:
    radial-gradient(circle at center, transparent 22%, rgba(4, 10, 20, 0.2) 58%, rgba(4, 10, 20, 0.62) 100%),
    linear-gradient(180deg, rgba(4, 10, 20, 0.14), rgba(4, 10, 20, 0.2));
}

.starfield-scene::after {
  background: radial-gradient(circle at center, rgba(3, 8, 19, 0.08), rgba(3, 8, 19, 0.5));
  opacity: 0;
  transition: opacity 0.35s ease;
}

.starfield-depth,
.starfield-traces,
.starfield-nodes,
.starfield-hud {
  position: absolute;
  inset: 0;
}

.starfield-depth {
  pointer-events: none;
}

.starfield-depth--far {
  opacity: 0.7;
  background:
    radial-gradient(circle at 15% 28%, rgba(255, 255, 255, 0.14) 0, transparent 18%),
    radial-gradient(circle at 70% 32%, rgba(170, 197, 255, 0.12) 0, transparent 20%),
    radial-gradient(circle at 40% 76%, rgba(124, 159, 255, 0.1) 0, transparent 26%);
}

.starfield-depth--mid {
  opacity: 0.9;
}

.starfield-depth--near {
  opacity: 1;
}

.ambient-particle {
  position: absolute;
  width: var(--particle-size);
  height: var(--particle-size);
  border-radius: 999px;
  background: rgba(237, 246, 255, 0.85);
  box-shadow: 0 0 12px rgba(186, 215, 255, 0.35);
  opacity: var(--particle-opacity);
  animation: particleDrift var(--particle-duration) ease-in-out infinite;
  animation-delay: var(--particle-delay);
}

.starfield-depth--near .ambient-particle {
  background: rgba(255, 247, 214, 0.9);
  box-shadow: 0 0 18px rgba(255, 223, 161, 0.3);
}

@keyframes particleDrift {
  0%, 100% {
    transform: translate3d(0, 0, 0) scale(1);
    opacity: calc(var(--particle-opacity) * 0.92);
  }
  50% {
    transform: translate3d(0.4rem, -0.55rem, 0) scale(1.08);
    opacity: var(--particle-opacity);
  }
}

.starfield-traces {
  width: 100%;
  height: 100%;
  z-index: 2;
}

.trace-path {
  fill: none;
  stroke: rgba(136, 168, 231, 0.22);
  stroke-width: 0.22;
  stroke-linecap: round;
  transition: stroke 0.35s ease, stroke-width 0.35s ease, opacity 0.35s ease;
}

.starfield-scene--trace .trace-path {
  opacity: 0.35;
}

.trace-path--active {
  stroke: rgba(165, 215, 255, 0.9);
  stroke-width: 0.34;
  opacity: 1;
  filter: drop-shadow(0 0 0.55rem rgba(165, 215, 255, 0.38));
}

.starfield-nodes {
  z-index: 3;
}

.star-node {
  position: absolute;
  width: calc(var(--star-size) * 1.1);
  height: calc(var(--star-size) * 1.1);
  transform: translate(-50%, -50%);
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  color: inherit;
}

.star-node__halo,
.star-node__core {
  position: absolute;
  inset: 0;
  border-radius: 999px;
}

.star-node__halo {
  background: radial-gradient(circle, rgba(150, 198, 255, 0.62) 0%, rgba(130, 164, 255, 0.18) 48%, transparent 72%);
  transform: scale(calc(1.15 * var(--star-glow-scale)));
  opacity: 0.82;
  animation: starPulse 4.8s ease-in-out infinite;
  animation-delay: var(--star-delay);
}

.star-node__core {
  background: radial-gradient(circle, rgba(255, 255, 255, 1) 0%, rgba(216, 233, 255, 0.94) 32%, rgba(152, 194, 255, 0.65) 62%, rgba(152, 194, 255, 0) 100%);
  box-shadow: 0 0 0.8rem rgba(189, 214, 255, 0.45);
}

.star-node__label {
  position: absolute;
  top: calc(100% + 0.45rem);
  left: 50%;
  transform: translateX(-50%);
  min-width: max-content;
  max-width: 9rem;
  text-align: center;
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  color: rgba(224, 234, 255, 0.82);
  text-shadow: 0 0 0.5rem rgba(7, 14, 27, 0.9);
  transition: color 0.25s ease, opacity 0.25s ease;
}

.star-node--far .star-node__label {
  opacity: 0.72;
}

.star-node--near .star-node__label {
  font-size: 0.78rem;
}

.star-node--active .star-node__halo {
  opacity: 1;
  transform: scale(calc(1.55 * var(--star-glow-scale)));
  background: radial-gradient(circle, rgba(214, 232, 255, 0.82) 0%, rgba(170, 203, 255, 0.3) 40%, rgba(120, 149, 255, 0.1) 72%, transparent 100%);
}

.star-node--active .star-node__core {
  box-shadow: 0 0 1.2rem rgba(208, 230, 255, 0.9), 0 0 2rem rgba(146, 177, 255, 0.45);
}

.star-node--active .star-node__label {
  color: rgba(247, 251, 255, 0.98);
}

.star-node--muted {
  opacity: 0.48;
}

@keyframes starPulse {
  0%, 100% {
    transform: scale(calc(1.1 * var(--star-glow-scale)));
    opacity: 0.72;
  }
  50% {
    transform: scale(calc(1.3 * var(--star-glow-scale)));
    opacity: 1;
  }
}

.story-card {
  position: absolute;
  z-index: 5;
  top: 50%;
  left: 50%;
  width: min(24rem, calc(100% - 3rem));
  aspect-ratio: 1 / 0.92;
  transform: translate(-50%, -50%);
  padding: 1.4rem 1.4rem 1.3rem;
  border-radius: 1.4rem;
  border: 1px solid rgba(201, 222, 255, 0.18);
  background: linear-gradient(180deg, rgba(13, 22, 41, 0.88) 0%, rgba(11, 18, 35, 0.82) 100%);
  backdrop-filter: blur(16px);
  box-shadow:
    0 1.4rem 3rem rgba(2, 8, 18, 0.5),
    inset 0 0 0 1px rgba(255, 255, 255, 0.03),
    0 0 1.25rem rgba(116, 158, 255, 0.16);
  color: #edf6ff;
}

.story-card__close {
  position: absolute;
  top: 0.85rem;
  right: 0.85rem;
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  border: 1px solid rgba(206, 225, 255, 0.16);
  background: rgba(255, 255, 255, 0.02);
  color: rgba(237, 246, 255, 0.8);
  cursor: pointer;
}

.story-card__eyebrow {
  margin-bottom: 0.8rem;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: rgba(166, 199, 255, 0.78);
}

.story-card__title {
  margin: 0 0 0.95rem;
  font-size: clamp(1.4rem, 2vw, 1.8rem);
  line-height: 1.1;
  color: #f4f8ff;
}

.story-card__body {
  margin: 0;
  max-width: 28ch;
  font-size: 1rem;
  line-height: 1.7;
  color: rgba(236, 245, 255, 0.92);
}

.story-card-fade-enter-active,
.story-card-fade-leave-active {
  transition: opacity 0.28s ease, transform 0.28s ease;
}

.story-card-fade-enter-from,
.story-card-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -47%);
}

.starfield-hud {
  z-index: 4;
  pointer-events: none;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 6rem 1.2rem 1.2rem;
}

.hud-chip {
  pointer-events: auto;
  max-width: min(20rem, 46vw);
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(186, 207, 255, 0.14);
  background: rgba(9, 17, 32, 0.44);
  backdrop-filter: blur(12px);
}

.hud-label {
  display: block;
  margin-bottom: 0.45rem;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: rgba(173, 196, 255, 0.76);
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem 0.8rem;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.8rem;
  color: rgba(237, 246, 255, 0.84);
}

.legend-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 999px;
  box-shadow: 0 0 0.55rem currentColor;
}

.graph-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.9rem;
  color: rgba(232, 242, 255, 0.7);
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.44;
}

.loading-spinner {
  width: 2.6rem;
  height: 2.6rem;
  border: 3px solid rgba(255, 255, 255, 0.14);
  border-top-color: rgba(190, 214, 255, 0.95);
  border-radius: 999px;
  animation: spin 1s linear infinite;
}

.graph-building-hint {
  position: absolute;
  bottom: 1.7rem;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(7, 16, 30, 0.76);
  backdrop-filter: blur(12px);
  color: #f0f7ff;
  padding: 0.72rem 1rem;
  border-radius: 999px;
  font-size: 0.82rem;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  border: 1px solid rgba(186, 207, 255, 0.14);
  z-index: 6;
}

.memory-icon-wrapper {
  display: inline-flex;
  animation: breathe 2s ease-in-out infinite;
}

.memory-icon,
.hint-icon {
  width: 1rem;
  height: 1rem;
  color: #b9d4ff;
}

.finished-hint .hint-text {
  white-space: nowrap;
}

.hint-close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  color: #edf6ff;
  background: rgba(255, 255, 255, 0.08);
}

@keyframes breathe {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.08); opacity: 1; }
}

@media (max-width: 960px) {
  .story-card {
    width: min(22rem, calc(100% - 2rem));
  }

  .starfield-hud {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
    padding-top: 5.2rem;
  }

  .hud-chip {
    max-width: 100%;
  }
}

@media (max-width: 640px) {
  .panel-header {
    padding: 14px 14px 0;
  }

  .tool-btn .btn-text {
    display: none;
  }

  .story-card {
    aspect-ratio: auto;
    min-height: 15rem;
  }

  .graph-building-hint,
  .finished-hint .hint-text {
    white-space: normal;
  }
}
</style>
