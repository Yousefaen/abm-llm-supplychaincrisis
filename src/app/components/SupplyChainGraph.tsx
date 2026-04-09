"use client";

import { useCallback, useEffect, useRef } from "react";
import * as d3 from "d3";
import type { AgentState, Tier } from "../lib/types";
import {
  AGENT_IDS,
  EMOTIONAL_COLORS,
  NETWORK_EDGES,
  TIER_COLORS,
  TIER_LABELS,
} from "../lib/types";

interface Props {
  agents: Record<string, AgentState>;
  onSelectAgent: (agentId: string | null) => void;
  selectedAgent: string | null;
  thinkingAgent: string | null;
}

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  tier: Tier;
  displayName: string;
  tierIndex: number; // 0-3 for vertical layering
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode;
  target: string | GraphNode;
}

const TIER_Y: Record<Tier, number> = {
  foundry: 0,
  chipDesigner: 1,
  tier1Supplier: 2,
  oem: 3,
};

const TIER_INDEX: Record<string, number> = {};
for (const id of AGENT_IDS) {
  const mapping: Record<string, Tier> = {
    TaiwanSemi: "foundry",
    KoreaSilicon: "foundry",
    EuroChip: "chipDesigner",
    AmeriSemi: "chipDesigner",
    BoschAuto: "tier1Supplier",
    ContiParts: "tier1Supplier",
    ToyotaMotors: "oem",
    FordAuto: "oem",
    VolkswagenAG: "oem",
  };
  TIER_INDEX[id] = TIER_Y[mapping[id]];
}

const DISPLAY_NAMES: Record<string, string> = {
  TaiwanSemi: "TaiwanSemi",
  KoreaSilicon: "KoreaSilicon",
  EuroChip: "EuroChip",
  AmeriSemi: "AmeriSemi",
  BoschAuto: "BoschAuto",
  ContiParts: "ContiParts",
  ToyotaMotors: "Toyota",
  FordAuto: "Ford",
  VolkswagenAG: "VW",
};

const AGENT_TIERS: Record<string, Tier> = {
  TaiwanSemi: "foundry",
  KoreaSilicon: "foundry",
  EuroChip: "chipDesigner",
  AmeriSemi: "chipDesigner",
  BoschAuto: "tier1Supplier",
  ContiParts: "tier1Supplier",
  ToyotaMotors: "oem",
  FordAuto: "oem",
  VolkswagenAG: "oem",
};

export default function SupplyChainGraph({
  agents,
  onSelectAgent,
  selectedAgent,
  thinkingAgent,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const simRef = useRef<d3.Simulation<GraphNode, GraphLink> | null>(null);
  const nodesRef = useRef<GraphNode[]>([]);
  const initializedRef = useRef(false);

  // Build static node/link data once
  const buildGraph = useCallback(() => {
    const nodes: GraphNode[] = AGENT_IDS.map((id) => ({
      id,
      tier: AGENT_TIERS[id],
      displayName: DISPLAY_NAMES[id],
      tierIndex: TIER_INDEX[id],
    }));

    const links: GraphLink[] = NETWORK_EDGES.map((e) => ({
      source: e.source,
      target: e.target,
    }));

    return { nodes, links };
  }, []);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    if (!svgRef.current || initializedRef.current) return;
    initializedRef.current = true;

    const container = svgRef.current.parentElement!;
    const width = container.clientWidth;
    const height = container.clientHeight || 500;

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const { nodes, links } = buildGraph();
    nodesRef.current = nodes;

    // Defs for glow filter
    const defs = svg.append("defs");
    const filter = defs.append("filter").attr("id", "glow");
    filter
      .append("feGaussianBlur")
      .attr("stdDeviation", "4")
      .attr("result", "coloredBlur");
    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    const g = svg.append("g");

    // Zoom
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.3, 3]).on("zoom", (e) => {
      g.attr("transform", e.transform);
    });
    (svg as unknown as d3.Selection<SVGSVGElement, unknown, null, undefined>).call(zoom);

    // Links
    const link = g
      .append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#555")
      .attr("stroke-opacity", 0.4)
      .attr("stroke-width", 2);

    // Nodes group
    const node = g
      .append("g")
      .attr("class", "nodes")
      .selectAll<SVGGElement, GraphNode>("g")
      .data(nodes, (d) => d.id)
      .join("g")
      .attr("cursor", "pointer")
      .on("click", (_e, d) => {
        onSelectAgent(d.id);
      });

    // Node circles
    node
      .append("circle")
      .attr("r", 24)
      .attr("fill", (d) => TIER_COLORS[d.tier])
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .attr("class", "node-circle");

    // Node labels
    node
      .append("text")
      .text((d) => d.displayName)
      .attr("text-anchor", "middle")
      .attr("dy", 40)
      .attr("fill", "currentColor")
      .attr("font-size", "11px")
      .attr("font-weight", "500");

    // Tier labels
    const tierLabels = [
      { tier: "foundry" as Tier, label: "Foundries", y: 0 },
      { tier: "chipDesigner" as Tier, label: "Chip Designers", y: 1 },
      { tier: "tier1Supplier" as Tier, label: "Tier-1 Suppliers", y: 2 },
      { tier: "oem" as Tier, label: "OEMs", y: 3 },
    ];

    const tierLabelG = g.append("g").attr("class", "tier-labels");
    tierLabelG
      .selectAll("text")
      .data(tierLabels)
      .join("text")
      .attr("x", 20)
      .attr("y", (d) => 60 + d.y * (height / 4.5))
      .attr("fill", (d) => TIER_COLORS[d.tier])
      .attr("font-size", "12px")
      .attr("font-weight", "600")
      .attr("opacity", 0.7)
      .text((d) => d.label);

    // Force simulation with strong vertical layering
    const sim = d3
      .forceSimulation<GraphNode>(nodes)
      .force(
        "link",
        d3
          .forceLink<GraphNode, GraphLink>(links)
          .id((d) => d.id)
          .distance(100)
          .strength(0.3)
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("x", d3.forceX(width / 2).strength(0.05))
      .force(
        "y",
        d3.forceY<GraphNode>((d) => 80 + d.tierIndex * (height / 4.5)).strength(0.8)
      )
      .force("collide", d3.forceCollide(40))
      .on("tick", () => {
        link
          .attr("x1", (d) => (d.source as GraphNode).x!)
          .attr("y1", (d) => (d.source as GraphNode).y!)
          .attr("x2", (d) => (d.target as GraphNode).x!)
          .attr("y2", (d) => (d.target as GraphNode).y!);

        node.attr("transform", (d) => `translate(${d.x},${d.y})`);
      });

    simRef.current = sim;

    // Drag behavior
    const drag = d3
      .drag<SVGGElement, GraphNode>()
      .on("start", (e, d) => {
        if (!e.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (e, d) => {
        d.fx = e.x;
        d.fy = e.y;
      })
      .on("end", (e, d) => {
        if (!e.active) sim.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    node.call(drag);

    return () => {
      sim.stop();
    };
  }, [buildGraph, onSelectAgent]);

  // Update visual state when agents data changes
  useEffect(() => {
    const svg = d3.select(svgRef.current);
    if (!svgRef.current) return;

    // Update link colors/thickness based on allocations
    svg.selectAll<SVGLineElement, GraphLink>(".links line").each(function (d) {
      const sourceId =
        typeof d.source === "string" ? d.source : (d.source as GraphNode).id;
      const targetId =
        typeof d.target === "string" ? d.target : (d.target as GraphNode).id;

      const supplier = agents[sourceId];
      const buyer = agents[targetId];
      if (!supplier || !buyer) return;

      const allocated =
        supplier.current_decision?.allocations?.[targetId] ?? 0;
      const ordered = buyer.current_decision?.orders?.[sourceId] ?? 0;

      const thickness = Math.max(1.5, Math.min(8, allocated / 30));
      const fillHealth =
        ordered > 0 ? Math.min(allocated / ordered, 1) : 1;

      const color =
        fillHealth >= 0.8
          ? "#22c55e"
          : fillHealth >= 0.4
            ? "#eab308"
            : "#ef4444";

      d3.select(this)
        .attr("stroke", color)
        .attr("stroke-width", thickness)
        .attr("stroke-opacity", 0.6);
    });

    // Update node appearance
    svg
      .selectAll<SVGGElement, GraphNode>(".nodes g")
      .each(function (d) {
        const agent = agents[d.id];
        const circle = d3.select(this).select<SVGCircleElement>(".node-circle");

        if (!agent) return;

        // Size proportional to inventory or capacity
        const size = Math.max(18, Math.min(36, 18 + (agent.inventory + agent.capacity) / 40));
        circle.attr("r", size);

        // Glow based on emotional state
        const emotionColor =
          EMOTIONAL_COLORS[agent.emotional_state] ?? "#888";

        if (
          agent.emotional_state === "panicked" ||
          agent.emotional_state === "angry"
        ) {
          circle.attr("filter", "url(#glow)").attr("stroke", emotionColor);
        } else {
          circle.attr("filter", null).attr("stroke", "#fff");
        }

        // Selected highlight
        if (selectedAgent === d.id) {
          circle.attr("stroke", "#fff").attr("stroke-width", 4);
        } else {
          circle.attr("stroke-width", 2);
        }

        // Thinking indicator
        if (thinkingAgent === d.id) {
          circle
            .attr("stroke", "#fbbf24")
            .attr("stroke-width", 3)
            .attr("stroke-dasharray", "4 4");
        } else {
          circle.attr("stroke-dasharray", null);
        }
      });
  }, [agents, selectedAgent, thinkingAgent]);

  return (
    <div className="relative w-full h-full min-h-[400px]">
      <svg
        ref={svgRef}
        className="w-full h-full"
        preserveAspectRatio="xMidYMid meet"
      />
      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex flex-wrap gap-3 text-xs bg-card/80 backdrop-blur p-2 rounded-md border border-border">
        {(Object.entries(TIER_LABELS) as [Tier, string][]).map(
          ([tier, label]) => (
            <div key={tier} className="flex items-center gap-1.5">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: TIER_COLORS[tier] }}
              />
              <span>{label}</span>
            </div>
          )
        )}
      </div>
    </div>
  );
}
