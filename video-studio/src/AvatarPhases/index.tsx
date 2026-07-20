import { getVideoMetadata } from "@remotion/media-utils";
import React from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  Easing,
  interpolate,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import {
  AnimatedBackground,
  deaccent,
  SentenceStack,
  Signature,
  useSentences,
} from "../PresenterPiP";
import { TheBoldFont } from "../load-font";

// Charte OmegaSoft
const TEAL = "#2AA7A0";
const WHITE = "#FFFFFF";

// TEMPLATE multi-phases « AvatarPhases » — 100 % paramétrable via props (1 JSON/vidéo) :
//   P1a 0→introSplit       : avatar PLEIN ÉCRAN + pastille + titre (style cadrage-metier)
//   P1b introSplit→introFin: carte avatar en HAUT + gros texte kinétique en BAS
//   P2  introFin→zoomDebut : sous-titres haut + avatar PiP RECTANGULAIRE bas-droite,
//                            CENTRE LIBRE (fond navy) pour le montage manuel d'Abdelilah
//   P3  zoomDebut→zoomFin  : avatar AGRANDI au centre (passage clé de la narration)
//   P4  zoomFin→fin        : retour PiP bas-droite
// Sous-titres : fichier <avatar>.json à côté du mp4 (généré par pipeline/avatar_prep.py).
// Cadrage : cropSource = bande utile du mp4 avatar (HeyGen exporte avec bandes blanches) ;
// mesurable via `python -m pipeline.avatar_prep measure <avatar.mp4>`.

export const avatarPhasesSchema = z.object({
  avatar: z.string(),
  pastille: z.string().optional(),
  titre: z.string().optional(),
  phases: z
    .object({
      introSplit: z.number(),
      introFin: z.number(),
      // Phase « avatar agrandi » OPTIONNELLE : omettre zoomDebut/zoomFin la supprime
      // (l'avatar reste en PiP bas-droite après l'intro, centre libre en continu).
      zoomDebut: z.number().optional(),
      zoomFin: z.number().optional(),
    })
    .optional(),
  cropSource: z.object({ x0: z.number(), largeur: z.number() }).optional(),
});
type Props = z.infer<typeof avatarPhasesSchema>;

// Défauts = vidéo « produire-ne-suffit-plus » (première vidéo produite avec ce template)
type Phases = { introSplit: number; introFin: number; zoomDebut?: number; zoomFin?: number };
const DEFAULT_PHASES: Phases = { introSplit: 6.5, introFin: 17.5 };
const DEFAULT_CROP = { x0: 712, largeur: 495 };

const resolveSrc = (s: string): string =>
  /^(https?:|\/)/.test(s) ? s : staticFile(s);

export const calculateAvatarPhasesMetadata: CalculateMetadataFunction<Props> = async ({
  props,
}) => {
  const fps = 30;
  const m = await getVideoMetadata(resolveSrc(props.avatar));
  return { fps, durationInFrames: Math.floor(m.durationInSeconds * fps) };
};

// Source avatar (HeyGen) : cadre 1920×1080, contenu utile = bande verticale.
const SRC_W = 1920;
const SRC_H = 1080;

// Boîtes d'affichage par phase (canvas 1080×1920).
// cropTop = fraction du HAUT du contenu coupée ; vAlign = ancrage vertical du reste.
type Box = { x: number; y: number; w: number; h: number; r: number; cropTop: number; vAlign: number; border: number };
const FULL: Box = { x: 0, y: 0, w: 1080, h: 1920, r: 0, cropTop: 0, vAlign: 0.25, border: 0 };
const CARD: Box = { x: 40, y: 40, w: 1000, h: 880, r: 40, cropTop: 0, vAlign: 0.3, border: 0 };
const PIP: Box = { x: 736, y: 1436, w: 300, h: 420, r: 28, cropTop: 0.2, vAlign: 0.25, border: 6 };
const BIG: Box = { x: 190, y: 610, w: 700, h: 1010, r: 40, cropTop: 0.3, vAlign: 0, border: 6 };

const TRANS = 0.5; // durée des transitions (s)

const boxAt = (t: number, ph: Phases): Box => {
  const keys: (keyof Box)[] = ["x", "y", "w", "h", "r", "cropTop", "vAlign", "border"];
  const seq: Box[] = [FULL, FULL, CARD, CARD, PIP];
  const times = [
    0,
    ph.introSplit, ph.introSplit + TRANS,
    ph.introFin, ph.introFin + TRANS,
  ];
  // Phase « agrandi » seulement si demandée dans les props
  if (ph.zoomDebut !== undefined && ph.zoomFin !== undefined) {
    seq.push(PIP, BIG, BIG, PIP);
    times.push(ph.zoomDebut, ph.zoomDebut + TRANS, ph.zoomFin, ph.zoomFin + TRANS);
  }
  const out = {} as Box;
  for (const k of keys) {
    out[k] = interpolate(t, times, seq.map((b) => b[k]), {
      easing: Easing.inOut(Easing.ease),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  }
  return out;
};

export const AvatarPhases: React.FC<Props> = ({
  avatar,
  pastille = "",
  titre = "",
  phases = DEFAULT_PHASES,
  cropSource = DEFAULT_CROP,
}) => {
  const src = resolveSrc(avatar);
  const sentences = useSentences(src);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const b = boxAt(t, phases);
  const CX0 = cropSource.x0;
  const CW = cropSource.largeur;
  const CH = SRC_H;
  // Mise à l'échelle du contenu utile (bande CW×CH, sans les bords blancs)
  const visibleH = CH * (1 - b.cropTop);
  const scale = Math.max(b.w / CW, b.h / visibleH);
  const dispW = CW * scale;
  const dispVisH = visibleH * scale;
  const left = -(CX0 * scale) - (dispW - b.w) / 2;
  const top = -(b.cropTop * CH * scale) - (dispVisH - b.h) * b.vAlign;

  // Opacités des couches par phase
  const { introSplit: T1, introFin: T2 } = phases;
  const titleOp = interpolate(t, [0, 0.4, T1 - 0.5, T1], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bigCapsOp = interpolate(t, [T1, T1 + 0.5, T2 - 0.3, T2 + 0.2], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const topCapsOp = interpolate(t, [T2, T2 + 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <AnimatedBackground />

      {/* Avatar : une seule vidéo, sa boîte se transforme entre les phases. */}
      <div
        style={{
          position: "absolute",
          left: b.x,
          top: b.y,
          width: b.w,
          height: b.h,
          borderRadius: b.r,
          overflow: "hidden",
          border: b.border > 0.3 ? `${Math.round(b.border)}px solid ${WHITE}` : "none",
          boxShadow: b.border > 0.3 ? "0 14px 44px rgba(0,0,0,0.55)" : "none",
          background: "#122C4A",
        }}
      >
        <OffthreadVideo
          src={src}
          style={{
            position: "absolute",
            width: SRC_W * scale,
            height: SRC_H * scale,
            left,
            top,
            maxWidth: "none",
          }}
        />
      </div>

      {/* P1a — pastille + titre sur le tiers haut (par-dessus l'avatar plein écran) */}
      <div style={{ position: "absolute", top: 150, left: 60, right: 60, textAlign: "center", opacity: titleOp, fontFamily: TheBoldFont }}>
        {pastille ? (
          <div
            style={{
              display: "inline-block",
              background: `${TEAL}E6`,
              color: WHITE,
              fontSize: 26,
              letterSpacing: 3,
              padding: "12px 26px",
              borderRadius: 999,
              marginBottom: 30,
            }}
          >
            {deaccent(pastille)}
          </div>
        ) : null}
        {titre ? (
          <div
            style={{
              color: WHITE,
              fontSize: 92,
              lineHeight: 1.08,
              textShadow: "0 8px 34px rgba(0,0,0,0.75)",
            }}
          >
            {deaccent(titre)}
          </div>
        ) : null}
      </div>

      {/* P1b — gros texte kinétique dans la moitié basse (sous la carte avatar) */}
      <div style={{ position: "absolute", inset: 0, opacity: bigCapsOp }}>
        <SentenceStack sentences={sentences} topInset={1000} bottomInset={170} justify="center" fontScale={1.2} maxPrev={0} />
      </div>

      {/* P2+ — sous-titres en bandeau haut (template narration-illustree) */}
      <div style={{ position: "absolute", inset: 0, opacity: topCapsOp }}>
        <SentenceStack sentences={sentences} topInset={60} bottomInset={1460} justify="center" fontScale={0.82} maxPrev={1} />
      </div>

      {/* Signature à partir de P2 */}
      <div style={{ position: "absolute", inset: 0, opacity: topCapsOp }}>
        <Signature />
      </div>
    </AbsoluteFill>
  );
};
