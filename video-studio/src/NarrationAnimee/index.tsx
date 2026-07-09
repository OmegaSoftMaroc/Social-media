import { getAudioDurationInSeconds } from "@remotion/media-utils";
import React from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction } from "remotion";
import { z } from "zod";
import {
  AnimatedBackground,
  CornerIcon,
  SentenceStack,
  Signature,
  useSentences,
} from "../PresenterPiP";

// Variante « sans avatar » du template presentateur-anime : mêmes fond animé, texte
// kinétique centré, icône contextuelle et signature — MAIS pas de clone en PiP.
// Seule la voix off (Audio) accompagne le texte. Entrée : un fichier audio (voix).
export const narrationAnimeeSchema = z.object({
  src: z.string(),
});

export const calculateNarrationAnimeeMetadata: CalculateMetadataFunction<
  z.infer<typeof narrationAnimeeSchema>
> = async ({ props }) => {
  const fps = 30;
  const durationInSeconds = await getAudioDurationInSeconds(props.src);
  return { fps, durationInFrames: Math.max(1, Math.floor(durationInSeconds * fps)) };
};

export const NarrationAnimee: React.FC<{ src: string }> = ({ src }) => {
  const sentences = useSentences(src);

  return (
    <AbsoluteFill>
      <AnimatedBackground />
      {/* Sans PiP, le texte occupe davantage l'écran (bottomInset réduit). */}
      <SentenceStack sentences={sentences} bottomInset={240} />
      <CornerIcon sentences={sentences} />
      <Audio src={src} />
      <Signature />
    </AbsoluteFill>
  );
};
