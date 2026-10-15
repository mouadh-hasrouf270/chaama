import { ArrowUpRight, ArrowRight, ShieldCheck, Scale, CalendarCheck2 } from "lucide-react";
import { Link } from "react-router-dom";
import hero from "../../../assets/justice-hero.jpg";
export default function HeroSection(){return <section className="relative isolate overflow-hidden bg-[#0a2e36] text-white min-h-[700px] flex items-center">
<img src={hero} alt="Cabinet juridique" className="absolute inset-0 w-full h-full object-cover opacity-40 -z-20"/>
<div className="absolute inset-0 bg-gradient-to-r from-[#082831] via-[#082831]/95 to-[#082831]/30 -z-10"/>
<div className="container-chaama mx-auto px-5 md:px-8 py-28 w-full"><div className="max-w-[800px]">
<p className="flex items-center gap-3 text-xs uppercase tracking-[.25em] text-[#dfc38d] mb-7"><Scale size={17}/> CHAAMA · Accompagnement juridique</p>
<h1 className="font-display text-[clamp(3.5rem,7.5vw,7rem)] leading-[.99] tracking-tight">Votre situation mérite <em className="text-[#e0c48c] not-italic">une réponse claire.</em></h1>
<p className="max-w-[570px] mt-8 text-lg leading-8 text-white/80">Une question juridique, une procédure à engager ou un dossier à défendre ? Expliquez-nous votre besoin. Nous vous guidons vers la prochaine étape.</p>
<div className="flex flex-wrap gap-4 mt-10"><Link to="/rendez-vous" className="inline-flex gap-4 items-center px-7 py-4 bg-[#e0c48c] text-[#0a2e36] font-bold hover:bg-white transition">Prendre rendez-vous <ArrowUpRight size={20}/></Link><Link to="/contact" className="inline-flex gap-3 items-center border border-white/45 px-7 py-4 font-semibold hover:bg-white/10 transition">Nous contacter <ArrowRight size={18}/></Link></div>
<div className="flex flex-wrap gap-7 mt-16 text-xs text-white/70"><span className="flex items-center gap-2"><ShieldCheck size={18} className="text-[#e0c48c]"/> Confidentialité des échanges</span><span className="flex items-center gap-2"><CalendarCheck2 size={18} className="text-[#e0c48c]"/> Demande de rendez-vous en ligne</span></div>
</div></div></section>}
