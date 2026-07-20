import { getAudioDurationInSeconds } from "@remotion/media-utils";
import React from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction, Img, staticFile } from "remotion";
import { z } from "zod";
import {
  AnimatedBackground,
  CornerIcon,
  SentenceStack,
  Signature,
  useSentences,
} from "../PresenterPiP";

const NAVY_LIGHT = "#122C4A";
const WHITE = "#FFFFFF";

// Variante du template presentateur-anime SANS avatar animé : fond animé, texte
// kinétique centré, icône contextuelle, signature + VOIX off — et une PHOTO DE
// PROFIL statique (rond bas-droite) en guise d'identité de marque (pas de visage animé).
export const narrationAnimeeSchema = z.object({
  src: z.string(),
  photo: z.string().optional(),
});

export const calculateNarrationAnimeeMetadata: CalculateMetadataFunction<
  z.infer<typeof narrationAnimeeSchema>
> = async ({ props }) => {
  const fps = 30;
  const durationInSeconds = await getAudioDurationInSeconds(props.src);
  return { fps, durationInFrames: Math.max(1, Math.floor(durationInSeconds * fps)) };
};

const PHOTO = 210; // diamètre du rond photo — discret (source basse résolution)

export const NarrationAnimee: React.FC<{ src: string; photo?: string }> = ({
  src, photo = staticFile("brand-photo-crop.png"),
}) => {
  const sentences = useSentences(src);

  return (
    <AbsoluteFill>
      <AnimatedBackground />
      {/* Espace réservé en bas pour la photo discrète. */}
      <SentenceStack sentences={sentences} bottomInset={340} />
      <CornerIcon sentences={sentences} />
      <Audio src={src} />

      {/* Photo de profil statique, rond bas-droite. Cadrage zoomé sur le visage
          (la source est une photo de conférence, pas un portrait serré). */}
      <div style={{
        position: "absolute", right: 52, bottom: 88,
        width: PHOTO, height: PHOTO, borderRadius: "50%", overflow: "hidden",
        border: `4px solid ${WHITE}D9`, boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
        background: NAVY_LIGHT,
      }}>
        <Img
          src={photo}
          style={{
            width: "100%", height: "100%",
            objectFit: "cover", objectPosition: "center",
          }}
        />
      </div>

      <Signature />
    </AbsoluteFill>
  );
};
