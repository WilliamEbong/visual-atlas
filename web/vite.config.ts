import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// `--mode demo` builds the read-only public demo from web/public-demo (made by scripts/build_demo.py).
export default defineConfig(({ mode }) => ({
  plugins: [react()], base: './', server: { host: '127.0.0.1' },
  publicDir: mode === 'demo' ? 'public-demo' : 'public',
}))
