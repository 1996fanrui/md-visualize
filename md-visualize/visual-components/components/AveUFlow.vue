<!--
  component: AveUFlow
  structure: U-shaped flow diagram. Nodes are arranged in rows of up to 3, snaking left→right, then down, then right→left, repeating. Supports 1–9 nodes.
  notes: |
    Node types map to mermaid classDef colors used in north-star diagrams:
      - input:   gray  (#f5f3f0) — entry point
      - process: blue  (#eef4ff) — work steps
      - review:  red   (#fdecea) — review/gate steps
      - output:  green (#d9f5e4) — final output
    Layout rules (each row holds up to 3 nodes):
      Even rows (0, 2, …): left → right; vertical drop on the RIGHT side
      Odd  rows (1, 3, …): right → left; vertical drop on the LEFT side
    Multi-row expansion is automatic — add more nodes and the U keeps snaking.
  usage-markdown: |
    <AveUFlow
      :nodes='[
        {"label":"Design Docs","type":"input"},
        {"label":"Development","type":"process"},
        {"label":"Code Review","type":"review"},
        {"label":"Unit + Integration Tests","type":"process"},
        {"label":"User Acceptance Testing","type":"process"},
        {"label":"Delivery","type":"output"}
      ]'
    />
  usage-json: |
    {
      "component": "AveUFlow",
      "props": {
        "nodes": [
          {"label":"Design Docs","type":"input"},
          {"label":"Development","type":"process"},
          {"label":"Code Review","type":"review"},
          {"label":"Unit + Integration Tests","type":"process"},
          {"label":"User Acceptance Testing","type":"process"},
          {"label":"Delivery","type":"output"}
        ]
      }
    }
  layout-constraints: |
    - nodes: 1–9 (U-shape supports up to 3 rows of 3)
    - node label: max ~12 chars CJK / ~24 chars EN (longer text wraps inside node)
    - recommended viewport width: 900
-->
<script setup lang="ts">
import { computed } from 'vue'

type NodeType = 'input' | 'process' | 'review' | 'output'

interface FlowNode {
  label: string
  type: NodeType
}

interface Row {
  nodes: (FlowNode & { origIndex: number })[]
  direction: 'ltr' | 'rtl'
}

const props = defineProps<{
  nodes: FlowNode[]
}>()

// 0xaa / 0xff ≈ 0.667 — matches the mermaid classDef fill opacity (aa suffix)
const typeStyle: Record<NodeType, { bg: string; border: string; color: string }> = {
  input:   { bg: 'rgba(245,243,240,0.667)', border: '#999',    color: '#333'    },
  process: { bg: 'rgba(238,244,255,0.667)', border: '#6366f1', color: '#4338ca' },
  review:  { bg: 'rgba(253,236,234,0.667)', border: '#dc2626', color: '#b91c1c' },
  output:  { bg: 'rgba(217,245,228,0.667)', border: '#34a853', color: '#1e7e34' },
}

const rows = computed<Row[]>(() => {
  const result: Row[] = []
  const indexed = props.nodes.map((n, i) => ({ ...n, origIndex: i }))
  for (let r = 0; r * 3 < indexed.length; r++) {
    const chunk = indexed.slice(r * 3, r * 3 + 3)
    const direction: 'ltr' | 'rtl' = r % 2 === 0 ? 'ltr' : 'rtl'
    result.push({ nodes: direction === 'rtl' ? [...chunk].reverse() : chunk, direction })
  }
  return result
})

</script>

<template>
  <div class="uflow">
    <template v-for="(row, rowIdx) in rows" :key="rowIdx">

      <!-- Node row: 3-column grid, nodes + arrows -->
      <div class="row-grid">
        <template v-for="(node, colIdx) in row.nodes" :key="node.origIndex">
          <div v-if="colIdx > 0" class="h-arrow">
            <template v-if="row.direction === 'ltr'">
              <div class="h-line" />
              <div class="arrowhead-right" />
            </template>
            <template v-else>
              <div class="arrowhead-left" />
              <div class="h-line" />
            </template>
          </div>

          <div
            class="node"
            :style="{
              background: typeStyle[node.type].bg,
              borderColor: typeStyle[node.type].border,
              color: typeStyle[node.type].color,
            }"
          >
            {{ node.label }}
          </div>
        </template>
      </div>

      <!--
        Vertical connector row between two node rows.
        Uses the same 5-column grid as the node row so columns align perfectly.
        ltr row ends at col 5 (rightmost) → put the vertical line in col 5.
        rtl row ends at col 1 (leftmost)  → put the vertical line in col 1.
        Empty divs fill the other columns.
      -->
      <div v-if="rowIdx < rows.length - 1" class="connector-grid">
        <template v-if="row.direction === 'ltr'">
          <div /><div /><div /><div />
          <div class="v-connector">
            <div class="v-line" />
            <div class="v-arrowhead" />
          </div>
        </template>
        <template v-else>
          <div class="v-connector">
            <div class="v-line" />
            <div class="v-arrowhead" />
          </div>
          <div /><div /><div /><div />
        </template>
      </div>

    </template>
  </div>
</template>

<style scoped>
.uflow {
  display: flex;
  flex-direction: column;
  width: 100%;
}

/* Both row-grid and connector-grid share the same 5-column layout so the
   vertical connector always aligns with the edge node's center column. */
.row-grid,
.connector-grid {
  display: grid;
  grid-template-columns: 1fr 40px 1fr 40px 1fr;
}

.row-grid {
  align-items: center;
}

/* connector-grid: its only job is to hold the v-connector at the correct column.
   Height = 36px; v-connector uses align-self:stretch to fill it fully,
   placing the arrowhead at the very bottom (= top of next row-grid). */
.connector-grid {
  align-items: start;
  flex-shrink: 0;
  /* Pull down into the next row's padding so arrowhead touches the node border.
     Node padding-top is 14px, so we extend by 14px. */
  margin-bottom: -14px;
}

/* Single node */
.node {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1.5px solid;
  text-align: center;
  font-size: var(--ave-body-size);
  font-weight: 500;
  line-height: 1.4;
  word-break: break-word;
}

/* Horizontal arrow */
.h-arrow {
  display: flex;
  align-items: center;
}
.h-line {
  flex: 1;
  height: 2px;
  background: #aaa;
}
.arrowhead-right {
  width: 0; height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 7px solid #aaa;
  flex-shrink: 0;
}
.arrowhead-left {
  width: 0; height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-right: 7px solid #aaa;
  flex-shrink: 0;
}

/* Vertical connector: lives inside a grid cell, centered horizontally.
   The cell height is driven by min-height on .v-connector itself (40px gap),
   and the arrowhead sits flush at the bottom so it touches the next row's top. */
.v-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  /* 36px gap + 14px node padding-top so arrowhead tip reaches the node border */
  height: 50px;
}
.v-line {
  flex: 1;
  width: 2px;
  background: #aaa;
  margin-bottom: -1px;
}
.v-arrowhead {
  width: 0; height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 7px solid #aaa;
  flex-shrink: 0;
}
</style>
