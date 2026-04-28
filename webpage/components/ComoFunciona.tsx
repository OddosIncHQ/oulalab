import React from 'react';

// Importación de TODAS las imágenes (Respetando las extensiones exactas de tus últimos archivos)
import imgPaso1 from '../src/assets/plp.jpg';
import imgPaso2 from '../src/assets/pdp1.jpg'; // Nueva: Detalle de producto
import imgTryOn from '../src/assets/virtual-try-on.jpg'; // Try-On Panorámico
import imgPaso4 from '../src/assets/pdp2.png'; // Recomendador IA
import imgPaso5 from '../src/assets/mis-alquileres-1.png';

interface ComoFuncionaProps {
  lang: 'es' | 'en' | 'pt';
}

const STRINGS = {
  es: {
    tag: 'Tu clóset infinito a un click',
    title: '¿Cómo funciona Oulalab?',
    desc: 'Redefinimos tu forma de consumir moda combinando tecnología de vanguardia con las mejores marcas de alta costura a través de una suscripción mensual.',
    step1_title: 'Explora una colección exclusiva',
    step1_desc: 'Olvídate de comprar prendas que usarás una sola vez. Navega por nuestro extenso catálogo y descubre piezas exclusivas de la temporada actual de marcas como Zadig & Voltaire, Bimba y Lola, y Sandro.',
    step2_title: 'Conoce cada detalle',
    step2_desc: 'Accede a la ficha completa de cada prenda. Revisa fotografías de alta calidad, conoce su composición, materiales y descubre la historia detrás de cada diseño antes de elegir.',
    step3_title: 'Crea tu avatar y pruébatelo todo',
    step3_desc: 'Con nuestra tecnología de Virtual Try-On, solo necesitas subir una foto tuya. En segundos, el sistema procesa tu imagen y te permite visualizar cómo te queda cada prenda de forma ultra realista.',
    step4_title: 'Ajuste perfecto con Inteligencia Artificial',
    step4_desc: 'Además de verte con la ropa, nuestro recomendador analiza tu colorimetría y medidas exactas para asegurar un ajuste impecable. Es como tener un Personal Shopper en tu bolsillo.',
    step5_title: 'Suscríbete, recibe y renueva tu estilo',
    step5_desc: 'Elige tu plan, selecciona tus prendas y recíbelas a domicilio. A los 15 días puedes realizar "swaps" para refrescar tu look, y al finalizar el mes coordinamos el retiro para que tu ciclo vuelva a comenzar.'
  },
  en: {
    tag: 'Your infinite closet just a click away',
    title: 'How does Oulalab work?',
    desc: 'We redefine how you consume fashion by combining cutting-edge technology with top haute couture brands through a monthly subscription.',
    step1_title: 'Explore an exclusive collection',
    step1_desc: "Forget buying clothes you'll only wear once. Browse our extensive catalog and discover exclusive current-season pieces from brands like Zadig & Voltaire, Bimba y Lola, and Sandro.",
    step2_title: 'Know every detail',
    step2_desc: 'Access the full profile of each garment. Review high-quality photographs, learn about its composition, materials, and discover the story behind each design before choosing.',
    step3_title: 'Create your avatar and try everything on',
    step3_desc: 'With our Virtual Try-On technology, you just need to upload a photo of yourself. In seconds, the system processes your image and lets you visualize how every garment looks on you ultra-realistically.',
    step4_title: 'Perfect fit with Artificial Intelligence',
    step4_desc: 'Besides seeing yourself in the clothes, our recommender analyzes your colorimetry and exact measurements to ensure flawless fit. It is like having a Personal Shopper in your pocket.',
    step5_title: 'Subscribe, receive, and renew your style',
    step5_desc: 'Choose your plan, select your garments, and receive them at home. After 15 days, you can make "swaps" to refresh your look, and at the end of the month, we coordinate the pickup.'
  },
  pt: {
    tag: 'Seu closet infinito a um clique',
    title: 'Como funciona a Oulalab?',
    desc: 'Redefinimos sua forma de consumir moda combinando tecnologia de ponta com as melhores marcas de alta-costura através de uma assinatura mensal.',
    step1_title: 'Explore uma coleção exclusiva',
    step1_desc: 'Esqueça comprar roupas que você só vai usar uma vez. Navegue pelo nosso extenso catálogo e descubra peças exclusivas da temporada atual de marcas como Zadig & Voltaire, Bimba y Lola e Sandro.',
    step2_title: 'Conheça cada detalhe',
    step2_desc: 'Acesse a ficha completa de cada peça. Revise fotografias de alta qualidade, conheça sua composição, materiais e descubra a história por trás de cada design antes de escolher.',
    step3_title: 'Crie seu avatar e experimente tudo',
    step3_desc: 'Com nossa tecnologia de Virtual Try-On, você só precisa enviar uma foto sua. Em segundos, o sistema processa sua imagem e permite visualizar de forma ultra-realista como cada peça fica em você.',
    step4_title: 'Caimento perfeito com Inteligência Artificial',
    step4_desc: 'Além de se ver com as roupas, nosso recomendador analisa sua colorimetria e medidas exatas para garantir um caimento impecável. É como ter um Personal Shopper no seu bolso.',
    step5_title: 'Assine, receba e renove seu estilo',
    step5_desc: 'Escolha seu plano, selecione suas roupas e receba em casa. Após 15 dias, você pode fazer "swaps" para renovar seu look, e no final do mês coordenamos a retirada.'
  }
};

const ComoFunciona: React.FC<ComoFuncionaProps> = ({ lang }) => {
  const t = STRINGS[lang];

  return (
    <section id="how-it-works" className="py-24 bg-white overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        
        {/* Cabecera */}
        <div className="text-center mb-20">
          <h2 className="text-base font-black text-[#DF3265] tracking-widest uppercase">
            {t.tag}
          </h2>
          <p className="mt-2 text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl">
            {t.title}
          </p>
          <p className="mt-4 max-w-2xl text-xl text-gray-500 mx-auto">
            {t.desc}
          </p>
        </div>

        <div className="space-y-32">
          
          {/* PASO 1 - PLP */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">
                1
              </div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">
                {t.step1_title}
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                {t.step1_desc}
              </p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img 
                src={imgPaso1} 
                alt="Catálogo Oulalab" 
                className="rounded-[2.5rem] md:rounded-[3rem] shadow-2xl border-[8px] border-gray-100 w-full max-w-[320px] md:max-w-[360px] aspect-[9/16] object-cover object-top transition-transform duration-500 group-hover:scale-105"
              />
            </div>
          </div>

          {/* PASO 2 - PDP Detalle (pdp1.jpg) */}
          <div className="flex flex-col-reverse lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img 
                src={imgPaso2} 
                alt="Detalle de Prenda" 
                className="rounded-[2.5rem] md:rounded-[3rem] shadow-2xl border-[8px] border-gray-100 w-full max-w-[320px] md:max-w-[360px] aspect-[9/16] object-cover object-top transition-transform duration-500 group-hover:scale-105"
              />
            </div>
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">
                2
              </div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">
                {t.step2_title}
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                {t.step2_desc}
              </p>
            </div>
          </div>

          {/* PASO 3 - TRY ON FLOW Panorámico */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">
                3
              </div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">
                {t.step3_title}
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                {t.step3_desc}
              </p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img 
                src={imgTryOn} 
                alt="Flujo de Virtual Try-On" 
                className="rounded-[1.5rem] shadow-2xl border-[4px] border-gray-100 w-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
            </div>
          </div>

          {/* PASO 4 - PDP Recomendador (pdp2.png) */}
          <div className="flex flex-col-reverse lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img 
                src={imgPaso4} 
                alt="Recomendaciones de IA Oulalab" 
                className="rounded-[2.5rem] md:rounded-[3rem] shadow-2xl border-[8px] border-gray-100 w-full max-w-[320px] md:max-w-[360px] aspect-[9/16] object-cover object-top transition-transform duration-500 group-hover:scale-105"
              />
            </div>
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">
                4
              </div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">
                {t.step4_title}
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                {t.step4_desc}
              </p>
            </div>
          </div>

          {/* PASO 5 - MIS ALQUILERES */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">
                5
              </div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">
                {t.step5_title}
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                {t.step5_desc}
              </p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img 
                src={imgPaso5} 
                alt="Mis Alquileres Oulalab" 
                className="rounded-[2.5rem] md:rounded-[3rem] shadow-2xl border-[8px] border-gray-100 w-full max-w-[320px] md:max-w-[360px] aspect-[9/16] object-cover object-top transition-transform duration-500 group-hover:scale-105"
              />
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default ComoFunciona;
