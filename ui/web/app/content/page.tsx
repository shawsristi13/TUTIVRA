"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useSession } from "@/components/SessionProvider";
import { uploadPdf } from "@/lib/api";

export default function ContentPage() {
  const router = useRouter();
  const { session, update } = useSession();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [mode, setMode] = useState<"pdf" | "topic">("topic");
  const [topic, setTopic] = useState(session.topic || "");
  const [goal, setGoal] = useState(session.goal || "");
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [uploadMsg, setUploadMsg] = useState("");
  const [error, setError] = useState("");

  async function handlePdfUpload(file: File) {
    if (!file.name.endsWith(".pdf")) {
      setError("Please upload a PDF file.");
      return;
    }
    setUploading(true);
    setUploadStatus("uploading");
    setError("");
    try {
      const res = await uploadPdf(file);
      setUploadStatus("done");
      setUploadMsg(`✅ ${res.documents_processed ?? 1} document(s) processed · ${res.chunks_created ?? "?"} knowledge chunks created`);
      update({
        materialContext: `Student uploaded ${file.name}. ${res.chunks_created ?? 0} chunks indexed.`,
        ragReady: true,
      });
    } catch (e: unknown) {
      setUploadStatus("error");
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading(false);
    }
  }

  function handleContinue() {
    if (mode === "topic") {
      if (!topic.trim()) { setError("Please enter a topic."); return; }
      update({ topic: topic.trim(), goal: goal.trim(), materialContext: "", ragReady: false });
    } else {
      if (uploadStatus !== "done") { setError("Please upload a PDF first."); return; }
      update({ topic: topic.trim() || "Uploaded Material", goal: goal.trim() });
    }
    router.push("/lesson");
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-1/4 w-96 h-96 rounded-full bg-blue-900/15 blur-3xl" />
        <div className="absolute bottom-0 left-1/4 w-96 h-96 rounded-full bg-purple-900/15 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl z-10"
      >
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">📖</div>
          <h1 className="text-3xl font-bold text-slate-100">What Would You Like to Learn?</h1>
          <p className="text-slate-400 mt-2">Upload your study material or enter any topic.</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-700/40 rounded-2xl p-8 backdrop-blur-sm space-y-6">

          {/* Mode selector */}
          <div className="flex gap-2 p-1 bg-slate-800/60 rounded-xl">
            <button
              onClick={() => setMode("topic")}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                mode === "topic"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Enter a Topic
            </button>
            <button
              onClick={() => setMode("pdf")}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                mode === "pdf"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Upload PDF / Notes
            </button>
          </div>

          <AnimatePresence mode="wait">
            {mode === "topic" ? (
              <motion.div
                key="topic"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Topic</label>
                  <input
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder='e.g. "Binary Search", "Newtons Laws", "React Hooks"'
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Specific Goal <span className="text-slate-500">(optional)</span>
                  </label>
                  <input
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    placeholder='e.g. "Understand for a technical interview"'
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="pdf"
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="space-y-4"
              >
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                    uploadStatus === "done"
                      ? "border-green-600 bg-green-900/20"
                      : uploadStatus === "error"
                      ? "border-red-600 bg-red-900/20"
                      : "border-slate-600 bg-slate-800/30 hover:border-indigo-500 hover:bg-indigo-900/10"
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    onChange={(e) => e.target.files?.[0] && handlePdfUpload(e.target.files[0])}
                  />
                  {uploadStatus === "uploading" ? (
                    <div className="text-slate-400">
                      <div className="text-3xl mb-2 animate-bounce">⏳</div>
                      <p>Processing your PDF…</p>
                    </div>
                  ) : uploadStatus === "done" ? (
                    <div className="text-green-400">
                      <div className="text-3xl mb-2">✅</div>
                      <p className="text-sm">{uploadMsg}</p>
                    </div>
                  ) : (
                    <div className="text-slate-400">
                      <div className="text-3xl mb-2">📄</div>
                      <p className="font-medium">Click to upload a PDF</p>
                      <p className="text-xs mt-1 text-slate-500">Books, lecture notes, textbooks, research papers</p>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Topic / Chapter <span className="text-slate-500">(optional — helps TUTIVRA focus)</span>
                  </label>
                  <input
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder='e.g. "Chapter 4 — Arrays", "Photosynthesis"'
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {error && (
            <p className="text-red-400 text-sm bg-red-900/20 border border-red-800/40 rounded-xl px-4 py-3">{error}</p>
          )}

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleContinue}
            disabled={uploading}
            className="w-full py-4 rounded-xl font-semibold text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-900/30"
          >
            Generate Lesson →
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}
