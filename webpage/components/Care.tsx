import React from 'react';
import { Wind, ShieldCheck, Droplets, Sun, Sparkles, Scissors } from 'lucide-react';

type Language = 'es' | 'en' | 'pt';

interface CareProps {
  lang: Language;
}

const CARE_CONTENT = {
  es: {
    tagline: 'Preservando el Lujo',
    title_1: 'Guía de',
    title_2: 'Cuidado',
    description: 'La longevidad de una prenda es la máxima expresión de la sostenibilidad. Aprende cómo mantener tus piezas Oulalab en perfecto estado durante tu rotación.',
    categories: [
      {
        title: "Limpieza Profesional",
        desc: "En Oulalab nos encargamos del proceso de limpieza profunda. No es necesario que laves las prendas antes de devolverlas; nuestro equipo utiliza tecnología de limpieza en seco eco-friendly."
      },
      {
        title: "Almacenamiento",
        desc: "Mantén las prendas en un lugar fresco y seco. Utiliza las perchas acolchadas que enviamos para mantener la estructura de los hombros en blazers y abrigos de alta costura."
      },
      {
        title: "Uso Consciente",
        desc: "Nuestras prendas son piezas de diseño. Evita el contacto directo con perfumes, aceites corporales o accesorios que puedan enganchar tejidos delicados como la seda o el encaje."
      },
      {
        title: "Luz y Temperatura",
        desc: "Evita exponer las prendas a la luz solar directa por tiempos prolongados para prevenir la decoloración de los tintes naturales y fibras orgánicas."
      }
    ],
    materials_title: 'Cuidados por Material',
    materials: [
      { mat: "Seda y Satén", care: "Extrema delicadeza. Evitar roces con bolsos de mimbre o superficies rugosas." },
      { mat: "Cueros y Cuerinas", care: "Si se moja por la lluvia, secar con un paño suave a temperatura ambiente. No aplicar calor." },
      { mat: "Lana y Cachemira", care: "No colgar las piezas de punto pesado; guardarlas dobladas para que no pierdan su forma original." }
    ],
    cta_title: '¿Tienes una duda específica?',
    cta_desc: 'Nuestro equipo de expertos en textiles está disponible para asesorarte.',
    cta_btn: 'Contactar Concierge'
  },
  en: {
    tagline: 'Preserving Luxury',
    title_1: 'Care',
    title_2: 'Guide',
    description: 'The longevity of a garment is the ultimate expression of sustainability. Learn how to keep your Oulalab pieces in perfect condition during your rotation.',
    categories: [
      {
        title: "Professional Cleaning",
        desc: "At Oulalab, we take care of the deep cleaning process. You don't need to wash the garments before returning them; our team uses eco-friendly dry cleaning technology."
      },
      {
        title: "Storage",
        desc: "Keep garments in a cool, dry place. Use the padded hangers we provide to maintain the shoulder structure in blazers and haute couture coats."
      },
      {
        title: "Conscious Use",
        desc: "Our garments are designer pieces. Avoid direct contact with perfumes, body oils, or accessories that could snag delicate fabrics like silk or lace."
      },
      {
        title: "Light and Temperature",
        desc: "Avoid exposing garments to direct sunlight for prolonged periods to prevent the fading of natural dyes and organic fibers."
      }
    ],
    materials_title: 'Care by Material',
    materials: [
      { mat: "Silk and Satin", care: "Extreme delicacy. Avoid rubbing against wicker bags or rough surfaces." },
      { mat: "Leather and Faux Leather", care: "If it gets wet in the rain, dry with a soft cloth at room temperature. Do not apply heat." },
      { mat: "Wool and Cashmere", care: "Do not hang heavy knit pieces; store them folded so they do not lose their original shape." }
    ],
    cta_title: 'Have a specific question?',
    cta_desc: 'Our team of textile experts is available to assist you.',
    cta_btn: 'Contact Concierge'
  },
  pt: {
    tagline: 'Preservando o Luxo',
    title_1: 'Guia de',
    title_2: 'Cuidados',
    description: 'A longevidade de uma peça é a expressão máxima da sustentabilidade. Aprenda como manter suas peças Oulalab em perfeito estado durante sua rotação.',
    categories: [
      {
        title: "Limpeza Profissional",
        desc: "Na Oulalab, cuidamos do processo de limpeza profunda. Não é necessário lavar as roupas antes de devolvê-las; nossa equipe utiliza tecnologia de lavagem a seco ecológica."
      },
      {
        title: "Armazenamento",
        desc: "Mantenha as roupas em local fresco e seco. Use os cabides acolchoados que enviamos para manter a estrutura dos ombros em blazers e casacos de alta costura."
      },
      {
        title: "Uso Consciente",
        desc: "Nossas roupas são peças de design. Evite o contato direto com perfumes, óleos corporais ou acessórios que possam puxar fios de tecidos delicados como seda ou renda."
      },
      {
        title: "Luz e Temperatura",
        desc: "Evite expor as roupas à luz solar direta por períodos prolongados para evitar o desbotamento de corantes naturais e fibras orgânicas."
      }
    ],
    materials_title: 'Cuidados por Material',
    materials: [
      { mat: "Seda e Cetim", care: "Extrema delicadeza. Evite o atrito com bolsas de vime ou superfícies ásperas." },
      { mat: "Couros e Sintéticos", care: "Se molhar na chuva, seque com um pano macio em temperatura ambiente. Não aplique calor." },
      { mat: "Lã e Cashmere", care: "Não pendure peças de malha pesada; guarde-as dobradas para que não percam a forma original." }
    ],
    cta_title: 'Tem uma dúvida específica?',
    cta_desc: 'Nossa equipe de especialistas em têxteis está disponível para orientá-la.',
    cta_btn: 'Contatar Concierge'
  }
};

const Care: React.FC<CareProps> = ({ lang }) => {
  const t = CARE_CONTENT[lang];

  // Mantenemos los iconos separados para inyectarlos dinámicamente en el map
  const categoryIcons = [
    <Droplets className="w-8 h-8" />,
    <Wind className="w-8 h-8" />,
    <Scissors className="w-8 h-8" />,
    <Sun className="w-8 h-8" />
  ];

  return (
    <div className="bg-white min-h-screen pt-32 pb-20">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header Editorial */}
        <div className="text-center mb-24">
          <span className="text-[#DF3265] font-black tracking-[0.3em] uppercase text-sm mb-4 block">
            {t.tagline}
          </span>
          <h1 className="text-5xl md:text-8xl font-black tracking-tighter uppercase mb-8">
            {t.title_1} <br/><span className="text-gray-300 italic">{t.title_2}</span>
          </h1>
          <p className="max-w-2xl mx-auto text-xl text-gray-500 font-medium leading-relaxed">
            {t.description}
          </p>
        </div>

        {/* Grid de Consejos */}
        <div className="grid md:grid-cols-2 gap-12 mb-32">
          {t.categories.map((cat, idx) => (
            <div key={idx} className="group p-12 bg-gray-50 rounded-[3rem] hover:bg-black hover:text-white transition-all duration-700">
              <div className="text-[#DF3265] mb-8 group-hover:scale-110 transition-transform duration-500">
                {categoryIcons[idx]}
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
            <Sparkles className="mr-4 text-[#DF3265]" /> {t.materials_title}
          </h2>
          <div className="space-y-12">
            {t.materials.map((item, i) => (
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
          <h2 className="text-3xl font-black uppercase mb-4">{t.cta_title}</h2>
          <p className="text-gray-600 mb-8 font-medium">{t.cta_desc}</p>
          <a href="mailto:concierge@oulalab.com" className="inline-block bg-black text-white px-12 py-5 rounded-full font-black uppercase tracking-widest hover:bg-[#DF3265] transition-colors">
            {t.cta_btn}
          </a>
        </div>
      </div>
    </div>
  );
};

export default Care;
