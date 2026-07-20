import { Composition, staticFile } from "remotion";
import {
  CaptionedVideo,
  calculateCaptionedVideoMetadata,
  captionedVideoSchema,
} from "./CaptionedVideo";
import {
  PresenterPiP,
  calculatePresenterPiPMetadata,
  presenterPiPSchema,
} from "./PresenterPiP";
import {
  NarrationAnimee,
  calculateNarrationAnimeeMetadata,
  narrationAnimeeSchema,
} from "./NarrationAnimee";
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
import {
  PresenterTemplate,
  calculatePresenterTemplateMetadata,
  presenterTemplateSchema,
} from "./PresenterTemplate";
import {
  AvatarPhases,
  calculateAvatarPhasesMetadata,
  avatarPhasesSchema,
} from "./AvatarPhases";

// Each <Composition> is an entry in the sidebar!

export const RemotionRoot: React.FC = () => {
  return (
    <>
    <Composition
      id="CaptionedVideo"
      component={CaptionedVideo}
      calculateMetadata={calculateCaptionedVideoMetadata}
      schema={captionedVideoSchema}
      width={1080}
      height={1920}
      defaultProps={{
        // Convention pipeline : la vidéo à sous-titrer est copiée en public/input.mp4
        // (+ input.json généré par sub.mjs) avant le rendu.
        src: staticFile("input.mp4"),
      }}
    />
    <Composition
      id="PresenterPiP"
      component={PresenterPiP}
      calculateMetadata={calculatePresenterPiPMetadata}
      schema={presenterPiPSchema}
      width={1080}
      height={1920}
      defaultProps={{
        src: staticFile("input.mp4"),
      }}
    />
    <Composition
      id="NarrationAnimee"
      component={NarrationAnimee}
      calculateMetadata={calculateNarrationAnimeeMetadata}
      schema={narrationAnimeeSchema}
      width={1080}
      height={1920}
      defaultProps={{
        // Convention : la voix off est copiée en public/narration.mp3
        // (+ narration.json généré par sub.mjs) avant le rendu.
        src: staticFile("narration.mp3"),
      }}
    />
    <Composition
      id="NarrationIllustree"
      component={NarrationIllustree}
      calculateMetadata={calculateNarrationIllustreeMetadata}
      schema={narrationIllustreeSchema}
      width={1080}
      height={1920}
      defaultProps={{
        // Convention : voix en public/narration.mp3 (+ narration.json).
        // `ideas` = découpage sémantique de la narration → média par idée
        // (illustration Ideogram public/illus/idea-N.png ou clip fourni).
        src: staticFile("narration.mp3"),
        // Clips fal Kling (image-to-video). clipSec = durée réelle du clip → étiré
        // sur la durée de l'idée. Fallback still .png en repli si un clip manque.
        ideas: [
          { start: 0.0, src: "illus/idea-1.mp4", kind: "video", clipSec: 5 },
          { start: 16.76, src: "illus/idea-2.mp4", kind: "video", clipSec: 10 },
          { start: 31.76, src: "illus/idea-3.mp4", kind: "video", clipSec: 5 },
          { start: 41.4, src: "illus/idea-4.mp4", kind: "video", clipSec: 5 },
          { start: 49.84, src: "illus/idea-5.mp4", kind: "video", clipSec: 5 },
          { start: 56.16, src: "illus/idea-6.mp4", kind: "video", clipSec: 10 },
          { start: 72.24, src: "illus/idea-7.mp4", kind: "video", clipSec: 10 },
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
    <Composition
      id="PresenterTemplate"
      component={PresenterTemplate}
      calculateMetadata={calculatePresenterTemplateMetadata}
      schema={presenterTemplateSchema}
      width={1080}
      height={1920}
      defaultProps={{
        // NOUVEAU workflow overlay : avatar HeyGen fourni par Abdelilah, centre transparent.
        // Rendu alpha : npx remotion render PresenterTemplate out/overlay.mov \
        //   --codec=prores --prores-profile=4444 --props='{"avatar":"verrou-avatar.mp4"}'
        avatar: "idee2.mp4",
      }}
    />
    <Composition
      id="AvatarPhases"
      component={AvatarPhases}
      calculateMetadata={calculateAvatarPhasesMetadata}
      schema={avatarPhasesSchema}
      width={1080}
      height={1920}
      defaultProps={{
        // TEMPLATE multi-phases paramétrable — 1 fichier de props par vidéo.
        // Rendu : npx remotion render AvatarPhases out/x.mp4 --props=<video>-props.json
        avatar: "metiers-avatar.mp4",
        pastille: "PRODUIRE NE SUFFIT PLUS",
        titre: "L'IA produit à votre place",
        phases: { introSplit: 6.5, introFin: 17.5, zoomDebut: 45.0, zoomFin: 64.6 },
        cropSource: { x0: 712, largeur: 495 },
      }}
    />
    </>
  );
};
