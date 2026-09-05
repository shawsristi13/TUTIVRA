"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useSession } from "@/components/SessionProvider";
import { SUPPORTED_LANGUAGES, SUBJECT_AREAS } from "@/lib/session";
import { setupStudent } from "@/lib/api";

const LEVELS = [
  { value: "beginner", label: "Beginner", icon: "🌱", desc: "Simple terms, analogies, fundamentals" },
  { value: "intermediate", label: "Intermediate", icon: "📚", desc: "Technical explanations, practical examples" },
  { value: "advanced", label: "Advanced", icon: "🔬", desc: "Deep concepts, math, implementation details" },
];

const TIME_OPTIONS = [
  { value: 5, label: "5 min", desc: "Quick overview" },
  { value: 10, label: "10 min", desc: "Core concepts" },
  { value: 20, label: "20 min", desc: "Structured lesson" },
  { value: 45, label: "45 min", desc: "Deep dive" },
  { value: 60, label: "60 min", desc: "Full session" },
];

export default function SetupPage() {
  const router = useRouter();
  const { update } = useSession();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [name, setName] = useState("Alex");
  const [level, setLevel] = useState<"beginner" | "intermediate" | "advanced">("beginner");
  const [language, setLanguage] = useState(SUPPORTED_LANGUAGES[0]);
  const [time, setTime] = useState(20);
  const [subject, setSubject] = useState("General");

  async function handleContinue() {
    if (!name.trim()) { setError("Please enter your name."); return; }
    setSaving(true);
    setError("");
    try {
      // We'll set up the student when the topic is known on the content page.
      // For now, persist settings to session and navigate.
      update({
        studentName: name.trim(),
        studentLevel: level,
        language: language.value,
        languageCode: language.code,
        availableTimeMinutes: time,
        subjectArea: subject === "General" ? "" : subject,
      });
      router.push("/content");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 rounded-full bg-purple-900/15 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 rounded-full bg-blue-900/15 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-2xl z-10"
      >
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">👋</div>
          <h1 className="text-3xl font-bold text-slate-100">Set Up Your Learning Profile</h1>
          <p className="text-slate-400 mt-2">TUTIVRA will personalise everything to your needs.</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-700/40 rounded-2xl p-8 backdrop-blur-sm space-y-8">

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Your Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {/* Level */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-3">Your Level</label>
            <div className="grid grid-cols-3 gap-3">
              {LEVELS.map((l) => (
                <button
                  key={l.value}
                  onClick={() => setLevel(l.value as typeof level)}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    level === l.value
                      ? "border-indigo-500 bg-indigo-900/40 text-indigo-200"
                      : "border-slate-700 bg-slate-800/40 text-slate-400 hover:border-slate-600"
                  }`}
                >
                  <div className="text-2xl mb-1">{l.icon}</div>
                  <div className="font-semibold text-sm">{l.label}</div>
                  <div className="text-xs opacity-70 mt-1">{l.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Language */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-3">Teaching Language</label>
            <div className="flex flex-wrap gap-2">
              {SUPPORTED_LANGUAGES.map((lang) => (
                <button
                  key={lang.value}
                  onClick={() => setLanguage(lang)}
                  className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                    language.value === lang.value
                      ? "border-indigo-500 bg-indigo-900/40 text-indigo-200"
                      : "border-slate-700 bg-slate-800/40 text-slate-400 hover:border-slate-600"
                  }`}
                >
                  {lang.flag} {lang.label}
                </button>
              ))}
            </div>
          </div>

          {/* Time */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-3">Available Time</label>
            <div className="flex flex-wrap gap-2">
              {TIME_OPTIONS.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTime(t.value)}
                  className={`px-4 py-2 rounded-lg border text-sm transition-all ${
                    time === t.value
                      ? "border-indigo-500 bg-indigo-900/40 text-indigo-200"
                      : "border-slate-700 bg-slate-800/40 text-slate-400 hover:border-slate-600"
                  }`}
                >
                  <span className="font-semibold">{t.label}</span>
                  <span className="text-xs opacity-60 ml-1">· {t.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Subject */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Subject Area</label>
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-indigo-500"
            >
              {SUBJECT_AREAS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {error && (
            <p className="text-red-400 text-sm bg-red-900/20 border border-red-800/40 rounded-xl px-4 py-3">{error}</p>
          )}

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleContinue}
            disabled={saving}
            className="w-full py-4 rounded-xl font-semibold text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-900/30"
          >
            {saving ? "Saving..." : "Continue →"}
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}
