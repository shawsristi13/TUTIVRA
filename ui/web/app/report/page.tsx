"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useSession } from "@/components/SessionProvider";
import { generateReport } from "@/lib/api";

const STATUS_CONFIG: Record<string, { color: string; icon: string; label: string }> = {
  excellent: { color: "text-green-400", icon: "🏆", label: "Excellent" },
  good: { color: "text-blue-400", icon: "✅", label: "Good Progress" },
  needs_revision: { color: "text-amber-400", icon: "📖", label: "Needs Revision" },
  repeat_lesson: { color: "text-red-400", icon: "🔄", label: "Repeat Lesson" },
};

export default function ReportPage() {
  const router = useRouter();
  const { session, update, reset } = useSession();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const report = session.report as Record<string, unknown> | null;

  useEffect(() => {
    if (!session.topic) { router.replace("/"); return; }
    if (report) return;
    runReport();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runReport() {
    setLoading(true);
    setError("");
    try {
      const sessionData = {
        session_questions: session.sessionInteractions.length,
        session_correct: session.sessionCorrect,
        mastery_before: 0,
        mastery_after: Math.min(
          100,
          session.sessionCorrect > 0
            ? (session.sessionCorrect / Math.max(1, session.sessionInteractions.length)) * 100
            : 0
        ),
        misconceptions: session.misconceptions,
        concepts_taught: session.scenes.map((s) => s.concept).filter(Boolean).slice(0, 8),
      };
      const res = await generateReport(
        session.studentName || "Student",
        session.topic,
        sessionData,
        session.assessmentResult ?? undefined
      );
      update({ report: res });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function handleNewTopic() {
    reset();
    router.push("/setup");
  }

  const statusConf = report
    ? STATUS_CONFIG[String(report.status)] ?? STATUS_CONFIG.good
    : STATUS_CONFIG.good;

  const scoreNum: number | null = report
    ? typeof report.overall_score_percentage === "number"
      ? report.overall_score_percentage
      : typeof report.score === "number"
      ? report.score
      : null
    : null;

  return (
    <div className="min-h-screen px-4 py-12">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/3 w-96 h-96 rounded-full bg-purple-900/15 blur-3xl" />
        <div className="absolute bottom-0 right-1/3 w-96 h-96 rounded-full bg-blue-900/15 blur-3xl" />
      </div>

      <div className="max-w-3xl mx-auto z-10">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="text-5xl mb-3">📊</div>
          <h1 className="text-3xl font-bold text-slate-100">Learning Report</h1>
          <p className="text-slate-400 mt-2">
            {session.studentName || "Student"} · <span className="text-indigo-400">{session.topic}</span>
          </p>
        </motion.div>

        {loading && (
          <div className="bg-slate-900/60 border border-slate-700/40 rounded-2xl p-8 text-center">
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: "linear" }} className="text-5xl mb-4">📈</motion.div>
            <p className="text-slate-400 animate-pulse">Generating your personalised learning report…</p>
          </div>
        )}

        {!loading && report && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">

            {/* Score card */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700/40 rounded-2xl p-8 text-center">
            <div className={`text-5xl mb-2 ${statusConf.icon === "🏆" ? "text-yellow-400" : ""}`}>
                {String(statusConf.icon)}
              </div>
              {scoreNum !== null && (
                <div className="text-6xl font-bold mb-1 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                  {typeof scoreNum === "number" ? `${Math.round(scoreNum)}%` : String(scoreNum)}
                </div>
              )}
              <div className={`text-lg font-semibold ${statusConf.color}`}>{statusConf.label}</div>

              <div className="grid grid-cols-3 gap-4 mt-6">
                {[
                  { label: "Questions", val: String(session.sessionInteractions.length) },
                  { label: "Correct", val: String(session.sessionCorrect) },
                  { label: "Mastery", val: report.mastery_after !== undefined ? `${Number(report.mastery_after).toFixed(0)}%` : "—" },
                ].map(({ label, val }) => (
                  <div key={label} className="bg-slate-800/60 rounded-xl py-3">
                    <div className="text-xl font-bold text-slate-200">{val}</div>
                    <div className="text-xs text-slate-500">{label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI message */}
            {report.personalised_message && (
              <div className="bg-indigo-900/20 border border-indigo-700/30 rounded-2xl p-6">
                <div className="flex items-start gap-3">
                  <div className="text-2xl">🎓</div>
                  <p className="text-slate-300 leading-relaxed italic">{String(report.personalised_message)}</p>
                </div>
              </div>
            )}

            {/* Strong / Weak */}
            <div className="grid grid-cols-2 gap-4">
              {/* Strong concepts */}
              <div className="bg-green-900/20 border border-green-700/30 rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-green-400 mb-3">✅ Strong Concepts</h3>
                {Array.isArray(report.concepts_understood) && (report.concepts_understood as string[]).length > 0 ? (
                  <ul className="space-y-1">
                    {(report.concepts_understood as string[]).map((c) => (
                      <li key={c} className="text-slate-300 text-sm">· {c}</li>
                    ))}
                  </ul>
                ) : <p className="text-slate-500 text-sm">—</p>}
              </div>

              {/* Weak concepts */}
              <div className="bg-red-900/20 border border-red-700/30 rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-red-400 mb-3">📌 Needs Revision</h3>
                {Array.isArray(report.weak_concepts) && (report.weak_concepts as string[]).length > 0 ? (
                  <ul className="space-y-1">
                    {(report.weak_concepts as string[]).map((c) => (
                      <li key={c} className="text-slate-300 text-sm">· {c}</li>
                    ))}
                  </ul>
                ) : <p className="text-slate-500 text-sm">—</p>}
              </div>
            </div>

            {/* Misconceptions */}
            {Array.isArray(report.misconceptions) && (report.misconceptions as string[]).length > 0 && (
              <div className="bg-amber-900/20 border border-amber-700/30 rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-amber-400 mb-3">⚠️ Misconceptions Identified</h3>
                <ul className="space-y-1">
                  {(report.misconceptions as string[]).map((m, i) => (
                    <li key={i} className="text-slate-300 text-sm">· {m}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Revision plan */}
            {Array.isArray(report.revision_plan) && (report.revision_plan as string[]).length > 0 && (
              <div className="bg-slate-900/60 border border-slate-700/40 rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-slate-300 mb-3">📚 Recommended Next Steps</h3>
                <ol className="space-y-2">
                  {(report.revision_plan as string[]).map((step, i) => (
                    <li key={i} className="flex gap-3 text-sm text-slate-400">
                      <span className="text-indigo-400 font-bold">{i + 1}.</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
                {report.recommended_next_topic != null && (
                  <div className="mt-4 pt-4 border-t border-slate-700/40 text-sm text-slate-400">
                    <span className="text-indigo-400 font-medium">Suggested next topic: </span>
                    {String(report.recommended_next_topic)}
                  </div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => { update({ currentSceneIndex: 0, sessionInteractions: [], sessionCorrect: 0, misconceptions: [], assessmentQuestions: [], assessmentAnswers: {}, assessmentResult: null, report: null }); router.push("/teach"); }}
                className="flex-1 py-3 rounded-xl font-medium text-slate-300 border border-slate-700 bg-slate-800 hover:bg-slate-700 transition-all text-sm"
              >
                ↺ Review Lesson
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleNewTopic}
                className="flex-1 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 transition-all shadow-lg shadow-purple-900/30 text-sm"
              >
                Learn Something New →
              </motion.button>
            </div>
          </motion.div>
        )}

        {error && (
          <div className="text-center mt-8">
            <p className="text-red-400 mb-4">{error}</p>
            <button onClick={runReport} className="px-6 py-2 bg-red-700/40 text-red-300 rounded-xl text-sm hover:bg-red-700/60 transition">Retry</button>
          </div>
        )}
      </div>
    </div>
  );
}
