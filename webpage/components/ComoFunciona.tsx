import React from 'react';

// Importación de las nuevas imágenes con nombres optimizados para web
import imgPaso1 from '../src/assets/plp.jpg';
import imgPaso2 from '../src/assets/pdp.jpg';
import imgPaso3 from '../src/assets/mis-alquileres-1.png';

const ComoFunciona: React.FC = () => {
  return (
    <section id="how-it-works" className="py-24 bg-white overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        
        {/* Cabecera */}
        <div className="text-center mb-20">
          <h2 className="text-base font-black text-[#DF3265] tracking-widest uppercase">
            Tu clóset infinito a un click
          </h2>
          <p className="mt-2 text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl">
            ¿Cómo funciona Oulalab?
          </p>
          <p className="mt-4 max-w-2xl text-xl text-gray-500 mx-auto">
            Redefinimos tu forma de consumir moda combinando tecnología de vanguardia con las mejores marcas de alta costura a través de una suscripción mensual.
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
                Explora una colección exclusiva y de temporada
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                Olvídate de comprar prendas que usarás una sola vez. Navega por nuestro extenso catálogo y descubre piezas exclusivas de marcas como Zadig & Voltaire, Bimba y Lola, Sandro y muchas más. Todo lo que siempre quisiste usar, ahora a tu alcance.
              </p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img 
                src={imgPaso1} 
                alt="Catálogo Oulalab" 
                className="rounded-[2rem] shadow-2xl border border-gray-100 w-full max-w-sm transition-transform duration-500 group-hover:scale-105 object-cover"
              />
            </div>
          </div>

          {/* PASO 2 */}
          <div className="flex flex-col-reverse lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img 
                src={imgPaso2} 
                alt="Virtual Try-On Oulalab" 
                className="rounded-[2rem] shadow-2xl border border-gray-100 w-full max-w-sm transition-transform duration-500 group-hover:scale-105 object-cover"
              />
            </div>
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F7E8F7] text-[#DF3265] font-black text-xl mb-6">
                2
              </div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 tracking-tighter">
                Pruébatelo todo con Inteligencia Artificial
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                Nuestra tecnología transforma tu celular en un probador virtual. Sube una foto y mira cómo lucirá la prenda en tu cuerpo antes de pedirla. Además, nuestro recomendador analiza tu colorimetría y medidas para asegurar un ajuste perfecto.
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
                Suscríbete, recibe y renueva tu estilo
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                Elige tu plan, selecciona tus prendas y recíbelas en la puerta de tu casa. A los 15 días puedes realizar "swaps" para refrescar tu look, y al finalizar el mes coordinamos el retiro para que tu clóset infinito vuelva a comenzar.
              </p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center group">
              <img 
                src={imgPaso3} 
                alt="Mis Alquileres Oulalab" 
                className="rounded-[2rem] shadow-2xl border border-gray-100 w-full max-w-sm transition-transform duration-500 group-hover:scale-105 object-cover"
              />
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default ComoFunciona;
