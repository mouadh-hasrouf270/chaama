import {Link} from 'react-router-dom';
import useApi from '../../../hooks/useApi';
import {PageHeader,Card,Badge} from '../../../components/ui/InternalUI';
export default function MattersListPage(){
 const {data,loading,error}=useApi<any[]>('/v1/matters/',true);
 return <div className="space-y-5"><PageHeader eyebrow="Gestion juridique" title="Dossiers" subtitle="Tous vos dossiers accessibles"/>{loading&&<p>Chargement…</p>}{error&&<p role="alert">{error}</p>}<Card className="divide-y p-5">{data?.map(m=><Link className="flex justify-between gap-4 py-4 hover:underline" to={`/app/matters/${m.id}`} key={m.id}><span><strong>{m.title}</strong><small className="block opacity-70">{m.reference} · {m.client_name} · {m.matter_type}</small></span><Badge tone="gold">{m.status}</Badge></Link>)}{!data?.length&&<p>Créez un dossier depuis la fiche d'un client.</p>}</Card></div>
}
