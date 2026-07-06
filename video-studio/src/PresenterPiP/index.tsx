import { Caption } from "@remotion/captions";
import { getVideoMetadata } from "@remotion/media-utils";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  cancelRender,
  interpolate,
  OffthreadVideo,
  Sequence,
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

type Sentence = { words: Caption[]; startMs: number; endMs: number };

// Regroupe les mots (captions whisper) en phrases : ponctuation forte ou 9 mots max
const groupSentences = (captions: Caption[]): Sentence[] => {
  const sentences: Sentence[] = [];
  let current: Caption[] = [];
  for (const word of captions) {
    current.push(word);
    const endOfSentence = /[.!?…]\s*$/.test(word.text.trim());
    if (endOfSentence || current.length >= 9) {
      sentences.push({
        words: current,
        startMs: current[0].startMs,
        endMs: current[current.length - 1].endMs,
      });
      current = [];
    }
  }
  if (current.length > 0) {
    sentences.push({
      words: current,
      startMs: current[0].startMs,
      endMs: current[current.length - 1].endMs,
    });
  }
  return sentences;
};

// Fond animé discret : anneaux et formes qui dérivent lentement (teal sur navy)
const AnimatedBackground: React.FC = () => {
  const frame = useCurrentFrame();
  const drift = frame * 0.35;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(160deg, ${NAVY} 55%, ${NAVY_LIGHT})` }}>
      <div
        style={{
          position: "absolute", width: 620, height: 620, borderRadius: "50%",
          border: `3px solid ${TEAL}33`, left: -180, top: 140,
          transform: `rotate(${drift}deg) translateX(${20 + 12 * Math.sin(frame / 40)}px)`,
        }}
      />
      <div
        style={{
          position: "absolute", width: 340, height: 340, borderRadius: "50%",
          border: `2px solid ${TEAL}22`, right: -90, top: 620,
          transform: `translateY(${18 * Math.cos(frame / 55)}px)`,
        }}
      />
      <div
        style={{
          position: "absolute", width: 260, height: 260,
          border: `2px solid ${ACCENT}26`, left: 90, bottom: 260,
          transform: `rotate(${45 + drift / 2}deg)`,
        }}
      />
    </AbsoluteFill>
  );
};

// Une phrase en typographie cinétique : chaque mot surgit quand il est prononcé
const KineticSentence: React.FC<{ sentence: Sentence }> = ({ sentence }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  return (
    <AbsoluteFill
      style={{
        alignItems: "center", justifyContent: "flex-start",
        paddingTop: 300, paddingLeft: 70, paddingRight: 70,
      }}
    >
      <div
        style={{
          display: "flex", flexWrap: "wrap", justifyContent: "center",
          gap: "10px 18px", fontFamily: TheBoldFont, textAlign: "center",
        }}
      >
        {sentence.words.map((word, i) => {
          // Horloge LOCALE à la Sequence → tout est exprimé relativement au début de phrase
          const relStartMs = word.startMs - sentence.startMs;
          const relEndMs = word.endMs - sentence.startMs;
          const appearFrame = (relStartMs / 1000) * fps;
          const localFrame = frame - appearFrame;
          const scale = spring({ frame: Math.max(localFrame, 0), fps, config: { damping: 200 }, durationInFrames: 8 });
          const isSpoken = nowMs >= relStartMs;
          const isCurrent = nowMs >= relStartMs && nowMs <= relEndMs + 120;
          // Mot « idée » (long) → accent teal ; mot en cours → surbrillance
          const isKeyword = word.text.trim().length >= 8;
          return (
            <span
              key={i}
              style={{
                fontSize: 84, lineHeight: 1.08,
                color: isCurrent ? ACCENT : isKeyword ? TEAL : WHITE,
                opacity: isSpoken ? 1 : 0,
                transform: `scale(${isSpoken ? scale : 0.6}) translateY(${interpolate(isSpoken ? scale : 0, [0, 1], [26, 0])}px)`,
                textShadow: "0 6px 26px rgba(0,0,0,0.55)",
              }}
            >
              {word.text.trim()}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const PresenterPiP: React.FC<{ src: string }> = ({ src }) => {
  const [captions, setCaptions] = useState<Caption[]>([]);
  const { delayRender, continueRender } = useDelayRender();
  const [handle] = useState(() => delayRender());
  const { fps } = useVideoConfig();

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

      {/* Typographie cinétique des idées, phrase par phrase */}
      {sentences.map((s, i) => {
        const from = (s.startMs / 1000) * fps;
        const until = i < sentences.length - 1
          ? (sentences[i + 1].startMs / 1000) * fps
          : (s.endMs / 1000) * fps + fps;
        return (
          <Sequence key={i} from={from} durationInFrames={Math.max(until - from, 1)}>
            <KineticSentence sentence={s} />
          </Sequence>
        );
      })}

      {/* Clone en petit, rond, bas-droite (fournit aussi la piste audio) */}
      <div
        style={{
          position: "absolute", right: 44, bottom: 64,
          width: PIP, height: PIP, borderRadius: "50%", overflow: "hidden",
          border: `7px solid ${WHITE}`, boxShadow: "0 14px 44px rgba(0,0,0,0.55)",
          background: NAVY_LIGHT,
        }}
      >
        <OffthreadVideo
          src={src}
          style={{
            width: "100%", height: "100%",
            objectFit: "cover", objectPosition: "center 18%",
            transform: "scale(1.45)", transformOrigin: "center 22%",
          }}
        />
      </div>

      {/* Signature discrète */}
      <div
        style={{
          position: "absolute", left: 56, bottom: 96, fontFamily: TheBoldFont,
          color: `${WHITE}B0`, fontSize: 30, letterSpacing: 1,
        }}
      >
        Abdelilah Kahaji — OmegaSoft
      </div>
    </AbsoluteFill>
  );
};
