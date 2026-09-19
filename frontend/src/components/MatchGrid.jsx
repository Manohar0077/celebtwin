import { motion } from 'framer-motion'
import MatchCard from './MatchCard'

export default function MatchGrid({ matches }) {
  if (!matches || matches.length === 0) return null

  const [top, ...rest] = matches

  return (
    <div className="w-full max-w-md mx-auto space-y-6">
      {/* #1 Main match */}
      <div>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-slate-400 text-xs uppercase tracking-widest mb-3 font-medium"
        >
          Your Celebrity Twin
        </motion.p>
        <MatchCard match={top} rank={1} isMain delay={0.1} />
      </div>

      {/* #2–5 */}
      {rest.length > 0 && (
        <div>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-slate-400 text-xs uppercase tracking-widest mb-3 font-medium"
          >
            Other Matches
          </motion.p>
          <div className="space-y-2">
            {rest.map((match, i) => (
              <MatchCard key={match.name} match={match} rank={i + 2} delay={0.5 + i * 0.1} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
