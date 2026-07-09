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
    </>
  );
};
