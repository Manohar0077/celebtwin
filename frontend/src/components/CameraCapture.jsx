import { useRef, useState, useCallback } from 'react'
import { Camera, X, RefreshCw, Check, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function CameraCapture({ onImageReady }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)

  const [phase, setPhase] = useState('idle') // idle | active | captured | error
  const [capturedSrc, setCapturedSrc] = useState(null)
  const [permissionError, setPermissionError] = useState(null)

  const startCamera = async () => {
    setPermissionError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setPhase('active')
    } catch (err) {
      const msg =
        err.name === 'NotAllowedError'
          ? 'Camera access was denied. Please allow camera access in your browser settings.'
          : err.name === 'NotFoundError'
          ? 'No camera found on this device.'
          : 'Could not start camera. Please try uploading a photo instead.'
      setPermissionError(msg)
      setPhase('error')
    }
  }

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }, [])

  const capturePhoto = () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)

    canvas.toBlob((blob) => {
      if (!blob) return
      const url = URL.createObjectURL(blob)
      setCapturedSrc(url)
      setPhase('captured')
      stopCamera()
      const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' })
      onImageReady?.(file)
    }, 'image/jpeg', 0.95)
  }

  const retake = () => {
    if (capturedSrc) URL.revokeObjectURL(capturedSrc)
    setCapturedSrc(null)
    onImageReady?.(null)
    setPhase('idle')
  }

  const cancel = () => {
    stopCamera()
    if (capturedSrc) URL.revokeObjectURL(capturedSrc)
    setCapturedSrc(null)
    setPhase('idle')
    onImageReady?.(null)
  }

  return (
    <div className="w-full">
      <canvas ref={canvasRef} className="hidden" />

      <AnimatePresence mode="wait">
        {/* Idle */}
        {phase === 'idle' && (
          <motion.div
            key="idle"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="w-full h-52 rounded-2xl border-2 border-dashed border-white/15 flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-violet-500/50 hover:bg-white/3 transition-all duration-300"
            onClick={startCamera}
          >
            <div className="w-14 h-14 rounded-2xl bg-violet-500/15 border border-violet-500/30 flex items-center justify-center">
              <Camera size={24} className="text-violet-400" />
            </div>
            <div className="text-center">
              <p className="text-white font-medium text-sm">Use your webcam</p>
              <p className="text-slate-500 text-xs mt-1">Click to start camera</p>
            </div>
          </motion.div>
        )}

        {/* Active */}
        {phase === 'active' && (
          <motion.div
            key="active"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="relative rounded-2xl overflow-hidden"
          >
            <video
              ref={videoRef}
              className="w-full h-64 object-cover"
              playsInline
              muted
            />
            {/* Face guide overlay */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="w-36 h-44 rounded-[50%] border-2 border-white/40 border-dashed" />
            </div>
            {/* Controls */}
            <div className="absolute bottom-4 left-0 right-0 flex items-center justify-center gap-4">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={cancel}
                className="w-10 h-10 rounded-full bg-black/60 backdrop-blur-sm border border-white/20 flex items-center justify-center text-white hover:bg-red-500/70 transition-colors"
              >
                <X size={16} />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={capturePhoto}
                className="w-16 h-16 rounded-full border-4 border-white/80 bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 transition-colors shadow-xl"
              >
                <div className="w-10 h-10 rounded-full bg-white" />
              </motion.button>
              <div className="w-10" /> {/* spacer */}
            </div>
            {/* Hint */}
            <div className="absolute top-3 left-0 right-0 flex justify-center">
              <span className="text-xs text-white/70 bg-black/40 backdrop-blur-sm px-3 py-1 rounded-full">
                Center your face in the oval
              </span>
            </div>
          </motion.div>
        )}

        {/* Captured */}
        {phase === 'captured' && capturedSrc && (
          <motion.div
            key="captured"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="relative rounded-2xl overflow-hidden group"
          >
            <img src={capturedSrc} alt="Captured" className="w-full h-64 object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
            <div className="absolute bottom-4 left-0 right-0 flex items-center justify-center gap-3">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={retake}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-black/60 backdrop-blur-sm border border-white/20 text-white text-sm hover:bg-white/10 transition-colors"
              >
                <RefreshCw size={14} /> Retake
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600/80 backdrop-blur-sm border border-violet-500/50 text-white text-sm hover:bg-violet-500/80 transition-colors"
              >
                <Check size={14} /> Use this
              </motion.button>
            </div>
          </motion.div>
        )}

        {/* Error */}
        {phase === 'error' && (
          <motion.div
            key="error"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full h-52 rounded-2xl border border-red-500/20 bg-red-500/5 flex flex-col items-center justify-center gap-3 px-6 text-center"
          >
            <AlertCircle size={28} className="text-red-400" />
            <p className="text-sm text-red-300">{permissionError}</p>
            <button
              onClick={() => setPhase('idle')}
              className="text-xs text-slate-400 hover:text-white underline mt-1 transition-colors"
            >
              Try again
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
