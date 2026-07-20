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

// Vidéo « Les métiers de demain » (produire-ne-suffit-plus) — montage multi-phases :
//   P1a 0→6.5s    : avatar PLEIN ÉCRAN + pastille + titre (template cadrage-metier, partie 1)
//   P1b 6.5→17.5s : carte avatar en HAUT + gros texte kinétique en BAS (cadrage, partie 2)
//   P2 17.5→45s   : template narration-illustree SANS média central (fond navy libre pour
//                   le montage d'Abdelilah) — sous-titres en haut, avatar PiP RECTANGULAIRE
//   P3 45→64.6s   : avatar AGRANDI au centre (compétence « vérification »), 1/3 haut du
//                   cadrage coupé (vide) pour centrer le visage
//   P4 64.6→fin   : retour PiP bas-droite
// Sortie : MP4 classique (pas d'alpha) — l'arrière-plan animé habituel reste visible.

export const metiersDemainSchema = z.object({
  avatar: z.string(),
});

const resolveSrc = (s: string): string =>
  /^(https?:|\/)/.test(s) ? s : staticFile(s);

export const calculateMetiersDemainMetadata: CalculateMetadataFunction<
  z.infer<typeof metiersDemainSchema>
> = async ({ props }) => {
  const fps = 30;
  const m = await getVideoMetadata(resolveSrc(props.avatar));
  return { fps, durationInFrames: Math.floor(m.durationInSeconds * fps) };
};

// Cadrage source : l'avatar HeyGen est en 1920×1080 avec bandes BLANCHES latérales ;
// le contenu utile est la bande verticale x 712→1207 (mesuré sur frame réelle).
const SRC_W = 1920;
const SRC_H = 1080;
const CX0 = 712;
const CW = 495;
const CH = 1080;

// Boîtes d'affichage de l'avatar par phase (canvas 1080×1920).
// cropTop = fraction du HAUT du contenu coupée ; vAlign = ancrage vertical du reste.
type Box = { x: number; y: number; w: number; h: number; r: number; cropTop: number; vAlign: number; border: number };
const FULL: Box = { x: 0, y: 0, w: 1080, h: 1920, r: 0, cropTop: 0, vAlign: 0.25, border: 0 };
const CARD: Box = { x: 40, y: 40, w: 1000, h: 880, r: 40, cropTop: 0, vAlign: 0.3, border: 0 };
const PIP: Box = { x: 736, y: 1436, w: 300, h: 420, r: 28, cropTop: 0.2, vAlign: 0.25, border: 6 };
const BIG: Box = { x: 190, y: 610, w: 700, h: 1010, r: 40, cropTop: 0.3, vAlign: 0, border: 6 };

// Frontières de phases (s), calées sur les mots de la narration.
const T1 = 6.5;   // « Produire du texte… »
const T2 = 17.5;  // « La production intellectuelle standardisée… »
const T3 = 45.0;  // « La troisième, c'est la vérification »
const T4 = 64.6;  // « Cela concerne la cybersécurité… »
const TRANS = 0.5; // durée des transitions (s)

const boxAt = (t: number): Box => {
  const keys: (keyof Box)[] = ["x", "y", "w", "h", "r", "cropTop", "vAlign", "border"];
  const seq: Box[] = [FULL, FULL, CARD, CARD, PIP, PIP, BIG, BIG, PIP];
  const times = [0, T1, T1 + TRANS, T2, T2 + TRANS, T3, T3 + TRANS, T4, T4 + TRANS];
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

export const MetiersDemain: React.FC<z.infer<typeof metiersDemainSchema>> = ({
  avatar,
}) => {
  const src = resolveSrc(avatar);
  const sentences = useSentences(src);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const b = boxAt(t);
  // Mise à l'échelle du contenu utile (bande 495×1080, sans les bords blancs)
  const visibleH = CH * (1 - b.cropTop);
  const scale = Math.max(b.w / CW, b.h / visibleH);
  const dispW = CW * scale;
  const dispVisH = visibleH * scale;
  const left = -(CX0 * scale) - (dispW - b.w) / 2;
  const top = -(b.cropTop * CH * scale) - (dispVisH - b.h) * b.vAlign;

  // Opacités des couches par phase
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
          {deaccent("PRODUIRE NE SUFFIT PLUS")}
        </div>
        <div
          style={{
            color: WHITE,
            fontSize: 92,
            lineHeight: 1.08,
            textShadow: "0 8px 34px rgba(0,0,0,0.75)",
          }}
        >
          {deaccent("L'IA produit à votre place")}
        </div>
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
