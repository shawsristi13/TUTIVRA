"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useSession } from "@/components/SessionProvider";
import {
  planScenes,
  generateVisual,
  generateTts,
  generateAvatar,
  adaptiveAnswer,
  reexplain,
  Scene,
} from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SCENE_TYPE_COLORS: Record<string, string> = {
  introduction: "bg-blue-900/40 text-blue-300 border-blue-700/40",
  explanation: "bg-indigo-900/40 text-indigo-300 border-indigo-700/40",
  example: "bg-violet-900/40 text-violet-300 border-violet-700/40",
  demonstration: "bg-purple-900/40 text-purple-300 border-purple-700/40",
  question: "bg-orange-900/40 text-orange-300 border-orange-700/40",
  summary: "bg-teal-900/40 text-teal-300 border-teal-700/40",
};

const SCENE_TYPE_ICONS: Record<string, string> = {
  introduction: "🌟",
  explanation: "💡",
  example: "📝",
  demonstration: "🔬",
  question: "❓",
  summary: "✅",
};

type AssetStatus = "idle" | "loading" | "done" | "error";

interface SceneAssets {
  visualHtml: string;
  audioUrl: string;      // browser-accessible URL for <audio> element
  audioDiskPath: string; // absolute local path for D-ID upload
  videoUrl: string;
  visualStatus: AssetStatus;
  audioStatus: AssetStatus;
  videoStatus: AssetStatus;
  videoError: string;
}

export default function TeachPage() {
  const router = useRouter();
  const { session, update } = useSession();

  const [planLoading, setPlanLoading] = useState(false);
  const [planError, setPlanError] = useState("");

  // Current scene
  const [sceneIdx, setSceneIdx] = useState(session.currentSceneIndex || 0);
  const [assets, setAssets] = useState<Record<number, SceneAssets>>({});

  // Q&A state
  const [phase, setPhase] = useState<"teaching" | "question" | "evaluating" | "feedback" | "reexplaining">("teaching");
  const [studentAnswer, setStudentAnswer] = useState("");
  const [evalResult, setEvalResult] = useState<Record<string, unknown> | null>(null);
  const [reexplainData, setReexplainData] = useState<{
    reexplanation: string; analogy: string; visual_suggestion: string; visual_content: string; check_question: string;
  } | null>(null);
  const [reexplainVisual, setReexplainVisual] = useState("");
  const [evalError, setEvalError] = useState("");

  const scenes = session.scenes || [];
  const scene: Scene | undefined = scenes[sceneIdx];

  // ── Step 1: Plan scenes if not yet done ────────────────────
  useEffect(() => {
    if (!session.topic || !session.lessonText) { router.replace("/lesson"); return; }
    if (scenes.length > 0) return;
    runPlanScenes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runPlanScenes() {
    setPlanLoading(true);
    setPlanError("");
    try {
      const res = await planScenes(
        session.topic,
        session.lessonText,
        session.studentLevel,
        session.language,
        session.availableTimeMinutes,
        session.subjectArea,
        session.goal
      );
      update({ scenes: res.scenes, currentSceneIndex: 0 });
    } catch (e: unknown) {
      setPlanError(e instanceof Error ? e.message : String(e));
    } finally {
      setPlanLoading(false);
    }
  }

  // ── Step 2: Generate assets for current scene ───────────────
  const generateSceneAssets = useCallback(
    async (idx: number, s: Scene) => {
      if (assets[idx]) return; // already loaded or loading

      const init: SceneAssets = {
        visualHtml: "", audioUrl: "", audioDiskPath: "", videoUrl: "",
        visualStatus: "loading", audioStatus: "loading", videoStatus: "idle", videoError: "",
      };
      setAssets((prev) => ({ ...prev, [idx]: init }));

      // Visual (parallel)
      const visualPromise = s.visual_type !== "none" && s.visual_content
        ? generateVisual(s.visual_type, s.visual_content, s.on_screen_text, session.subjectArea)
            .then((v) => v.html)
            .catch(() => "")
        : Promise.resolve("");

      // TTS — capture BOTH audio_url (for <audio> playback) and audio_path (for D-ID upload)
      const ttsResult = s.narration
        ? await generateTts(s.narration, session.languageCode).catch(() => null)
        : null;
      const audioUrl = ttsResult?.audio_url ?? "";
      const audioDiskPath = ttsResult?.audio_path ?? ""; // absolute local path for D-ID upload

      const [visualHtml] = await Promise.all([visualPromise]);

      setAssets((prev) => ({
        ...prev,
        [idx]: {
          ...prev[idx],
          visualHtml,
          audioUrl,
          audioDiskPath,
          visualStatus: visualHtml ? "done" : "idle",
          audioStatus: audioUrl ? "done" : "error",
          videoStatus: "loading",
          videoError: "",
        },
      }));

      // Avatar video — pass local disk path so FastAPI uploads to D-ID (avoids localhost URL)
      if (audioDiskPath) {
        try {
          const vid = await generateAvatar(audioDiskPath);
          if (vid.status === "done" && vid.video_url) {
            setAssets((prev) => ({
              ...prev,
              [idx]: { ...prev[idx], videoUrl: vid.video_url!, videoStatus: "done" },
            }));
          } else {
            setAssets((prev) => ({
              ...prev,
              [idx]: { ...prev[idx], videoStatus: "error", videoError: vid.error ?? "Avatar unavailable" },
            }));
          }
        } catch (e: unknown) {
          setAssets((prev) => ({
            ...prev,
            [idx]: {
              ...prev[idx],
              videoStatus: "error",
              videoError: e instanceof Error ? e.message : "Avatar unavailable",
            },
          }));
        }
      } else {
        setAssets((prev) => ({ ...prev, [idx]: { ...prev[idx], videoStatus: "error", videoError: "No audio for avatar" } }));
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [assets, session.subjectArea, session.languageCode, session.topic]
  );

  useEffect(() => {
    if (scene && !assets[sceneIdx]) {
      generateSceneAssets(sceneIdx, scene);
    }
    // Preload next scene
    const next = scenes[sceneIdx + 1];
    if (next && !assets[sceneIdx + 1]) {
      generateSceneAssets(sceneIdx + 1, next);
    }
    // When scene changes reset Q&A phase
    setPhase(scene?.interaction_required ? "question" : "teaching");
    setStudentAnswer("");
    setEvalResult(null);
    setReexplainData(null);
    setReexplainVisual("");
    setEvalError("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sceneIdx, scenes]);

  // ── Submit answer ────────────────────────────────────────────
  async function handleSubmitAnswer() {
    if (!scene || !studentAnswer.trim()) return;
    setPhase("evaluating");
    setEvalError("");
    try {
      const res = await adaptiveAnswer(
        session.studentName || "Student",
        session.topic,
        scene.concept,
        scene.question,
        scene.narration, // expected answer = narration context
        studentAnswer
      );
      const evaluation = (res as { evaluation?: Record<string, unknown> }).evaluation ?? res;
      setEvalResult(evaluation);

      // Track for report
      const interaction = {
        question: scene.question,
        expectedAnswer: scene.narration,
        studentAnswer,
        evaluation,
      };
      update({
        sessionInteractions: [...(session.sessionInteractions || []), interaction],
        sessionCorrect: (session.sessionCorrect || 0) + (evaluation.correct ? 1 : 0),
        misconceptions: evaluation.misconception_detected
          ? [...(session.misconceptions || []), String(evaluation.misconception || "")]
          : session.misconceptions,
      });

      setPhase("feedback");
    } catch (e: unknown) {
      setEvalError(e instanceof Error ? e.message : String(e));
      setPhase("question");
    }
  }

  // ── Trigger re-explanation ───────────────────────────────────
  async function handleReexplain() {
    if (!scene || !evalResult) return;
    setPhase("reexplaining");
    try {
      const data = await reexplain(
        session.topic,
        scene.concept,
        String(evalResult.misconception ?? ""),
        session.studentLevel,
        session.language,
        session.materialContext
      );
      setReexplainData(data);

      // Generate visual for reexplanation
      if (data.visual_suggestion !== "none" && data.visual_content) {
        const v = await generateVisual(data.visual_suggestion, data.visual_content, "", session.subjectArea).catch(() => ({ html: "" }));
        setReexplainVisual(v.html);
      }
    } catch (e: unknown) {
      setEvalError(e instanceof Error ? e.message : String(e));
      setPhase("feedback");
    }
  }

  function handleNextScene() {
    if (sceneIdx < scenes.length - 1) {
      const nextIdx = sceneIdx + 1;
      setSceneIdx(nextIdx);
      update({ currentSceneIndex: nextIdx });
    } else {
      router.push("/assess");
    }
  }

  // ── Guard: plan not ready ────────────────────────────────────
  if (planLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
            className="text-5xl mb-6"
          >
            🎬
          </motion.div>
          <h2 className="text-2xl font-bold text-slate-200 mb-3">Preparing Your Video Lesson</h2>
          <p className="text-slate-400 text-sm">Breaking your lesson into teaching scenes…</p>
        </div>
      </div>
    );
  }

  if (planError) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="text-5xl mb-4">⚠️</div>
          <p className="text-red-400 mb-4">{planError}</p>
          <button onClick={runPlanScenes} className="px-6 py-2 bg-red-700/40 text-red-300 rounded-xl text-sm hover:bg-red-700/60 transition">Retry</button>
        </div>
      </div>
    );
  }

  if (!scene) return null;

  const sa = assets[sceneIdx];

  return (
    <div className="min-h-screen flex flex-col bg-[#090915]">

      {/* ── Top bar ── */}
      <div className="border-b border-slate-800 px-6 py-3 flex items-center gap-4">
        <div className="text-lg font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">🎓 TUTIVRA</div>
        <div className="text-sm text-slate-500">{session.topic}</div>
        <div className="ml-auto flex items-center gap-2">
          <span className={`text-xs px-2 py-1 rounded-full border ${SCENE_TYPE_COLORS[scene.scene_type] ?? "bg-slate-800 text-slate-400"}`}>
            {SCENE_TYPE_ICONS[scene.scene_type]} {scene.scene_type}
          </span>
          <span className="text-xs text-slate-500">{sceneIdx + 1} / {scenes.length}</span>
        </div>
      </div>

      {/* ── Progress bar ── */}
      <div className="h-1 bg-slate-800">
        <motion.div
          className="h-full bg-gradient-to-r from-purple-600 to-blue-600"
          animate={{ width: `${((sceneIdx + 1) / scenes.length) * 100}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      <div className="flex flex-1 overflow-hidden">

        {/* ── Left: scene timeline sidebar ── */}
        <div className="hidden lg:flex flex-col w-56 border-r border-slate-800 bg-slate-900/40 overflow-y-auto">
          {scenes.map((s, i) => (
            <button
              key={s.scene_id}
              onClick={() => { setSceneIdx(i); update({ currentSceneIndex: i }); }}
              className={`text-left px-4 py-3 border-b border-slate-800/60 transition-all ${
                i === sceneIdx
                  ? "bg-indigo-900/40 border-l-2 border-l-indigo-500"
                  : "hover:bg-slate-800/30"
              }`}
            >
              <div className="text-xs font-medium text-slate-400 mb-0.5">
                {SCENE_TYPE_ICONS[s.scene_type]} Scene {i + 1}
              </div>
              <div className="text-xs text-slate-500 truncate">{s.concept}</div>
              {s.interaction_required && (
                <div className="text-xs text-orange-400 mt-0.5">● Question</div>
              )}
            </button>
          ))}
        </div>

        {/* ── Main content ── */}
        <div className="flex-1 flex flex-col overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={sceneIdx + (phase === "reexplaining" ? "-reexplain" : "")}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -40 }}
              transition={{ duration: 0.35 }}
              className="flex-1 flex flex-col lg:flex-row gap-6 p-6"
            >
              {/* Left column: Visual */}
              <div className="lg:w-1/2 flex flex-col gap-4">
                {phase === "reexplaining" && reexplainData ? (
                  /* Re-explanation visual */
                  <div className="bg-amber-900/20 border border-amber-700/40 rounded-2xl p-5 flex-1">
                    <div className="text-xs text-amber-400 font-semibold mb-3">⚡ Alternative Explanation</div>
                    <p className="text-slate-200 leading-relaxed mb-3">{reexplainData.reexplanation}</p>
                    <p className="text-slate-400 text-sm italic border-l-2 border-amber-700 pl-3">{reexplainData.analogy}</p>
                    {reexplainVisual && (
                      <div
                        className="mt-4 rounded-xl overflow-hidden"
                        dangerouslySetInnerHTML={{ __html: reexplainVisual }}
                      />
                    )}
                  </div>
                ) : (
                  /* Normal visual */
                  <div className="bg-slate-900/60 border border-slate-700/40 rounded-2xl p-5 flex-1 min-h-48">
                    {!sa || sa.visualStatus === "loading" ? (
                      <div className="flex items-center justify-center h-full text-slate-500 text-sm animate-pulse">
                        Generating visual…
                      </div>
                    ) : sa.visualHtml ? (
                      <div dangerouslySetInnerHTML={{ __html: sa.visualHtml }} />
                    ) : (
                      <div className="flex items-center justify-center h-full text-slate-600 text-sm">
                        No visual for this scene
                      </div>
                    )}
                  </div>
                )}

                {/* On-screen text */}
                {scene.on_screen_text && (
                  <div className="bg-indigo-900/20 border border-indigo-700/30 rounded-xl px-4 py-3">
                    <p className="text-indigo-200 text-sm font-medium">{scene.on_screen_text}</p>
                  </div>
                )}
              </div>

              {/* Right column: Video / Audio + Q&A */}
              <div className="lg:w-1/2 flex flex-col gap-4">

                {/* Avatar video or audio-only fallback */}
                <div className="bg-slate-900/60 border border-slate-700/40 rounded-2xl p-4">
                  {!sa || sa.videoStatus === "loading" ? (
                    <div className="text-center py-8 text-slate-500 text-sm">
                      <motion.div className="text-4xl mb-3" animate={{ scale: [1, 1.05, 1] }} transition={{ repeat: Infinity, duration: 2 }}>🤖</motion.div>
                      <p className="animate-pulse">Generating avatar video…</p>
                      {sa?.audioStatus === "done" && sa.audioUrl && (
                        <div className="mt-4">
                          <p className="text-xs text-slate-600 mb-2">Audio ready — play while video generates:</p>
                          <audio
                            src={`${API_BASE}${sa.audioUrl}`}
                            controls
                            className="w-full"
                            autoPlay
                          />
                        </div>
                      )}
                    </div>
                  ) : sa.videoStatus === "done" && sa.videoUrl ? (
                    <video
                      src={sa.videoUrl}
                      controls
                      autoPlay
                      className="w-full rounded-xl bg-black"
                      onEnded={() => {
                        if (scene.interaction_required) setPhase("question");
                      }}
                    />
                  ) : (
                    /* Audio-only fallback when D-ID is unavailable */
                    <div className="text-center py-6">
                      <div className="text-5xl mb-3">🎓</div>
                      <div className="text-xs text-slate-500 mb-1 bg-slate-800/50 rounded-lg px-3 py-1 inline-block">
                        {sa.videoError?.includes("402") ? "D-ID credits unavailable — audio mode" : "Avatar unavailable — audio mode"}
                      </div>
                      {sa.audioUrl ? (
                        <audio
                          src={`${API_BASE}${sa.audioUrl}`}
                          controls
                          autoPlay
                          className="w-full mt-3"
                          onEnded={() => {
                            if (scene.interaction_required) setPhase("question");
                          }}
                        />
                      ) : (
                        <p className="text-slate-500 text-sm mt-2">Audio unavailable</p>
                      )}
                    </div>
                  )}
                </div>

                {/* Narration text */}
                <div className="bg-slate-800/40 rounded-xl px-5 py-4 border border-slate-700/30">
                  <div className="text-xs text-slate-500 mb-2 font-medium">Teacher narration:</div>
                  <p className="text-slate-300 text-sm leading-relaxed italic">
                    "{phase === "reexplaining" && reexplainData ? reexplainData.reexplanation : scene.narration}"
                  </p>
                </div>

                {/* Q&A Section */}
                <AnimatePresence>
                  {(phase === "question" || phase === "evaluating" || phase === "feedback" || phase === "reexplaining") && scene.interaction_required && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 20 }}
                      className="bg-blue-900/20 border border-blue-700/30 rounded-2xl p-5"
                    >
                      {phase === "reexplaining" && reexplainData ? (
                        <>
                          <div className="text-xs text-amber-400 font-semibold mb-2">Check your understanding:</div>
                          <p className="text-slate-200 text-sm mb-3">{reexplainData.check_question}</p>
                          <textarea
                            value={studentAnswer}
                            onChange={(e) => setStudentAnswer(e.target.value)}
                            placeholder="Your answer…"
                            rows={2}
                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm resize-none"
                          />
                          <button
                            onClick={handleSubmitAnswer}
                            className="w-full mt-3 py-2 rounded-xl font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 transition-all text-sm"
                          >
                            Submit →
                          </button>
                        </>
                      ) : phase === "question" ? (
                        <>
                          <div className="flex items-center gap-2 mb-3">
                            <span className="text-lg">❓</span>
                            <span className="text-xs text-orange-400 font-semibold uppercase tracking-wide">
                              {scene.question_type} · {scene.difficulty}
                            </span>
                          </div>
                          <p className="text-slate-200 font-medium mb-4">{scene.question}</p>
                          {scene.question_type === "mcq" && scene.choices?.length > 0 ? (
                            <div className="space-y-2 mb-4">
                              {scene.choices.map((c) => (
                                <button
                                  key={c}
                                  onClick={() => setStudentAnswer(c)}
                                  className={`w-full text-left px-4 py-2 rounded-xl border text-sm transition-all ${
                                    studentAnswer === c
                                      ? "border-blue-500 bg-blue-900/40 text-blue-200"
                                      : "border-slate-700 bg-slate-800/40 text-slate-400 hover:border-slate-600"
                                  }`}
                                >
                                  {c}
                                </button>
                              ))}
                            </div>
                          ) : (
                            <textarea
                              value={studentAnswer}
                              onChange={(e) => setStudentAnswer(e.target.value)}
                              placeholder="Type your answer…"
                              rows={3}
                              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm resize-none mb-4"
                            />
                          )}
                          {evalError && <p className="text-red-400 text-xs mb-3">{evalError}</p>}
                          <button
                            onClick={handleSubmitAnswer}
                            disabled={!studentAnswer.trim()}
                            className="w-full py-2 rounded-xl font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 transition-all text-sm"
                          >
                            Submit Answer →
                          </button>
                        </>
                      ) : phase === "evaluating" ? (
                        <div className="text-center py-4 text-slate-400 text-sm animate-pulse">
                          🧠 TUTIVRA is evaluating your answer…
                        </div>
                      ) : phase === "feedback" && evalResult ? (
                        <>
                          <div className={`rounded-xl p-4 mb-4 ${evalResult.correct ? "bg-green-900/30 border border-green-700/40" : "bg-red-900/30 border border-red-700/40"}`}>
                            <div className="font-semibold text-sm mb-1 flex items-center gap-2">
                              {evalResult.correct ? <span className="text-green-400">✅ Correct!</span> : <span className="text-red-400">❌ Not quite</span>}
                              <span className="text-xs text-slate-500">Understanding: {String(evalResult.understanding_level)}</span>
                            </div>
                            <p className="text-slate-300 text-sm">{String(evalResult.feedback)}</p>
                          </div>

                          {evalResult.misconception_detected && evalResult.misconception && (
                            <div className="bg-amber-900/20 border border-amber-700/30 rounded-xl p-4 mb-4">
                              <div className="text-xs text-amber-400 font-semibold mb-1">⚠️ Misconception detected</div>
                              <p className="text-slate-300 text-sm mb-3">{String(evalResult.misconception)}</p>
                              <button
                                onClick={handleReexplain}
                                className="w-full py-2 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-amber-700 to-orange-700 hover:from-amber-600 hover:to-orange-600 transition-all"
                              >
                                Let TUTIVRA Re-explain →
                              </button>
                            </div>
                          )}

                          <button
                            onClick={handleNextScene}
                            className="w-full py-2 rounded-xl font-medium text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 transition-all text-sm"
                          >
                            {sceneIdx < scenes.length - 1 ? "Continue →" : "Finish Lesson →"}
                          </button>
                        </>
                      ) : null}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Next button (non-interactive scenes) */}
                {phase === "teaching" && !scene.interaction_required && (
                  <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleNextScene}
                    className="w-full py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 transition-all shadow-lg shadow-purple-900/30 text-sm"
                  >
                    {sceneIdx < scenes.length - 1 ? "Next Scene →" : "Finish Lesson & Take Assessment →"}
                  </motion.button>
                )}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
