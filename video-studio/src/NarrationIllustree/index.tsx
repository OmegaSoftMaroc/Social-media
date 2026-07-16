import { getAudioDurationInSeconds } from "@remotion/media-utils";
import React from "react";
import {
  AbsoluteFill,
  Audio,
  CalculateMetadataFunction,
  Img,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { AnimatedBackground, SentenceStack, Signature, useSentences } from "../PresenterPiP";

// Charte OmegaSoft
const NAVY = "#0B1E33";
const NAVY_LIGHT = "#122C4A";
const TEAL = "#2AA7A0";
const ACCENT = "#FFB454";
const WHITE = "#FFFFFF";

// Template narration-illustree : même voix off + texte kinétique que narration-animee,
// mais le TEXTE passe en bandeau HAUT et le centre accueille une SCÈNE MÉDIA (illustrations
// Ideogram par idée, ou clips fournis) synchronisée aux idées, avec fondu + Ken Burns.
// Pas d'avatar, pas de musique. Signature + photo de profil conservées.
export const narrationIllustreeSchema = z.object({
  src: z.string(),
  photo: z.string().optional(),
  // Chaque idée : instant de départ (s) + média à afficher (image ou vidéo, chemin public).
  // `clipSec` = durée réelle du clip vidéo (sert à l'étirer sur la durée de l'idée).
  ideas: z.array(
    z.object({
      start: z.number(),
      src: z.string(),
      kind: z.enum(["image", "video"]).optional(),
      clipSec: z.number().optional(),
    }),
  ),
});

type Props = z.infer<typeof narrationIllustreeSchema>;

// Accepte un src déjà résolu (staticFile → "/x", ou http) OU un nom de fichier brut
// (résolu via staticFile au runtime). Rend le rendu via --props possible : un nom brut
// passé en props n'a pas d'origine tant que staticFile n'est pas appelé au runtime.
const resolveSrc = (s: string): string =>
  /^(https?:|\/)/.test(s) ? s : staticFile(s);

export const calculateNarrationIllustreeMetadata: CalculateMetadataFunction<Props> = async ({
  props,
}) => {
  const fps = 30;
  const durationInSeconds = await getAudioDurationInSeconds(resolveSrc(props.src));
  return { fps, durationInFrames: Math.max(1, Math.floor(durationInSeconds * fps)) };
};

// Cadre de la scène média (1080×1920). Bandeau texte au-dessus (top ≈ 70→600),
// signature + photo en dessous (bas ≈ 1520→1900).
const STAGE = { left: 90, top: 500, width: 900, height: 940, radius: 40 };
const PHOTO = 210;
const FPS = 30; // cf. calculateNarrationIllustreeMetadata

// Ken Burns VARIÉ par idée : chaque idée a un mouvement distinct (zoom in/out +
// travelling directionnel) pour que la scène « bouge » vraiment et sans monotonie.
const MOTIONS = [
  { zoom: [1.10, 1.30], pan: [42, -30] }, // zoom avant, dérive haut-droite
  { zoom: [1.30, 1.10], pan: [-46, 22] }, // zoom arrière, dérive bas-gauche
  { zoom: [1.08, 1.26], pan: [-54, -12] }, // travelling gauche
  { zoom: [1.26, 1.08], pan: [52, 14] }, // travelling droite
  { zoom: [1.12, 1.32], pan: [6, -52] }, // poussée vers le haut
];

const FADE = 0.5; // fondu d'entrée (s)

// Rendu média d'UNE idée, dans une Sequence locale (frame 0 = start-FADE).
// Vidéo (clip fal Kling) → jouée étirée sur la durée de l'idée, Ken Burns coupé.
// Image (fallback) → Ken Burns directionnel + entrée glissée.
const IdeaMedia: React.FC<{
  idea: Props["ideas"][number];
  dur: number; // durée de l'idée (s)
  index: number;
}> = ({ idea, dur, index }) => {
  const frame = useCurrentFrame(); // local à la Sequence
  const { fps } = useVideoConfig();
  const local = frame / fps; // s depuis start-FADE

  // Fondu d'entrée par-dessus l'idée précédente.
  const opacity = interpolate(local, [0, FADE], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Entrée : le média surgit (échelle qui se pose) et glisse depuis la droite.
  const enter = spring({
    frame: Math.max(frame - FADE * fps, 0),
    fps,
    config: { damping: 200 },
    durationInFrames: 20,
  });
  const enterScale = interpolate(enter, [0, 1], [1.14, 1]);
  const enterX = interpolate(enter, [0, 1], [70, 0]);

  const isVideo = idea.kind === "video";

  if (isVideo) {
    // Étire le clip pour couvrir la durée de l'idée (jamais accéléré au-delà de 1).
    const clipSec = idea.clipSec ?? 5;
    const rate = Math.min(1, clipSec / dur);
    return (
      <OffthreadVideo
        src={staticFile(idea.src)}
        muted
        playbackRate={rate}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          opacity,
          transform: `scale(${1.04 * enterScale}) translate(${enterX}px, 0px)`,
          zIndex: index,
        }}
      />
    );
  }

  // Fallback image : Ken Burns directionnel sur la durée de l'idée.
  const m = MOTIONS[index % MOTIONS.length];
  const p = Math.min(1, Math.max(0, (local - FADE) / dur));
  const kbScale = interpolate(p, [0, 1], m.zoom);
  const kbX = interpolate(p, [0, 1], [0, m.pan[0]]);
  const kbY = interpolate(p, [0, 1], [0, m.pan[1]]);
  return (
    <Img
      src={staticFile(idea.src)}
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        objectFit: "cover",
        opacity,
        transform: `scale(${kbScale * enterScale}) translate(${kbX + enterX}px, ${kbY}px)`,
        zIndex: index,
      }}
    />
  );
};

// Particules teal qui dérivent lentement vers le haut — donnent de la vie à toute
// la scène (au-dessus de l'image, sous le vignettage). Positions déterministes.
const StageParticles: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const N = 16;
  return (
    <div style={{ position: "absolute", inset: 0, zIndex: 40, pointerEvents: "none" }}>
      {Array.from({ length: N }).map((_, i) => {
        const cycle = fps * (4 + (i % 5) * 0.6);
        const t = ((frame + i * 37) % cycle) / cycle; // 0..1 durée de vie
        const baseX = (i * 149) % STAGE.width;
        const wobble = 26 * Math.sin((frame / 30) + i);
        const x = baseX + wobble;
        const y = STAGE.height - t * (STAGE.height + 60);
        const size = 3 + (i % 3);
        const op = Math.sin(t * Math.PI) * 0.4;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: size,
              height: size,
              borderRadius: "50%",
              background: TEAL,
              opacity: op,
              boxShadow: `0 0 ${size * 2}px ${TEAL}`,
            }}
          />
        );
      })}
    </div>
  );
};

// Balayage de lumière diagonal, lent, très discret — anime la surface de l'image.
const LightSweep: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cycle = fps * 8;
  const t = (frame % cycle) / cycle;
  const x = interpolate(t, [0, 1], [-STAGE.width * 0.6, STAGE.width * 1.2]);
  return (
    <div
      style={{
        position: "absolute",
        top: -STAGE.height * 0.2,
        left: x,
        width: STAGE.width * 0.35,
        height: STAGE.height * 1.4,
        transform: "rotate(18deg)",
        background: `linear-gradient(90deg, transparent, ${WHITE}12, transparent)`,
        zIndex: 45,
        pointerEvents: "none",
      }}
    />
  );
};

const MediaStage: React.FC<{ ideas: Props["ideas"] }> = ({ ideas }) => {
  return (
    <div
      style={{
        position: "absolute",
        left: STAGE.left,
        top: STAGE.top,
        width: STAGE.width,
        height: STAGE.height,
        borderRadius: STAGE.radius,
        overflow: "hidden",
        border: `3px solid ${TEAL}59`,
        boxShadow: "0 24px 64px rgba(0,0,0,0.55)",
        background: NAVY_LIGHT,
      }}
    >
      {ideas.map((idea, i) => {
        const end = i + 1 < ideas.length ? ideas[i + 1].start : idea.start + 30;
        const dur = Math.max(end - idea.start, 1);
        const fromF = Math.max(0, Math.round((idea.start - FADE) * FPS));
        const durF = Math.round((dur + FADE + 0.2) * FPS);
        return (
          <Sequence key={i} from={fromF} durationInFrames={durF} layout="none">
            <IdeaMedia idea={idea} dur={dur} index={i} />
          </Sequence>
        );
      })}
      <LightSweep />
      <StageParticles />
      {/* Vignettage bas pour ancrer l'image et détacher la signature. */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(180deg, transparent 68%, ${NAVY}B3)`,
          zIndex: 99,
        }}
      />
    </div>
  );
};

export const NarrationIllustree: React.FC<Props> = ({
  src,
  ideas,
  photo = staticFile("brand-photo-crop.png"),
}) => {
  const sentences = useSentences(resolveSrc(src));

  return (
    <AbsoluteFill>
      <AnimatedBackground />

      {/* Texte kinétique en bandeau HAUT (le centre est occupé par la scène média). */}
      <SentenceStack
        sentences={sentences}
        topInset={60}
        bottomInset={1460}
        justify="center"
        fontScale={0.82}
        maxPrev={1}
      />

      {/* Scène média centrale synchronisée aux idées. */}
      <MediaStage ideas={ideas} />

      <Audio src={resolveSrc(src)} />

      {/* Photo de profil statique, rond bas-droite. */}
      <div
        style={{
          position: "absolute",
          right: 52,
          bottom: 88,
          width: PHOTO,
          height: PHOTO,
          borderRadius: "50%",
          overflow: "hidden",
          border: `4px solid ${WHITE}D9`,
          boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
          background: NAVY_LIGHT,
        }}
      >
        <Img
          src={photo}
          style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }}
        />
      </div>

      <Signature />
    </AbsoluteFill>
  );
};
