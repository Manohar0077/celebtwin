import { useRef, useState, useCallback, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Camera, ZapOff, RefreshCw, Sparkles,
  Star, Trophy, Info, AlertCircle, Loader2, X
} from 'lucide-react'

// ─── constants ────────────────────────────────────────────────
const API = import.meta.env.VITE_API_URL || '' // Uses VITE_API_URL on Vercel or local proxy in dev
const TOP_N = 5

// ─── tiny helpers ─────────────────────────────────────────────
const pct = (score) => Math.round(score * 100)

const CATEGORY_MAP = {
  'Actor':   { color: '#7c3aed', bg: 'rgba(124,58,237,0.15)' },
  'Actress': { color: '#ec4899', bg: 'rgba(236,72,153,0.15)' },
  'Singer':  { color: '#f59e0b', bg: 'rgba(245,158,11,0.15)' },
  'Cricketer': { color: '#10b981', bg: 'rgba(16,185,129,0.15)' },
}
const catStyle = (cat) => CATEGORY_MAP[cat] || { color: '#94a3b8', bg: 'rgba(148,163,184,0.1)' }

// ─── WhatsApp icon & share helper ─────────────────────────────
function WhatsAppIcon({ size = 16, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M17.472 14.382c-.301-.15-1.78-.878-2.056-.978-.276-.1-.477-.15-.678.15-.2.301-.778.978-.954 1.179-.175.2-.351.226-.652.075-.301-.15-1.272-.469-2.423-1.496-.895-.799-1.5-1.786-1.676-2.087-.175-.301-.019-.464.132-.614.136-.135.301-.351.451-.527.15-.175.2-.301.301-.502.1-.2.05-.376-.025-.526-.075-.15-.678-1.634-.928-2.235-.244-.587-.492-.507-.678-.517-.175-.01-.376-.01-.577-.01-.2 0-.527.075-.803.376s-1.054 1.029-1.054 2.509 1.079 2.91 1.23 3.111c.15.2 2.124 3.243 5.145 4.549.719.311 1.28.497 1.718.636.722.23 1.378.197 1.898.121.579-.086 1.78-.727 2.03-1.43.251-.703.251-1.305.176-1.43-.075-.126-.276-.201-.577-.351z"/>
      <path d="M12.04 2c-5.464 0-9.915 4.451-9.915 9.915 0 1.745.456 3.447 1.323 4.954L2 22.04l5.313-1.394c1.457.795 3.097 1.214 4.727 1.214 5.464 0 9.915-4.451 9.915-9.915 0-5.464-4.451-9.915-9.915-9.915zm0 18.067c-1.48 0-2.929-.398-4.195-1.15l-.301-.179-3.119.818.832-3.041-.196-.312a8.125 8.125 0 0 1-1.246-4.288c0-4.498 3.659-8.157 8.157-8.157 4.498 0 8.157 3.659 8.157 8.157 0 4.498-3.659 8.157-8.157 8.157z"/>
    </svg>
  )
}

const shareAllMatches = async (matches) => {
  if (!matches || matches.length === 0) return
  const top = matches[0]
  const topPct = Math.round(top.score * 100)
  const appUrl = window.location.origin
  const heroImageUrl = top.image ? `${API || appUrl}/celebrity-images/${top.image}` : ''

  const lines = [
    "🤩 *My Celebrity Doppelgängers on CelebTwin!*",
    "",
    `👑 *#1 Twin Match: ${top.name}* (${top.category})`,
    `🔥 *Similarity: ${topPct}% Match*`,
    "",
    "✨ *My Top 5 Celebrity Lookalikes:*",
  ]

  const medals = ['🥇', '🥈', '🥉', '⭐️', '⭐️']
  matches.slice(0, 5).forEach((m, idx) => {
    lines.push(`${medals[idx]} ${idx + 1}. ${m.name} — ${Math.round(m.score * 100)}%`)
  })

  if (heroImageUrl) {
    lines.push("")
    lines.push(`📸 *${top.name}'s Photo:* ${heroImageUrl}`)
  }
  lines.push("")
  lines.push(`👉 Find your celebrity twin here: ${appUrl}`)

  const shareText = lines.join("\n")

  // Try native Web Share with hero image file on mobile devices
  try {
    if (navigator.share && heroImageUrl) {
      const response = await fetch(heroImageUrl)
      const blob = await response.blob()
      const fileName = `${top.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_twin.jpg`
      const file = new File([blob], fileName, { type: blob.type || 'image/jpeg' })

      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({
          title: `My Celebrity Twin: ${top.name} (${topPct}%)`,
          text: shareText,
          files: [file],
        })
        return
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') return
  }

  // Direct WhatsApp share fallback
  const waUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText)}`
  window.open(waUrl, '_blank')
}

// ─── celebrity pool for reel animation ─────────────────────────
const CELEB_POOL = [
  // South Indian Stars
  { name: 'Vijay', image: 'vijay/11.jpg', category: 'Actor' },
  { name: 'Suriya', image: 'surya/1.jpeg', category: 'Actor' },
  { name: 'Samantha', image: 'samantha/1.jpeg', category: 'Actress' },
  { name: 'Dhanush', image: 'danush/1.jpeg', category: 'Actor' },
  { name: 'Nayanthara', image: 'nayanthara/1.jpeg', category: 'Actress' },
  { name: 'Rajinikanth', image: 'rajinikanth/1.jpg', category: 'Actor' },
  { name: 'Keerthy Suresh', image: 'keerthi/1.jpeg', category: 'Actress' },
  { name: 'Mahesh Babu', image: 'makeshbabu/1.jpeg', category: 'Actor' },
  { name: 'Sai Pallavi', image: 'saipallavi/1.jpeg', category: 'Actress' },
  { name: 'Prabhas', image: 'prabas/1.jpg', category: 'Actor' },
  { name: 'Trisha', image: 'trisha/1.jpg', category: 'Actress' },
  { name: 'Allu Arjun', image: 'allu_arjun/1.jpg', category: 'Actor' },
  { name: 'Yash', image: 'yash/1.jpg', category: 'Actor' },
  { name: 'Rashmika Mandanna', image: 'rashmika_mandanna/1.jpg', category: 'Actress' },
  { name: 'Dulquer Salmaan', image: 'dulquer_salmaan/1.jpg', category: 'Actor' },
  { name: 'Fahadh Faasil', image: 'fahadh_faasil/1.jpg', category: 'Actor' },
  // Cricket Stars (Men & Women)
  { name: 'Virat Kohli', image: 'virat_kohli/1.jpg', category: 'Cricketer' },
  { name: 'MS Dhoni', image: 'ms_dhoni/1.jpg', category: 'Cricketer' },
  { name: 'Rohit Sharma', image: 'rohit_sharma/1.jpg', category: 'Cricketer' },
  { name: 'Sachin Tendulkar', image: 'sachin_tendulkar/1.jpg', category: 'Cricketer' },
  { name: 'Smriti Mandhana', image: 'smriti_mandhana/1.jpg', category: 'Cricketer' },
  { name: 'Harmanpreet Kaur', image: 'harmanpreet_kaur/1.jpg', category: 'Cricketer' },
  // Bollywood Stars
  { name: 'Shah Rukh Khan', image: 'shah_rukh_khan/1.jpg', category: 'Actor' },
  { name: 'Deepika Padukone', image: 'deepika_padukone/1.jpg', category: 'Actress' },
  { name: 'Alia Bhatt', image: 'alia_bhatt/1.jpg', category: 'Actress' },
  { name: 'Ranbir Kapoor', image: 'ranbir_kapoor/1.jpg', category: 'Actor' },
  { name: 'Ranveer Singh', image: 'ranveer_singh/1.jpg', category: 'Actor' },
  { name: 'Hrithik Roshan', image: 'hrithik_roshan/1.jpg', category: 'Actor' },
  { name: 'Katrina Kaif', image: 'katrina_kaif/1.jpg', category: 'Actress' },
  { name: 'Priyanka Chopra', image: 'priyanka_chopra/1.jpg', category: 'Actress' },
]

// ─── sound synthesizers (Web Audio API) ─────────────────────────
function playReelTick(pitch = 600) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'triangle'
    osc.frequency.setValueAtTime(pitch, ctx.currentTime)
    gain.gain.setValueAtTime(0.06, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.04)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + 0.05)
  } catch {}
}

function playCelebrationChord() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()
    ;[523.25, 659.25, 783.99, 1046.5].forEach((freq, i) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(freq, ctx.currentTime + i * 0.06)
      gain.gain.setValueAtTime(0.1, ctx.currentTime + i * 0.06)
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + i * 0.06 + 0.5)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(ctx.currentTime + i * 0.06)
      osc.stop(ctx.currentTime + i * 0.06 + 0.6)
    })
  } catch {}
}

// ─── ScoreRing ─────────────────────────────────────────────────
function ScoreRing({ score, size = 64 }) {
  const r = (size / 2) - 5
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - score)
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="4"/>
      <motion.circle
        cx={size/2} cy={size/2} r={r}
        fill="none"
        stroke="url(#sg)"
        strokeWidth="4"
        strokeLinecap="round"
        strokeDasharray={circ}
        initial={{ strokeDashoffset: circ }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 1, ease: 'easeOut', delay: 0.2 }}
      />
      <defs>
        <linearGradient id="sg" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#a78bfa"/>
          <stop offset="100%" stopColor="#ec4899"/>
        </linearGradient>
      </defs>
    </svg>
  )
}

// ─── TopMatch card ─────────────────────────────────────────────
function TopMatch({ match }) {
  const { name, category, score, image } = match
  const s = catStyle(category)
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.34,1.56,0.64,1] }}
      className="glass rounded-2xl overflow-hidden border border-white/10 shadow-xl"
    >
      {/* Celebrity image */}
      <div className="relative h-52 bg-[#0e0e1e]">
        {image ? (
          <img
            src={`${API}/celebrity-images/${image}`}
            alt={name}
            className="w-full h-full object-cover object-top"
            style={{ objectPosition: 'center 20%' }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Star size={40} className="text-violet-400/30" />
          </div>
        )}
        <div className="absolute inset-0" style={{ background: 'linear-gradient(to top, rgba(9,9,15,0.95) 0%, rgba(9,9,15,0.2) 50%, transparent 100%)' }} />

        {/* #1 badge */}
        <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full"
          style={{ background: 'rgba(245,158,11,0.2)', border: '1px solid rgba(245,158,11,0.4)' }}>
          <Trophy size={11} className="text-amber-400" />
          <span className="text-amber-300 text-[11px] font-bold">#1 Match</span>
        </div>

        {/* Score ring overlay */}
        <div className="absolute top-3 right-3 relative flex items-center justify-center">
          <ScoreRing score={score} size={58} />
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-white font-bold text-sm leading-none">{pct(score)}%</span>
            <span className="text-slate-400 text-[8px] uppercase tracking-wider">match</span>
          </div>
        </div>

        {/* Name at bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <h3 className="text-white text-lg font-bold leading-tight" style={{ fontFamily: 'Syne, sans-serif' }}>{name}</h3>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full"
              style={{ color: s.color, background: s.bg, border: `1px solid ${s.color}44` }}>
              {category}
            </span>
            <span className="text-[11px] font-bold text-amber-300 bg-amber-400/15 border border-amber-400/30 px-2 py-0.5 rounded-full">
              {pct(score)}% Match
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// ─── CompactMatch row ──────────────────────────────────────────
function CompactMatch({ match, rank }) {
  const { name, category, score, image } = match
  return (
    <motion.div
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: rank * 0.08 }}
      className="flex items-center gap-3 p-2.5 rounded-xl"
      style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}
    >
      {/* rank */}
      <span className="w-5 text-center text-slate-500 text-xs font-bold flex-shrink-0">#{rank}</span>

      {/* avatar */}
      <div className="w-9 h-9 rounded-lg overflow-hidden flex-shrink-0 bg-[#0e0e1e]">
        {image
          ? <img src={`${API}/celebrity-images/${image}`} alt={name} className="w-full h-full object-cover" style={{ objectPosition: 'center 15%' }} />
          : <div className="w-full h-full flex items-center justify-center"><Star size={12} className="text-violet-400/30"/></div>
        }
      </div>

      {/* name + cat */}
      <div className="flex-1 min-w-0">
        <p className="text-white text-xs font-semibold truncate">{name}</p>
        <p className="text-slate-500 text-[10px]">{category}</p>
      </div>

      {/* score bar */}
      <div className="flex-shrink-0 flex flex-col items-end gap-1 min-w-[56px]">
        <span className="text-xs font-bold text-violet-300">{pct(score)}%</span>
        <div className="w-14 h-1.5 rounded-full bg-white/10 overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: 'linear-gradient(90deg, #7c3aed, #ec4899)' }}
            initial={{ width: 0 }}
            animate={{ width: `${pct(score)}%` }}
            transition={{ duration: 0.8, delay: 0.2 + rank * 0.08, ease: 'easeOut' }}
          />
        </div>
      </div>
    </motion.div>
  )
}

// ─── Vertical Spinning Reel Component ─────────────────────────
const ITEM_HEIGHT = 220

function ReelSpinner({ targetMatch, onComplete }) {
  const [locked, setLocked] = useState(false)

  // strip: 14 random celebrity items ending on the target match
  const strip = useMemo(() => {
    const pool = CELEB_POOL.filter(c => c.name !== targetMatch.name)
    const shuffled = [...pool].sort(() => Math.random() - 0.5).slice(0, 13)
    return [...shuffled, targetMatch]
  }, [targetMatch])

  useEffect(() => {
    // sound ticks that decelerate alongside the animation
    const delays = [0, 80, 160, 240, 330, 430, 550, 690, 850, 1040, 1260, 1510, 1800, 2130, 2450]
    const timers = delays.map((ms, idx) => {
      return setTimeout(() => {
        playReelTick(450 + idx * 22)
      }, ms)
    })
    return () => timers.forEach(t => clearTimeout(t))
  }, [])

  const handleAnimationDone = () => {
    setLocked(true)
    playCelebrationChord()
    setTimeout(() => {
      onComplete()
    }, 750)
  }

  const targetY = -((strip.length - 1) * ITEM_HEIGHT)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      className="flex flex-col items-center justify-center h-full py-4"
    >
      {/* status indicator pill */}
      <div className="flex items-center gap-2 px-3 py-1 rounded-full mb-3 bg-violet-500/15 border border-violet-500/30">
        <Sparkles size={13} className="text-violet-400 animate-spin" />
        <span className="text-[11px] font-bold text-violet-300 tracking-wider uppercase">
          {locked ? 'MATCH IDENTIFIED!' : 'SCANNING DATABASE...'}
        </span>
      </div>

      {/* Reel Slot Frame */}
      <div
        className={`relative w-full rounded-2xl overflow-hidden border-2 transition-all duration-300 ${
          locked
            ? 'border-amber-400 shadow-[0_0_35px_rgba(245,158,11,0.5)]'
            : 'border-violet-500/40 shadow-[0_0_30px_rgba(124,58,237,0.3)]'
        }`}
        style={{ height: ITEM_HEIGHT, background: '#090914' }}
      >
        {/* Moving Reel Strip */}
        <motion.div
          initial={{ y: 0 }}
          animate={{ y: targetY }}
          transition={{
            duration: 2.5,
            ease: [0.12, 0.85, 0.32, 1], // fast spin then smooth realistic mechanical slowdown
          }}
          onAnimationComplete={handleAnimationDone}
          className="flex flex-col"
        >
          {strip.map((c, i) => (
            <div
              key={i}
              className="relative w-full flex-shrink-0 flex items-center justify-center overflow-hidden"
              style={{ height: ITEM_HEIGHT }}
            >
              <img
                src={`${API}/celebrity-images/${c.image}`}
                alt={c.name}
                className="w-full h-full object-cover"
                style={{ objectPosition: 'center 20%' }}
              />
              <div
                className="absolute inset-0"
                style={{
                  background:
                    'linear-gradient(to top, rgba(9,9,15,0.95) 0%, rgba(9,9,15,0.15) 55%, rgba(9,9,15,0.6) 100%)',
                }}
              />
              {/* Celebrity label on reel */}
              <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between">
                <div>
                  <p className="text-white text-base font-bold drop-shadow leading-tight" style={{ fontFamily: 'Syne, sans-serif' }}>
                    {c.name}
                  </p>
                  <span className="text-[10px] text-slate-300 font-medium">
                    {c.category}
                  </span>
                </div>
                {i === strip.length - 1 && locked && (
                  <span className="text-[11px] font-bold text-amber-300 bg-amber-500/25 border border-amber-400/60 px-2.5 py-0.5 rounded-full shadow-lg">
                    {pct(targetMatch.score)}% MATCH
                  </span>
                )}
              </div>
            </div>
          ))}
        </motion.div>

        {/* Cylinder / Vignette Depth Shadows */}
        <div
          className="absolute top-0 left-0 right-0 h-16 pointer-events-none"
          style={{ background: 'linear-gradient(to bottom, rgba(4,4,8,0.9) 0%, transparent 100%)' }}
        />
        <div
          className="absolute bottom-0 left-0 right-0 h-16 pointer-events-none"
          style={{ background: 'linear-gradient(to top, rgba(4,4,8,0.9) 0%, transparent 100%)' }}
        />

        {/* Framing Crosshair Corners */}
        <div className="absolute top-2.5 left-2.5 w-3 h-3 border-t-2 border-l-2 border-violet-400/70 pointer-events-none" />
        <div className="absolute top-2.5 right-2.5 w-3 h-3 border-t-2 border-r-2 border-violet-400/70 pointer-events-none" />
        <div className="absolute bottom-2.5 left-2.5 w-3 h-3 border-b-2 border-l-2 border-violet-400/70 pointer-events-none" />
        <div className="absolute bottom-2.5 right-2.5 w-3 h-3 border-b-2 border-r-2 border-violet-400/70 pointer-events-none" />

        {/* Golden flash when locked */}
        <AnimatePresence>
          {locked && (
            <motion.div
              initial={{ opacity: 0.85 }}
              animate={{ opacity: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
              className="absolute inset-0 bg-amber-200 pointer-events-none"
            />
          )}
        </AnimatePresence>
      </div>

      <p className="text-slate-500 text-[11px] text-center mt-3">
        {locked ? 'Locking in similarity score…' : 'Revolving through facial embeddings…'}
      </p>
    </motion.div>
  )
}

// ─── Results Panel ─────────────────────────────────────────────
function ResultsPanel({ state, matches, error, userSnap, onSpinComplete, onClose, onReset }) {
  return (
    <div className="flex flex-col h-full">
      {/* header */}
      <div className="flex-shrink-0 px-5 pt-4 pb-3 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${state === 'spinning' ? 'bg-amber-400 animate-ping' : state === 'done' ? 'bg-emerald-400' : 'bg-violet-400'}`} />
          <h2 className="text-xs font-bold text-slate-300 uppercase tracking-widest">
            {state === 'done' ? 'Twin Found' : state === 'spinning' ? 'Scanning Stars…' : state === 'processing' ? 'Analyzing Face' : 'Your Matches'}
          </h2>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-full bg-white/10 hover:bg-white/20 active:scale-95 flex items-center justify-center text-slate-300 hover:text-white transition-all"
            aria-label="Close"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* content */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        <AnimatePresence mode="wait">

          {/* idle */}
          {state === 'idle' && (
            <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="h-full flex flex-col items-center justify-center gap-4 text-center py-12">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                style={{ background: 'rgba(124,58,237,0.1)', border: '1px solid rgba(124,58,237,0.2)' }}>
                <Sparkles size={28} className="text-violet-400" />
              </div>
              <div>
                <p className="text-white font-medium mb-1">Snap a photo</p>
                <p className="text-slate-500 text-sm">Your celebrity matches will appear here instantly</p>
              </div>
            </motion.div>
          )}

          {/* processing backend request */}
          {state === 'processing' && (
            <motion.div key="proc" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="h-full flex flex-col items-center justify-center gap-5 py-12">
              <div className="relative">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                  style={{ background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.3)' }}>
                  <Loader2 size={28} className="text-violet-400 animate-spin" />
                </div>
              </div>
              <ProcessingSteps />
            </motion.div>
          )}

          {/* spinning reel animation before reveal */}
          {state === 'spinning' && matches.length > 0 && (
            <ReelSpinner
              key="spinning"
              targetMatch={matches[0]}
              onComplete={onSpinComplete}
            />
          )}

          {/* error */}
          {state === 'error' && (
            <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="h-full flex flex-col items-center justify-center gap-4 text-center py-8">
              <AlertCircle size={36} className="text-red-400" />
              <div>
                <p className="text-red-300 font-medium mb-1">Could not process</p>
                <p className="text-slate-500 text-xs px-4">{error}</p>
              </div>
              {onReset && (
                <button
                  onClick={onReset}
                  className="mt-2 flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold btn-primary active:scale-95 transition-transform"
                >
                  <RefreshCw size={13} /> Try Again
                </button>
              )}
            </motion.div>
          )}

          {/* results */}
          {state === 'done' && matches.length > 0 && (
            <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
              {/* user snap thumbnail */}
              {userSnap && (
                <div className="flex items-center gap-3 mb-1">
                  <img src={userSnap} alt="You" className="w-8 h-8 rounded-full object-cover border-2 border-violet-500/50" />
                  <div>
                    <p className="text-slate-400 text-[11px]">Your photo</p>
                    <p className="text-white text-xs font-medium">vs {matches.length} celebrities</p>
                  </div>
                </div>
              )}

              {/* top match */}
              <TopMatch match={matches[0]} />

              {/* rest */}
              {matches.slice(1).length > 0 && (
                <div>
                  <p className="text-slate-500 text-[10px] uppercase tracking-widest my-2 px-0.5">Other matches</p>
                  <div className="space-y-1.5">
                    {matches.slice(1).map((m, i) => (
                      <CompactMatch key={m.name} match={m} rank={i + 2} />
                    ))}
                  </div>
                </div>
              )}

              {/* Bottom Actions: Share All 5 Matches + Scan Again */}
              <div className="pt-2 space-y-2">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => shareAllMatches(matches)}
                  className="w-full py-3 px-4 rounded-xl bg-[#25D366] hover:bg-[#20bd5a] text-white font-bold text-xs flex items-center justify-center gap-2.5 shadow-lg shadow-emerald-500/25 transition-all"
                >
                  <WhatsAppIcon size={17} /> Share All 5 Matches on WhatsApp
                </motion.button>

                {onReset && (
                  <button
                    onClick={onReset}
                    className="w-full py-2.5 px-4 rounded-xl text-xs font-bold btn-primary flex items-center justify-center gap-2 shadow-md shadow-violet-500/20 active:scale-98 transition-transform"
                  >
                    <Camera size={14} /> Scan Face Again
                  </button>
                )}
              </div>

              <p className="text-slate-600 text-[10px] text-center pt-2 pb-1">
                Based on visual similarity · not identity recognition
              </p>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
  )
}

// ─── Processing steps ticker ───────────────────────────────────
const STEPS = [
  'Detecting your face…',
  'Generating face embedding…',
  'Searching celebrity database…',
  'Finding closest matches…',
]

function ProcessingSteps() {
  const [step, setStep] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setStep(s => (s + 1) % STEPS.length), 900)
    return () => clearInterval(t)
  }, [])
  return (
    <AnimatePresence mode="wait">
      <motion.p
        key={step}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        className="text-slate-400 text-sm text-center"
      >
        {STEPS[step]}
      </motion.p>
    </AnimatePresence>
  )
}

// ─── Camera Panel ──────────────────────────────────────────────
function CameraPanel({ onMatch }) {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [camState, setCamState] = useState('idle')   // idle | live | error
  const [camError, setCamError] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState(0) // 0 to 100
  const [scanCount, setScanCount] = useState(0)       // 0 to 5
  const [scanFlash, setScanFlash] = useState(false)

  const startCamera = async () => {
    setCamError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setCamState('live')
    } catch (err) {
      const msg = err.name === 'NotAllowedError'
        ? 'Camera access denied. Please allow camera access in your browser settings and refresh.'
        : err.name === 'NotFoundError'
        ? 'No camera found on this device.'
        : 'Could not start camera: ' + err.message
      setCamError(msg)
      setCamState('error')
    }
  }

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach(t => t.stop())
    streamRef.current = null
  }, [])

  // auto-start on mount
  useEffect(() => {
    startCamera()
    return stopCamera
  }, [])

  const scanAndMatch = async () => {
    const video = videoRef.current
    if (!video || scanning) return
    setScanning(true)
    setScanProgress(0)

    const TOTAL_SHOTS = 5
    const TOTAL_TIME_MS = 2400
    const INTERVAL_MS = TOTAL_TIME_MS / TOTAL_SHOTS

    const capturedBlobs = []
    let primarySnapUrl = null

    // Play subtle high-tech scanning tone at start
    playReelTick(680)

    // Smooth continuous progress timer from 0% -> 100%
    const startTime = Date.now()
    const progressTimer = setInterval(() => {
      const elapsed = Date.now() - startTime
      const p = Math.min(99, Math.round((elapsed / TOTAL_TIME_MS) * 100))
      setScanProgress(p)
    }, 35)

    // Seamlessly capture frames in background for high-accuracy composite embedding
    for (let i = 0; i < TOTAL_SHOTS; i++) {
      const canvas = document.createElement('canvas')
      canvas.width  = video.videoWidth || 640
      canvas.height = video.videoHeight || 480
      canvas.getContext('2d').drawImage(video, 0, 0)

      const snapUrl = canvas.toDataURL('image/jpeg', 0.92)
      if (i === 0) primarySnapUrl = snapUrl

      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.92))
      capturedBlobs.push(blob)

      if (i < TOTAL_SHOTS - 1) {
        await new Promise(resolve => setTimeout(resolve, INTERVAL_MS))
      }
    }

    clearInterval(progressTimer)
    setScanProgress(100)

    const files = capturedBlobs.map((blob, idx) => new File([blob], `snap_${idx + 1}.jpg`, { type: 'image/jpeg' }))
    await onMatch(files, primarySnapUrl)
    setScanning(false)
  }

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center bg-[#040408]">

      {/* video */}
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        style={{
          display: camState === 'live' ? 'block' : 'none',
          transform: 'scaleX(-1)',  // mirror for selfie
        }}
        autoPlay
        playsInline
        webkit-playsinline="true"
        muted
      />

      {/* idle / loading */}
      {camState === 'idle' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
          <Loader2 size={32} className="text-violet-400 animate-spin" />
          <p className="text-slate-400 text-sm">Starting camera…</p>
        </div>
      )}

      {/* error */}
      {camState === 'error' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-5 px-8 text-center">
          <ZapOff size={36} className="text-red-400" />
          <p className="text-red-300 text-sm leading-relaxed">{camError}</p>
          <button onClick={startCamera} className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium btn-primary">
            <RefreshCw size={14} /> Try Again
          </button>
        </div>
      )}

      {/* dark overlay + face guide (when live) */}
      {camState === 'live' && (
        <>
          {/* subtle vignette */}
          <div className="absolute inset-0 pointer-events-none"
            style={{ background: 'radial-gradient(ellipse 60% 70% at 50% 40%, transparent 40%, rgba(4,4,8,0.6) 100%)' }} />

          {/* face oval guide - responsive with smooth laser scanning beam */}
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center pb-12 sm:pb-8">
            <div
              className={`w-[210px] h-[285px] sm:w-[260px] sm:h-[350px] transition-all duration-300 pointer-events-none relative overflow-hidden ${
                scanning
                  ? 'border-cyan-400 shadow-[0_0_35px_rgba(34,211,238,0.7),0_0_0_2000px_rgba(4,4,8,0.48)]'
                  : 'border-violet-400/70 shadow-[0_0_0_2000px_rgba(4,4,8,0.38)]'
              }`}
              style={{
                borderRadius: '50%',
                borderWidth: '2.5px',
                borderStyle: scanning ? 'solid' : 'dashed',
              }}
            >
              {/* Smooth animated laser scanning beam */}
              {scanning && (
                <motion.div
                  initial={{ top: '5%' }}
                  animate={{ top: ['5%', '92%', '5%'] }}
                  transition={{ duration: 1.1, repeat: Infinity, ease: 'easeInOut' }}
                  className="absolute left-2 right-2 h-1 bg-cyan-300 shadow-[0_0_16px_#22d3ee] rounded-full pointer-events-none"
                />
              )}
            </div>
          </div>

          {/* Top Status Badge */}
          <div className="absolute top-14 sm:top-5 left-0 right-0 flex justify-center pointer-events-none z-20 px-4">
            {scanning ? (
              <motion.div
                initial={{ scale: 0.92, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-950/85 border border-cyan-400/60 backdrop-blur-md shadow-xl shadow-cyan-500/25"
              >
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                <span className="text-cyan-200 text-xs font-bold tracking-wider uppercase">
                  Scanning Face • Stay Still
                </span>
              </motion.div>
            ) : (
              <span className="text-[11px] sm:text-xs text-white/70 bg-black/50 backdrop-blur-md px-3.5 py-1 rounded-full border border-white/10">
                Center your face in the oval
              </span>
            )}
          </div>
        </>
      )}

      {/* Bottom Area: Snap Button or Smooth Scanning Progress HUD */}
      {camState === 'live' && (
        <div className="absolute bottom-6 sm:bottom-8 left-0 right-0 flex flex-col items-center z-20 px-6">
          {scanning ? (
            /* Futuristic Face Scan Progress HUD */
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center gap-2 bg-[#090914]/90 border border-cyan-500/30 backdrop-blur-md px-6 py-3.5 rounded-2xl shadow-2xl w-full max-w-xs"
            >
              <div className="flex items-center justify-between w-full text-xs font-bold">
                <span className="text-cyan-300 flex items-center gap-1.5">
                  <Sparkles size={13} className="animate-spin text-cyan-400" />
                  Scanning Facial Features…
                </span>
                <span className="text-white font-mono text-sm">{scanProgress}%</span>
              </div>

              {/* Smooth Progress Bar */}
              <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{
                    width: `${scanProgress}%`,
                    background: 'linear-gradient(90deg, #22d3ee, #a855f7, #ec4899)'
                  }}
                />
              </div>

              <p className="text-[10px] text-slate-400 text-center font-medium">
                Mapping facial geometry &amp; contours
              </p>
            </motion.div>
          ) : (
            /* Snap Button */
            <div className="flex flex-col items-center gap-2.5">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={scanAndMatch}
                className="relative touch-manipulation"
                aria-label="Scan face and find twin"
              >
                <div className="w-18 h-18 sm:w-20 sm:h-20 rounded-full border-4 border-white/30 flex items-center justify-center">
                  <div className="w-13 h-13 sm:w-14 sm:h-14 rounded-full btn-primary flex items-center justify-center shadow-xl">
                    <Camera size={22} className="text-white" />
                  </div>
                </div>
              </motion.button>
              <p className="text-white/60 text-[11px] sm:text-xs font-medium tracking-wide">
                Scan Face &amp; Find Twin
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── App ───────────────────────────────────────────────────────
export default function App() {
  const [resultState, setResultState] = useState('idle')
  const [matches, setMatches]         = useState([])
  const [matchError, setMatchError]   = useState(null)
  const [userSnap, setUserSnap]       = useState(null)
  const [mobileSheetOpen, setMobileSheetOpen] = useState(false)

  const handleMatch = async (files, snapUrl) => {
    setResultState('processing')
    setUserSnap(snapUrl)
    setMatchError(null)
    setMobileSheetOpen(true) // auto-open bottom sheet on mobile when photo is snapped

    try {
      const form = new FormData()
      if (Array.isArray(files)) {
        files.forEach(f => form.append('files', f))
      } else {
        form.append('files', files)
      }

      const res = await fetch(`${API}/api/match`, { method: 'POST', body: form })
      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Server error')
      }

      setMatches(data.matches ?? [])
      if (data.matches && data.matches.length > 0) {
        setResultState('spinning')
      } else {
        setResultState('done')
      }
    } catch (err) {
      setMatchError(err.message || 'Failed to reach backend. Is it running?')
      setResultState('error')
    }
  }

  const handleReset = () => {
    setResultState('idle')
    setMobileSheetOpen(false)
  }

  return (
    <div className="relative h-[100dvh] w-screen overflow-hidden flex flex-col md:flex-row bg-[#040408]">

      {/* ── Camera View: Full screen on mobile, left column on desktop ── */}
      <div className="relative flex-1 w-full h-full min-w-0">
        <CameraPanel onMatch={handleMatch} />

        {/* logo watermark */}
        <div className="absolute top-4 left-4 flex items-center gap-2 pointer-events-none z-20">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center shadow-lg"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #ec4899)' }}>
            <Sparkles size={14} className="text-white" />
          </div>
          <span className="text-white text-xs font-bold tracking-wide drop-shadow" style={{ fontFamily: 'Syne, sans-serif' }}>
            CelebTwin
          </span>
        </div>

        {/* Mobile floating pill to reopen results if user closed sheet */}
        {matches.length > 0 && !mobileSheetOpen && (
          <motion.button
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            onClick={() => setMobileSheetOpen(true)}
            className="md:hidden absolute top-4 right-4 z-20 flex items-center gap-1.5 px-3 py-1.5 rounded-full glass border border-amber-400/40 text-amber-300 text-xs font-bold shadow-xl active:scale-95 transition-all"
          >
            <Trophy size={13} className="text-amber-400" />
            <span>View Twin ({pct(matches[0].score)}%)</span>
          </motion.button>
        )}
      </div>

      {/* ── Desktop: Right Results Panel ── */}
      <div className="hidden md:flex w-84 lg:w-96 flex-shrink-0 glass flex-col h-full z-10" style={{ borderLeft: '1px solid rgba(255,255,255,0.06)' }}>
        <ResultsPanel
          state={resultState}
          matches={matches}
          error={matchError}
          userSnap={userSnap}
          onSpinComplete={() => setResultState('done')}
          onReset={handleReset}
        />

        {/* footer */}
        <div className="flex-shrink-0 px-5 py-3 border-t border-white/5">
          <div className="flex items-start gap-2">
            <Info size={11} className="text-slate-600 flex-shrink-0 mt-0.5" />
            <p className="text-slate-600 text-[10px] leading-relaxed">
              Results are visual similarity estimates for entertainment. Photos are not stored.
            </p>
          </div>
        </div>
      </div>

      {/* ── Mobile: Smooth Slide-up Bottom Sheet ── */}
      <AnimatePresence>
        {mobileSheetOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => {
                if (resultState === 'done' || resultState === 'error') {
                  setMobileSheetOpen(false)
                }
              }}
              className="md:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-30"
            />

            {/* Bottom Sheet Modal */}
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 28, stiffness: 280 }}
              className="md:hidden fixed inset-x-0 bottom-0 z-40 max-h-[86dvh] bg-[#0b0b16] border-t border-white/10 rounded-t-3xl shadow-2xl flex flex-col overflow-hidden"
            >
              {/* drag handle pill */}
              <div className="w-full flex justify-center pt-2.5 pb-1 flex-shrink-0">
                <div className="w-10 h-1 rounded-full bg-white/25" />
              </div>

              {/* panel content */}
              <div className="flex-1 overflow-hidden flex flex-col">
                <ResultsPanel
                  state={resultState}
                  matches={matches}
                  error={matchError}
                  userSnap={userSnap}
                  onSpinComplete={() => setResultState('done')}
                  onClose={() => setMobileSheetOpen(false)}
                  onReset={handleReset}
                />
              </div>

              {/* mobile footer */}
              <div className="flex-shrink-0 px-5 py-2.5 bg-black/40 border-t border-white/5">
                <p className="text-slate-600 text-[9px] text-center">
                  Visual similarity estimate · Photos are not stored
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
