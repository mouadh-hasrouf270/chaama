import useApi from "../../../hooks/useApi";
export default function StatsBar(){
 const {data}=useApi('/accounts/public-stats/');
 const stats=[
 {label:"Années d’expérience", value:data?.years_experience == null ? '—' : `${data.years_experience}+`},
 {label:"Dossiers traités", value:data?.matters_count == null ? '—' : data.matters_count},
 {label:"Clients satisfaits", value:data?.satisfied_clients == null ? '—' : data.satisfied_clients},
 {label:"Avocats vérifiés", value:data?.verified_lawyers == null ? '—' : data.verified_lawyers},
 ];
 return <section className="bg-[#082831] text-white"><div className="container-chaama mx-auto grid grid-cols-2 lg:grid-cols-4 divide-x divide-white/10">{stats.map(s=><div key={s.label} className="py-9 px-4 text-center"><p className="font-display text-4xl lg:text-5xl text-[#e0c48c]">{s.value}</p><p className="mt-3 uppercase tracking-wider text-[11px] text-white/70">{s.label}</p></div>)}</div></section>;
}
