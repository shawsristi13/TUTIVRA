"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background gradient orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-purple-900/20 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] rounded-full bg-blue-900/20 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] rounded-full bg-indigo-900/10 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: "easeOut" }}
        className="text-center z-10 px-4"
      >
        <motion.div
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-7xl mb-6"
        >
          🎓
        </motion.div>

        <h1 className="text-6xl md:text-7xl font-bold mb-4 bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
          TUTIVRA
        </h1>

        <p className="text-xl md:text-2xl text-slate-400 mb-4 max-w-2xl mx-auto">
          The AI Teacher that actually teaches.
        </p>

        <p className="text-slate-500 mb-12 max-w-xl mx-auto text-sm leading-relaxed">
          Upload your study material or enter any topic — TUTIVRA will understand, plan a lesson,
          explain with visuals and voice, quiz you, adapt when you struggle, and report your progress.
        </p>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-2 mb-12">
          {[
            "📖 RAG-Grounded Lessons",
            "🎬 AI Teaching Video",
            "🗣️ Natural Voice",
            "🤖 Human-Like Avatar",
            "🧠 Misconception Detection",
            "🌐 Multilingual",
            "📊 Learning Report",
          ].map((f) => (
            <span
              key={f}
              className="px-3 py-1 text-xs rounded-full bg-indigo-900/40 border border-indigo-700/40 text-indigo-300"
            >
              {f}
            </span>
          ))}
        </div>

        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => router.push("/setup")}
          className="px-10 py-4 text-lg font-semibold rounded-2xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white shadow-lg shadow-purple-900/40 transition-all"
        >
          Start Learning →
        </motion.button>

        {/* Teaching loop diagram */}
        <div className="mt-16 flex flex-wrap justify-center items-center gap-1 text-xs text-slate-600">
          {["Understand", "Plan", "Explain", "Demonstrate", "Question", "Evaluate", "Adapt", "Continue"].map(
            (step, i, arr) => (
              <span key={step} className="flex items-center gap-1">
                <span className="text-slate-500">{step}</span>
                {i < arr.length - 1 && <span className="text-slate-700">→</span>}
              </span>
            )
          )}
        </div>
      </motion.div>
    </div>
  );
}
