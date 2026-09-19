import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload, Camera, Sparkles, ArrowRight,
  Shield, Zap, Users, ChevronDown
} from 'lucide-react'
import UploadBox from '../components/UploadBox'
import CameraCapture from '../components/CameraCapture'
import ProcessingAnimation from '../components/ProcessingAnimation'

// ──────────────────────────────────────────────
// Floating celebrity avatar placeholder bubbles
// ──────────────────────────────────────────────
const CELEBRITY_PLACEHOLDERS = [
  { id: 1, initials: 'AK',  color: '#7c3aed', size: 64, top: '12%', left: '8%',  animClass: 'animate-float-slow'   },
  { id: 2, initials: 'RK',  color: '#db2777', size: 48, top: '20%', right: '10%', animClass: 'animate-float-medium' },
  { id: 3, initials: 'NR',  color: '#0891b2', size: 56, top: '55%', left: '5%',  animClass: 'animate-float-fast'   },
  { id: 4, initials: 'SS',  color: '#059669', size: 44, top: '60%', right: '7%', animClass: 'animate-float-slow'   },
  { id: 5, initials: 'VP',  color: '#d97706', size: 52, top: '35%', left: '3%',  animClass: 'animate-float-medium' },
  { id: 6, initials: 'TR',  color: '#be185d', size: 40, top: '40%', right: '4%', animClass: 'animate-float-fast'   },
]

// Category pill data
const CATEGORIES = [
  'All', 'Bollywood', 'South Indian', 'Cricket', 'Football', 'Singers',
]

const FEATURES = [
  {
    icon: Zap,
    title: 'Instant Matching',
    desc: 'Results in seconds using advanced face embedding technology',
  },
  {
    icon: Shield,
    title: 'Privacy First',
    desc: 'Your photo is processed and immediately discarded — never stored',
  },
  {
    icon: Users,
    title: '24+ Celebrities',
    desc: "Growing database of South Indian cinema's biggest stars",
  },
]

export default function Home() {
  const [mode, setMode] = useState(null) // null | 'upload' | 'camera'
  const [imageFile, setImageFile] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [category, setCategory] = useState('All')
  const inputSectionRef = useRef(null)

  const scrollToInput = () => {
    inputSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  const handleFindMatches = async () => {
    if (!imageFile) return
    setIsProcessing(true)
    // Backend call will be wired in Phase 4
    // For now, simulate processing then reset
    setTimeout(() => {
      setIsProcessing(false)
    }, 8000)
  }

  return (
    <div className="relative min-h-screen flex flex-col overflow-hidden">
      {/* ── Background orbs ── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div
          className="absolute animate-orb-pulse"
          style={{
            width: 600, height: 600,
            top: '-10%', left: '-15%',
            background: 'radial-gradient(circle, rgba(124,58,237,0.18) 0%, transparent 70%)',
            borderRadius: '50%',
          }}
        />
        <div
          className="absolute animate-orb-pulse"
          style={{
            width: 500, height: 500,
            bottom: '-5%', right: '-10%',
            background: 'radial-gradient(circle, rgba(236,72,153,0.14) 0%, transparent 70%)',
            borderRadius: '50%',
            animationDelay: '2s',
          }}
        />
        <div
          className="absolute"
          style={{
            width: 300, height: 300,
            top: '40%', left: '40%',
            background: 'radial-gradient(circle, rgba(245,158,11,0.08) 0%, transparent 70%)',
            borderRadius: '50%',
          }}
        />
      </div>

      {/* ── Floating celebrity bubbles ── */}
      <div className="fixed inset-0 pointer-events-none hidden lg:block">
        {CELEBRITY_PLACEHOLDERS.map((celeb) => (
          <div
            key={celeb.id}
            className={`absolute ${celeb.animClass} opacity-40`}
            style={{
              top: celeb.top,
              left: celeb.left,
              right: celeb.right,
              width: celeb.size,
              height: celeb.size,
            }}
          >
            <div
              className="w-full h-full rounded-full border-2 border-white/20 flex items-center justify-center text-white font-bold shadow-lg"
              style={{
                background: `radial-gradient(circle at 30% 30%, ${celeb.color}aa, ${celeb.color}44)`,
                fontSize: celeb.size * 0.28,
              }}
            >
              {celeb.initials}
            </div>
          </div>
        ))}
      </div>

      {/* ── Main content ── */}
      <main className="relative z-10 flex flex-col items-center pt-28 pb-24 px-4">

        {/* Hero badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="flex items-center gap-2 px-4 py-2 rounded-full border border-violet-500/30 bg-violet-500/10 mb-8"
        >
          <Sparkles size={13} className="text-violet-400" />
          <span className="text-violet-300 text-xs font-medium tracking-wide">
            Powered by Face Embedding AI
          </span>
        </motion.div>

        {/* Hero heading */}
        <motion.h1
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-5xl sm:text-6xl md:text-7xl font-black text-center leading-[1.05] max-w-3xl"
          style={{ fontFamily: 'Syne, sans-serif' }}
        >
          Who is your{' '}
          <span className="gradient-text">celebrity</span>
          <br />
          twin?
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.25 }}
          className="mt-6 text-lg text-slate-400 text-center max-w-lg leading-relaxed"
        >
          Upload a selfie and discover which South Indian celebrities you look most like —
          powered by face similarity, not guesswork.
        </motion.p>

        {/* CTA buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.38 }}
          className="flex flex-col sm:flex-row items-center gap-3 mt-10"
        >
          <button
            onClick={() => { setMode('upload'); scrollToInput() }}
            className="flex items-center gap-2.5 px-7 py-3.5 rounded-2xl text-white font-semibold text-base btn-shimmer shadow-xl"
          >
            <Upload size={18} />
            Upload Photo
            <ArrowRight size={16} className="opacity-70" />
          </button>
          <button
            onClick={() => { setMode('camera'); scrollToInput() }}
            className="flex items-center gap-2.5 px-7 py-3.5 rounded-2xl text-white font-semibold text-base transition-all duration-200 hover:bg-white/10 hover:scale-105"
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)' }}
          >
            <Camera size={18} />
            Use Camera
          </button>
        </motion.div>

        {/* Scroll hint */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="mt-12 flex flex-col items-center gap-1"
        >
          <ChevronDown size={18} className="text-slate-600 animate-bounce" />
        </motion.div>

        {/* ── Upload / Camera section ── */}
        <div ref={inputSectionRef} className="w-full max-w-md mt-8">
          <AnimatePresence mode="wait">
            {mode && (
              <motion.div
                key="input-card"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 30 }}
                transition={{ duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
                className="glass rounded-3xl p-6 shadow-2xl"
                style={{ boxShadow: '0 25px 80px rgba(124,58,237,0.2)' }}
              >
                {/* Tab switcher */}
                <div className="flex gap-1 p-1 rounded-xl mb-5"
                  style={{ background: 'rgba(255,255,255,0.05)' }}>
                  {[
                    { id: 'upload', icon: Upload, label: 'Upload' },
                    { id: 'camera', icon: Camera, label: 'Camera' },
                  ].map(({ id, icon: Icon, label }) => (
                    <button
                      key={id}
                      onClick={() => setMode(id)}
                      className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                        mode === id
                          ? 'bg-violet-600 text-white shadow-md'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <Icon size={14} />
                      {label}
                    </button>
                  ))}
                </div>

                {/* Category filter */}
                <div className="mb-5">
                  <p className="text-slate-500 text-xs font-medium mb-2 uppercase tracking-wide">Search category</p>
                  <div className="flex flex-wrap gap-2">
                    {CATEGORIES.map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setCategory(cat)}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-all duration-200 ${
                          category === cat
                            ? 'bg-violet-600 text-white'
                            : 'text-slate-400 hover:text-white border border-white/10 hover:border-white/20'
                        }`}
                        style={category !== cat ? { background: 'rgba(255,255,255,0.04)' } : {}}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Input component */}
                {mode === 'upload'
                  ? <UploadBox onImageReady={setImageFile} />
                  : <CameraCapture onImageReady={setImageFile} />
                }

                {/* Find matches CTA */}
                <motion.button
                  layout
                  disabled={!imageFile}
                  onClick={handleFindMatches}
                  whileHover={imageFile ? { scale: 1.02 } : {}}
                  whileTap={imageFile ? { scale: 0.98 } : {}}
                  className={`mt-5 w-full py-3.5 rounded-2xl font-semibold text-base flex items-center justify-center gap-2.5 transition-all duration-300 ${
                    imageFile
                      ? 'btn-shimmer text-white shadow-xl'
                      : 'bg-white/5 text-slate-600 cursor-not-allowed border border-white/5'
                  }`}
                >
                  <Sparkles size={17} />
                  Find My Celebrity Twin
                  {imageFile && <ArrowRight size={16} className="opacity-70" />}
                </motion.button>

                {/* Disclaimer */}
                <p className="mt-4 text-center text-slate-600 text-[11px] leading-relaxed">
                  <Shield size={10} className="inline mr-1 mb-0.5" />
                  Lookalike results are estimates based on visual similarity and are not identity recognition.
                  Your photo is processed temporarily and never stored.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* ── Features ── */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          id="how-it-works"
          className="mt-24 w-full max-w-3xl"
        >
          <h2
            className="text-2xl font-bold text-center text-white mb-10"
            style={{ fontFamily: 'Syne, sans-serif' }}
          >
            How it works
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 + i * 0.1 }}
                className="glass rounded-2xl p-5 card-hover text-center"
              >
                <div className="w-10 h-10 rounded-xl bg-violet-500/15 border border-violet-500/30 flex items-center justify-center mx-auto mb-3">
                  <f.icon size={18} className="text-violet-400" />
                </div>
                <h3 className="text-white font-semibold text-sm mb-1">{f.title}</h3>
                <p className="text-slate-500 text-xs leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Step visual */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
          className="mt-16 w-full max-w-2xl"
        >
          <div className="grid grid-cols-3 gap-2 sm:gap-4 text-center">
            {[
              { step: '01', label: 'Upload or snap a selfie' },
              { step: '02', label: 'AI analyzes your facial features' },
              { step: '03', label: 'See your celebrity matches' },
            ].map((item, i) => (
              <div key={i} className="flex flex-col items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-pink-500 flex items-center justify-center text-white font-bold text-sm shadow-lg"
                  style={{ boxShadow: '0 4px 20px rgba(124,58,237,0.3)' }}>
                  {item.step}
                </div>
                <p className="text-slate-400 text-xs">{item.label}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </main>

      {/* ── Processing overlay ── */}
      <ProcessingAnimation isVisible={isProcessing} />
    </div>
  )
}
