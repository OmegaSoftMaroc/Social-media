import { getAudioDurationInSeconds } from "@remotion/media-utils";
import React, { useCallback, useEffect, useState } from "react";
import {
  AbsoluteFill,
  Audio,
  CalculateMetadataFunction,
  cancelRender,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useDelayRender,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { loadFont, TheBoldFont } from "../load-font";

// Motion-graphics designées « MotionBrief » — variante SANS avatar, un cran au-dessus
// de narration-illustree : scènes designées (notice navigateur, gros chiffres, courbes,
// cartes stratégie) calées sur la voix off. Fond navy, teal/accent, zéro musique.
const NAVY = "#0B1E33";
const NAVY_LIGHT = "#122C4A";
const TEAL = "#2AA7A0";
const ACCENT = "#FFB454";
const RED = "#E5544B";
const WHITE = "#FFFFFF";
const SANS = 'Inter, "Segoe UI", system-ui, -apple-system, sans-serif';
const FPS = 30;

export const motionBriefSchema = z.object({ src: z.string() });

export const calculateMotionBriefMetadata: CalculateMetadataFunction<
  z.infer<typeof motionBriefSchema>
> = async ({ props }) => {
  const durationInSeconds = await getAudioDurationInSeconds(props.src);
  return { fps: FPS, durationInFrames: Math.max(1, Math.floor(durationInSeconds * FPS)) };
};

const useFont = () => {
  const { delayRender, continueRender } = useDelayRender();
  const [h] = useState(() => delayRender());
  const go = useCallback(async () => {
    try { await loadFont(); continueRender(h); } catch (e) { cancelRender(e); }
  }, [continueRender, h]);
  useEffect(() => { go(); }, [go]);
};

// Logo de marque réel (SVG simple-icons chargé + teinté à la couleur de marque).
const BRAND: Record<string, string> = {
  claude: "#D97757", anthropic: "#D97757", openai: "#FFFFFF", deepseek: "#4D6BFE",
  mistralai: "#FA520F", qwen: "#615CED", alibabadotcom: "#FF6A00", github: "#FFFFFF",
  huggingface: "#FFD21E", uber: "#FFFFFF",
};
const Logo: React.FC<{ name: string; size: number; color?: string }> = ({ name, size, color }) => {
  const { delayRender, continueRender } = useDelayRender();
  const [h] = useState(() => delayRender());
  const [ds, setDs] = useState<string[] | null>(null);
  useEffect(() => {
    (async () => {
      try {
        const t = await (await fetch(staticFile(`logos/${name}.svg`))).text();
        setDs([...t.matchAll(/<path[^>]*\sd="([^"]+)"/g)].map((m) => m[1]));
        continueRender(h);
      } catch (e) { cancelRender(e); }
    })();
  }, [continueRender, h, name]);
  if (!ds) return null;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      {ds.map((d, i) => <path key={i} d={d} fill={color || BRAND[name] || WHITE} />)}
    </svg>
  );
};

// ---- fond animé (grille + halos dérivants) --------------------------------
const Bg: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: `radial-gradient(120% 90% at 50% 0%, ${NAVY_LIGHT}, ${NAVY})` }}>
      <AbsoluteFill style={{
        backgroundImage:
          `linear-gradient(${TEAL}14 1px, transparent 1px), linear-gradient(90deg, ${TEAL}14 1px, transparent 1px)`,
        backgroundSize: "80px 80px",
        maskImage: "radial-gradient(80% 70% at 50% 40%, #000 40%, transparent 100%)",
        transform: `translateY(${(f * 0.3) % 80}px)`,
      }} />
      <div style={{
        position: "absolute", width: 700, height: 700, borderRadius: "50%",
        left: -220, top: 220, background: `radial-gradient(circle, ${TEAL}22, transparent 70%)`,
        transform: `translateX(${18 * Math.sin(f / 50)}px)`,
      }} />
      <div style={{
        position: "absolute", width: 520, height: 520, borderRadius: "50%",
        right: -160, bottom: 240, background: `radial-gradient(circle, ${ACCENT}18, transparent 70%)`,
        transform: `translateY(${18 * Math.cos(f / 60)}px)`,
      }} />
    </AbsoluteFill>
  );
};

// helpers d'animation --------------------------------------------------------
const useIn = (delay = 0, dur = 14) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: Math.max(f - delay, 0), fps, config: { damping: 200 }, durationInFrames: dur });
};
const rise = (p: number, px = 40): React.CSSProperties => ({
  opacity: p, transform: `translateY(${(1 - p) * px}px)`,
});

const Kicker: React.FC<{ children: React.ReactNode; delay?: number }> = ({ children, delay = 0 }) => {
  const p = useIn(delay);
  return (
    <div style={{
      ...rise(p, 24), fontFamily: SANS, fontWeight: 700, color: TEAL,
      fontSize: 30, letterSpacing: 6, textTransform: "uppercase",
    }}>{children}</div>
  );
};

// signature discrète (le plein 3-lignes ira sur la carte finale de la vidéo complète)
const Wordmark: React.FC = () => (
  <div style={{
    position: "absolute", left: 60, bottom: 56, fontFamily: SANS, fontWeight: 700,
    color: `${WHITE}CC`, fontSize: 26, letterSpacing: 1,
  }}>
    Abdelilah Kahaji
    <span style={{ color: `${WHITE}66`, fontWeight: 500, fontSize: 20 }}> · Expert SI & IA</span>
  </div>
);

// ---- Scène 1 : HOOK --------------------------------------------------------
const SceneHook: React.FC = () => {
  const p1 = useIn(4), p2 = useIn(16), p3 = useIn(34);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 80, textAlign: "center" }}>
      <Kicker delay={2}>Cette semaine · en direct</Kicker>
      <div style={{ ...rise(p1), fontFamily: TheBoldFont, color: WHITE, fontSize: 118, lineHeight: 1.02, marginTop: 40 }}>
        ÇA SE JOUE
      </div>
      <div style={{ ...rise(p2), fontFamily: TheBoldFont, fontSize: 118, lineHeight: 1.02, color: ACCENT }}>
        EN DIRECT
      </div>
      <div style={{ ...rise(p3), fontFamily: SANS, fontWeight: 600, color: `${WHITE}BB`, fontSize: 40, marginTop: 44, maxWidth: 800 }}>
        et presque personne ne l'a vu
      </div>
    </AbsoluteFill>
  );
};

// ---- Scène 2 : NOTICE navigateur + timeline 7/12/19 ------------------------
const BrowserNotice: React.FC = () => {
  const p = useIn(4, 18);
  return (
    <div style={{
      ...rise(p, 60), width: 900, borderRadius: 20, overflow: "hidden",
      boxShadow: "0 30px 80px rgba(0,0,0,.5)", background: "#fff", fontFamily: SANS,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "16px 20px", background: "#F3F0EB", borderBottom: "1px solid #E2DCD2" }}>
        <span style={{ width: 13, height: 13, borderRadius: "50%", background: "#F7655A" }} />
        <span style={{ width: 13, height: 13, borderRadius: "50%", background: "#F7BE4F" }} />
        <span style={{ width: 13, height: 13, borderRadius: "50%", background: "#5FC466" }} />
        <div style={{ flex: 1, marginLeft: 8, background: "#fff", border: "1px solid #E2DCD2", borderRadius: 9, padding: "8px 16px", fontSize: 17, color: "#6b6257" }}>
          🔒 support.claude.com<span style={{ color: "#141414" }}>/…/claude-fable-5-promotional-access</span>
        </div>
      </div>
      <div style={{ padding: "34px 40px 40px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 11, marginBottom: 18 }}>
          <Logo name="claude" size={26} color="#D97757" />
          <span style={{ fontWeight: 700, color: "#141414", fontSize: 18 }}>Claude</span>
          <span style={{ color: "#9a9084", fontSize: 18 }}>· Help Center</span>
        </div>
        <div style={{ fontWeight: 700, color: "#141414", fontSize: 40, lineHeight: 1.1, letterSpacing: -0.5 }}>
          Claude Fable 5 promotional access
        </div>
        <div style={{ color: "#9a9084", fontSize: 17, marginTop: 10 }}>Updated today</div>
        <div style={{ marginTop: 24, background: "#FBF3E9", borderLeft: "5px solid #D97757", borderRadius: 10, padding: "20px 24px" }}>
          <div style={{ color: "#B8632F", fontWeight: 700, fontSize: 15, letterSpacing: 0.6, textTransform: "uppercase", marginBottom: 8 }}>Note</div>
          <div style={{ color: "#242424", fontSize: 22, lineHeight: 1.45 }}>
            We've <b>extended this promotion through July&nbsp;19, 2026</b> — after that, Fable&nbsp;5 is no longer included; you keep using it through <b>usage credits</b>.
          </div>
        </div>
      </div>
    </div>
  );
};

const Timeline: React.FC = () => {
  const dates = [
    { d: "7 JUIL.", delay: 150 },
    { d: "12 JUIL.", delay: 195 },
    { d: "19 JUIL.", delay: 240 },
  ];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0, marginTop: 54 }}>
      {dates.map((x, i) => {
        const p = useIn(x.delay, 12);
        return (
          <React.Fragment key={i}>
            {i > 0 && <div style={{ width: 70, height: 3, background: `${TEAL}`, opacity: p, transformOrigin: "left", transform: `scaleX(${p})` }} />}
            <div style={{
              ...rise(p, 20), fontFamily: TheBoldFont, fontSize: 34,
              color: i === 2 ? ACCENT : WHITE, border: `2px solid ${i === 2 ? ACCENT : TEAL}`,
              borderRadius: 14, padding: "12px 22px", background: `${NAVY}CC`,
            }}>{x.d}</div>
          </React.Fragment>
        );
      })}
    </div>
  );
};

const Stamp: React.FC<{ text: string; delay: number; color?: string }> = ({ text, delay, color = ACCENT }) => {
  const p = useIn(delay, 10);
  const rot = interpolate(p, [0, 1], [-9, -6]);
  return (
    <div style={{
      opacity: p, transform: `scale(${0.8 + 0.2 * p}) rotate(${rot}deg)`,
      fontFamily: TheBoldFont, fontSize: 46, color, border: `4px solid ${color}`,
      borderRadius: 14, padding: "14px 30px", letterSpacing: 2, marginTop: 46,
      boxShadow: `0 0 40px ${color}44`,
    }}>{text}</div>
  );
};

const SceneNotice: React.FC = () => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 60 }}>
    <BrowserNotice />
    <Timeline />
    <Stamp text="SURSIS, PAS RENONCEMENT" delay={597} />
  </AbsoluteFill>
);

// ---- Scène 3 : GROS CHIFFRES 10 / 50 --------------------------------------
const BigPrice: React.FC<{ value: string; label: string; delay: number }> = ({ value, label, delay }) => {
  const p = useIn(delay, 12);
  return (
    <div style={{ ...rise(p, 30), textAlign: "center" }}>
      <div style={{ fontFamily: TheBoldFont, fontSize: 168, color: ACCENT, lineHeight: 1 }}>{value}</div>
      <div style={{ fontFamily: SANS, fontWeight: 700, color: `${WHITE}AA`, fontSize: 28, letterSpacing: 2, textTransform: "uppercase" }}>{label}</div>
    </div>
  );
};
const SceneStat: React.FC = () => {
  const p = useIn(201);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 70, textAlign: "center" }}>
      <Kicker delay={2}>Le jour où la fenêtre se referme</Kicker>
      <div style={{ display: "flex", gap: 90, marginTop: 50, alignItems: "flex-start" }}>
        <BigPrice value="$10" label="/ M entrée" delay={87} />
        <div style={{ fontFamily: TheBoldFont, fontSize: 120, color: `${WHITE}44`, marginTop: 20 }}>/</div>
        <BigPrice value="$50" label="/ M sortie" delay={150} />
      </div>
      <div style={{ ...rise(p, 26), marginTop: 60, fontFamily: SANS, fontWeight: 700, fontSize: 42, color: WHITE }}>
        Inclus aujourd'hui <span style={{ color: RED }}>→</span> facturé demain
      </div>
    </AbsoluteFill>
  );
};

// ---- Scène 4 : DOUBLE COURBE ----------------------------------------------
const LogoBadge: React.FC<{ name: string; delay: number }> = ({ name, delay }) => {
  const p = useIn(delay, 12);
  return (
    <div style={{
      opacity: p, transform: `scale(${0.5 + 0.5 * p})`,
      width: 62, height: 62, borderRadius: 14, background: `${WHITE}12`, border: `1px solid ${WHITE}22`,
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <Logo name={name} size={38} />
    </div>
  );
};

const SceneCurves: React.FC = () => {
  const f = useCurrentFrame();
  const draw = interpolate(f, [20, 170], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const W = 940, H = 540;
  const west = `M 0 ${H * 0.72} C ${W * 0.4} ${H * 0.7}, ${W * 0.6} ${H * 0.3}, ${W} ${H * 0.12}`;
  const china = `M 0 ${H * 0.3} C ${W * 0.35} ${H * 0.34}, ${W * 0.6} ${H * 0.8}, ${W} ${H * 0.9}`;
  const pk = useIn(4);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 60 }}>
      <div style={{ ...rise(pk, 20), fontFamily: TheBoldFont, fontSize: 58, color: WHITE, textAlign: "center", marginBottom: 26 }}>
        DEUX COURBES OPPOSÉES
      </div>
      <div style={{ position: "relative", width: W, height: H }}>
        <svg width={W} height={H} style={{ overflow: "visible" }}>
          <line x1="0" y1={H} x2={W} y2={H} stroke={`${WHITE}33`} strokeWidth="2" />
          <path d={west} fill="none" stroke={RED} strokeWidth="7" strokeLinecap="round"
            strokeDasharray={2000} strokeDashoffset={2000 * (1 - draw)} />
          <path d={china} fill="none" stroke={TEAL} strokeWidth="7" strokeLinecap="round"
            strokeDasharray={2000} strokeDashoffset={2000 * (1 - draw)} />
        </svg>
        {/* Occident (prix ↑) : logos près du sommet de la courbe rouge */}
        <div style={{ position: "absolute", right: 0, top: -6, textAlign: "right" }}>
          <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 27, color: RED, marginBottom: 10 }}>PRIX OCCIDENTAL ↑</div>
          <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
            <LogoBadge name="anthropic" delay={30} />
            <LogoBadge name="openai" delay={48} />
          </div>
        </div>
        {/* Chine (coût ↓) : logos près du bas de la courbe teal */}
        <div style={{ position: "absolute", right: 0, bottom: -12, textAlign: "right" }}>
          <div style={{ display: "flex", gap: 12, justifyContent: "flex-end", marginBottom: 10 }}>
            <LogoBadge name="deepseek" delay={180} />
            <LogoBadge name="qwen" delay={205} />
          </div>
          <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 27, color: TEAL }}>COÛT CHINOIS ↓</div>
        </div>
      </div>
      <div style={{ display: "flex", gap: 20, marginTop: 40 }}>
        <div style={{ ...rise(useIn(180, 12), 20), display: "flex", alignItems: "center", gap: 12, fontFamily: SANS, fontWeight: 700, fontSize: 27, color: WHITE, border: `2px solid ${TEAL}66`, background: `${TEAL}1A`, borderRadius: 40, padding: "12px 24px" }}>
          <Logo name="deepseek" size={30} color="#7C93FF" /> DeepSeek · quelques ¢ / M
        </div>
        <div style={{ ...rise(useIn(288, 12), 20), fontFamily: SANS, fontWeight: 700, fontSize: 27, color: WHITE, border: `2px solid ${TEAL}66`, background: `${TEAL}1A`, borderRadius: 40, padding: "12px 24px" }}>
          GLM 5.2 · MIT · poids ouverts
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---- Scène 5 : TAMPON rouge -----------------------------------------------
const ScenePivot: React.FC = () => {
  const p = useIn(6);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 80, textAlign: "center" }}>
      <div style={{ ...rise(p, 20), fontFamily: SANS, fontWeight: 700, fontSize: 40, color: `${WHITE}BB` }}>
        Face à cette instabilité,
      </div>
      <Stamp text="LA DÉFENSE EST SUICIDAIRE" delay={20} color={RED} />
    </AbsoluteFill>
  );
};

// ---- CARTE STRATÉGIE (générique, réutilisée pour les 5 mouvements) --------
const StrategyScene: React.FC<{ num: number; titleLines: string[]; points: string[] }> = ({
  num, titleLines, points,
}) => {
  const badge = useIn(4, 14);
  const title = useIn(14);
  return (
    <AbsoluteFill style={{ justifyContent: "center", padding: 90 }}>
      <div style={{ ...rise(useIn(0), 10), fontFamily: SANS, fontWeight: 700, color: TEAL, fontSize: 28, letterSpacing: 6, marginBottom: 26 }}>
        MOUVEMENT {num} / 5
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
        <div style={{
          opacity: badge, transform: `scale(${0.6 + 0.4 * badge})`,
          fontFamily: TheBoldFont, fontSize: 96, color: NAVY, background: ACCENT,
          width: 150, height: 150, borderRadius: 28, display: "flex", alignItems: "center", justifyContent: "center",
        }}>{num}</div>
        <div style={{ ...rise(title, 30), fontFamily: TheBoldFont, fontSize: 70, color: WHITE, lineHeight: 1.05 }}>
          {titleLines.map((l, i) => <React.Fragment key={i}>{l}{i < titleLines.length - 1 && <br />}</React.Fragment>)}
        </div>
      </div>
      <div style={{ marginTop: 56, display: "flex", flexDirection: "column", gap: 24 }}>
        {points.map((t, i) => {
          const p = useIn(40 + i * 55, 12);
          return (
            <div key={i} style={{ ...rise(p, 30), display: "flex", alignItems: "flex-start", gap: 20 }}>
              <div style={{ width: 16, height: 16, borderRadius: 4, background: TEAL, marginTop: 12 }} />
              <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 38, color: `${WHITE}E6`, maxWidth: 820 }}>{t}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
const Strat1: React.FC = () => <StrategyScene num={1} titleLines={["SATURER LE", "MILIEU DE GAMME"]}
  points={["Modèles intermédiaires : coût quasi nul", "Les multiplier, les faire voter, créer des consensus", "Ne plus escalader vers la pointe par réflexe"]} />;
const Strat2: React.FC = () => <StrategyScene num={2} titleLines={["VAMPIRISER", "L'EXPERTISE US"]}
  points={["La pointe génère et valide le cadrage", "On verrouille la logique dans son harness", "L'exécution aux petits modèles ouverts, locaux"]} />;
const Strat3: React.FC = () => <StrategyScene num={3} titleLines={["RESTER", "LIQUIDE"]}
  points={["Fuir les engagements de capacité long terme", "La souplesse coûte, mais protège", "Ne pas s'enchaîner à une archi qui peut s'effondrer"]} />;
const Strat4: React.FC = () => <StrategyScene num={4} titleLines={["CARTOGRAPHIER", "SES TÂCHES"]}
  points={["Centre : le quotidien → ouvert chinois = pointe US, pour une fraction du prix", "Bord : rare, ambigu, fort enjeu → la pointe mérite son tarif", "Presque personne n'a mesuré son partage → on surpaie"]} />;
const Strat5: React.FC = () => <StrategyScene num={5} titleLines={["RECRUTER", "L'EFFICIENCE"]}
  points={["Faire du haut niveau avec des modèles médiocres", "Routage, évaluation systémique, spécialisation", "Un architecte du harness vaut 100× un « prompteur »"]} />;

// ---- Scène : PREUVES « fin des subventions » (vrais logos) ----------------
const ProofCard: React.FC<{ logo: string; title: string; cap: string; delay: number }> = ({ logo, title, cap, delay }) => {
  const p = useIn(delay, 14);
  return (
    <div style={{
      ...rise(p, 40), display: "flex", alignItems: "center", gap: 26, width: 860,
      background: `${NAVY_LIGHT}CC`, border: `1px solid ${WHITE}1A`, borderRadius: 20, padding: "24px 32px",
    }}>
      <div style={{ width: 86, height: 86, borderRadius: 18, background: `${WHITE}10`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <Logo name={logo} size={50} color="#FFFFFF" />
      </div>
      <div>
        <div style={{ fontFamily: TheBoldFont, fontSize: 40, color: WHITE }}>{title}</div>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 27, color: `${WHITE}99`, marginTop: 4 }}>{cap}</div>
      </div>
    </div>
  );
};
const SubsidyProof: React.FC = () => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 70, gap: 24 }}>
    <div style={{ ...rise(useIn(2), 20), fontFamily: TheBoldFont, fontSize: 56, color: WHITE, textAlign: "center", marginBottom: 16 }}>
      LA FIN DES SUBVENTIONS
    </div>
    <ProofCard logo="github" title="GitHub Copilot" cap="bascule à la facturation au token" delay={54} />
    <ProofCard logo="uber" title="Uber" cap="budget IA 2026 cramé dès avril" delay={144} />
    <ProofCard logo="openai" title="OpenAI" cap="la fin annoncée du « 20 $ illimité »" delay={339} />
  </AbsoluteFill>
);

// ---- Scène : NUANCE (recul PME) -------------------------------------------
const NuanceRow: React.FC<{ big: string; sub: string; ok: boolean; delay: number }> = ({ big, sub, ok, delay }) => {
  const p = useIn(delay, 14);
  const c = ok ? TEAL : RED;
  return (
    <div style={{ ...rise(p, 40), display: "flex", alignItems: "center", gap: 26, width: 880, background: `${NAVY_LIGHT}AA`, border: `2px solid ${c}55`, borderRadius: 20, padding: "26px 34px" }}>
      <div style={{ fontFamily: TheBoldFont, fontSize: 52, color: c }}>{ok ? "✓" : "✕"}</div>
      <div>
        <div style={{ fontFamily: TheBoldFont, fontSize: 42, color: WHITE }}>{big}</div>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 28, color: `${WHITE}AA`, marginTop: 2 }}>{sub}</div>
      </div>
    </div>
  );
};
const SceneNuance: React.FC = () => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 70, gap: 26 }}>
    <div style={{ textAlign: "center", marginBottom: 10 }}><Kicker delay={2}>Gardons un recul</Kicker></div>
    <div style={{ ...rise(useIn(10), 20), fontFamily: TheBoldFont, fontSize: 50, color: WHITE, textAlign: "center", marginBottom: 20 }}>
      L'AUTO-HÉBERGEMENT, POUR QUI ?
    </div>
    <NuanceRow big="Entreprise à très gros volume" sub="rentable — le calcul tient" ok delay={70} />
    <NuanceRow big="Particulier · petite · moyenne entreprise" sub="encore théorique — ce qui protège les géants du cloud" ok={false} delay={200} />
  </AbsoluteFill>
);

// ---- Scène : RÉCAP (le verrou s'est déplacé) ------------------------------
const SceneRecap: React.FC = () => {
  const l1 = useIn(10), l2 = useIn(130), big = useIn(490), sub = useIn(560);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 80, textAlign: "center" }}>
      <div style={{ ...rise(l1, 24), fontFamily: SANS, fontWeight: 600, fontSize: 38, color: `${WHITE}AA`, maxWidth: 900 }}>
        Washington met son haut de gamme sous cloche.
      </div>
      <div style={{ ...rise(l2, 24), fontFamily: SANS, fontWeight: 600, fontSize: 38, color: `${WHITE}AA`, marginTop: 18, maxWidth: 900 }}>
        La Chine sature le quotidien avec des modèles bradés.
      </div>
      <div style={{ ...rise(big, 34), fontFamily: TheBoldFont, fontSize: 92, color: ACCENT, marginTop: 54, lineHeight: 1.05 }}>
        LE VERROU S'EST<br />DÉPLACÉ
      </div>
      <div style={{ ...rise(sub, 24), fontFamily: SANS, fontWeight: 700, fontSize: 40, color: WHITE, marginTop: 34, maxWidth: 940 }}>
        du modèle → au <span style={{ color: TEAL }}>harness d'orchestration</span>, où ils capturent votre contexte.
      </div>
    </AbsoluteFill>
  );
};

// ---- Scène : EUROPE / Mistral ---------------------------------------------
const SceneEurope: React.FC = () => {
  const head = useIn(6, 16), punch = useIn(550);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 80, textAlign: "center" }}>
      <div style={{ ...rise(head, 30), display: "flex", flexDirection: "column", alignItems: "center", gap: 18 }}>
        <Logo name="mistralai" size={130} color="#FA520F" />
        <div style={{ fontFamily: TheBoldFont, fontSize: 60, color: WHITE }}>ET L'EUROPE ?</div>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 34, color: `${WHITE}AA`, maxWidth: 880 }}>
          Mistral coche les cases : ouvert (Apache), hébergeable, données en UE. Un vrai atout de souveraineté.
        </div>
      </div>
      <div style={{ ...rise(punch, 30), marginTop: 46 }}>
        <div style={{ fontFamily: TheBoldFont, fontSize: 52, color: ACCENT }}>La rentabilité a un passeport chinois</div>
        <Stamp text="PERDRE AVEC LES HONNEURS" delay={760} color={RED} />
      </div>
    </AbsoluteFill>
  );
};

// ---- Scène : AVERTISSEMENT (l'ouverture est temporaire) -------------------
const SceneWarning: React.FC = () => {
  const l1 = useIn(100), big = useIn(650), l3 = useIn(930);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 80, textAlign: "center" }}>
      <div style={{ ...rise(l1, 24), fontFamily: SANS, fontWeight: 600, fontSize: 38, color: `${WHITE}AA`, maxWidth: 940 }}>
        Si la Chine publie ses poids, c'est une stratégie d'État — <span style={{ color: RED }}>une arme industrielle</span>.
      </div>
      <div style={{ ...rise(big, 34), fontFamily: TheBoldFont, fontSize: 108, color: ACCENT, marginTop: 44 }}>
        6 MOIS À VIVRE ?
      </div>
      <div style={{ ...rise(l3, 30), display: "flex", alignItems: "center", gap: 18, marginTop: 44, fontFamily: SANS, fontWeight: 700, fontSize: 40, color: WHITE }}>
        <Logo name="deepseek" size={44} color="#7C93FF" />
        Le prochain DeepSeek peut sortir <span style={{ color: RED }}>fermé</span> 🔒
      </div>
    </AbsoluteFill>
  );
};

// ---- Scène : CHUTE + signature 3 lignes -----------------------------------
const SceneClose: React.FC = () => {
  const l1 = useIn(10), big = useIn(430), sub = useIn(640), sig = useIn(720);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 80, textAlign: "center" }}>
      <div style={{ ...rise(l1, 24), fontFamily: SANS, fontWeight: 600, fontSize: 36, color: `${WHITE}AA`, maxWidth: 900 }}>
        Le modèle téléchargé reste à vous — mais ce n'est qu'une photographie. Coupez le robinet, il vieillit.
      </div>
      {/* fallback SANS gras : la police display (theboldfont) n'a pas le glyphe « È » de MODÈLE */}
      <div style={{ ...rise(big, 34), fontFamily: `${TheBoldFont}, ${SANS}`, fontWeight: 800, fontSize: 78, color: WHITE, marginTop: 46, lineHeight: 1.06 }}>
        LE VERROU N'A JAMAIS<br />ÉTÉ LE MODÈLE
      </div>
      <div style={{ ...rise(sub, 24), fontFamily: SANS, fontWeight: 700, fontSize: 42, color: ACCENT, marginTop: 26 }}>
        C'est ce que vous construisez autour.
      </div>
      <div style={{ ...rise(sig, 24), marginTop: 64, fontFamily: TheBoldFont, color: `${WHITE}F0`, fontSize: 40 }}>
        Abdelilah Kahaji
        <div style={{ marginTop: 10, fontFamily: SANS, fontWeight: 600, fontSize: 24, color: `${WHITE}AA`, lineHeight: 1.5 }}>
          Enseignant-Chercheur
          <br />
          Expert en Systèmes d'Information &amp; Intelligence Artificielle
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---- assemblage : scènes calées sur les timings de la voix ----------------
const SC = (s: number) => Math.round(s * FPS);
const SCENES: { c: React.FC; from: number; to: number }[] = [
  { c: SceneHook, from: 0.0, to: 3.88 },
  { c: SceneNotice, from: 3.88, to: 30.84 },
  { c: SceneStat, from: 30.84, to: 42.60 },
  { c: SubsidyProof, from: 42.60, to: 65.80 },
  { c: SceneCurves, from: 65.80, to: 99.80 },
  { c: SceneNuance, from: 99.80, to: 116.76 },
  { c: ScenePivot, from: 116.76, to: 132.24 },
  { c: Strat1, from: 132.24, to: 150.68 },
  { c: Strat2, from: 150.68, to: 171.04 },
  { c: Strat3, from: 171.04, to: 188.44 },
  { c: Strat4, from: 188.44, to: 234.24 },
  { c: Strat5, from: 234.24, to: 256.25 },
  { c: SceneRecap, from: 256.25, to: 288.40 },
  { c: SceneEurope, from: 288.40, to: 317.04 },
  { c: SceneWarning, from: 317.04, to: 355.00 },
  { c: SceneClose, from: 355.00, to: 381.5 },
].map((x) => ({ c: x.c, from: SC(x.from), to: SC(x.to) }));

export const MotionBrief: React.FC<{ src: string }> = ({ src }) => {
  useFont();
  return (
    <AbsoluteFill style={{ background: NAVY }}>
      <Bg />
      {SCENES.map((s, i) => (
        <Sequence key={i} from={s.from} durationInFrames={s.to - s.from} layout="none">
          <AbsoluteFill>{React.createElement(s.c)}</AbsoluteFill>
        </Sequence>
      ))}
      {/* Wordmark discret partout SAUF la chute (qui porte la signature 3 lignes) */}
      <Sequence from={0} durationInFrames={SC(355.0)} layout="none"><Wordmark /></Sequence>
      <Audio src={src} />
    </AbsoluteFill>
  );
};
