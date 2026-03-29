import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AgroLidar Live Demo',
  description: 'Interactive LiDAR perception system demonstration',
}

export default function DemoPage() {
  return (
    <main style={{ width: '100vw', height: '100vh', overflow: 'hidden', background: '#030508' }}>
      <iframe
        src="/lidar-demo.html"
        style={{ width: '100%', height: '100%', border: 'none' }}
        title="AgroLidar Interactive Demo"
      />
    </main>
  )
}
