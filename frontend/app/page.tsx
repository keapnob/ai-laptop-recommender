'use client'

import { useState } from 'react'

interface Laptop {
  name: string
  price: number
  specs: string
  image_url: string  // We added this earlier!
  match_score: number
}

export default function Home() {
  const [query, setQuery] = useState('')
  const [price, setPrice] = useState(35000)
  const [laptops, setLaptops] = useState<Laptop[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  async function handleSearch() {
    if (!query) return
    setLoading(true)
    setSearched(true)
    setLaptops([])

    try {
      // Connect to your Python Backend
      const res = await fetch(`http://127.0.0.1:8000/search?query=${query}&max_price=${price}`)
      const data = await res.json()
      setLaptops(data.results)
    } catch (error) {
      console.error("Failed to fetch:", error)
      alert("Error connecting to server. Make sure backend is running!")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#0f172a] text-white font-sans selection:bg-blue-500 selection:text-white">
      <div className="max-w-6xl mx-auto p-8">
        
        {/* HEADER */}
        <div className="text-center mb-12 pt-10">
          <h1 className="text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 mb-4 tracking-tight">
            AI Laptop Recommender
          </h1>
          <p className="text-slate-400 text-xl max-w-2xl mx-auto">
            Tell our AI what you need (e.g. "coding and light gaming"), and we'll find the perfect match from NotebookSpec.
          </p>
        </div>

        {/* SEARCH SECTION */}
        <div className="bg-slate-800/50 backdrop-blur-lg p-8 rounded-3xl shadow-2xl border border-slate-700 mb-12">
          <div className="flex flex-col md:flex-row gap-4">
            <input 
              type="text" 
              placeholder="What will you use this laptop for?" 
              className="flex-1 bg-slate-900 text-white p-5 rounded-2xl border border-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none text-lg transition-all placeholder:text-slate-600"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button 
              onClick={handleSearch}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 px-10 rounded-2xl transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-600/20"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Thinking...
                </div>
              ) : "Find Laptops"}
            </button>
          </div>
          
          {/* SLIDER */}
          <div className="mt-8 px-2">
            <div className="flex justify-between text-slate-400 mb-2">
              <span>Max Budget</span>
              <span className="text-blue-400 font-mono font-bold">฿{price.toLocaleString()}</span>
            </div>
            <input 
              type="range" 
              min="10000" 
              max="100000" 
              step="1000" 
              value={price}
              onChange={(e) => setPrice(Number(e.target.value))}
              className="w-full h-3 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500 hover:accent-blue-400 transition-all"
            />
          </div>
        </div>

        {/* RESULTS GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {laptops.map((laptop, index) => (
            <div key={index} className="group bg-slate-800 rounded-3xl border border-slate-700 hover:border-blue-500/50 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:shadow-blue-500/10 overflow-hidden flex flex-col">
              
              {/* IMAGE AREA */}
              <div className="h-56 bg-white p-6 flex items-center justify-center relative overflow-hidden">
                 {/* Match Badge */}
                <div className="absolute top-4 right-4 bg-green-500/90 backdrop-blur text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg z-10">
                  {laptop.match_score}% MATCH
                </div>
                
                <img 
                  src={laptop.image_url} 
                  alt={laptop.name}
                  className="max-h-full w-auto object-contain group-hover:scale-110 transition-transform duration-500"
                />
              </div>

              {/* CONTENT AREA */}
              <div className="p-6 flex-1 flex flex-col">
                <h2 className="text-lg font-bold text-white leading-tight mb-2 line-clamp-2 h-14">
                  {laptop.name}
                </h2>
                
                <p className="text-3xl font-bold text-blue-400 mb-4 font-mono">
                  ฿{laptop.price.toLocaleString()}
                </p>
                
                <div className="bg-slate-900/50 rounded-xl p-4 mb-6 flex-1">
                  <p className="text-slate-400 text-sm leading-relaxed line-clamp-4">
                    {laptop.specs}
                  </p>
                </div>

                {/* GOOGLE SEARCH LINK */}
                <a 
                  href={`https://www.google.com/search?q=${encodeURIComponent(laptop.name + " NotebookSpec")}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full block text-center bg-slate-700 hover:bg-white hover:text-slate-900 text-white font-semibold py-3 rounded-xl transition-colors"
                >
                  View Details ↗
                </a>
              </div>
            </div>
          ))}
        </div>

        {/* EMPTY STATE */}
        {!loading && searched && laptops.length === 0 && (
          <div className="text-center py-24 opacity-50">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-2xl font-bold text-white mb-2">No laptops found</h3>
            <p className="text-slate-400">Try increasing your budget or changing your search terms.</p>
          </div>
        )}

      </div>
    </main>
  )
}