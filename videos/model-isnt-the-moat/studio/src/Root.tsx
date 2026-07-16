import { Composition, staticFile } from "remotion";
import {
  NarrationIllustree,
  calculateNarrationIllustreeMetadata,
  narrationIllustreeSchema,
} from "./NarrationIllustree";
import {
  MotionBrief,
  calculateMotionBriefMetadata,
  motionBriefSchema,
} from "./MotionBrief";

// Projet Remotion AUTONOME « model-isnt-the-moat » — uniquement les compositions
// utilisées par cette vidéo (extrait de video-studio partagé).
//
// Studio interactif :  npm run dev            (puis ouvrir NarrationIllustree)
// Rendre un short    :  npx remotion render NarrationIllustree out/short-fusion.mp4 --props=props/short-fusion-props.json
//                       (idem avec props/short-A-props.json, props/short-B-props.json)

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="NarrationIllustree"
        component={NarrationIllustree}
        calculateMetadata={calculateNarrationIllustreeMetadata}
        schema={narrationIllustreeSchema}
        width={1080}
        height={1920}
        defaultProps={{
          // Défaut = short fusionné (dernier livrable). Les 3 shorts sont dans props/.
          // src brut : NarrationIllustree.resolveSrc() le résout via staticFile au runtime.
          src: "short-fusion-voice.mp3",
          ideas: [
            { start: 0.0, src: "illus/fusion-1-robinet.mp4", kind: "video", clipSec: 6 },
            { start: 7.6, src: "illus/fusion-2-compteur.mp4", kind: "video", clipSec: 6 },
            { start: 25.0, src: "illus/fusion-3-effondre.mp4", kind: "video", clipSec: 6 },
            { start: 39.7, src: "illus/fusion-4-courbes.mp4", kind: "video", clipSec: 6 },
          ],
        }}
      />
      <Composition
        id="MotionBrief"
        component={MotionBrief}
        calculateMetadata={calculateMotionBriefMetadata}
        schema={motionBriefSchema}
        width={1080}
        height={1920}
        defaultProps={{ src: staticFile("narration.mp3") }}
      />
    </>
  );
};
