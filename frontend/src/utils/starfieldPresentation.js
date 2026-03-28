const DEPTH_BAND_ORDER = ['far', 'mid', 'near']

function hashString(value = '') {
  let hash = 0
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0
  }
  return hash
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function toDepthWeight(depthBand) {
  const normalized = DEPTH_BAND_ORDER.includes(depthBand) ? depthBand : 'mid'
  return { far: 0.72, mid: 1, near: 1.22 }[normalized]
}

export function mapNodesToStarfield(nodes = [], edges = []) {
  const edgeCounts = new Map()
  edges.forEach((edge) => {
    edgeCounts.set(edge.source_node_uuid, (edgeCounts.get(edge.source_node_uuid) || 0) + 1)
    edgeCounts.set(edge.target_node_uuid, (edgeCounts.get(edge.target_node_uuid) || 0) + 1)
  })

  const sortedNodes = [...nodes].sort((left, right) => {
    const leftImportance = right.presentation?.importance || right.edge_count || 0
    const rightImportance = left.presentation?.importance || left.edge_count || 0
    return leftImportance - rightImportance
  })

  return sortedNodes.map((node, index) => {
    const seed = hashString(`${node.uuid}:${node.name || ''}`)
    const depthBand = node.presentation?.depth_band || ['far', 'mid', 'near'][seed % 3] || 'mid'
    const depthWeight = toDepthWeight(depthBand)
    const edgeCount = edgeCounts.get(node.uuid) || node.edge_count || 0
    const importance = clamp(node.presentation?.importance || node.size_hint || edgeCount + 1 || 1, 1, 6)
    const orbitX = 12 + ((index * 17 + seed % 61) % 76)
    const orbitY = 14 + ((index * 11 + Math.floor(seed / 61) % 59) % 72)
    const drift = ((seed % 200) - 100) / 100

    return {
      ...node,
      depthBand,
      importance,
      depthWeight,
      orbitX,
      orbitY,
      drift,
      starSize: Number((0.8 + importance * 0.2 * depthWeight).toFixed(2)),
      glowScale: Number((0.7 + importance * 0.08).toFixed(2)),
      pulseDelay: `${(seed % 15) * 0.18}s`,
      accentHue: seed % 360,
    }
  })
}

export function mapEdgesToTraces(nodes = [], edges = []) {
  const nodeMap = new Map(nodes.map((node) => [node.uuid, node]))

  return edges
    .filter((edge) => nodeMap.has(edge.source_node_uuid) && nodeMap.has(edge.target_node_uuid))
    .map((edge, index) => {
      const source = nodeMap.get(edge.source_node_uuid)
      const target = nodeMap.get(edge.target_node_uuid)
      const seed = hashString(`${edge.uuid || `${edge.source_node_uuid}-${edge.target_node_uuid}`}:${index}`)
      const midpointX = (source.orbitX + target.orbitX) / 2
      const midpointY = (source.orbitY + target.orbitY) / 2
      const deltaX = target.orbitX - source.orbitX
      const deltaY = target.orbitY - source.orbitY
      const length = Math.max(Math.sqrt(deltaX * deltaX + deltaY * deltaY), 1)
      const curveIntensity = ((seed % 9) - 4) * 1.6
      const controlX = midpointX - (deltaY / length) * curveIntensity
      const controlY = midpointY + (deltaX / length) * curveIntensity

      return {
        ...edge,
        source,
        target,
        path: `M ${source.orbitX} ${source.orbitY} Q ${controlX.toFixed(2)} ${controlY.toFixed(2)} ${target.orbitX} ${target.orbitY}`,
      }
    })
}

export function buildAmbientParticles(maxParticles = 24) {
  const budget = clamp(Number.isFinite(maxParticles) ? maxParticles : 24, 0, 48)

  return Array.from({ length: budget }, (_, index) => {
    const seed = hashString(`particle:${index}`)
    const band = ['far', 'mid', 'near'][index % 3]
    return {
      id: `particle-${index}`,
      band,
      x: 2 + (seed % 96),
      y: 4 + (Math.floor(seed / 17) % 92),
      size: Number((0.12 + ((seed % 7) + 1) * 0.08).toFixed(2)),
      opacity: Number((0.18 + (seed % 5) * 0.08).toFixed(2)),
      duration: `${10 + (seed % 9)}s`,
      delay: `${(seed % 12) * 0.4}s`,
    }
  })
}
