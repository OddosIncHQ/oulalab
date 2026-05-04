import React from 'react';
import { Wind, ShieldCheck, Droplets, Sun, Sparkles, Scissors } from 'lucide-react';

const Care: React.FC = () => {
  const categories = [
    {
      icon: <Droplets className="w-8 h-8" />,
      title: "Limpieza Profesional",
      desc: "En Oulalab nos encargamos del proceso de limpieza profunda. No es necesario que laves las prendas antes de devolverlas; nuestro equipo utiliza tecnología de limpieza en seco eco-friendly."
    },
    {
      icon: <Wind className="w-8 h-8" />,
      title: "Almacenamiento",
      desc: "Mantén las prendas en un lugar fresco y seco. Utiliza las perchas acolchadas que enviamos para mantener la estructura de los hombros en blazers y abrigos de alta costura."
    },
    {
      icon: <Scissors className="w-8 h-8" />,
      title: "Uso Consciente",
      desc: "Nuestras prendas son piezas de diseño. Evita el contacto directo con perfumes, aceites corporales o accesorios que puedan enganchar tejidos delicados como la seda o el encaje."
    },
    {
      icon: <Sun className="w-8 h-8" />,
      title: "Luz y Temperatura",
      desc: "Evita exponer las prendas a la luz solar directa por tiempos prolongados para prevenir la decoloración de los tintes naturales y fibras orgánicas."
    }
  ];

  return (
    <div className="bg-white min-h-screen pt-32 pb-20">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header Editorial */}
        <div className="text-center mb-24">
          <span className="text-[#DF3265] font-black tracking-[0.3em] uppercase text-sm mb-4 block">Preservando el Lujo</span>
          <h1 className="text-5xl md:text-8xl font-black tracking-tighter uppercase mb-8">Guía de <br/><span className="text-gray-300 italic">Cuidado</span></h1>
          <p className="max-w-2xl mx-auto text-xl text-gray-500 font-medium leading-relaxed">
            La longevidad de una prenda es la máxima expresión de la sostenibilidad. Aprende cómo mantener tus piezas Oulalab en perfecto estado durante tu rotación.
          </p>
        </div>

        {/* Grid de Consejos */}
        <div className="grid md:grid-cols-2 gap-12 mb-32">
          {categories.map((cat, idx) => (
            <div key={idx} className="group p-12 bg-gray-50 rounded-[3rem] hover:bg-black hover:text-white transition-all duration-700">
              <div className="text-[#DF3265] mb-8 group-hover:scale-110 transition-transform duration-500">
                {cat.icon}
              </div>
              <h3 className="text-2xl font-black uppercase mb-4 tracking-tighter">{cat.title}</h3>
              <p className="text-gray-500 group-hover:text-gray-400 leading-relaxed font-medium">
                {cat.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Sección Especial: Materiales */}
        <div className="border-t border-gray-100 pt-24">
          <h2 className="text-3xl font-black uppercase mb-16 tracking-tighter flex items-center">
            <Sparkles className="mr-4 text-[#DF3265]" /> Cuidados por Material
          </h2>
          <div className="space-y-12">
            {[
              { mat: "Seda y Satén", care: "Extrema delicadeza. Evitar roces con bolsos de mimbre o superficies rugosas." },
              { mat: "Cueros y Cuerinas", care: "Si se moja por la lluvia, secar con un paño suave a temperatura ambiente. No aplicar calor." },
              { mat: "Lana y Cachemira", care: "No colgar las piezas de punto pesado; guardarlas dobladas para que no pierdan su forma original." }
            ].map((item, i) => (
              <div key={i} className="flex flex-col md:flex-row md:items-center justify-between border-b border-gray-50 pb-8 group">
                <span className="text-2xl font-bold uppercase group-hover:text-[#DF3265] transition-colors">{item.mat}</span>
                <span className="text-gray-500 md:max-w-md font-medium">{item.care}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Call to action final */}
        <div className="mt-32 p-16 bg-[#F7E8F7] rounded-[4rem] text-center">
          <ShieldCheck className="w-16 h-16 text-[#DF3265] mx-auto mb-8" />
          <h2 className="text-3xl font-black uppercase mb-4">¿Tienes una duda específica?</h2>
          <p className="text-gray-600 mb-8 font-medium">Nuestro equipo de expertos en textiles está disponible para asesorarte.</p>
          <a href="mailto:concierge@oulalab.com" className="inline-block bg-black text-white px-12 py-5 rounded-full font-black uppercase tracking-widest hover:bg-[#DF3265] transition-colors">
            Contactar Concierge
          </a>
        </div>
      </div>
    </div>
  );
};

export default Care;
