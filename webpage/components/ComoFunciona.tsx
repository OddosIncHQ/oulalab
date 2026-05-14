import React, { useEffect, useRef } from 'react';

// Importación de imágenes
import imgPaso2 from '../src/assets/pdp1.png';
import imgPaso4 from '../src/assets/pdp2.png';

// Importación de videos
import vidPaso1 from '../src/assets/vid-2.mp4'; 
import vidPaso3 from '../src/assets/vid-1.mp4'; 
import vidPaso5 from '../src/assets/vid-3.mp4'; 

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
    step4_desc: 'Nuestro recomendador analiza tu colorimetría y medidas exactas para asegurar un ajuste impecable. Un Personal Stylist en tu bolsillo.',
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

  // Referencias para forzar la reproducción de los videos
  const videoRef1 = useRef<HTMLVideoElement>(null);
  const videoRef3 = useRef<HTMLVideoElement>(null);
  const videoRef5 = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const playVideo = (ref: React.RefObject<HTMLVideoElement>) => {
      if (ref.current) {
        ref.current.defaultMuted = true;
        ref.current.muted = true;
        ref.current.play().catch(error => console.log("Autoplay prevented:", error));
      }
    };
    playVideo(videoRef1);
    playVideo(videoRef3);
    playVideo(videoRef5);
  }, []);

  const phoneFrameClass = "rounded-[2.5rem] md:rounded-[3rem] shadow-2xl border-[8px] border-gray-100 w-full max-w-[280px] sm:max-w-[320px] md:max-w-[360px] aspect-[9/16] object-cover transition-transform duration-500 group-hover:scale-105 bg-black";

  return (
    <section id="how-it-works" className="py-20 md:py-32 bg-white overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        
        {/* Cabecera */}
        <div className="text-center mb-16 md:mb-24">
          <span className="text-[10px] md:text-xs font-black tracking-widest uppercase text-gray-400 mb-4 md:mb-6 block">
            {t.tag}
          </span>
          {/* Título adaptado a Claven Responsivo */}
          <h2 className="font-claven text-4xl md:text-5xl lg:text-7xl font-black tracking-tighter uppercase mb-6 md:mb-8 leading-none">
            {t.title}
          </h2>
          <p className="max-w-2xl mx-auto text-lg md:text-xl text-gray-600 font-medium leading-relaxed">
            {t.desc}
          </p>
        </div>

        <div className="space-y-24 md:space-y-32">
          
          {/* PASO 1 - VIDEO */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative text-center lg:text-left mb-10 lg:mb-0">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6 mx-auto lg:mx-0">1</div>
              {/* Títulos de pasos adaptados a Claven Responsivo */}
              <h3 className="font-claven text-3xl md:text-4xl lg:text-5xl font-black uppercase tracking-tighter mb-4 md:mb-6 leading-[0.9]">
                {t.step1_title}
              </h3>
              <p className="text-base md:text-lg text-gray-600 leading-relaxed font-medium">{t.step1_desc}</p>
            </div>
            <div className="flex justify-center group">
              <video ref={videoRef1} autoPlay={true} muted={true} loop={true} playsInline={true} className={phoneFrameClass}>
                <source src={vidPaso1} type="video/mp4" />
              </video>
            </div>
          </div>

          {/* PASO 2 - IMAGEN */}
          <div className="flex flex-col-reverse lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img src={imgPaso2} alt="Detalle" className={phoneFrameClass + " object-top"} />
            </div>
            <div className="relative text-center lg:text-left">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6 mx-auto lg:mx-0">2</div>
              <h3 className="font-claven text-3xl md:text-4xl lg:text-5xl font-black uppercase tracking-tighter mb-4 md:mb-6 leading-[0.9]">
                {t.step2_title}
              </h3>
              <p className="text-base md:text-lg text-gray-600 leading-relaxed font-medium">{t.step2_desc}</p>
            </div>
          </div>

          {/* PASO 3 - VIDEO */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative text-center lg:text-left mb-10 lg:mb-0">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6 mx-auto lg:mx-0">3</div>
              <h3 className="font-claven text-3xl md:text-4xl lg:text-5xl font-black uppercase tracking-tighter mb-4 md:mb-6 leading-[0.9]">
                {t.step3_title}
              </h3>
              <p className="text-base md:text-lg text-gray-600 leading-relaxed font-medium">{t.step3_desc}</p>
            </div>
            <div className="flex justify-center group">
              <video ref={videoRef3} autoPlay={true} muted={true} loop={true} playsInline={true} className={phoneFrameClass}>
                <source src={vidPaso3} type="video/mp4" />
              </video>
            </div>
          </div>

          {/* PASO 4 - IMAGEN */}
          <div className="flex flex-col-reverse lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img src={imgPaso4} alt="Recomendador IA" className={phoneFrameClass + " object-top"} />
            </div>
            <div className="relative text-center lg:text-left">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6 mx-auto lg:mx-0">4</div>
              <h3 className="font-claven text-3xl md:text-4xl lg:text-5xl font-black uppercase tracking-tighter mb-4 md:mb-6 leading-[0.9]">
                {t.step4_title}
              </h3>
              <p className="text-base md:text-lg text-gray-600 leading-relaxed font-medium">{t.step4_desc}</p>
            </div>
          </div>

          {/* PASO 5 - VIDEO */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative text-center lg:text-left mb-10 lg:mb-0">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6 mx-auto lg:mx-0">5</div>
              <h3 className="font-claven text-3xl md:text-4xl lg:text-5xl font-black uppercase tracking-tighter mb-4 md:mb-6 leading-[0.9]">
                {t.step5_title}
              </h3>
              <p className="text-base md:text-lg text-gray-600 leading-relaxed font-medium">{t.step5_desc}</p>
            </div>
            <div className="flex justify-center group">
              <video ref={videoRef5} autoPlay={true} muted={true} loop={true} playsInline={true} className={phoneFrameClass}>
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
