import { motion } from 'framer-motion'
import { Trophy, Star } from 'lucide-react'

const RANK_COLORS = [
  'from-amber-400 to-orange-400',   // #1
  'from-slate-300 to-slate-400',     // #2
  'from-amber-600 to-yellow-700',    // #3
  'from-violet-400 to-violet-500',   // #4
  'from-violet-400 to-violet-500',   // #5
]

export default function MatchCard({ match, rank, isMain = false, delay = 0 }) {
  const { name, category, score, image } = match
  const scorePercent = Math.round(score * 100)

  if (isMain) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay, duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
        className="relative rounded-3xl overflow-hidden group card-hover"
        style={{
          background: 'linear-gradient(135deg, rgba(124,58,237,0.15) 0%, rgba(236,72,153,0.1) 100%)',
          border: '1px solid rgba(124,58,237,0.3)',
        }}
      >
        {/* Rank badge */}
        <div className="absolute top-4 left-4 z-10 flex items-center gap-1.5 bg-amber-400/20 backdrop-blur-sm border border-amber-400/40 px-3 py-1.5 rounded-full">
          <Trophy size={13} className="text-amber-400" />
          <span className="text-amber-300 text-xs font-bold">#1 Match</span>
        </div>

        {/* Image */}
        <div className="relative h-72 overflow-hidden">
          {image ? (
            <img
              src={`/api/celebrity-image/${image}`}
              alt={name}
              className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-500"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-violet-900/50 to-pink-900/50">
              <Star size={48} className="text-violet-400/50" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
        </div>

        {/* Info */}
        <div className="p-5">
          <div className="flex items-end justify-between">
            <div>
              <h3 className="text-xl font-bold text-white">{name}</h3>
              <p className="text-violet-300 text-sm mt-0.5">{category}</p>
            </div>
            {/* Score ring */}
            <div className="flex flex-col items-center">
              <div className="relative w-16 h-16">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 64 64">
                  <circle cx="32" cy="32" r="26" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="4" />
                  <motion.circle
                    cx="32" cy="32" r="26"
                    fill="none"
                    stroke="url(#scoreGrad)"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={`${2 * Math.PI * 26}`}
                    initial={{ strokeDashoffset: 2 * Math.PI * 26 }}
                    animate={{ strokeDashoffset: 2 * Math.PI * 26 * (1 - score) }}
                    transition={{ delay: delay + 0.3, duration: 1, ease: 'easeOut' }}
                  />
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor="#a855f7" />
                      <stop offset="100%" stopColor="#ec4899" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-white font-bold text-lg leading-none">{scorePercent}</span>
                  <span className="text-slate-400 text-[9px]">match</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    )
  }

  // Compact card for #2–#5
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="flex items-center gap-4 p-4 rounded-2xl card-hover cursor-default"
      style={{
        background: 'rgba(14,20,32,0.7)',
        border: '1px solid rgba(30,42,69,0.8)',
      }}
    >
      {/* Rank */}
      <div className={`w-8 h-8 rounded-xl bg-gradient-to-br ${RANK_COLORS[rank - 1]} flex items-center justify-center flex-shrink-0`}>
        <span className="text-white font-bold text-xs">#{rank}</span>
      </div>

      {/* Avatar */}
      <div className="w-12 h-12 rounded-xl overflow-hidden flex-shrink-0 bg-violet-900/40">
        {image ? (
          <img
            src={`/api/celebrity-image/${image}`}
            alt={name}
            className="w-full h-full object-cover object-top"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Star size={16} className="text-violet-400/50" />
          </div>
        )}
      </div>

      {/* Name + category */}
      <div className="flex-1 min-w-0">
        <p className="text-white font-semibold text-sm truncate">{name}</p>
        <p className="text-slate-500 text-xs">{category}</p>
      </div>

      {/* Score */}
      <div className="flex-shrink-0 text-right">
        <div className="text-lg font-bold gradient-text">{scorePercent}</div>
        <div className="text-slate-500 text-[10px]">match</div>
      </div>
    </motion.div>
  )
}
