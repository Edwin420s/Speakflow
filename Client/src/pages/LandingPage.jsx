import Navbar from '../components/Navbar'

export default function LandingPage({ onStartDemo }) {
  return (
    <div className="min-h-screen bg-[#0B1120] text-white">
      <Navbar />

      {/* Hero */}
      <section className="text-center py-32 px-6">
        <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          Turn Conversations Into Actions
        </h1>
        <p className="text-xl text-gray-300 mb-10 max-w-2xl mx-auto">
          SpeakFlow listens to meetings and automatically creates tasks in Trello 
          and sends WhatsApp follow‑ups.
        </p>
        <button
          onClick={onStartDemo}
          className="bg-gradient-to-r from-blue-500 to-cyan-400 px-8 py-4 rounded-lg text-lg font-semibold hover:scale-105 transition-transform"
        >
          Try Live Demo
        </button>
      </section>

      {/* How it works */}
      <section className="py-20 text-center bg-[#111827]">
        <h2 className="text-3xl font-bold mb-12">How It Works</h2>
        <div className="grid md:grid-cols-4 gap-8 px-4 md:px-20">
          <div className="p-6">
            <div className="text-4xl mb-4">🎤</div>
            <h3 className="text-blue-400 text-xl font-semibold mb-2">1. Speak</h3>
            <p className="text-gray-400">Capture conversations in meetings</p>
          </div>
          <div className="p-6">
            <div className="text-4xl mb-4">🧠</div>
            <h3 className="text-blue-400 text-xl font-semibold mb-2">2. AI Understands</h3>
            <p className="text-gray-400">Extract tasks and decisions</p>
          </div>
          <div className="p-6">
            <div className="text-4xl mb-4">📋</div>
            <h3 className="text-blue-400 text-xl font-semibold mb-2">3. Tasks Created</h3>
            <p className="text-gray-400">Added to Trello or Notion</p>
          </div>
          <div className="p-6">
            <div className="text-4xl mb-4">💬</div>
            <h3 className="text-blue-400 text-xl font-semibold mb-2">4. Follow‑ups Sent</h3>
            <p className="text-gray-400">WhatsApp summaries automatically sent</p>
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="py-20 text-center">
        <h2 className="text-3xl font-bold mb-8">Integrations</h2>
        <div className="flex justify-center gap-12 flex-wrap">
          <div className="flex items-center gap-2 bg-[#1E293B] px-6 py-3 rounded-full">
            <span className="text-2xl">📱</span> WhatsApp
          </div>
          <div className="flex items-center gap-2 bg-[#1E293B] px-6 py-3 rounded-full">
            <span className="text-2xl">📌</span> Trello
          </div>
          <div className="flex items-center gap-2 bg-[#1E293B] px-6 py-3 rounded-full">
            <span className="text-2xl">📓</span> Notion
          </div>
        </div>
      </section>
    </div>
  )
}