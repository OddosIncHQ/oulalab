import React from 'react';

// Importación de imágenes desde assets
import imgPaso1 from '../assets/paso1.png';
import imgPaso2 from '../assets/paso2.png';
// Cambiamos a .jpg para que coincida con tu archivo real
import imgPaso3 from '../assets/paso3.jpg'; 

const ComoFunciona: React.FC = () => {
  return (
    <section id="how-it-works" className="py-24 bg-white overflow-hidden scroll-mt-20">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        
        <div className="text-center mb-20">
          <h2 className="text-base font-semibold text-[#E91E63] tracking-wide uppercase">
            Proceso Simple
          </h2>
          <p className="mt-2 text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl uppercase italic leading-none">
            ¿Cómo funciona Oulalab?
          </p>
        </div>

        <div className="space-y-24">
          
          {/* PASO 1 */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-pink-100 text-[#E91E63] font-black text-xl mb-6 shadow-sm">
                1
              </div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 uppercase tracking-tighter">
                Configura tus reglas de envío
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                Desde tu panel de administración, conecta tu tienda y define cuándo se enviarán las solicitudes de feedback. Automatiza los correos con control total.
              </p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center">
              <img 
                src={imgPaso1} 
                alt="Configuración Oulalab" 
                className="rounded-[2.5rem] shadow-2xl border border-gray-100 w-full max-w-lg transform hover:scale-105 transition-transform duration-500"
              />
            </div>
          </div>

          {/* PASO 2 */}
          <div className="flex flex-col-reverse lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="mt-10 lg:mt-0 flex justify-center">
              <img 
                src={imgPaso2} 
                alt="Experiencia del Cliente" 
                className="rounded-[2.5rem] shadow-2xl border border-gray-100 w-full max-w-lg transform hover:scale-105 transition-transform duration-500"
              />
            </div>
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-pink-100 text-[#E91E63] font-black text-xl mb-6 shadow-sm">
                2
              </div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 uppercase tracking-tighter">
                Tus clientes evalúan su experiencia
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                Tus clientes reciben un email personalizado. Con un sistema de estrellas intuitivo, califican su experiencia en segundos, asegurando alta participación.
              </p>
            </div>
          </div>

          {/* PASO 3 */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-pink-100 text-[#E91E63] font-black text-xl mb-6 shadow-sm">
                3
              </div>
              <h3 className="text-3xl font-black text-gray-900 mb-4 uppercase tracking-tighter">
                Analiza datos y toma mejores decisiones
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed font-medium">
                Visualiza el NPS y CSAT en tiempo real. Identifica puntos críticos de mejora y celebra los éxitos con métricas claras y accionables.
              </p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center">
              <img 
                src={imgPaso3} 
                alt="Dashboard Oulalab" 
                className="rounded-[2.5rem] shadow-2xl border border-gray-100 w-full max-w-lg transform hover:scale-105 transition-transform duration-500"
              />
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default ComoFunciona;
