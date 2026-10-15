import { useEffect, useState } from "react";
import api, { errorMessage } from "../../api/client";

type Application = { id:number; full_name:string; cabinet:string; email:string; phone:string; bar_number:string; jurisdiction:string; specialties:string[]; status:string; created_at:string };
export default function PartnerApplicationsPage(){
 const [items,setItems]=useState<Application[]>([]); const [error,setError]=useState(""); const [busy,setBusy]=useState(0);
 const [credentials,setCredentials]=useState<{username:string;temporary_password:string;phone:string}|null>(null);
 async function load(){try {const {data}=await api.get("/accounts/partner-applications/");setItems(data);}catch(e){setError(errorMessage(e));}}
 useEffect(()=>{void load();},[]);
 async function decide(id:number,decision:"approve"|"reject"){
  if(decision==='reject' && !window.confirm('Refuser cette candidature ?'))return;
  setBusy(id);setError("");
  try {const {data}=await api.post(`/accounts/partner-applications/${id}/decide/`,{decision}); if(data.temporary_password)setCredentials(data);await load();}
  catch(e){setError(errorMessage(e));}finally{setBusy(0);}
 }
 const message=credentials ? `Bonjour, votre candidature CHAAMA a été acceptée.\nIdentifiant : ${credentials.username}\nMot de passe temporaire : ${credentials.temporary_password}\nVeuillez changer votre mot de passe dès votre première connexion.` : '';
 return <main className="p-6 lg:p-10 space-y-6"><div><p className="uppercase text-xs tracking-widest text-chaama-gold">Administration</p><h1 className="text-3xl font-display">Demandes de partenariat</h1><p className="text-sm text-chaama-muted">Examinez les justificatifs avant d'accepter un avocat.</p></div>
 {error && <p role="alert" className="text-red-700">{error}</p>}
 {credentials && <section className="p-5 border-2 border-amber-500 bg-amber-50 text-slate-900"><h2 className="font-bold">Identifiants créés — affichage unique</h2><p>Copiez ces informations avant de fermer. Elles ne sont pas conservées en clair.</p><pre className="whitespace-pre-wrap my-3 p-3 bg-white">{message}</pre><div className="flex gap-3 flex-wrap"><button className="p-3 bg-slate-900 text-white" onClick={()=>navigator.clipboard.writeText(message)}>Copier</button><a className="p-3 bg-emerald-700 text-white" target="_blank" rel="noreferrer" href={`https://wa.me/${credentials.phone.replace(/\D/g,'')}?text=${encodeURIComponent(message)}`}>Ouvrir WhatsApp</a><button className="p-3 border" onClick={()=>setCredentials(null)}>J'ai sauvegardé les identifiants</button></div><p className="text-xs mt-2">WhatsApp ouvre un brouillon : l'envoi reste manuel. Vérifiez le destinataire.</p></section>}
 <div className="space-y-4">{items.length===0 && <p>Aucune demande reçue.</p>}{items.map(i=><article key={i.id} className="bg-white border border-chaama-border p-5 space-y-3"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="font-semibold text-lg">{i.full_name} — {i.cabinet}</h2><span className="text-xs font-bold">{i.status}</span></div><div className="grid md:grid-cols-2 gap-2 text-sm"><p>Email : {i.email}</p><p>Téléphone : {i.phone}</p><p>Barreau : {i.bar_number}</p><p>Juridiction : {i.jurisdiction}</p><p>Spécialités : {i.specialties.join(', ')}</p><p>Reçue : {new Date(i.created_at).toLocaleDateString('fr-FR')}</p></div><button className="underline text-sm" onClick={async()=>{try{const {data}=await api.get(`/accounts/partner-applications/${i.id}/proof/`,{responseType:'blob'});const url=URL.createObjectURL(data);const a=document.createElement('a');a.href=url;a.download=`justificatif-${i.id}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){setError(errorMessage(e));}}}>Télécharger le justificatif</button>{i.status==='PENDING'&&<div className="flex gap-3"><button disabled={busy===i.id} onClick={()=>decide(i.id,'approve')} className="bg-chaama-dark text-white px-5 py-2 disabled:opacity-40">Accepter et créer le compte</button><button disabled={busy===i.id} onClick={()=>decide(i.id,'reject')} className="border border-red-400 text-red-700 px-5 py-2">Refuser</button></div>}</article>)}</div></main>;
}
