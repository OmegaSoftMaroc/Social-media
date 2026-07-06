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

// Illustration par phrase : pictogramme choisi selon les mots-clés du propos
const EMOJI_RULES: [RegExp, string][] = [
  [/prospect|client|vente|commercial/i, "🎯"],
  [/donn[ée]e|data|fichier|crm|base/i, "📊"],
  [/agent|ia\b|intelligence|robot|automatis/i, "🤖"],
  [/pme|industri|usine|entreprise|atelier/i, "🏭"],
  [/question|pourquoi|comment|demandez/i, "❓"],
  [/commenc|d[ée]marr|lanc|premier/i, "🚀"],
  [/temps|heure|matin|quotidien|jour/i, "⏱️"],
  [/argent|co[ûu]t|budget|roi|rentab/i, "💰"],
  [/propre|nettoy|qualit|fiab/i, "✅"],
  [/outil|brancher|connect|syst[èe]me/i, "🔌"],
  [/id[ée]e|r[ée]fl[ée]ch|pens/i, "💡"],
  [/r[ée]sultat|gagn|efficac|performan/i, "📈"],
];

const emojiFor = (sentence: Sentence, index: number): string => {
  for (const [re, emoji] of EMOJI_RULES) {
    if (re.test(sentence.text)) return emoji;
  }
  return ["💡", "🔍", "🧭", "⚙️"][index % 4]; // variation si aucun mot-clé
};

// Fond animé discret : anneaux et formes qui dérivent lentement (teal sur navy)
const AnimatedBackground: React.FC = () => {
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

// Pile de phrases : la courante (kinétique, mot à mot) + les 2 précédentes (estompées)
const SentenceStack: React.FC<{ sentences: Sentence[] }> = ({ sentences }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  let currentIdx = 0;
  for (let i = 0; i < sentences.length; i++) {
    if (sentences[i].startMs <= nowMs) currentIdx = i;
  }
  const firstVisible = Math.max(0, currentIdx - 2);
  const visible = sentences.slice(firstVisible, currentIdx + 1);

  return (
    <div style={{
      position: "absolute", top: 110, left: 60, right: 60,
      display: "flex", flexDirection: "column", gap: 34,
      fontFamily: TheBoldFont, textAlign: "center",
    }}>
      {visible.map((s, vi) => {
        const isCurrent = firstVisible + vi === currentIdx;
        if (!isCurrent) {
          // Phrase déjà dite : reste affichée, plus petite et estompée
          return (
            <div key={s.startMs} style={{
              fontSize: 46, lineHeight: 1.15, color: `${WHITE}77`,
              textShadow: "0 4px 18px rgba(0,0,0,0.45)",
            }}>
              {s.text}
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
                  fontSize: 66, lineHeight: 1.1,
                  color: isNow ? ACCENT : isKeyword ? TEAL : WHITE,
                  opacity: isSpoken ? 1 : 0,
                  transform: `scale(${isSpoken ? scale : 0.6})`,
                  textShadow: "0 6px 26px rgba(0,0,0,0.55)",
                }}>
                  {word.text.trim()}
                </span>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

// Illustration centrale : pictogramme de la phrase courante, pop + flottement
const Illustration: React.FC<{ sentences: Sentence[] }> = ({ sentences }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  let currentIdx = 0;
  for (let i = 0; i < sentences.length; i++) {
    if (sentences[i].startMs <= nowMs) currentIdx = i;
  }
  const sentence = sentences[currentIdx];
  if (!sentence) return null;

  const sentenceStartFrame = (sentence.startMs / 1000) * fps;
  const pop = spring({
    frame: Math.max(frame - sentenceStartFrame, 0), fps,
    config: { damping: 12, stiffness: 120 }, durationInFrames: 18,
  });
  const float = 10 * Math.sin(frame / 18);

  return (
    <div style={{
      position: "absolute", top: "50%", left: 0, right: 0,
      display: "flex", justifyContent: "center", alignItems: "center",
    }}>
      {/* halo de marque derrière le pictogramme */}
      <div style={{
        position: "absolute", width: 420, height: 420, borderRadius: "50%",
        background: `radial-gradient(circle, ${TEAL}2E 0%, transparent 70%)`,
        transform: `scale(${pop})`,
      }} />
      <div style={{
        fontSize: 300,
        transform: `scale(${pop}) translateY(${float}px)`,
        filter: "drop-shadow(0 18px 40px rgba(0,0,0,0.45))",
      }}>
        {emojiFor(sentence, currentIdx)}
      </div>
    </div>
  );
};

export const PresenterPiP: React.FC<{ src: string }> = ({ src }) => {
  const [captions, setCaptions] = useState<Caption[]>([]);
  const { delayRender, continueRender } = useDelayRender();
  const [handle] = useState(() => delayRender());

  const captionsFile = src.replace(/.mp4$/, ".json");

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

  const sentences = useMemo(() => groupSentences(captions), [captions]);

  const PIP = 380; // diamètre du rond avatar

  return (
    <AbsoluteFill>
      <AnimatedBackground />
      <SentenceStack sentences={sentences} />
      <Illustration sentences={sentences} />

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

      {/* Signature discrète */}
      <div style={{
        position: "absolute", left: 56, bottom: 96, fontFamily: TheBoldFont,
        color: `${WHITE}B0`, fontSize: 30, letterSpacing: 1,
      }}>
        Abdelilah Kahaji — OmegaSoft
      </div>
    </AbsoluteFill>
  );
};
