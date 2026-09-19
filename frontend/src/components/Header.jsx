import { Sparkles, Star } from 'lucide-react'
import { motion } from 'framer-motion'
import { Link, useLocation } from 'react-router-dom'

export default function Header() {
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <motion.header
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="fixed top-0 left-0 right-0 z-50 glass"
      style={{ borderBottom: '1px solid rgba(124,58,237,0.15)', borderLeft: 'none', borderRight: 'none', borderTop: 'none' }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-gradient-to-br from-violet-600 to-pink-500 shadow-lg group-hover:shadow-violet-500/40 transition-shadow">
              <Sparkles size={18} className="text-white" />
            </div>
            <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-amber-400 border-2 border-[#080b14]" />
          </div>
          <div className="leading-none">
            <span className="font-display text-base font-700 text-white tracking-tight"
              style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700 }}>
              Celebrity
            </span>
            <span className="font-display text-base gradient-text ml-1"
              style={{ fontFamily: 'Syne, sans-serif', fontWeight: 800 }}>
              Doppelgänger
            </span>
          </div>
        </Link>

        {/* Nav items */}
        <nav className="flex items-center gap-2">
          <a
            href="#how-it-works"
            className="hidden sm:flex items-center gap-1.5 text-sm text-slate-400 hover:text-white px-3 py-1.5 rounded-lg hover:bg-white/5 transition-all"
          >
            How it works
          </a>
          <Link
            to="/"
            className="flex items-center gap-1.5 text-sm font-medium px-4 py-2 rounded-xl text-white btn-shimmer"
          >
            <Star size={14} />
            Try Now
          </Link>
        </nav>
      </div>
    </motion.header>
  )
}
