import React from 'react';

import imgPaso1 from '../src/assets/plp.png';
import imgPaso2 from '../src/assets/pdp.png';
import imgPaso3 from '../src/assets/mis-alquileres-1.png';

// 1. Definimos que este componente va a recibir el idioma ("lang")
interface ComoFuncionaProps {
  lang: 'es' | 'en' | 'pt';
}

// 2. Diccionario de traducciones exclusivo para esta sección
const STRINGS = {
  es: {
    tag: 'Tu clóset infinito a un click',
    title: '¿Cómo funciona Oulalab?',
    desc: 'Redefinimos tu forma de consumir moda combinando tecnología de vanguardia con las mejores marcas de alta costura a través de una suscripción mensual.',
    step1_title: 'Explora una colección exclusiva y de temporada',
    step1_desc: 'Olvídate de comprar prendas que usarás una sola vez. Navega por nuestro extenso catálogo y descubre piezas exclusivas de marcas como Zadig & Voltaire, Bimba y Lola, Sandro y muchas más. Todo lo que siempre quisiste usar, ahora a tu alcance.',
    step2_title: 'Pruébatelo todo con Inteligencia Artificial',
    step2_desc: 'Nuestra tecnología transforma tu celular en un probador virtual. Sube una foto y mira cómo lucirá la prenda en tu cuerpo antes de pedirla. Además, nuestro recomendador analiza tu colorimetría y medidas para asegurar un ajuste perfecto.',
    step3_title: 'Suscríbete, recibe y renueva tu estilo',
    step3_desc: 'Elige tu plan, selecciona tus prendas y recíbelas en la puerta de tu casa. A los 15 días puedes realizar "swaps" para refrescar tu look, y al finalizar el mes coordinamos el retiro para que tu clóset infinito vuelva a comenzar.'
  },
  en: {
    tag: 'Your infinite closet just a click away',
    title: 'How does Oulalab work?',
    desc: 'We redefine how you consume fashion by combining cutting-edge technology with top haute couture brands through a monthly subscription.',
    step1_title: 'Explore an exclusive, in-season collection',
    step1_desc: "Forget buying clothes you'll only wear once. Browse our extensive catalog and discover exclusive pieces from brands like Zadig & Voltaire, Bimba y Lola, Sandro, and many more. Everything you've always wanted to wear, now within your reach.",
    step2_title: 'Try everything on with Artificial Intelligence',
    step2_desc: 'Our technology turns your phone into a virtual fitting room. Upload a photo and see how the garment will look on your body before ordering. Plus, our recommender analyzes your colorimetry and measurements to ensure a perfect fit.',
    step3_title: 'Subscribe, receive, and renew your style',
    step3_desc: 'Choose your plan, select your garments, and receive them at your doorstep. After 15 days, you can make "swaps" to refresh your look, and at the end of the month, we coordinate the pickup so your infinite closet can start over.'
  },
  pt: {
    tag: 'Seu closet infinito a um clique',
    title: 'Como funciona a Oulalab?',
    desc: 'Redefinimos sua forma de consumir moda combinando tecnologia de ponta com las melhores marcas de alta-costura através de uma assinatura mensal.',
    step1_title: 'Explore uma coleção exclusiva e da temporada',
    step1_desc: 'Esqueça comprar roupas que você só vai usar uma vez. Navegue pelo nosso extenso catálogo e descubra peças exclusivas de marcas como Zadig & Voltaire, Bimba y Lola, Sandro e muitas outras. Tudo o que você sempre quis usar, agora ao seu alcance.',
    step2_title: 'Experimente tudo com Inteligência Artificial',
    step2_desc: 'Nossa tecnología transforma seu celular em un provador virtual. Envie uma foto e veja como a peça ficará no seu corpo antes de fazer o pedido. Además, nosso recomendador analisa sua colorimetría y medidas para garantir um caimento perfeito.',
    step3_title: 'Assine, receba e renove seu estilo',
    step3_desc: 'Escolha seu plano, selecione suas roupas e receba na porta de casa. Após 15 dias, você pode fazer "swaps" para renovar seu look, e no final do mês coordenamos a retirada para que seu closet infinito possa recomeçar.'
  }
};

const ComoFunciona: React.FC<ComoFuncionaProps> = ({ lang }) => {
  const t = STRINGS[lang]; // Obtenemos el idioma actual

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

        <div className="space-y-24">
          
          {/* PASO 1 */}
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
                {/* CAMBIO: Se cambió object-top por object-center para mostrar la mitad de la imagen */}
                className="rounded-[2.5rem] md:rounded-[3rem] shadow-2xl border-[8px] border-gray-100 w-full max-w-[320px] md:max-w-[360px] aspect-[9/16] object-cover object-center transition-transform duration-500 group-hover:scale-105"
              />
            </div>
          </div>

          {/* PASO 2 */}
          <div className="flex flex-col-reverse lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img 
                src={imgPaso2} 
                alt="Virtual Try-On Oulalab" 
                {/* CAMBIO: Se cambió object-top por object-center para mostrar la mitad de la imagen */}
                className="rounded-[2.5rem] md:rounded-[3rem] shadow-2xl border-[8px] border-gray-100 w-full max-w-[320px] md:max-w-[360px] aspect-[9/16] object-cover object-center transition-transform duration-500 group-hover:scale-105"
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

          {/* PASO 3 */}
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
                src={imgPaso3} 
                alt="Mis Alquileres Oulalab" 
                {/* Nota: Este paso se mantiene object-top como estaba, ya que no se solicitó cambio */}
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
