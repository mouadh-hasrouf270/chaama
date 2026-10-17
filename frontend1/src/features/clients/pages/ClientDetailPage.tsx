import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Plus } from 'lucide-react';
import useApi from '../../../hooks/useApi';
import api, { errorMessage } from '../../../api/client';
import { PageHeader, Card, Badge } from '../../../components/ui/InternalUI';

export default function ClientDetailPage() {
  const { id } = useParams();
  const { data: currentUser } = useApi<any>("/accounts/me/");
  const isPartner = currentUser?.role === "EXTERNAL_SUBCONTRACTOR";
  const isAdmin = currentUser?.role === "SUPER_ADMIN";
  const { data: lawyers } = useApi<any[]>('/accounts/lawyers/', true);
  const { data: client, loading, error } = useApi(id ? `/v1/clients/${id}/` : null);
  const { data: matters, reload } = useApi<any[]>(id ? `/v1/matters/?client=${id}` : null, true);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ title:'', matter_type:'', description:'', opposing_party:'', jurisdiction:'', court_reference:'', opened_at:new Date().toISOString().slice(0,10), lead_lawyer: '' });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  async function create(e: React.FormEvent) {
    e.preventDefault();setSaving(true);setMessage('');
    try { await api.post('/v1/matters/', {...form, lead_lawyer: form.lead_lawyer ? Number(form.lead_lawyer) : null, client: Number(id)});setShow(false);setForm({...form,title:'',description:'',opposing_party:''});reload(); }
    catch(err){setMessage(errorMessage(err));}finally{setSaving(false);}
  }
  return <div className="w-full space-y-5">
    <Link to="/app/clients" className="inline-flex items-center gap-2 text-sm"><ArrowLeft size={16}/> Retour aux clients</Link>
    <PageHeader eyebrow="Fiche client" title={client ? `${client.first_name} ${client.last_name}` : 'Client'} subtitle={`Référence ${id}`} />
    {loading && <p>Chargement…</p>}{error && <p role="alert">{error}</p>}
    <div className="grid gap-5 lg:grid-cols-[1fr_290px]">
      <Card className="p-5">
        <div className="mb-5 flex items-center justify-between gap-3"><h2 className="text-lg font-semibold">Dossiers juridiques ({matters?.length || 0})</h2>{currentUser?.role === "SUPER_ADMIN" && <button onClick={()=>setShow(!show)} className="flex items-center gap-2 bg-chaama-dark px-3 py-2 text-xs text-white"><Plus size={15}/> Nouveau dossier</button>}</div>
        {show && currentUser?.role === "SUPER_ADMIN" && <form onSubmit={create} className="mb-6 grid gap-3 rounded border border-chaama-border p-4 sm:grid-cols-2">
          {([['title','Intitulé du dossier'],['matter_type','Domaine juridique'],['opposing_party','Partie adverse'],['jurisdiction','Tribunal / Juridiction'],['court_reference','Référence judiciaire']] as const).map(([key,label])=><label key={key} className="text-xs">{label}<input required={key==='title'} value={form[key]} onChange={e=>setForm({...form,[key]:e.target.value})} className="mt-1 w-full border p-2 text-sm" /></label>)}
          {isAdmin && <label className="text-xs">Avocat responsable
            <select className="mt-1 w-full border p-2 text-sm" value={form.lead_lawyer} onChange={e=>setForm({...form,lead_lawyer:e.target.value})}>
              <option value="">À attribuer ultérieurement</option>
              {lawyers?.map((lawyer:any)=><option key={lawyer.id} value={lawyer.id}>{lawyer.user_name || lawyer.bar_number || `Avocat ${lawyer.id}`}</option>)}
            </select>
          </label>}
          <label className="text-xs">Date d'ouverture<input type="date" required value={form.opened_at} onChange={e=>setForm({...form,opened_at:e.target.value})} className="mt-1 w-full border p-2 text-sm" /></label>
          <label className="text-xs sm:col-span-2">Description<textarea value={form.description} onChange={e=>setForm({...form,description:e.target.value})} className="mt-1 w-full border p-2 text-sm" /></label>
          {message && <p role="alert" className="text-red-700 sm:col-span-2">{message}</p>}
          <button disabled={saving} className="bg-chaama-dark px-4 py-2 text-white disabled:opacity-50">{saving?'Enregistrement…':'Créer le dossier'}</button>
        </form>}
        <div className="divide-y">{matters?.map((m:any)=><Link key={m.id} to={`/app/matters/${m.id}`} className="flex justify-between gap-3 py-4 hover:underline"><span><strong>{m.title}</strong><small className="block opacity-70">{m.reference} · {m.matter_type || 'Général'}</small></span><Badge tone="gold">{m.status}</Badge></Link>)}{!matters?.length && <p className="text-sm opacity-70">Aucun dossier enregistré.</p>}</div>
      </Card>
      <Card className="h-fit space-y-3 p-5"><h3 className="font-semibold">Coordonnées</h3><p className="break-all text-sm">{client?.email || '—'}</p><p className="text-sm">{client?.phone || '—'}</p><p className="text-sm">{[client?.address,client?.city].filter(Boolean).join(', ') || '—'}</p></Card>
    </div>
  </div>;
}
