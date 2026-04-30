import React from 'react';

// Importación de imágenes
import imgPaso2 from '../src/assets/pdp1.png';
import imgPaso4 from '../src/assets/pdp2.png';

// Importación de videos (Asegúrate de que los nombres coincidan exactamente en tu carpeta)
import vidPaso1 from '../src/assets/vid-2.mp4'; // App y catálogo
import vidPaso3 from '../src/assets/vid-1.mp4'; // Virtual Try-On
import vidPaso5 from '../src/assets/vid-3.mp4'; // Recibiendo el pedido

interface ComoFuncionaProps {
  lang: 'es' | 'en' | 'pt';
}

const STRINGS = {
  es: {
    tag: 'Tu clóset infinito a un click',
    title: '¿Cómo funciona Oulalab?',
    desc: 'Redefinimos tu forma de consumir moda combinando tecnología de vanguardia con las mejores marcas de alta costura.',
    step1_title: 'Explora una colección exclusiva',
    step1_desc: 'Navega por nuestro extenso catálogo y descubre piezas exclusivas de la temporada actual de marcas como Zadig & Voltaire, Bimba y Lola, y Sandro.',
    step2_title: 'Conoce cada detalle',
    step2_desc: 'Accede a la ficha completa. Revisa fotografías de alta calidad, conoce su composición y descubre la historia detrás de cada diseño.',
    step3_title: 'Crea tu avatar y pruébatelo todo',
    step3_desc: 'Con nuestra tecnología de Virtual Try-On, visualiza cómo te queda cada prenda de forma ultra realista antes de pedirla.',
    step4_title: 'Ajuste perfecto con IA',
    step4_desc: 'Nuestro recomendador analiza tu colorimetría y medidas exactas para asegurar un ajuste impecable. Un Personal Shopper en tu bolsillo.',
    step5_title: 'Suscríbete, recibe y renueva',
    step5_desc: 'Elige tu plan, recibe tus prendas y cámbialas cada 15 días para refrescar tu look. Nosotros coordinamos el retiro por ti.',
  },
  en: {
    tag: 'Your infinite closet just a click away',
    title: 'How does Oulalab work?',
    desc: 'We redefine how you consume fashion by combining cutting-edge technology with top haute couture brands.',
    step1_title: 'Explore an exclusive collection',
    step1_desc: "Browse our extensive catalog and discover exclusive current-season pieces from leading brands.",
    step2_title: 'Know every detail',
    step2_desc: 'Access the full profile. Review high-quality photographs and learn the story behind each design.',
    step3_title: 'Create your avatar and try it on',
    step3_desc: 'With our Virtual Try-On technology, visualize how every garment looks on you ultra-realistically.',
    step4_title: 'Perfect fit with AI',
    step4_desc: 'Our recommender analyzes your colorimetry and exact measurements to ensure a flawless fit.',
    step5_title: 'Subscribe, receive, and renew',
    step5_desc: 'Choose your plan, receive your garments, and make swaps every 15 days to refresh your look.',
  },
  pt: {
    tag: 'Seu closet infinito a um clique',
    title: 'Como funciona a Oulalab?',
    desc: 'Redefinimos sua forma de consumir moda combinando tecnologia de ponta com as melhores marcas de alta-costura.',
    step1_title: 'Explore uma coleção exclusiva',
    step1_desc: 'Navegue pelo nosso extenso catálogo e descubra peças exclusivas da temporada atual.',
    step2_title: 'Conheça cada detalhe',
    step2_desc: 'Acesse a ficha completa de cada peça e conheça sua composição e materiais.',
    step3_title: 'Crie seu avatar e experimente tudo',
    step3_desc: 'Com nossa tecnologia de Virtual Try-On, veja como cada peça fica em você de forma ultra-realista.',
    step4_title: 'Caimento perfeito com IA',
    step4_desc: 'Nosso recomendador analisa sua colorimetria e medidas para garantir um caimento impecável.',
    step5_title: 'Assine, receba e renove seu estilo',
    step5_desc: 'Escolha seu plano, receba em casa e faça "swaps" a cada 15 dias para renovar seu look.',
  }
};

const ComoFunciona: React.FC<ComoFuncionaProps> = ({ lang }) => {
  const t = STRINGS[lang];

  // Definimos una clase común para el "Marco de Celular" para mantener consistencia
  const phoneFrameClass = "rounded-[2.5rem] md:rounded-[3rem] shadow-2xl border-[8px] border-gray-100 w-full max-w-[320px] md:max-w-[360px] aspect-[9/16] object-cover transition-transform duration-500 group-hover:scale-105 bg-black";

  return (
    <section id="how-it-works" className="py-24 bg-white overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        
        {/* Cabecera */}
        <div className="text-center mb-20">
          <h2 className="text-base font-black text-[#DF3265] tracking-widest uppercase">{t.tag}</h2>
          <p className="mt-2 text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl">{t.title}</p>
          <p className="mt-4 max-w-2xl text-xl text-gray-500 mx-auto">{t.desc}</p>
        </div>

        <div className="space-y-32">
          
          {/* PASO 1 - VIDEO: Catálogo (vid-2) */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">1</div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">{t.step1_title}</h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">{t.step1_desc}</p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <video autoPlay muted loop playsInline className={phoneFrameClass}>
                <source src={vidPaso1} type="video/mp4" />
              </video>
            </div>
          </div>

          {/* PASO 2 - IMAGEN: Detalle (pdp1) */}
          <div className="flex flex-col-reverse lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img src={imgPaso2} alt="Detalle" className={phoneFrameClass + " object-top"} />
            </div>
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">2</div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">{t.step2_title}</h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">{t.step2_desc}</p>
            </div>
          </div>

          {/* PASO 3 - VIDEO: Virtual Try-On (vid-1) */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">3</div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">{t.step3_title}</h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">{t.step3_desc}</p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <video autoPlay muted loop playsInline className={phoneFrameClass}>
                <source src={vidPaso3} type="video/mp4" />
              </video>
            </div>
          </div>

          {/* PASO 4 - IMAGEN: Recomendador (pdp2) */}
          <div className="flex flex-col-reverse lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img src={imgPaso4} alt="Recomendador IA" className={phoneFrameClass + " object-top"} />
            </div>
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">4</div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">{t.step4_title}</h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">{t.step4_desc}</p>
            </div>
          </div>

          {/* PASO 5 - VIDEO: Recibe y Renueva (vid-3) */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">5</div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">{t.step5_title}</h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">{t.step5_desc}</p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <video autoPlay muted loop playsInline className={phoneFrameClass}>
                <source src={vidPaso5} type="video/mp4" />
              </video>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default ComoFunciona;
