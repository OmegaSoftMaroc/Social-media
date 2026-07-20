import { Caption } from "@remotion/captions";
import { getVideoMetadata } from "@remotion/media-utils";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  cancelRender,
  OffthreadVideo,
  spring,
  useCurrentFrame,
  useDelayRender,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { loadFont, TheBoldFont } from "../load-font";

// Charte OmegaSoft (cf. pipeline/config.py BRAND_STYLE)
const NAVY = "#0B1E33";
const NAVY_LIGHT = "#122C4A";
const TEAL = "#2AA7A0";
const ACCENT = "#FFB454";
const WHITE = "#FFFFFF";

export const presenterPiPSchema = z.object({
  src: z.string(),
});

export const calculatePresenterPiPMetadata: CalculateMetadataFunction<
  z.infer<typeof presenterPiPSchema>
> = async ({ props }) => {
  const fps = 30;
  const metadata = await getVideoMetadata(props.src);
  return { fps, durationInFrames: Math.floor(metadata.durationInSeconds * fps) };
};

// TheBoldFont est une police tout-capitales sans glyphe majuscule accentué (É, È, Ç…) :
// on désaccentue le texte affiché pour éviter les « SYSTèMES » (les accents en capitales
// disparaissent de toute façon, conformément à l'usage typographique).
export const deaccent = (s: string): string =>
  s.normalize("NFD").replace(/[̀-ͯ]/g, "");

type Sentence = { words: Caption[]; startMs: number; endMs: number; text: string };

// Regroupe les mots (captions whisper) en phrases : ponctuation forte ou 9 mots max
const groupSentences = (captions: Caption[]): Sentence[] => {
  const sentences: Sentence[] = [];
  let current: Caption[] = [];
  const push = () => {
    if (current.length === 0) return;
    sentences.push({
      words: current,
      startMs: current[0].startMs,
      endMs: current[current.length - 1].endMs,
      text: current.map((w) => w.text.trim()).join(" "),
    });
    current = [];
  };
  for (const word of captions) {
    current.push(word);
    if (/[.!?…]\s*$/.test(word.text.trim()) || current.length >= 9) push();
  }
  push();
  return sentences;
};

// Icônes line-art raffinées (SVG, traits fins, couleurs marque) — affichées en
// bas à gauche UNIQUEMENT quand un mot-clé du propos le justifie (sinon rien).
type IconKey = "target" | "chart" | "chip" | "factory" | "rocket" | "check" | "plug" | "bulb";

const ICON_RULES: [RegExp, IconKey][] = [
  [/prospect|client|vente|commercial/i, "target"],
  [/donn[ée]e|data|fichier|crm|base/i, "chart"],
  [/agent|\bia\b|intelligence|automatis/i, "chip"],
  [/pme|industri|usine|atelier/i, "factory"],
  [/commenc|d[ée]marr|lanc/i, "rocket"],
  [/propre|nettoy|qualit|fiab/i, "check"],
  [/brancher|connect|outil|syst[èe]me/i, "plug"],
  [/id[ée]e|r[ée]fl[ée]ch|conseil/i, "bulb"],
];

const iconFor = (sentence: Sentence): IconKey | null => {
  for (const [re, key] of ICON_RULES) {
    if (re.test(sentence.text)) return key;
  }
  return null; // pas pertinent → pas d'icône
};

// Tracés SVG minimalistes (viewBox 24x24, stroke uniquement)
const ICON_PATHS: Record<IconKey, React.ReactNode> = {
  target: (<>
    <circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" />
    <circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none" />
  </>),
  chart: (<>
    <path d="M4 20V6" /><path d="M4 20h16" />
    <path d="M8 16v-5" /><path d="M12 16V8" /><path d="M16 16v-3" />
  </>),
  chip: (<>
    <rect x="7" y="7" width="10" height="10" rx="1.5" />
    <path d="M10 7V4M14 7V4M10 20v-3M14 20v-3M7 10H4M7 14H4M20 10h-3M20 14h-3" />
  </>),
  factory: (<>
    <path d="M4 20V10l5 3v-3l5 3v-3l6 4v6" /><path d="M4 20h16" />
  </>),
  rocket: (<>
    <path d="M12 3c3 2 4 6 4 9l-4 4-4-4c0-3 1-7 4-9Z" />
    <path d="M8 12l-3 3 3 .5M16 12l3 3-3 .5M12 16v4" />
  </>),
  check: (<>
    <circle cx="12" cy="12" r="9" /><path d="M8 12.5l2.6 2.6L16 9.5" />
  </>),
  plug: (<>
    <path d="M9 3v5M15 3v5" /><path d="M7 8h10v3a5 5 0 0 1-10 0V8Z" /><path d="M12 16v5" />
  </>),
  bulb: (<>
    <path d="M9 18h6M10 21h4" />
    <path d="M12 3a6 6 0 0 1 3.5 10.9c-.8.6-1.5 1.2-1.5 2.1h-4c0-.9-.7-1.5-1.5-2.1A6 6 0 0 1 12 3Z" />
  </>),
};

// Fond animé discret : anneaux et formes qui dérivent lentement (teal sur navy)
export const AnimatedBackground: React.FC = () => {
  const frame = useCurrentFrame();
  const drift = frame * 0.35;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(160deg, ${NAVY} 55%, ${NAVY_LIGHT})` }}>
      <div style={{
        position: "absolute", width: 620, height: 620, borderRadius: "50%",
        border: `3px solid ${TEAL}33`, left: -180, top: 140,
        transform: `rotate(${drift}deg) translateX(${20 + 12 * Math.sin(frame / 40)}px)`,
      }} />
      <div style={{
        position: "absolute", width: 340, height: 340, borderRadius: "50%",
        border: `2px solid ${TEAL}22`, right: -90, top: 620,
        transform: `translateY(${18 * Math.cos(frame / 55)}px)`,
      }} />
      <div style={{
        position: "absolute", width: 260, height: 260,
        border: `2px solid ${ACCENT}26`, left: 90, bottom: 260,
        transform: `rotate(${45 + drift / 2}deg)`,
      }} />
    </AbsoluteFill>
  );
};

// Pile de phrases : la courante (kinétique, mot à mot) + les précédentes (estompées).
// `bottomInset` réserve l'espace bas (470 = zone du PiP presentateur ; plus petit
// quand il n'y a pas de PiP, le texte occupe alors davantage l'écran).
// `topInset`/`justify`/`fontScale`/`maxPrev` permettent de repositionner la pile
// (ex. bandeau HAUT pour le template narration-illustree, où le centre est occupé
// par une scène média illustrée).
export const SentenceStack: React.FC<{
  sentences: Sentence[];
  bottomInset?: number;
  topInset?: number;
  justify?: React.CSSProperties["justifyContent"];
  fontScale?: number;
  maxPrev?: number;
}> = ({
  sentences, bottomInset = 470, topInset = 90, justify = "center",
  fontScale = 1, maxPrev = 2,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  let currentIdx = 0;
  for (let i = 0; i < sentences.length; i++) {
    if (sentences[i].startMs <= nowMs) currentIdx = i;
  }
  const firstVisible = Math.max(0, currentIdx - maxPrev);
  const visible = sentences.slice(firstVisible, currentIdx + 1);

  const curSize = Math.round(66 * fontScale);
  const prevSize = Math.round(46 * fontScale);

  return (
    <div style={{
      // Texte centré horizontalement, positionné dans la région [topInset, bottomInset]
      position: "absolute", top: topInset, left: 60, right: 60, bottom: bottomInset,
      display: "flex", flexDirection: "column", gap: Math.round(40 * fontScale),
      justifyContent: justify,
      fontFamily: TheBoldFont, textAlign: "center",
    }}>
      {visible.map((s, vi) => {
        const isCurrent = firstVisible + vi === currentIdx;
        if (!isCurrent) {
          // Phrase déjà dite : reste affichée, plus petite et estompée
          return (
            <div key={s.startMs} style={{
              fontSize: prevSize, lineHeight: 1.15, color: `${WHITE}77`,
              textShadow: "0 4px 18px rgba(0,0,0,0.45)",
            }}>
              {deaccent(s.text)}
            </div>
          );
        }
        // Phrase courante : chaque mot surgit quand il est prononcé (repère ABSOLU)
        return (
          <div key={s.startMs} style={{
            display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "8px 14px",
          }}>
            {s.words.map((word, i) => {
              const appearFrame = (word.startMs / 1000) * fps;
              const localFrame = frame - appearFrame;
              const scale = spring({
                frame: Math.max(localFrame, 0), fps,
                config: { damping: 200 }, durationInFrames: 8,
              });
              const isSpoken = nowMs >= word.startMs;
              const isNow = nowMs >= word.startMs && nowMs <= word.endMs + 120;
              const isKeyword = word.text.trim().length >= 8;
              return (
                <span key={i} style={{
                  fontSize: curSize, lineHeight: 1.1,
                  color: isNow ? ACCENT : isKeyword ? TEAL : WHITE,
                  opacity: isSpoken ? 1 : 0,
                  transform: `scale(${isSpoken ? scale : 0.6})`,
                  textShadow: "0 6px 26px rgba(0,0,0,0.55)",
                }}>
                  {deaccent(word.text.trim())}
                </span>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

// Badge icône raffiné, bas-gauche — seulement quand le propos le justifie
export const CornerIcon: React.FC<{ sentences: Sentence[] }> = ({ sentences }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  let currentIdx = 0;
  for (let i = 0; i < sentences.length; i++) {
    if (sentences[i].startMs <= nowMs) currentIdx = i;
  }
  const sentence = sentences[currentIdx];
  if (!sentence) return null;
  const icon = iconFor(sentence);
  if (!icon) return null; // pas pertinent → rien

  const sentenceStartFrame = (sentence.startMs / 1000) * fps;
  const pop = spring({
    frame: Math.max(frame - sentenceStartFrame, 0), fps,
    config: { damping: 200 }, durationInFrames: 12,
  });

  return (
    <div style={{
      position: "absolute", left: 56, bottom: 190,
      width: 128, height: 128, borderRadius: 28,
      background: `${NAVY_LIGHT}E6`, border: `2px solid ${TEAL}66`,
      boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
      display: "flex", alignItems: "center", justifyContent: "center",
      opacity: pop, transform: `scale(${0.85 + 0.15 * pop})`,
    }}>
      <svg width="72" height="72" viewBox="0 0 24 24" fill="none"
        stroke={TEAL} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"
        style={{ color: TEAL }}>
        {ICON_PATHS[icon]}
      </svg>
    </div>
  );
};

// Hook partagé : charge les captions (JSON whisper à côté du média) → phrases groupées.
export const useSentences = (src: string): Sentence[] => {
  const [captions, setCaptions] = useState<Caption[]>([]);
  const { delayRender, continueRender } = useDelayRender();
  const [handle] = useState(() => delayRender());
  const captionsFile = src.replace(/\.(mp4|mp3|m4a|wav|webm|mov)$/i, ".json");
  const fetchCaptions = useCallback(async () => {
    try {
      await loadFont();
      const res = await fetch(captionsFile);
      setCaptions((await res.json()) as Caption[]);
      continueRender(handle);
    } catch (e) {
      cancelRender(e);
    }
  }, [captionsFile, continueRender, handle]);
  useEffect(() => {
    fetchCaptions();
  }, [fetchCaptions]);
  return useMemo(() => groupSentences(captions), [captions]);
};

// Signature bas-gauche — RÈGLE STRICTE Abdelilah : signature 3 lignes (nom / Enseignant-Chercheur / Expert...).
export const Signature: React.FC = () => (
  <div style={{
    position: "absolute", left: 56, bottom: 96, fontFamily: TheBoldFont,
    color: `${WHITE}D9`, fontSize: 30, letterSpacing: 1,
  }}>
    Abdelilah Kahaji
    <div style={{ marginTop: 8, fontSize: 19, letterSpacing: 0.3, color: `${WHITE}99`, lineHeight: 1.4 }}>
      Enseignant-Chercheur
      <br />
      {deaccent("Expert en Systèmes d'Information & Intelligence Artificielle")}
    </div>
  </div>
);

export const PresenterPiP: React.FC<{ src: string }> = ({ src }) => {
  const sentences = useSentences(src);

  const PIP = 380; // diamètre du rond avatar

  return (
    <AbsoluteFill>
      <AnimatedBackground />
      <SentenceStack sentences={sentences} />
      <CornerIcon sentences={sentences} />

      {/* Clone en petit, rond, bas-droite (fournit aussi la piste audio).
          Cadrage : zoom fort + recadrage vers le visage (retour Abdelilah). */}
      <div style={{
        position: "absolute", right: 44, bottom: 64,
        width: PIP, height: PIP, borderRadius: "50%", overflow: "hidden",
        border: `7px solid ${WHITE}`, boxShadow: "0 14px 44px rgba(0,0,0,0.55)",
        background: NAVY_LIGHT,
      }}>
        <OffthreadVideo
          src={src}
          style={{
            width: "100%", height: "100%",
            objectFit: "cover", objectPosition: "center 30%",
            transform: "scale(2.05)", transformOrigin: "center 34%",
          }}
        />
      </div>

      <Signature />
    </AbsoluteFill>
  );
};
