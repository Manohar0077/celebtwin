import { useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Share2, Download, RefreshCw } from 'lucide-react'
import MatchGrid from '../components/MatchGrid'

export default function Results() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state || {}
  const { matches = [], userPhotoUrl = null } = state

  if (!matches.length) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 pt-20">
        <p className="text-slate-400 text-lg">No results found.</p>
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl btn-shimmer text-white font-medium"
        >
          <ArrowLeft size={16} />
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen pt-24 pb-20 px-4">
      <div className="max-w-md mx-auto">
        {/* Back */}
        <motion.button
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-6 transition-colors"
        >
          <ArrowLeft size={16} />
          Try another photo
        </motion.button>

        {/* User photo */}
        {userPhotoUrl && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-6 text-center"
          >
            <p className="text-slate-500 text-xs uppercase tracking-widest mb-3">Your Photo</p>
            <img
              src={userPhotoUrl}
              alt="Your photo"
              className="w-24 h-24 rounded-full object-cover mx-auto border-2 border-violet-500/50 shadow-lg"
              style={{ boxShadow: '0 0 30px rgba(124,58,237,0.4)' }}
            />
          </motion.div>
        )}

        {/* Results */}
        <MatchGrid matches={matches} />

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="flex gap-3 mt-8"
        >
          <button
            onClick={() => navigate('/')}
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl text-slate-300 text-sm font-medium hover:text-white transition-all"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
          >
            <RefreshCw size={15} />
            Try Again
          </button>
          <button
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl text-white text-sm font-semibold btn-shimmer"
          >
            <Share2 size={15} />
            Share Result
          </button>
        </motion.div>

        <p className="mt-6 text-center text-slate-600 text-[11px] leading-relaxed">
          Results are based on visual similarity estimates and are intended for entertainment purposes.
        </p>
      </div>
    </div>
  )
}
