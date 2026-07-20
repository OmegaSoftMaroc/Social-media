import React from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";

// Charte OmegaSoft
const NAVY = "#0B1E33";
const NAVY_LIGHT = "#122C4A";
const TEAL = "#2AA7A0";
const ACCENT = "#FFB454";
const WHITE = "#FFFFFF";

// Animations conçues pour la vidéo « GPT-5.6 / conjecture de la double couverture par
// cycles » (900×940 = scène média d'AvatarPhases). Trois variantes :
//   reseau  : un réseau (points + lignes) se dessine — « Imaginez un réseau… »
//   boucles : 5 boucles colorées couvrent le graphe, chaque arête exactement 2 fois.
//             Le graphe est un PRISME TRIANGULAIRE (planaire) : ses 5 faces forment
//             une double couverture par cycles EXACTE — l'animation est donc juste.
//   agents  : 64 agents en parallèle (grille 8×8), certains « vérificateurs » flashent.

export const cdcAnimSchema = z.object({
  variant: z.enum(["reseau", "boucles", "agents"]),
});
type Props = z.infer<typeof cdcAnimSchema>;

export const calculateCdcAnimMetadata: CalculateMetadataFunction<Props> = async () => ({
  fps: 30,
  durationInFrames: 360, // 12 s
});

// ---------- Géométrie du prisme triangulaire (canvas 900×940) ----------
const CX = 450;
const CY = 470;
const polar = (r: number, deg: number): [number, number] => [
  CX + r * Math.cos((deg * Math.PI) / 180),
  CY + r * Math.sin((deg * Math.PI) / 180),
];
// Sommets : triangle extérieur A,B,C + triangle intérieur a,b,c
const A = polar(330, -90), B = polar(330, 30), C = polar(330, 150);
const ia = polar(150, -90), ib = polar(150, 30), ic = polar(150, 150);
const NODES = [A, B, C, ia, ib, ic];
// Arêtes : 3 extérieures, 3 intérieures, 3 rayons
const EDGES: [number, number][] = [
  [0, 1], [1, 2], [2, 0], // extérieur
  [3, 4], [4, 5], [5, 3], // intérieur
  [0, 3], [1, 4], [2, 5], // rayons
];
// Les 5 faces = double couverture exacte (chaque arête dans 2 cycles)
const CYCLES: number[][] = [
  [0, 1, 2],       // face extérieure
  [3, 4, 5],       // face intérieure
  [0, 1, 4, 3],    // quad A-B-b-a
  [1, 2, 5, 4],    // quad B-C-c-b
  [2, 0, 3, 5],    // quad C-A-a-c
];
const CYCLE_COLORS = [TEAL, ACCENT, "#4FA3E3", "#7BD3CE", "#FFD28A"];

const pathOf = (idxs: number[], inflate: number): string => {
  // Polygone légèrement gonflé/dégonflé depuis le centre pour que les boucles
  // superposées restent distinguables (2 brins visibles par arête).
  const pts = idxs.map((i) => {
    const [x, y] = NODES[i];
    return [CX + (x - CX) * inflate, CY + (y - CY) * inflate];
  });
  return "M " + pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(" L ") + " Z";
};

const hash = (i: number): number => {
  const s = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
};

// ---------- Variante « reseau » ----------
const Reseau: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <svg width={900} height={940} style={{ position: "absolute" }}>
      {EDGES.map(([u, v], i) => {
        const [x1, y1] = NODES[u];
        const [x2, y2] = NODES[v];
        const len = Math.hypot(x2 - x1, y2 - y1);
        const p = spring({ frame: Math.max(frame - 20 - i * 7, 0), fps,
                           config: { damping: 200 }, durationInFrames: 26 });
        const pulse = 0.5 + 0.5 * Math.sin(frame / 14 + i * 1.7);
        return (
          <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
            stroke={TEAL} strokeWidth={5} strokeLinecap="round"
            strokeDasharray={len} strokeDashoffset={len * (1 - p)}
            opacity={0.55 + 0.35 * pulse} />
        );
      })}
      {NODES.map(([x, y], i) => {
        const s = spring({ frame: Math.max(frame - i * 6, 0), fps,
                           config: { damping: 12 }, durationInFrames: 24 });
        const halo = 10 + 4 * Math.sin(frame / 12 + i * 2.1);
        return (
          <g key={i} transform={`translate(${x} ${y}) scale(${s})`}>
            <circle r={halo + 14} fill={`${TEAL}22`} />
            <circle r={14} fill={WHITE} stroke={TEAL} strokeWidth={5} />
          </g>
        );
      })}
    </svg>
  );
};

// ---------- Variante « boucles » ----------
const Boucles: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Chaque cycle se dessine l'un après l'autre (~55 frames chacun)
  const INFLATES = [1.12, 0.86, 0.97, 1.0, 1.03];
  // Compte de couverture par arête au fil des cycles terminés
  const done = CYCLES.map((_, c) => frame > 30 + c * 55 + 50);
  const coverage = EDGES.map((_, e) =>
    CYCLES.reduce((n, cyc, c) => n + (done[c] && cyc.some((_, k) => {
      const u = cyc[k], v = cyc[(k + 1) % cyc.length];
      const [eu, ev] = EDGES[e];
      return (u === eu && v === ev) || (u === ev && v === eu);
    }) ? 1 : 0), 0));
  return (
    <svg width={900} height={940} style={{ position: "absolute" }}>
      {/* graphe de base, sombre — s'illumine quand couvert 2 fois */}
      {EDGES.map(([u, v], i) => {
        const [x1, y1] = NODES[u];
        const [x2, y2] = NODES[v];
        const full = coverage[i] >= 2;
        return (
          <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
            stroke={full ? WHITE : `${WHITE}44`} strokeWidth={full ? 7 : 4}
            strokeLinecap="round" opacity={full ? 0.95 : 0.5} />
        );
      })}
      {/* les 5 boucles, tracées en séquence */}
      {CYCLES.map((cyc, c) => {
        const start = 30 + c * 55;
        const p = interpolate(frame, [start, start + 50], [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        if (p <= 0) return null;
        const d = pathOf(cyc, INFLATES[c]);
        // longueur approx : périmètre du polygone gonflé
        const pts = cyc.map((i) => NODES[i]);
        const per = pts.reduce((s, pt, k) => {
          const nx = pts[(k + 1) % pts.length];
          return s + Math.hypot(nx[0] - pt[0], nx[1] - pt[1]) * INFLATES[c];
        }, 0);
        return (
          <path key={c} d={d} fill="none" stroke={CYCLE_COLORS[c]}
            strokeWidth={6} strokeLinejoin="round" strokeLinecap="round"
            strokeDasharray={per} strokeDashoffset={per * (1 - p)}
            opacity={0.9}
            style={{ filter: `drop-shadow(0 0 6px ${CYCLE_COLORS[c]})` }} />
        );
      })}
      {NODES.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={13} fill={NAVY_LIGHT}
          stroke={WHITE} strokeWidth={4} />
      ))}
    </svg>
  );
};

// ---------- Variante « agents » ----------
const Agents: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const N = 8; // 8×8 = 64 agents
  const CELL = 96;
  const X0 = 450 - (N - 1) * CELL * 0.5;
  const Y0 = 470 - (N - 1) * CELL * 0.5;
  return (
    <svg width={900} height={940} style={{ position: "absolute" }}>
      {Array.from({ length: N * N }).map((_, i) => {
        const gx = i % N;
        const gy = Math.floor(i / N);
        const x = X0 + gx * CELL;
        const y = Y0 + gy * CELL;
        const enter = spring({ frame: Math.max(frame - (gx + gy) * 3, 0), fps,
                               config: { damping: 200 }, durationInFrames: 18 });
        // pulsation de « travail » désynchronisée
        const pulse = 0.5 + 0.5 * Math.sin(frame / 9 + hash(i) * Math.PI * 2);
        // ~1 agent sur 5 = vérificateur : flash orange périodique
        const checker = hash(i * 3 + 1) < 0.2;
        const flash = checker && ((frame + Math.floor(hash(i) * 90)) % 90) < 12;
        const r = 13 + 6 * pulse;
        return (
          <g key={i} transform={`translate(${x} ${y}) scale(${enter})`}>
            <circle r={r + 9} fill={flash ? `${ACCENT}33` : `${TEAL}1A`} />
            <circle r={r * 0.55} fill={flash ? ACCENT : TEAL}
              opacity={0.55 + 0.45 * pulse} />
          </g>
        );
      })}
    </svg>
  );
};

export const CdcAnim: React.FC<Props> = ({ variant }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 42%, ${NAVY_LIGHT}, ${NAVY})` }}>
    {variant === "reseau" ? <Reseau /> : variant === "boucles" ? <Boucles /> : <Agents />}
  </AbsoluteFill>
);
