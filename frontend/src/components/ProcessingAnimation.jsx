import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Scan, Brain, Search, Star, Sparkles } from 'lucide-react'

const STAGES = [
  { icon: Scan,     label: 'Detecting your face…',          duration: 1500 },
  { icon: Brain,    label: 'Creating face embedding…',       duration: 1800 },
  { icon: Search,   label: 'Searching celebrity database…',  duration: 2000 },
  { icon: Star,     label: 'Finding your closest matches…',  duration: 1600 },
  { icon: Sparkles, label: 'Preparing your results…',        duration: 1000 },
]

export default function ProcessingAnimation({ isVisible }) {
  const [stageIndex, setStageIndex] = useState(0)

  useEffect(() => {
    if (!isVisible) {
      setStageIndex(0)
      return
    }

    let idx = 0
    const advance = () => {
      idx++
      if (idx < STAGES.length) {
        setStageIndex(idx)
        timers.push(setTimeout(advance, STAGES[idx].duration))
      }
    }

    const timers = [setTimeout(advance, STAGES[0].duration)]
    return () => timers.forEach(clearTimeout)
  }, [isVisible])

  const stage = STAGES[stageIndex]
  const Icon = stage.icon
  const progress = ((stageIndex + 1) / STAGES.length) * 100

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: 'rgba(8,11,20,0.92)', backdropFilter: 'blur(12px)' }}
        >
          <div className="flex flex-col items-center gap-8 px-6 max-w-sm w-full">
            {/* Pulsing icon ring */}
            <div className="relative">
              {/* Outer rings */}
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="absolute inset-0 rounded-full border border-violet-500/30"
                  animate={{ scale: [1, 1.5 + i * 0.3], opacity: [0.6, 0] }}
                  transition={{ duration: 2, repeat: Infinity, delay: i * 0.5, ease: 'easeOut' }}
                  style={{ margin: `-${i * 16}px` }}
                />
              ))}
              {/* Center icon */}
              <motion.div
                key={stageIndex}
                initial={{ scale: 0.5, opacity: 0, rotate: -20 }}
                animate={{ scale: 1, opacity: 1, rotate: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                className="relative w-20 h-20 rounded-3xl bg-gradient-to-br from-violet-600 to-pink-500 flex items-center justify-center shadow-2xl"
                style={{ boxShadow: '0 0 40px rgba(124,58,237,0.6)' }}
              >
                <Icon size={32} className="text-white" />
              </motion.div>
            </div>

            {/* Stage label */}
            <AnimatePresence mode="wait">
              <motion.p
                key={stageIndex}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.4 }}
                className="text-center text-white text-lg font-medium"
              >
                {stage.label}
              </motion.p>
            </AnimatePresence>

            {/* Progress bar */}
            <div className="w-full">
              <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-violet-500 to-pink-500"
                  initial={{ width: '0%' }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.6, ease: 'easeInOut' }}
                />
              </div>
              <div className="flex justify-between mt-2">
                {STAGES.map((s, i) => (
                  <motion.div
                    key={i}
                    className={`w-1.5 h-1.5 rounded-full transition-colors duration-300 ${
                      i <= stageIndex ? 'bg-violet-400' : 'bg-white/15'
                    }`}
                  />
                ))}
              </div>
            </div>

            <p className="text-slate-500 text-xs text-center">
              Using visual similarity — not identity recognition
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
