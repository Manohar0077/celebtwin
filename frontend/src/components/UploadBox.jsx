import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, ImagePlus, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const MAX_SIZE_MB = 10
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024
const ACCEPTED_TYPES = { 'image/jpeg': ['.jpg', '.jpeg'], 'image/png': ['.png'] }

export default function UploadBox({ onImageReady }) {
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState(null)

  const handleFile = (file) => {
    setError(null)
    if (!file) return
    if (file.size > MAX_SIZE_BYTES) {
      setError(`File too large. Maximum size is ${MAX_SIZE_MB} MB.`)
      return
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    onImageReady?.(file)
  }

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      const err = rejectedFiles[0].errors[0]
      if (err.code === 'file-too-large') setError(`File too large. Max ${MAX_SIZE_MB} MB.`)
      else if (err.code === 'file-invalid-type') setError('Invalid file type. Please upload JPG or PNG.')
      else setError('Could not read file.')
      return
    }
    handleFile(acceptedFiles[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE_BYTES,
    multiple: false,
  })

  const clearImage = (e) => {
    e.stopPropagation()
    if (preview) URL.revokeObjectURL(preview)
    setPreview(null)
    setError(null)
    onImageReady?.(null)
  }

  return (
    <div className="w-full">
      <AnimatePresence mode="wait">
        {preview ? (
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="relative rounded-2xl overflow-hidden group"
          >
            <img
              src={preview}
              alt="Your photo"
              className="w-full h-64 object-cover"
            />
            {/* Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
            {/* Remove button */}
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={clearImage}
              className="absolute top-3 right-3 w-9 h-9 rounded-full bg-black/60 backdrop-blur-sm border border-white/20 flex items-center justify-center text-white hover:bg-red-500/80 transition-colors"
              aria-label="Remove photo"
            >
              <X size={16} />
            </motion.button>
            {/* Label */}
            <div className="absolute bottom-3 left-3 flex items-center gap-2 text-sm text-white/80">
              <ImagePlus size={14} />
              <span>Looking good!</span>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            {...getRootProps()}
            className={`relative w-full h-52 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-300 flex flex-col items-center justify-center gap-3
              ${isDragActive
                ? 'border-violet-400 bg-violet-500/10 scale-[1.01]'
                : 'border-white/15 hover:border-violet-500/50 hover:bg-white/3'
              }`}
          >
            <input {...getInputProps()} />
            <motion.div
              animate={isDragActive ? { scale: 1.2, rotate: 5 } : { scale: 1, rotate: 0 }}
              className="w-14 h-14 rounded-2xl bg-violet-500/15 border border-violet-500/30 flex items-center justify-center"
            >
              <Upload size={24} className="text-violet-400" />
            </motion.div>
            <div className="text-center px-4">
              <p className="text-white font-medium text-sm">
                {isDragActive ? 'Drop it here!' : 'Drop your photo here'}
              </p>
              <p className="text-slate-500 text-xs mt-1">
                or <span className="text-violet-400 font-medium">browse files</span> · JPG, PNG up to {MAX_SIZE_MB} MB
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-3 flex items-center gap-2 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2.5"
          >
            <AlertCircle size={14} className="flex-shrink-0" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
