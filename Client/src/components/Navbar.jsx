export default function Navbar() {
  return (
    <nav className="flex justify-between items-center p-5 bg-[#0B1120]/80 backdrop-blur-sm border-b border-gray-800">
      <h1 className="text-xl font-bold text-blue-400">SpeakFlow</h1>

      <div className="hidden md:flex gap-6">
        <a href="#features" className="hover:text-blue-400 transition">Features</a>
        <a href="#demo" className="hover:text-blue-400 transition">Demo</a>
        <a href="#integrations" className="hover:text-blue-400 transition">Integrations</a>
      </div>

      <button className="bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded transition">
        Start Demo
      </button>
    </nav>
  )
}