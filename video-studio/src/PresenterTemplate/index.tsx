import { getVideoMetadata } from "@remotion/media-utils";
import React from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  OffthreadVideo,
  staticFile,
} from "remotion";
import { z } from "zod";
import { SentenceStack, Signature, useSentences } from "../PresenterPiP";

// Charte OmegaSoft
const WHITE = "#FFFFFF";
const NAVY_LIGHT = "#122C4A";

// Nouveau workflow « overlay » : produit le CALQUE marque (avatar PiP + sous-titres +
// signature) avec un CENTRE TRANSPARENT — Abdelilah y compose ses propres visuels au
// montage. Rendu en codec alpha (ex. prores 4444) → .mov avec canal alpha.

export const presenterTemplateSchema = z.object({
  // Vidéo avatar (HeyGen) fournie par Abdelilah ; porte aussi la piste audio + le timing.
  avatar: z.string(),
});

// Accepte un src déjà résolu ("/x" ou http) OU un nom de fichier brut (résolu au runtime).
const resolveSrc = (s: string): string =>
  /^(https?:|\/)/.test(s) ? s : staticFile(s);

export const calculatePresenterTemplateMetadata: CalculateMetadataFunction<
  z.infer<typeof presenterTemplateSchema>
> = async ({ props }) => {
  const fps = 30;
  const m = await getVideoMetadata(resolveSrc(props.avatar));
  return { fps, durationInFrames: Math.floor(m.durationInSeconds * fps) };
};

export const PresenterTemplate: React.FC<
  z.infer<typeof presenterTemplateSchema>
> = ({ avatar }) => {
  const src = resolveSrc(avatar);
  const sentences = useSentences(src);
  const PIP = 380; // diamètre du rond avatar (identique à PresenterPiP)

  return (
    // PAS de background → tout le hors-éléments reste TRANSPARENT (zone de montage).
    <AbsoluteFill>
      {/* Sous-titres kinétiques, bandeau haut */}
      <SentenceStack sentences={sentences} />

      {/* Avatar rond bas-droite (fournit aussi la piste audio + le timing des sous-titres). */}
      <div
        style={{
          position: "absolute",
          right: 44,
          bottom: 64,
          width: PIP,
          height: PIP,
          borderRadius: "50%",
          overflow: "hidden",
          border: `7px solid ${WHITE}`,
          boxShadow: "0 14px 44px rgba(0,0,0,0.55)",
          background: NAVY_LIGHT,
        }}
      >
        <OffthreadVideo
          src={src}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center 30%",
            transform: "scale(2.05)",
            transformOrigin: "center 34%",
          }}
        />
      </div>

      {/* Signature 3 lignes, bas-gauche */}
      <Signature />
    </AbsoluteFill>
  );
};
