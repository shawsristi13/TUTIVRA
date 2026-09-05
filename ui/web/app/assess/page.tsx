"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useSession } from "@/components/SessionProvider";
import { generateAssessment, evaluateAssessment } from "@/lib/api";

export default function AssessPage() {
  const router = useRouter();
  const { session, update } = useSession();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const questions = session.assessmentQuestions || [];

  useEffect(() => {
    if (!session.lessonText) { router.replace("/lesson"); return; }
    if (questions.length > 0) return;
    runGenerate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runGenerate() {
    setLoading(true);
    setError("");
    try {
      const concepts = session.scenes.map((s) => s.concept).filter(Boolean).slice(0, 8);
      const res = await generateAssessment(
        session.topic,
        concepts,
        session.studentLevel,
        session.misconceptions || [],
        session.weakConcepts || [],
        session.materialContext,
        session.language,
        5
      );
      update({ assessmentQuestions: res.questions });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    if (Object.keys(answers).length === 0) { setError("Please answer at least one question."); return; }
    setSubmitting(true);
    setError("");
    try {
      const res = await evaluateAssessment(questions, answers, session.studentLevel, session.topic);
      update({ assessmentResult: res, assessmentAnswers: answers });
      router.push("/report");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen px-4 py-12">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full bg-teal-900/15 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 rounded-full bg-blue-900/15 blur-3xl" />
      </div>

      <div className="max-w-3xl mx-auto z-10">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="text-5xl mb-3">📝</div>
          <h1 className="text-3xl font-bold text-slate-100">Final Assessment</h1>
          <p className="text-slate-400 mt-2">Topic: <span className="text-indigo-400">{session.topic}</span></p>
        </motion.div>

        {loading && (
          <div className="bg-slate-900/60 border border-slate-700/40 rounded-2xl p-8 text-center">
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: "linear" }} className="text-5xl mb-4">⚙️</motion.div>
            <p className="text-slate-400 animate-pulse">Generating personalised assessment based on your session…</p>
          </div>
        )}

        {!loading && questions.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            {questions.map((q: Record<string, unknown>, i: number) => (
              <div key={i} className="bg-slate-900/60 border border-slate-700/40 rounded-2xl p-6 backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-sm font-semibold text-indigo-400">Q{i + 1}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400">
                    {String(q.type ?? "question")} · {String(q.marks ?? 1)} mark{Number(q.marks) !== 1 ? "s" : ""}
                  </span>
                </div>
                <p className="text-slate-200 mb-4">{String(q.question)}</p>

                {q.type === "mcq" && Array.isArray(q.options) ? (
                  <div className="space-y-2">
                    {(q.options as string[]).map((opt) => (
                      <button
                        key={opt}
                        onClick={() => setAnswers((prev) => ({ ...prev, [String(i)]: opt }))}
                        className={`w-full text-left px-4 py-3 rounded-xl border text-sm transition-all ${
                          answers[String(i)] === opt
                            ? "border-indigo-500 bg-indigo-900/40 text-indigo-200"
                            : "border-slate-700 bg-slate-800/40 text-slate-400 hover:border-slate-600"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : (
                  <textarea
                    value={answers[String(i)] ?? ""}
                    onChange={(e) => setAnswers((prev) => ({ ...prev, [String(i)]: e.target.value }))}
                    placeholder="Write your answer here…"
                    rows={3}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm resize-none"
                  />
                )}
              </div>
            ))}

            {error && (
              <p className="text-red-400 text-sm bg-red-900/20 border border-red-800/40 rounded-xl px-4 py-3">{error}</p>
            )}

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSubmit}
              disabled={submitting}
              className="w-full py-4 rounded-xl font-semibold text-white bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-500 hover:to-blue-500 disabled:opacity-50 transition-all shadow-lg shadow-teal-900/30"
            >
              {submitting ? "Evaluating…" : "Submit Assessment →"}
            </motion.button>
          </motion.div>
        )}

        {error && !loading && (
          <div className="text-center mt-8">
            <p className="text-red-400 mb-4">{error}</p>
            <button onClick={runGenerate} className="px-6 py-2 bg-red-700/40 text-red-300 rounded-xl text-sm hover:bg-red-700/60 transition">Retry</button>
          </div>
        )}
      </div>
    </div>
  );
}
