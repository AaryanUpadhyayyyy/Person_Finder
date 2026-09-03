"use client";

import { useState, useRef, useEffect, Suspense } from 'react';
import dynamic from 'next/dynamic';
import { ScanFace, Crosshair, Key, ExternalLink, User, Printer, XCircle, Play, Share2, MapPin, Mic, Sliders, Eye, Globe as GlobeIcon, Layers, Compass } from 'lucide-react';
import { motion } from 'framer-motion';

const EarthGlobe = dynamic(() => import('./components/EarthGlobe'), { ssr: false });

type AppState = 'idle' | 'processing' | 'verified' | 'error';

interface Candidate { thumbnail: string; link: string; source: string; title: string; score: number; verified: boolean; }
interface SocialProfile { platform: string; url: string; title: string; snippet: string; }
interface OsintResult { extracted: { name: string; location: string; org: string }; profiles: SocialProfile[]; }
interface ScanResult { passed: boolean; best_score: number; best_source: string; best_link: string; llm_context?: string; threshold: number; faces_found: number; det_score: number; age: string; gender: string; candidates: Candidate[]; blockchain_tx: string; block_number: string; total_searched?: number; scored_count?: number; skipped_count?: number; osint_profiles?: OsintResult | null; }

function LiveClock() {
  const [time, setTime] = useState('');
  useEffect(() => {
    const tick = () => setTime(new Date().toISOString().slice(11, 23).replace('T', ' ') + ' UTC');
    tick();
    const id = setInterval(tick, 100);
    return () => clearInterval(id);
  }, []);
  return <>{time}</>;
}

export default function Home() {
  const [appState, setAppState] = useState<AppState>('idle');
  const [pipelineStep, setPipelineStep] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [results, setResults] = useState<ScanResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [serpApiKey, setSerpApiKey] = useState('');
  const [groqApiKey, setGroqApiKey] = useState('');
  const [thresholdSlider, setThresholdSlider] = useState(40);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const savedKey = localStorage.getItem('serpApiKey');
    if (savedKey) setSerpApiKey(savedKey);
    const savedGroq = localStorage.getItem('groqApiKey');
    if (savedGroq) setGroqApiKey(savedGroq);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setPreviewUrl(URL.createObjectURL(e.target.files[0]));
    }
  };

  const handleStartTalaash = async () => {
    if (!selectedFile) return;
    setAppState('processing');
    setLogs([]);
    const formData = new FormData();
    formData.append("file", selectedFile);
    if (serpApiKey.trim()) formData.append("serpapi_key", serpApiKey.trim());
    if (groqApiKey.trim()) formData.append("groq_api_key", groqApiKey.trim());
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/scan`, { method: "POST", body: formData });
      
      if (!res.ok) {
        let errDetail = "Pipeline failed or server is down";
        try {
          const errData = await res.json();
          if (errData.detail) errDetail = errData.detail;
        } catch(e) {}
        throw new Error(errDetail);
      }
      
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response stream");
      
      const decoder = new TextDecoder();
      let buffer = "";
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === "log") {
                setLogs(prev => [...prev, data.data]);
              } else if (data.type === "result") {
                setResults(data.data);
                setAppState('verified');
              } else if (data.type === "log_background") {
                 // Background tasks starting after verified
              } else if (data.type === "update_llm") {
                setResults(prev => prev ? { ...prev, llm_context: data.data } : prev);
              } else if (data.type === "update_blockchain") {
                setResults(prev => prev ? { ...prev, blockchain_tx: data.data.tx_hash, block_number: data.data.block_number } : prev);
              } else if (data.type === "update_osint") {
                setResults(prev => prev ? { ...prev, osint_profiles: data.data } : prev);
              } else if (data.type === "error") {
                throw new Error(data.data);
              }
            } catch(e) {}
          }
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message);
      setAppState('error');
    }
  };
  const handleReset = () => {
    setAppState('idle'); setPipelineStep(0); setSelectedFile(null); setPreviewUrl(null); setResults(null); setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // ═══════════════════════════════════════════════════════
  // ─── STATE: IDLE — Command Center UI ───
  // ═══════════════════════════════════════════════════════
  if (appState === 'idle') {
    return (
      <main className="h-screen w-screen bg-[#020202] overflow-hidden flex items-center justify-center p-2 md:p-6"
        style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '30px 30px' }}>
        
        {/* Outer Frame Wrapper */}
        <div className="relative w-full h-full border border-[#222222] rounded-2xl bg-[#000000] overflow-hidden shadow-[0_0_80px_rgba(0,0,0,0.8)]">
        
          <style dangerouslySetInnerHTML={{__html: `
            @keyframes text-reveal {
              0% { opacity: 0; filter: blur(10px); transform: scale(1.05) translateY(-5px); letter-spacing: 0.1em; }
              100% { opacity: 1; filter: blur(0); transform: scale(1) translateY(0); letter-spacing: 0.25em; }
            }
            @keyframes flicker {
              0%, 19.999%, 22%, 62.999%, 64%, 64.999%, 70%, 100% { opacity: 1; }
              20%, 21.999%, 63%, 63.999%, 65%, 69.999% { opacity: 0; filter: drop-shadow(0 0 5px #FF1111); }
            }
            @keyframes slide-in-left {
              0% { opacity: 0; transform: translateX(-40px); }
              100% { opacity: 1; transform: translateX(0); }
            }
            @keyframes slide-in-right {
              0% { opacity: 0; transform: translateX(40px); }
              100% { opacity: 1; transform: translateX(0); }
            }
            @keyframes scanline {
              0% { transform: translateY(-100%); }
              100% { transform: translateY(100vh); }
            }
            .anim-title { animation: text-reveal 1.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
            .anim-logo { animation: text-reveal 1s cubic-bezier(0.16, 1, 0.3, 1) forwards, flicker 4s infinite 2s; }
            .anim-left { opacity: 0; animation: slide-in-left 1s cubic-bezier(0.16, 1, 0.3, 1) 0.6s forwards; }
            .anim-right { opacity: 0; animation: slide-in-right 1s cubic-bezier(0.16, 1, 0.3, 1) 0.9s forwards; }
            .scanline-overlay {
              position: absolute; top: 0; left: 0; width: 100%; height: 5px;
              background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.05), transparent);
              opacity: 0.5; pointer-events: none; z-index: 50; animation: scanline 8s linear infinite;
            }
          `}} />

          {/* Scanline Effect */}
          <div className="scanline-overlay" />

          {/* ── GLOBE (Z-0) ── */}
          <Suspense fallback={null}>
            <EarthGlobe />
          </Suspense>

          {/* ── TOP-CENTER GLOBE CONTROLS ── */}
          <div className="absolute top-[80px] left-1/2 -translate-x-1/2 z-20 flex gap-2 pointer-events-auto">
            {[Eye, GlobeIcon, Layers].map((Icon, i) => (
              <button key={i} className="w-8 h-8 rounded-full border border-[#222222] bg-[#000000]/80 flex items-center justify-center hover:border-[#FF1111] hover:text-[#FF1111] text-[#777777] transition-colors cursor-pointer">
                <Icon size={12} className="currentColor" />
              </button>
            ))}
          </div>

          {/* ── TOP BAR (Z-20) ── */}
          <div className="absolute top-0 left-0 right-0 z-20 px-8 pt-8 pb-3 pointer-events-none flex justify-between items-start">
            
            {/* Top-Left: Logo & Metadata Stack */}
            <div className="flex flex-col gap-3 pointer-events-auto">
              <div className="flex items-center gap-3">
                <div className="anim-logo w-6 h-6 rounded-full border border-[#FF1111] flex items-center justify-center">
                  <Crosshair size={12} className="text-[#FF1111]" />
                </div>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="anim-title text-[18px] font-bold tracking-[0.25em] text-[#FFFFFF]">TALAASH</span>
              </div>
              <div className="anim-left ml-9 flex flex-col gap-1">
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#AAAAAA] tracking-[0.15em]">PIPELINE // FACE-ID // BLOCKCHAIN</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#FF1111] tracking-[0.15em] font-bold">MODE: ACTIVE</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#777777] tracking-[0.1em] uppercase">TARGET SECTOR: GLOBAL</span>
              </div>
            </div>

            {/* Top-Right: Status & Actions */}
            <div className="anim-right flex gap-6 pointer-events-auto items-start">
              <div className="flex flex-col items-end gap-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#FF1111] animate-pulse" />
                  <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[12px] font-bold text-[#FF1111] tracking-[0.2em]">
                    {selectedFile ? 'SCANNING' : 'ACTIVE'}
                  </span>
                </div>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#AAAAAA] tracking-[0.1em]">
                  <LiveClock />
                </span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[8px] text-[#555555] tracking-[0.1em]">
                  SESSION FID-2026-0847
                </span>
              </div>
              <div className="flex gap-2">
                <button className="w-8 h-8 rounded-full border border-[#333333] flex items-center justify-center hover:border-[#FF1111] hover:text-[#FF1111] text-[#AAAAAA] transition-colors bg-[#000000]/50 cursor-pointer">
                  <Play size={12} className="ml-0.5 currentColor" />
                </button>
                <button className="w-8 h-8 rounded-full border border-[#333333] flex items-center justify-center hover:border-[#FF1111] hover:text-[#FF1111] text-[#AAAAAA] transition-colors bg-[#000000]/50 cursor-pointer">
                  <Share2 size={12} className="currentColor" />
                </button>
              </div>
            </div>
          </div>

          {/* ── LEFT SIDEBAR (Z-20) ── */}
          <div className="anim-left absolute left-8 top-[140px] z-20 w-[260px] flex flex-col gap-4 pointer-events-auto">
            {/* Configuration Block (API Key) */}
            <div className="border border-[#222222] rounded bg-[#000000]/80 p-4 backdrop-blur-sm hover:border-[#444444] transition-colors flex flex-col gap-4">
                            <div className="flex flex-col gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Key size={12} className="text-[#FFFFFF]" />
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">SERPAPI KEY (SEARCH)</span>
                  </div>
                  <input
                    type="text"
                    autoComplete="off"
                    placeholder="Enter SerpApi Key"
                    style={{ fontFamily: "'JetBrains Mono', monospace", WebkitTextSecurity: "disc" } as React.CSSProperties}
                    className="w-full bg-[#111111] border border-[#222222] rounded px-3 py-2 text-[10px] text-[#FFFFFF] placeholder-[#555555] outline-none focus:border-[#FF1111] transition-colors"
                    value={serpApiKey}
                    onChange={(e) => { setSerpApiKey(e.target.value); localStorage.setItem('serpApiKey', e.target.value); }}
                  />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Key size={12} className="text-[#FFFFFF]" />
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">GROQ KEY (INTEL)</span>
                  </div>
                  <input
                    type="text"
                    autoComplete="off"
                    placeholder="Enter Groq API Key"
                    style={{ fontFamily: "'JetBrains Mono', monospace", WebkitTextSecurity: "disc" } as React.CSSProperties}
                    className="w-full bg-[#111111] border border-[#222222] rounded px-3 py-2 text-[10px] text-[#FFFFFF] placeholder-[#555555] outline-none focus:border-[#FF1111] transition-colors"
                    value={groqApiKey}
                    onChange={(e) => { setGroqApiKey(e.target.value); localStorage.setItem('groqApiKey', e.target.value); }}
                  />
                </div>
              </div>
            </div>

            {/* Upload */}
            <div className="border border-[#222222] rounded bg-[#000000]/80 p-4 backdrop-blur-sm hover:border-[#444444] transition-colors">
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF] block mb-3">IDENTITY SCANNER</span>
              <div
                onClick={() => fileInputRef.current?.click()}
                className="group w-full h-[140px] border border-dashed border-[#444444] rounded flex flex-col items-center justify-center cursor-pointer hover:border-[#FF1111] hover:bg-[#FF1111]/5 transition-all bg-[#050505]"
              >
                {previewUrl ? (
                  <img src={previewUrl} alt="Preview" className="h-full w-full object-cover rounded p-1" />
                ) : (
                  <>
                    <ScanFace size={28} className="text-[#AAAAAA] group-hover:text-[#FF1111] transition-colors mb-3" strokeWidth={1.5} />
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] tracking-[0.1em] text-[#AAAAAA] group-hover:text-[#FF1111] transition-colors">CLICK TO UPLOAD FACE</span>
                  </>
                )}
              </div>
              <input type="file" ref={fileInputRef} onChange={handleFileSelect} className="hidden" accept="image/*" />
              
              <button
                onClick={handleStartTalaash}
                disabled={!selectedFile || !serpApiKey.trim()}
                style={{ fontFamily: "'JetBrains Mono', monospace" }}
                className={`w-full mt-4 text-[10px] font-bold tracking-[0.2em] py-3 rounded transition-all ${
                  selectedFile && serpApiKey.trim() ? "bg-[#FF1111] text-[#FFFFFF] cursor-pointer hover:opacity-90 shadow-[0_0_15px_rgba(255,17,17,0.4)]" : "bg-[#111111] text-[#555555] cursor-not-allowed"
                }`}
              >
                {!serpApiKey.trim() ? "ENTER API KEY" : "INITIATE SCAN"}
              </button>
            </div>
          </div>

          {/* ── RIGHT SIDEBAR (Z-20) ── */}
          <div className="anim-right absolute right-8 top-[140px] z-20 w-[280px] flex flex-col gap-4 pointer-events-auto">
            {/* Talaash Description */}
            <div className="border border-[#222222] rounded bg-[#000000]/80 p-4 backdrop-blur-sm hover:border-[#444444] transition-colors relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-[#FF1111]" />
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FF1111] block mb-2 font-bold ml-2">SYSTEM OVERVIEW</span>
              <p className="text-[11px] leading-relaxed text-[#AAAAAA] ml-2">
                TALAASH is an advanced Face Identification & Blockchain Verification system. It utilizes triple-engine deep search (Google, Yandex, Bing) coupled with biometric AI to track and verify human identities across the global intelligence network. All verified records are permanently hashed onto the Sepolia blockchain.
              </p>
            </div>

            {/* Recent Verified Log */}
            <div className="border border-[#222222] rounded bg-[#000000]/80 p-4 backdrop-blur-sm hover:border-[#444444] transition-colors">
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF] block mb-3 font-bold">VERIFIED LOG</span>
              <div className="flex flex-col gap-2">
                {[
                  {id: 'REC-0091', stat: 'VERIFIED', col: '#FFFFFF'},
                  {id: 'REC-0090', stat: 'NO MATCH', col: '#FF1111'},
                  {id: 'REC-0089', stat: 'VERIFIED', col: '#FFFFFF'}
                ].map((r, i) => (
                  <div key={i} className="flex items-center justify-between py-1.5 border-b border-[#111111] last:border-0">
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full" style={{backgroundColor: r.col}} />
                      <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#AAAAAA] tracking-wider">{r.id}</span>
                    </div>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", color: r.col }} className="text-[9px] tracking-[0.1em] font-bold">{r.stat}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Threshold meter */}
            <div className="border border-[#222222] rounded bg-[#000000]/80 p-4 backdrop-blur-sm hover:border-[#444444] transition-colors">
              <div className="flex justify-between items-center mb-3">
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">MATCH THRESHOLD</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#FF1111] font-bold">{(thresholdSlider / 100).toFixed(2)}</span>
              </div>
              <input 
                type="range" min="0" max="100" value={thresholdSlider} onChange={(e) => setThresholdSlider(Number(e.target.value))}
                className="w-full h-1 bg-gradient-to-r from-[#555555] to-[#FF1111] rounded appearance-none cursor-pointer"
                style={{ WebkitAppearance: 'none' }}
              />
              <style jsx>{`
                input[type='range']::-webkit-slider-thumb {
                  -webkit-appearance: none; appearance: none; width: 8px; height: 14px; background: #FFFFFF; cursor: pointer; border-radius: 1px;
                }
              `}</style>
            </div>
          </div>

          {/* ── BOTTOM-LEFT TELEMETRY (Z-20) ── */}
          <div className="anim-left absolute bottom-8 left-8 z-20 pointer-events-none flex items-center gap-4">
            <div className="w-10 h-10 rounded-full border border-[#333333] bg-[#000000]/80 flex items-center justify-center text-[#777777]">
              <Compass size={18} />
            </div>
            <div className="flex flex-col gap-1">
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#777777] tracking-[0.15em] uppercase">LOC: GLOBAL COORDS</span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#777777] tracking-[0.15em] uppercase">REF: GEO-TRACK-GLB-8472</span>
            </div>
          </div>

          {/* ── BOTTOM DOCK COMMAND CENTER (Z-20) ── */}
          <div className="anim-title absolute bottom-8 left-0 right-0 z-20 flex items-center justify-center gap-6 pointer-events-auto">
            {/* Location */}
            <button className="border border-[#222222] rounded-full bg-[#000000]/90 px-6 py-2.5 flex items-center gap-2 hover:border-[#FF1111] hover:text-[#FF1111] text-[#AAAAAA] transition-colors cursor-pointer backdrop-blur-sm">
              <MapPin size={12} className="currentColor" />
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] tracking-[0.15em] currentColor font-bold">LOCATION</span>
            </button>
            
            {/* Voice Command Module */}
            <button className="group border border-[#222222] rounded-full bg-[#000000]/90 px-8 py-2.5 flex items-center gap-4 hover:border-[#FF1111] transition-colors cursor-pointer backdrop-blur-sm">
              <Mic size={14} className="text-[#FF1111]" />
              <div className="flex items-center gap-0.5">
                {[
                  {h: 2, op: 0.6}, {h: 4, op: 0.8}, {h: 7, op: 0.9}, 
                  {h: 10, op: 1.0}, {h: 6, op: 0.7}, {h: 8, op: 0.9}, 
                  {h: 3, op: 0.6}, {h: 5, op: 0.8}, {h: 2, op: 0.5}
                ].map((bar, i) => (
                  <div key={i} className="w-[2px] bg-[#FF1111] rounded-full group-hover:animate-pulse" style={{ height: `${bar.h+4}px`, opacity: bar.op }} />
                ))}
              </div>
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] tracking-[0.1em] text-[#FF1111] font-bold">VOICE COMMAND</span>
            </button>

            {/* Visual Presets / Network */}
            <button className="border border-[#222222] rounded-full bg-[#000000]/90 px-6 py-2.5 flex items-center gap-2 hover:border-[#FF1111] hover:text-[#FF1111] text-[#AAAAAA] transition-colors cursor-pointer backdrop-blur-sm">
              <Sliders size={12} className="currentColor" />
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] tracking-[0.15em] currentColor font-bold">NETWORK</span>
            </button>
          </div>

        </div>
      </main>
    );
  }

  // ═══════════════════════════════════════════
  // ─── STATE: PROCESSING — Pipeline Steps ───
  // ═══════════════════════════════════════════
    if (appState === 'processing') {
    return (
      <main className="h-screen w-screen bg-[#020202] flex items-center justify-center p-2 md:p-6 overflow-hidden relative"
        style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '30px 30px' }}>
        
        <div className="relative w-full h-full border border-[#222222] rounded-2xl bg-[#000000] overflow-hidden flex items-center justify-center shadow-[0_0_80px_rgba(0,0,0,0.8)]">
          <Suspense fallback={null}>
            <EarthGlobe />
          </Suspense>

          <div className="absolute bottom-8 left-8 z-20 pointer-events-none flex items-center gap-4">
            <div className="w-10 h-10 rounded-full border border-[#333333] bg-[#000000]/80 flex items-center justify-center text-[#777777]">
              <Compass size={18} />
            </div>
            <div className="flex flex-col gap-1">
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#777777] tracking-[0.15em] uppercase">LOC: GLOBAL COORDS</span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#777777] tracking-[0.15em] uppercase">REF: GEO-TRACK-GLB-8472</span>
            </div>
          </div>

          <div className="w-full max-w-[500px] flex flex-col gap-4 relative z-20 pointer-events-auto">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full border border-[#FF1111] flex items-center justify-center">
                  <Crosshair size={10} className="text-[#FF1111]" />
                </div>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[15px] font-bold tracking-[0.25em] text-[#FFFFFF]">TALAASH</span>
              </div>
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[11px] text-[#FF1111] tracking-[0.2em] font-bold animate-pulse">STREAMING TELEMETRY...</span>
            </div>

            <div className="border border-[#222222] rounded-sm bg-[#0A0A0A]/95 p-4 flex items-center gap-4 backdrop-blur-md">
              <div className="w-12 h-12 rounded-sm border border-[#333333] overflow-hidden flex-shrink-0 bg-[#000000] flex items-center justify-center">
                {previewUrl ? (
                   <img src={previewUrl} alt="Candidate" className="w-full h-full object-cover opacity-70" />
                ) : (
                   <User size={18} className="text-[#555555]" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[11px] font-bold text-[#FFFFFF] truncate">
                  {selectedFile?.name || "TARGET ACQUIRED"}
                </p>
                <p style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] tracking-[0.15em] text-[#777777] mt-1.5">
                  STATUS: ANALYZING
                </p>
              </div>
              <div className="w-4 h-4 border border-[#333333] border-t-[#FF1111] rounded-full animate-spin flex-shrink-0" />
            </div>

            <div className="border border-[#222222] rounded-sm bg-[#0A0A0A]/95 p-5 shadow-2xl backdrop-blur-md flex flex-col h-[300px]">
              <div className="flex items-center justify-between mb-4 border-b border-[#222222] pb-3">
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">LIVE TERMINAL</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#FF1111] animate-pulse">REC</span>
              </div>
              <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-2">
                {logs.map((log, i) => (
                  <div key={i} className="flex gap-3">
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#555555]">{(i + 1).toString().padStart(2, '0')}</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className={`text-[10px] ${i === logs.length - 1 ? 'text-[#FFFFFF]' : 'text-[#888888]'}`}>{log}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  // ═══════════════════
  // ─── STATE: ERROR ───
  // ═══════════════════
  if (appState === 'error') {
    return (
      <main className="h-screen w-screen bg-[#020202] flex items-center justify-center p-2 md:p-6"
        style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '30px 30px' }}>
        <div className="relative w-full h-full border border-[#222222] rounded-2xl bg-[#000000] overflow-hidden flex items-center justify-center shadow-[0_0_80px_rgba(0,0,0,0.8)]">
          <div className="w-full max-w-md border border-[#444444] rounded bg-[#0A0A0A] p-8 text-center shadow-[0_0_30px_rgba(255,17,17,0.1)]">
            <div className="w-10 h-10 rounded-full border border-[#FF1111] flex items-center justify-center mx-auto mb-4">
              <XCircle size={20} className="text-[#FF1111]" />
            </div>
            <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[12px] font-bold tracking-[0.2em] text-[#FF1111]">STATUS: ERROR</span>
            <p className="text-[13px] text-[#FFFFFF] mt-5 mb-8 leading-relaxed">{errorMsg}</p>
            <button onClick={handleReset} style={{ fontFamily: "'JetBrains Mono', monospace" }} className="w-full text-[11px] font-bold tracking-[0.2em] py-4 rounded bg-[#111111] border border-[#444444] text-[#FFFFFF] hover:border-[#FF1111] transition-colors cursor-pointer">
              RETRY SCAN
            </button>
          </div>
        </div>
      </main>
    );
  }
  // ═══════════════════════════════════════════
  // ─── STATE: VERIFIED — Final Dashboard ───
  // ═══════════════════════════════════════════
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

          {/* STATS BAR (BOTTOM CENTER) */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 pointer-events-auto flex items-center gap-2">
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm px-4 py-2 flex flex-col items-center min-w-[120px] shadow-2xl">
               <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[16px] font-bold text-[#FFFFFF]">{results.faces_found}</span>
               <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[8px] text-[#777777] tracking-[0.1em] mt-1 uppercase">FACES DETECTED</span>
            </div>
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm px-4 py-2 flex flex-col items-center min-w-[120px] shadow-2xl">
               <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[16px] font-bold text-[#FFFFFF]">{results.total_searched}</span>
               <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[8px] text-[#777777] tracking-[0.1em] mt-1 uppercase">WEB LINKS</span>
            </div>
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm px-4 py-2 flex flex-col items-center min-w-[120px] shadow-2xl">
               <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[16px] font-bold text-[#FFFFFF]">{results.scored_count}</span>
               <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[8px] text-[#777777] tracking-[0.1em] mt-1 uppercase">FACES SCORED</span>
            </div>
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm px-4 py-2 flex flex-col items-center min-w-[120px] shadow-2xl">
               <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[16px] font-bold text-[#FFFFFF]">{results.skipped_count}</span>
               <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[8px] text-[#777777] tracking-[0.1em] mt-1 uppercase">SKIPPED</span>
            </div>
          </div>

          {/* LEFT PANEL: VERDICT & INTELLIGENCE (Z-20) */}
          <motion.div initial={{ x: -100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ type: "spring", stiffness: 100, damping: 20 }} className="absolute top-24 bottom-24 left-2 right-2 md:left-6 md:right-auto w-auto md:w-[420px] flex flex-col gap-4 pointer-events-auto z-20 overflow-y-auto custom-scrollbar pr-2 pb-4">
            
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

            {/* NEW: BIOMETRICS CARD */}
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm flex flex-col shadow-2xl flex-shrink-0">
              <div className="px-5 py-3 border-b border-[#222222] flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#FFFFFF]" />
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">BIOMETRIC ANALYSIS</span>
              </div>
              <div className="p-4 flex flex-col">
                {[
                  ['DETECTION CONFIDENCE', results.det_score],
                  ['ESTIMATED AGE', results.age],
                  ['ESTIMATED GENDER', results.gender === 'M' ? 'MALE' : results.gender === 'F' ? 'FEMALE' : results.gender],
                  ['SYSTEM THRESHOLD', '> ' + results.threshold]
                ].map(([l, v], i) => (
                  <div key={i} className="flex justify-between items-center py-2.5 border-b border-[#1A1A1A] last:border-0">
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.1em] text-[#777777]">{l as string}</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[11px] font-bold text-[#FFFFFF]">{v as string}</span>
                  </div>
                ))}
              </div>
            </div>

                        {/* NEW: BLOCKCHAIN RECORD CARD */}
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm flex flex-col shadow-2xl flex-shrink-0">
              <div className="px-5 py-3 border-b border-[#222222] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#FFFFFF]" />
                  <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">BLOCKCHAIN RECORD</span>
                </div>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className={`text-[8px] tracking-wider px-2 py-1 rounded-sm font-bold ${results.blockchain_tx === 'PENDING...' ? 'text-[#FF1111] bg-transparent animate-pulse' : results.blockchain_tx && results.blockchain_tx !== 'Hardhat offline' && results.blockchain_tx !== 'N/A' ? 'text-[#000000] bg-[#FFFFFF]' : 'text-[#FFFFFF] bg-[#FF1111]'}`}>
                  {results.blockchain_tx === 'PENDING...' ? 'RECORDING...' : results.blockchain_tx && results.blockchain_tx !== 'Hardhat offline' && results.blockchain_tx !== 'N/A' ? 'VERIFIED' : 'OFFLINE'}
                </span>
              </div>
              <div className="p-4 flex flex-col relative">
                {results.blockchain_tx === 'PENDING...' && (
                  <div className="absolute inset-0 z-10 bg-[#0A0A0A]/80 backdrop-blur-sm flex items-center justify-center">
                    <div className="w-4 h-4 border border-[#333333] border-t-[#FFFFFF] rounded-full animate-spin flex-shrink-0" />
                  </div>
                )}
                <div className="flex flex-col py-2.5 border-b border-[#1A1A1A]">
                  <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] tracking-[0.1em] text-[#777777] mb-1.5">TRANSACTION HASH</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#FFFFFF] bg-[#111111] px-2 py-1.5 border border-[#222222] truncate rounded-sm">{results.blockchain_tx === 'PENDING...' ? '' : results.blockchain_tx}</span>
                </div>
                <div className="flex justify-between items-center py-2.5">
                  <div className="flex flex-col">
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] tracking-[0.1em] text-[#777777] mb-1">BLOCK NUMBER</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[11px] font-bold text-[#FFFFFF]">{results.block_number === 'PENDING...' ? '-' : results.block_number}</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] tracking-[0.1em] text-[#777777] mb-1">NETWORK</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[11px] font-bold text-[#FF1111]">SEPOLIA TESTNET</span>
                  </div>
                </div>
              </div>
            </div>

                        {/* 2. INTELLIGENCE BRIEF CARD */}
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm flex flex-col shadow-2xl flex-shrink-0 min-h-[250px]">
              <div className="px-5 py-3 border-b border-[#222222] flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#FF1111]" />
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">INTELLIGENCE BRIEF</span>
              </div>
              <div className="p-5 overflow-y-auto custom-scrollbar flex-1 relative">
                {results.llm_context && results.llm_context !== "N/A" && results.llm_context !== "PENDING..." ? (
                  <div className="text-[11px] text-[#AAAAAA] leading-[1.8] font-['Inter'] whitespace-pre-wrap">
                    {results.llm_context.split('\n').map((line, i) => (
                      <p key={i} className="mb-3 last:mb-0">{line.replace(/\*\*/g, '')}</p>
                    ))}
                  </div>
                ) : results.llm_context === "PENDING..." ? (
                  <div className="h-full flex items-center justify-center flex-col gap-3">
                    <div className="w-4 h-4 border border-[#333333] border-t-[#FF1111] rounded-full animate-spin flex-shrink-0" />
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#FF1111] tracking-widest animate-pulse">GENERATING INTEL...</span>
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center flex-col gap-3 opacity-50">
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#555555] tracking-widest">NO ADDITIONAL INTEL</span>
                  </div>
                )}
              </div>
            </div>
            
            {/* 3. SOCIAL PROFILES CARD (OSINT) */}
            <div className="bg-[#0A0A0A]/90 backdrop-blur-md border border-[#222222] rounded-sm flex flex-col shadow-2xl flex-shrink-0">
              <div className="px-5 py-3 border-b border-[#222222] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#FF1111]" />
                  <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] tracking-[0.15em] text-[#FFFFFF]">SOCIAL PROFILES</span>
                </div>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#FF1111]">
                  {results.osint_profiles?.profiles ? `${results.osint_profiles.profiles.length} FOUND` : '...'}
                </span>
              </div>
              <div className="p-4 flex flex-col">
                {!results.osint_profiles ? (
                  <div className="flex items-center justify-center py-6 gap-3">
                    <div className="w-4 h-4 border border-[#333333] border-t-[#FF1111] rounded-full animate-spin flex-shrink-0" />
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#FF1111] tracking-widest animate-pulse">SCANNING PROFILES...</span>
                  </div>
                ) : results.osint_profiles.profiles.length === 0 ? (
                  <div className="flex items-center justify-center py-6 opacity-50">
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#555555] tracking-widest">NO PROFILES DISCOVERED</span>
                  </div>
                ) : (
                  <>
                    {results.osint_profiles.extracted?.name && (
                      <div className="mb-3 pb-3 border-b border-[#1A1A1A]">
                        <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#777777] tracking-[0.1em]">TARGET: </span>
                        <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#FFFFFF] font-bold">{results.osint_profiles.extracted.name.toUpperCase()}</span>
                        {results.osint_profiles.extracted.location && (
                          <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] text-[#777777]"> | {results.osint_profiles.extracted.location}</span>
                        )}
                      </div>
                    )}
                    {results.osint_profiles.profiles.map((p, i) => (
                      <a key={i} href={p.url} target="_blank" rel="noreferrer"
                         className="flex items-start gap-3 py-2.5 border-b border-[#1A1A1A] last:border-0 hover:bg-[#111111] transition-colors px-2 -mx-2 rounded-sm group">
                        <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[9px] tracking-[0.1em] text-[#FF1111] font-bold min-w-[90px] flex-shrink-0 pt-0.5">{p.platform.toUpperCase()}</span>
                        <div className="flex flex-col min-w-0">
                          <span style={{ fontFamily: "'JetBrains Mono', monospace" }} className="text-[10px] text-[#FFFFFF] truncate group-hover:text-[#FF1111] transition-colors">{p.title || p.url}</span>
                          {p.snippet && <span className="text-[9px] text-[#555555] font-['Inter'] line-clamp-1 mt-0.5">{p.snippet}</span>}
                        </div>
                      </a>
                    ))}
                  </>
                )}
              </div>
            </div>
            
          </motion.div>

          {/* RIGHT PANEL: MATCH CANDIDATES (Z-20) */}
          <motion.div initial={{ x: 100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ type: "spring", stiffness: 100, damping: 20 }} className="hidden md:flex absolute top-24 bottom-24 right-6 w-[450px] flex-col z-20 pointer-events-auto">
            
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
                        <div className="h-full bg-[#FF1111]" style={{ width: `${Math.min(100, (candidate.score || 0) * 100)}%` }} />
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
          </motion.div>

        </div>

        {/* Global Scrollbar Styles for this component only */}
        <style dangerouslySetInnerHTML={{__html: `
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
        `}} />
      </main>
    );
  }

}










