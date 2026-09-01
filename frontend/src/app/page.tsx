"use client";

import { useState, useRef, useEffect } from 'react';
import { ScanFace, Upload, Search, ShieldCheck, CheckCircle, XCircle, ExternalLink, User, Globe, Hash, Layers, Printer, Key } from 'lucide-react';

type AppState = 'idle' | 'processing' | 'verified' | 'error';

interface Candidate {
  thumbnail: string;
  link: string;
  source: string;
  title: string;
  score: number;
  verified: boolean;
}

interface ScanResult {
  passed: boolean;
  best_score: number;
  best_source: string;
  best_link: string;
  threshold: number;
  faces_found: number;
  det_score: number;
  age: string;
  gender: string;
  social_matches: number;
  visual_matches: number;
  total_searched: number;
  scored_count: number;
  skipped_count: number;
  from_cache: boolean;
  candidates: Candidate[];
  blockchain_tx: string;
  block_number: string;
}

export default function Home() {
  const [appState, setAppState] = useState<AppState>('idle');
  const [pipelineStep, setPipelineStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [results, setResults] = useState<ScanResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [serpApiKey, setSerpApiKey] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const savedKey = localStorage.getItem('serpApiKey');
    if (savedKey) setSerpApiKey(savedKey);
  }, []);

  const bgImage = appState === 'verified' && results?.passed
    ? "url('/bg2.png')" : "url('/Talaash_bg.png')";

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleStartTalaash = async () => {
    if (!selectedFile) return;
    setAppState('processing');
    setPipelineStep(1); // Detecting & Encoding
    
    const formData = new FormData();
    formData.append("file", selectedFile);
    if (serpApiKey.trim()) {
      formData.append("serpapi_key", serpApiKey.trim());
    }
    
    // Realistic fake progress for the 5 steps while we wait for the long API call
    const timers = [
      setTimeout(() => setPipelineStep(2), 2000),   // Google Lens Search
      setTimeout(() => setPipelineStep(3), 5000),   // Verifying Candidates
      setTimeout(() => setPipelineStep(4), 8000),   // Deep Search (Triple Engine)
      setTimeout(() => setPipelineStep(5), 20000),  // Blockchain Record
    ];

    try {
      // Use deployed backend URL if available, otherwise local
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/scan`, {
        method: "POST",
        body: formData,
      });
      
      timers.forEach(clearTimeout);
      
      if (!res.ok) throw new Error("Pipeline failed or server is down");
      
      const data: ScanResult = await res.json();
      setResults(data);
      setAppState('verified');
    } catch (err: any) {
      timers.forEach(clearTimeout);
      setErrorMsg(err.message);
      setAppState('error');
    }
  };

  const handleReset = () => {
    setAppState('idle');
    setPipelineStep(0);
    setSelectedFile(null);
    setPreviewUrl(null);
    setResults(null);
    setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // The Canva elements
  const CanvaElements = () => (
    <>
      {/* Background */}
      <div 
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat transition-all duration-1000" 
        style={{ backgroundImage: bgImage }} 
      />
    </>
  );

  const Header = () => (
    <div className="relative z-10 text-center mt-12 mb-8">
      <h1 
        className="text-[82px] leading-none text-black drop-shadow-md"
        style={{ fontFamily: "var(--font-leckerli-one), cursive" }}
      >
        Talaash
      </h1>
    </div>
  );

  // ─── IDLE: Upload Card ───
  if (appState === 'idle') {
    return (
      <main className="min-h-screen w-full relative overflow-hidden flex flex-col items-center bg-[#FDF8EE] pb-8 px-4">
        <CanvaElements />
        
        {/* Custom API Key Input */}
        <div className="absolute top-4 right-4 z-20 flex items-center gap-2 bg-white/80 backdrop-blur neo-border px-3 py-1.5 rounded-xl shadow-sm">
          <Key size={16} className="text-gray-500" />
          <input 
            type="password"
            placeholder="Enter your SerpApi Key"
            className="bg-transparent border-none outline-none text-sm w-56 placeholder-gray-500 text-black font-bold"
            value={serpApiKey}
            onChange={(e) => {
              setSerpApiKey(e.target.value);
              localStorage.setItem('serpApiKey', e.target.value);
            }}
          />
        </div>

        <Header />
        
        <div className="relative z-10 w-full max-w-md bg-white neo-border neo-shadow p-6 rounded-2xl flex flex-col items-center text-center mt-4">
          <div className="w-14 h-14 bg-talaash-yellow neo-border rounded-full flex items-center justify-center mb-4">
            <ScanFace size={28} strokeWidth={2.5} className="text-black" />
          </div>
          <h2 className="text-2xl font-black mb-2 uppercase tracking-tight">Identity Scanner</h2>
          <p className="text-gray-600 font-medium text-sm mb-6">Upload a photo to detect faces, reverse search, and verify via Blockchain.</p>

          <div
            onClick={() => fileInputRef.current?.click()}
            className="w-full h-40 border-[3px] border-dashed border-black bg-gray-50 rounded-xl p-2 flex flex-col items-center justify-center mb-6 cursor-pointer hover:bg-talaash-yellow/10 transition-colors"
          >
            {previewUrl ? (
              <img src={previewUrl} alt="Preview" className="h-full w-full object-contain" />
            ) : (
              <>
                <Upload size={32} strokeWidth={2} className="mb-3 text-black" />
                <span className="font-bold text-base">Click to Upload Face</span>
              </>
            )}
          </div>
          <input type="file" ref={fileInputRef} onChange={handleFileSelect} className="hidden" accept="image/*" />

          <button
            onClick={handleStartTalaash}
            disabled={!selectedFile || !serpApiKey.trim()}
            className={`w-full font-black text-xl py-4 rounded-xl neo-border transition-all ${
              selectedFile && serpApiKey.trim()
                ? "bg-talaash-pink text-white neo-shadow hover:translate-y-[2px] hover:translate-x-[2px] hover:shadow-none cursor-pointer"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"
            }`}
          >
            {(!serpApiKey.trim()) ? "ENTER API KEY FIRST" : "START TALAASH"}
          </button>
        </div>
      </main>
    );
  }

  // ─── PROCESSING: Pipeline Steps ───
  if (appState === 'processing') {
    const steps = [
      { icon: <ScanFace size={20} strokeWidth={3} />, label: "Detecting & Encoding Face", sub: "InsightFace AI analyzing landmarks..." },
      { icon: <Search size={20} strokeWidth={3} />, label: "Google Lens Search", sub: "Dual search: original + cropped face..." },
      { icon: <ScanFace size={20} strokeWidth={3} />, label: "Verifying Candidates", sub: "Multi-face scoring with HD fallback..." },
      { icon: <Globe size={20} strokeWidth={3} />, label: "Deep Search (Yandex + Bing)", sub: "Triple engine parallel scan..." },
      { icon: <ShieldCheck size={20} strokeWidth={3} />, label: "Blockchain Record", sub: "Hashing & uploading proof on-chain..." },
    ];

    return (
      <main className="min-h-screen w-full relative overflow-hidden flex flex-col items-center bg-[#FDF8EE] pb-8 px-4">
        <CanvaElements />
        <Header />
        
        <div className="relative z-10 w-full max-w-md mt-4 flex flex-col gap-4">
          
          {/* Image Preview Card */}
          {previewUrl && (
            <div className="bg-white neo-border neo-shadow rounded-2xl p-4 flex items-center gap-4">
              <div className="w-20 h-20 rounded-xl neo-border overflow-hidden flex-shrink-0">
                <img src={previewUrl} alt="Scanning" className="w-full h-full object-cover" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-black text-sm text-gray-800 truncate">{selectedFile?.name}</p>
                <p className="text-xs text-gray-500 font-bold mt-1">Scanning in progress...</p>
                <div className="mt-2 h-2 bg-gray-200 rounded-full neo-border overflow-hidden">
                  <div className="h-full bg-talaash-pink rounded-full animate-pulse" style={{ width: `${Math.min(95, pipelineStep * 25)}%`, transition: 'width 1s ease' }}></div>
                </div>
              </div>
            </div>
          )}

          {/* Pipeline Steps Card */}
          <div className="bg-white neo-border neo-shadow p-5 rounded-2xl">
            <h2 className="font-black text-base mb-4 border-b-[3px] border-black pb-2 text-center uppercase tracking-wide">Verification Pipeline</h2>
            <div className="space-y-3">
              {steps.map((step, i) => {
                const stepNum = i + 1;
                const isActive = pipelineStep === stepNum;
                const isDone = pipelineStep > stepNum;
                const isPending = pipelineStep < stepNum;

                return (
                  <div key={i} className={`flex items-start gap-3 p-2.5 rounded-xl transition-all duration-300 ${isActive ? 'bg-talaash-yellow/15 neo-border' : isDone ? 'opacity-60' : 'opacity-30'}`}>
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 neo-border ${isDone ? 'bg-talaash-green text-white' : isActive ? 'bg-talaash-yellow text-black animate-pulse' : 'bg-gray-100 text-gray-400'}`}>
                      {isDone ? <CheckCircle size={16} strokeWidth={3} /> : step.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`font-black text-sm ${isPending ? 'text-gray-400' : 'text-black'}`}>{step.label}</p>
                      {isActive && <p className="text-[11px] text-gray-500 font-bold mt-0.5 animate-pulse">{step.sub}</p>}
                    </div>
                    {isDone && <span className="text-[10px] font-black text-talaash-green uppercase mt-1">Done</span>}
                    {isActive && (
                      <div className="flex gap-0.5 mt-2">
                        <div className="w-1.5 h-1.5 bg-talaash-pink rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-1.5 h-1.5 bg-talaash-pink rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-1.5 h-1.5 bg-talaash-pink rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Tip */}
          <div className="text-center px-4">
            <p className="text-xs font-bold text-gray-400">💡 Triple Engine Deep Search scans Google, Yandex & Bing simultaneously</p>
          </div>

        </div>
      </main>
    );
  }

  // ─── ERROR ───
  if (appState === 'error') {
    return (
      <main className="min-h-screen w-full relative overflow-hidden flex flex-col items-center bg-[#FDF8EE] pb-8 px-4">
        <CanvaElements />
        <Header />
        
        <div className="relative z-10 w-full max-w-md bg-white neo-border neo-shadow p-8 rounded-2xl text-center mt-4">
          <XCircle size={48} className="mx-auto mb-4 text-red-600" />
          <h2 className="font-black text-2xl text-red-700">Error Occurred</h2>
          <p className="text-base font-medium mt-3 text-gray-700">{errorMsg}</p>
          <button onClick={handleReset} className="w-full mt-6 bg-black text-white font-black py-4 rounded-xl neo-border cursor-pointer text-lg">TRY AGAIN</button>
        </div>
      </main>
    );
  }

  // ─── VERIFIED: Professional Dashboard Results ───
  const bestCandidateThumb = results?.candidates?.find(c => c.verified)?.thumbnail || results?.candidates?.[0]?.thumbnail;

  const handlePrint = () => {
    window.print();
  };

  return (
    <main className="min-h-screen w-full bg-[#FDF8EE] overflow-y-auto pb-16 font-sans text-black print:bg-white print:pb-0">
      
      {/* Navbar */}
      <nav className="w-full border-b-[3px] border-black bg-white mb-6 sticky top-0 z-50 print:hidden">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <h1 
            className="text-3xl leading-none text-black drop-shadow-sm mt-1"
            style={{ fontFamily: "var(--font-leckerli-one), cursive" }}
          >
            Talaash
          </h1>
          <div className="flex gap-3">
            <button
              onClick={handlePrint}
              className="bg-white text-black font-black text-xs px-5 py-2.5 rounded-lg neo-border hover:translate-y-[2px] hover:translate-x-[2px] hover:shadow-none transition-all cursor-pointer shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex items-center gap-2"
            >
              <Printer size={16} /> SAVE REPORT
            </button>
            <button
              onClick={handleReset}
              className="bg-black text-white font-black text-xs px-5 py-2.5 rounded-lg neo-border hover:translate-y-[2px] hover:translate-x-[2px] hover:shadow-none transition-all cursor-pointer shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex items-center gap-2"
            >
              <ScanFace size={16} /> NEW SCAN
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-6 flex flex-col gap-6">

        {/* ── HERO MATCH CARD ── */}
        <div className={`w-full neo-border neo-shadow rounded-2xl p-6 flex flex-col lg:flex-row items-center justify-between gap-6 ${results?.passed ? 'bg-[#E7F8E8]' : 'bg-[#FEECEB]'}`}>
          
          {/* Left: Images */}
          <div className="flex items-center gap-3">
            <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-xl neo-border overflow-hidden bg-white shadow-inner">
              <img src={previewUrl!} alt="Target" className="w-full h-full object-cover" />
            </div>
            <div className="flex flex-col gap-1 items-center justify-center px-1">
              <div className="w-6 h-1 bg-black rounded-full"></div>
              <div className="w-6 h-1 bg-black rounded-full"></div>
            </div>
            <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-xl neo-border overflow-hidden bg-white shadow-inner flex items-center justify-center">
              {bestCandidateThumb ? (
                <img src={bestCandidateThumb} alt="Match" className="w-full h-full object-cover" />
              ) : (
                <User size={32} className="text-gray-300" />
              )}
            </div>
          </div>

          {/* Middle: Verdict */}
          <div className="flex-1 text-center lg:text-left flex flex-col justify-center px-2">
            <span className="inline-block bg-black text-white text-[10px] font-black px-2.5 py-1 rounded uppercase mb-2 w-max mx-auto lg:mx-0">
              Final Verdict
            </span>
            <h2 className={`font-black text-3xl sm:text-4xl leading-none mb-2 tracking-tight ${results?.passed ? 'text-talaash-darkgreen' : 'text-red-700'}`}>
              {results?.passed ? 'IDENTITY VERIFIED' : 'NO MATCH FOUND'}
            </h2>
            {results?.passed ? (
               <p className="text-sm font-bold text-gray-700">
                Confirmed match found on <a href={results?.best_link} target="_blank" className="underline decoration-2 text-blue-600 hover:text-blue-800 transition-colors">{results?.best_source}</a>
              </p>
            ) : (
              <p className="text-sm font-bold text-gray-700">Similarity below threshold ({results?.threshold})</p>
            )}
          </div>

          {/* Right: Score */}
          <div className="flex flex-col items-center justify-center lg:border-l-[3px] border-black lg:pl-8 pt-5 lg:pt-0 w-full lg:w-auto border-t-[3px] lg:border-t-0">
             <div className={`text-white font-black text-5xl px-5 py-3 rounded-xl neo-border shadow-[4px_4px_0px_0px_rgba(0,0,0,0.15)] ${results?.passed ? 'bg-talaash-green' : 'bg-red-600'}`}>
              {results?.best_score.toFixed(2)}
            </div>
            <span className="text-xs font-black uppercase mt-2 text-gray-800 tracking-widest">Confidence</span>
          </div>
        </div>

        {/* ── STATS GRID ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white neo-border neo-shadow rounded-2xl p-5 flex flex-col items-center justify-center hover:-translate-y-1 transition-transform">
            <User size={28} className="mb-2 text-talaash-pink" strokeWidth={2.5} />
            <p className="font-black text-3xl mb-1">{results?.faces_found}</p>
            <p className="text-[10px] font-black text-gray-500 uppercase tracking-wide">Faces Detected</p>
          </div>
          <div className="bg-white neo-border neo-shadow rounded-2xl p-5 flex flex-col items-center justify-center hover:-translate-y-1 transition-transform">
            <Globe size={28} className="mb-2 text-talaash-green" strokeWidth={2.5} />
            <p className="font-black text-3xl mb-1">{results?.total_searched}</p>
            <p className="text-[10px] font-black text-gray-500 uppercase tracking-wide">Web Links</p>
          </div>
          <div className="bg-white neo-border neo-shadow rounded-2xl p-5 flex flex-col items-center justify-center hover:-translate-y-1 transition-transform">
            <CheckCircle size={28} className="mb-2 text-talaash-yellow" strokeWidth={2.5} />
            <p className="font-black text-3xl mb-1">{results?.scored_count}</p>
            <p className="text-[10px] font-black text-gray-500 uppercase tracking-wide">Faces Scored</p>
          </div>
          <div className="bg-white neo-border neo-shadow rounded-2xl p-5 flex flex-col items-center justify-center hover:-translate-y-1 transition-transform">
            <Hash size={28} className="mb-2 text-gray-400" strokeWidth={2.5} />
            <p className="font-black text-3xl mb-1">{results?.skipped_count}</p>
            <p className="text-[10px] font-black text-gray-500 uppercase tracking-wide">Skipped (No Face)</p>
          </div>
        </div>

        {/* ── DETAILS ROW ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          <div className="bg-white neo-border neo-shadow rounded-2xl p-6 flex flex-col">
            <h3 className="font-black text-xl mb-5 flex items-center gap-2">
              <ScanFace size={24} className="text-talaash-yellow" strokeWidth={3} /> Biometric Analysis
            </h3>
            <div className="flex-1 bg-gray-50 p-5 rounded-xl neo-border flex flex-col justify-between gap-3">
              <div className="flex justify-between items-center border-b-2 border-dashed border-gray-300 pb-2">
                <span className="text-sm text-gray-600 font-bold">Detection Confidence</span>
                <span className="text-black font-black text-base">{results?.det_score}</span>
              </div>
              <div className="flex justify-between items-center border-b-2 border-dashed border-gray-300 pb-2">
                <span className="text-sm text-gray-600 font-bold">Estimated Age</span>
                <span className="text-black font-black text-base">{results?.age}</span>
              </div>
              <div className="flex justify-between items-center border-b-2 border-dashed border-gray-300 pb-2">
                <span className="text-sm text-gray-600 font-bold">Estimated Gender</span>
                <span className="text-black font-black text-base">{results?.gender === 'M' ? 'Male' : results?.gender === 'F' ? 'Female' : results?.gender}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 font-bold">System Threshold</span>
                <span className="text-black font-black text-base">&gt; {results?.threshold}</span>
              </div>
            </div>
          </div>

          <div className="bg-white neo-border neo-shadow rounded-2xl p-6 flex flex-col">
            <h3 className="font-black text-xl mb-5 flex items-center gap-2">
              <Layers size={24} className="text-talaash-pink" strokeWidth={3} /> Blockchain Record
            </h3>
            <div className="flex-1 bg-gray-50 p-5 rounded-xl neo-border flex flex-col justify-center gap-5">
              <div>
                <span className="text-xs font-black text-gray-500 uppercase tracking-widest block mb-2">Transaction Hash</span> 
                <div className="font-mono text-xs text-black break-all bg-white p-2.5 border-[3px] border-black rounded-lg shadow-inner">
                  {results?.blockchain_tx}
                </div>
              </div>
              <div>
                <span className="text-xs font-black text-gray-500 uppercase tracking-widest block mb-1">Block Number</span> 
                <span className="font-black text-2xl text-black">{results?.block_number}</span>
              </div>
            </div>
          </div>

        </div>

        {/* ── CANDIDATES ROSTER ── */}
        <div className="bg-white neo-border neo-shadow rounded-2xl p-6 mt-1">
          <h2 className="font-black text-2xl mb-6 flex items-center gap-2">
            <Search size={28} strokeWidth={3} /> Match Candidates <span className="text-gray-400 text-xl">({results?.candidates.length})</span>
          </h2>

          {results?.candidates.length === 0 ? (
            <div className="bg-gray-50 border-[3px] border-dashed border-gray-300 rounded-2xl p-10 text-center">
              <p className="text-gray-500 font-bold text-lg">No comparable faces were found online.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {results?.candidates.map((c, i) => (
                <div key={i} className={`bg-white neo-border rounded-xl flex flex-col overflow-hidden relative ${c.verified ? 'ring-4 ring-talaash-green shadow-[4px_4px_0px_0px_rgba(0,166,81,0.3)]' : 'hover:-translate-y-1 hover:neo-shadow transition-all'}`}>
                  
                  {c.verified && (
                    <div className="absolute top-2 right-2 bg-talaash-green text-white text-[9px] font-black px-2 py-1 rounded neo-border z-10 flex items-center gap-1 shadow-sm">
                      <CheckCircle size={10} strokeWidth={3} /> VERIFIED
                    </div>
                  )}

                  <div className="h-40 w-full bg-gray-100 border-b-[3px] border-black flex items-center justify-center overflow-hidden">
                    {c.thumbnail ? (
                      <img src={c.thumbnail} alt={c.source} className="w-full h-full object-cover" />
                    ) : (
                      <User size={40} className="text-gray-300" />
                    )}
                  </div>

                  <div className="p-4 flex flex-col flex-1 bg-gray-50">
                    <div className="flex-1">
                      <h4 className="font-black text-base truncate mb-1" title={c.source}>{c.source || 'Unknown'}</h4>
                      <p className="text-[11px] text-gray-500 font-bold line-clamp-2 leading-snug" title={c.title || c.link}>{c.title || c.link}</p>
                    </div>
                    
                    <div className="flex items-center justify-between mt-4 pt-3 border-t-[3px] border-black">
                      <span className={`font-black text-2xl ${c.verified ? 'text-talaash-darkgreen' : c.score > 0.3 ? 'text-talaash-yellow' : 'text-red-500'}`}>
                        {c.score.toFixed(2)}
                      </span>
                      <a href={c.link} target="_blank" rel="noreferrer" className="text-black bg-white p-2 rounded-xl neo-border hover:bg-black hover:text-white transition-colors">
                        <ExternalLink size={16} strokeWidth={2.5} />
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </main>
  );
}
