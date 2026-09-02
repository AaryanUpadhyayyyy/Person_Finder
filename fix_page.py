import re

with open('frontend/src/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the last closing brace
last_brace_index = content.rfind('}')

verified_block = '''
  // -------------------------------------------
  // --- STATE: VERIFIED — Final Dashboard ---
  // -------------------------------------------
  if (appState === 'verified' && results) {
    const bestMatch = results.candidates.length > 0 ? results.candidates[0] : null;

    return (
      <main className="h-screen w-screen bg-[#020202] flex items-center justify-center p-2 md:p-6 overflow-hidden relative"
        style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '30px 30px' }}>
        
        <div className="relative w-full h-full border border-[#222222] rounded-2xl bg-[#000000] overflow-hidden flex shadow-[0_0_80px_rgba(0,0,0,0.8)]">
          
          {/* GLOBE BACKGROUND (Z-0) */}
          <Suspense fallback={null}>
            <EarthGlobe />
          </Suspense>

          {/* TELEMETRY OVERLAYS */}
          <div className="absolute top-6 left-6 z-20 flex items-center gap-3 pointer-events-none">
            <div className="w-6 h-6 rounded-full border border-[#FF1111] flex items-center justify-center">
              <Crosshair size={12} className="text-[#FF1111]" />
            </div>
            <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[16px] font-bold tracking-[0.25em] text-[#FFFFFF]">TALAASH</span>
          </div>

          <div className="absolute top-6 right-6 z-20 flex items-center gap-4 pointer-events-auto">
            <button 
              onClick={() => window.print()}
              className="flex items-center gap-2 px-4 py-2 border border-[#333333] hover:border-[#FFFFFF] bg-[#0A0A0A]/90 text-[#FFFFFF] rounded-sm transition-colors backdrop-blur-md"
            >
              <Printer size={12} />
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-wider font-bold">EXPORT</span>
            </button>
            <button 
              onClick={() => { setAppState('idle'); setResults(null); setSelectedFile(null); setPreviewUrl(''); }}
              className="flex items-center gap-2 px-4 py-2 bg-[#FF1111] text-[#FFFFFF] font-bold rounded-sm hover:bg-[#CC0000] transition-colors"
            >
              <ScanFace size={12} />
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-wider">NEW SCAN</span>
            </button>
          </div>

          <div className="absolute bottom-6 left-6 z-20 pointer-events-none flex items-center gap-4">
            <div className="w-10 h-10 rounded-full border border-[#333333] bg-[#0A0A0A]/90 backdrop-blur-md flex items-center justify-center text-[#777777]">
              <Compass size={18} />
            </div>
            <div className="flex flex-col gap-1">
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#777777] tracking-[0.15em] uppercase">LOC: GLOBAL COORDS</span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#777777] tracking-[0.15em] uppercase">REF: GEO-TRACK-GLB-8472</span>
            </div>
          </div>

          {/* LEFT PANEL: VERDICT & INTELLIGENCE (Z-20) */}
          <div className="absolute top-24 bottom-24 left-6 w-[420px] flex flex-col gap-4 pointer-events-auto z-20">
            
            {/* 1. VERDICT CARD */}
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm flex flex-col shadow-2xl">
              <div className="px-5 py-3 border-b border-[#222222] flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#FFFFFF]" />
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">FINAL VERDICT</span>
              </div>
              <div className="p-5">
                <div className="flex items-center justify-between mb-6">
                  {/* Images */}
                  <div className="flex items-center gap-3">
                    <div className="w-16 h-16 border border-[#333333] rounded-sm overflow-hidden bg-black">
                      <img src={previewUrl || ''} className="w-full h-full object-cover" alt="Target" />
                    </div>
                    <div className="w-4 h-[1px] bg-[#333333]" />
                    <div className="w-16 h-16 border border-[#333333] rounded-sm overflow-hidden bg-black">
                      {bestMatch?.thumbnail ? (
                        <img src={bestMatch.thumbnail} className="w-full h-full object-cover" alt="Match" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center"><User size={20} className="text-[#333333]" /></div>
                      )}
                    </div>
                  </div>
                  {/* Score */}
                  <div className="text-right">
                    <div style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[32px] font-bold text-[#FFFFFF] leading-none">
                      {(results.best_score || 0).toFixed(2)}
                    </div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[8px] tracking-[0.15em] text-[#777777] mt-1 uppercase">MATCH CONFIDENCE</div>
                  </div>
                </div>

                {/* Status */}
                <div className="flex flex-col">
                  <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[18px] font-bold text-[#FFFFFF] tracking-wide shadow-[0_0_10px_rgba(255,255,255,0.2)]">
                    {results.passed ? "IDENTITY VERIFIED" : "NO MATCH FOUND"}
                  </span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[11px] text-[#777777] mt-1">
                    Match confirmed on <span className="text-[#FF1111] font-bold">{bestMatch?.source || "N/A"}</span>
                  </span>
                </div>
              </div>
            </div>

            {/* 2. INTELLIGENCE BRIEF CARD */}
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm flex flex-col flex-1 min-h-0 shadow-2xl">
              <div className="px-5 py-3 border-b border-[#222222] flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#FF1111]" />
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">INTELLIGENCE BRIEF</span>
              </div>
              <div className="p-5 overflow-y-auto custom-scrollbar flex-1">
                {results.llm_context && results.llm_context !== "N/A" ? (
                  <div className="text-[11px] text-[#AAAAAA] leading-[1.8] font-['Inter'] whitespace-pre-wrap">
                    {results.llm_context.split('\\n').map((line, i) => (
                      <p key={i} className="mb-3 last:mb-0" dangerouslySetInnerHTML={{__html: line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-bold">1</strong>')}} />
                    ))}
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center flex-col gap-3 opacity-50">
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#555555] tracking-widest">NO ADDITIONAL INTEL</span>
                  </div>
                )}
              </div>
            </div>
            
          </div>

          {/* RIGHT PANEL: MATCH CANDIDATES (Z-20) */}
          <div className="absolute top-24 bottom-24 right-6 w-[450px] flex flex-col z-20 pointer-events-auto">
            
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm flex flex-col h-full shadow-2xl overflow-hidden">
              <div className="px-5 py-3 border-b border-[#222222] flex items-center justify-between bg-[#050505]">
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">MATCH CANDIDATES</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#FF1111]">{results.candidates.length} RESULTS</span>
              </div>
              
              <div className="flex-1 overflow-y-auto custom-scrollbar">
                {results.candidates.map((candidate, i) => (
                  <div key={i} className="flex gap-4 p-4 border-b border-[#1A1A1A] hover:bg-[#111111] transition-colors group">
                    {/* Thumb */}
                    <div className="w-14 h-14 bg-[#000000] border border-[#333333] rounded-sm flex-shrink-0 overflow-hidden">
                      {candidate.thumbnail ? (
                        <img src={candidate.thumbnail} className="w-full h-full object-cover" alt="Thumb" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center"><User size={16} className="text-[#333333]" /></div>
                      )}
                    </div>

                    {/* Details */}
                    <div className="flex-1 flex flex-col justify-between py-0.5">
                      <div className="flex items-start justify-between">
                        <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[11px] font-bold text-[#FFFFFF]">{candidate.source}</span>
                        <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[12px] font-bold text-[#FF1111]">{(candidate.score || 0).toFixed(2)}</span>
                      </div>
                      
                      <p className="text-[10px] text-[#777777] font-['Inter'] line-clamp-2 leading-relaxed">
                        {candidate.title || "No title provided"}
                      </p>

                      <div className="w-full h-[2px] bg-[#1A1A1A] mt-2">
                        <div className="h-full bg-[#FF1111]" style={{ width: ${Math.min(100, (candidate.score || 0) * 100)}% }} />
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col justify-center gap-2">
                      <a href={candidate.link} target="_blank" rel="noreferrer"
                         className="flex items-center justify-center px-3 py-1.5 bg-[#FFFFFF] text-[#000000] hover:bg-[#FF1111] hover:text-[#FFFFFF] transition-colors rounded-sm"
                         title="Open Source Link"
                      >
                         <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] font-bold">MATCH</span>
                      </a>
                    </div>
                  </div>
                ))}
                
                {results.candidates.length === 0 && (
                  <div className="p-8 text-center flex flex-col items-center justify-center h-full opacity-50">
                    <User size={32} className="text-[#555555] mb-3" />
                    <p style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[11px] text-[#777777]">NO CANDIDATES FOUND</p>
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>

        {/* Global Scrollbar Styles for this component only */}
        <style dangerouslySetInnerHTML={{__html: 
          .custom-scrollbar::-webkit-scrollbar {
            width: 4px;
          }
          .custom-scrollbar::-webkit-scrollbar-track {
            background: transparent;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: #333333;
            border-radius: 4px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: #FF1111;
          }
        }} />
      </main>
    );
  }
'''

new_content = content[:last_brace_index] + verified_block + '\n' + content[last_brace_index:]

with open('frontend/src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("SUCCESSFULLY APPLIED VERIFIED STATE")
