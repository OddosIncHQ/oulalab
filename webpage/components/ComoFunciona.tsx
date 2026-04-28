import React from 'react';

// Importación de imágenes con la ruta corregida apuntando a src/assets
import imgPaso1 from '../src/assets/paso1.png';
import imgPaso2 from '../src/assets/paso2.png';
import imgPaso3 from '../src/assets/paso3.png';

const ComoFunciona: React.FC = () => {
  return (
    <section id="how-it-works-detail" className="py-24 bg-white overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        
        {/* Cabecera */}
        <div className="text-center mb-20">
          <h2 className="text-base font-semibold text-[#E91E63] tracking-wide uppercase">
            Proceso Simple
          </h2>
          <p className="mt-2 text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl">
            ¿Cómo funciona Oulalab?
          </p>
          <p className="mt-4 max-w-2xl text-xl text-gray-500 mx-auto">
            Automatiza la recolección de feedback y mejora la experiencia de tus clientes en tres pasos sencillos.
          </p>
        </div>

        <div className="space-y-24">
          
          {/* PASO 1 */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-pink-100 text-[#E91E63] font-bold text-xl mb-6">
                1
              </div>
              <h3 className="text-3xl font-bold text-gray-900 mb-4">
                Configura tus reglas de envío
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed">
                Desde tu panel de administración, conecta tu tienda y define cuándo se enviarán las solicitudes de feedback. Tú tienes el control total.
              </p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center">
              <img 
                src={imgPaso1} 
                alt="Configuración Oulalab" 
                className="rounded-2xl shadow-2xl border border-gray-100 w-full max-w-lg"
              />
            </div>
          </div>

          {/* PASO 2 */}
          <div className="flex flex-col-reverse lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="mt-10 lg:mt-0 flex justify-center">
              <img 
                src={imgPaso2} 
                alt="Experiencia del Cliente" 
                className="rounded-2xl shadow-2xl border border-gray-100 w-full max-w-lg"
              />
            </div>
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-pink-100 text-[#E91E63] font-bold text-xl mb-6">
                2
              </div>
              <h3 className="text-3xl font-bold text-gray-900 mb-4">
                Tus clientes evalúan su experiencia
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed">
                Tus clientes reciben un email personalizado y profesional. Pueden calificar su experiencia en segundos, asegurando altas tasas de respuesta.
              </p>
            </div>
          </div>

          {/* PASO 3 */}
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center">
            <div className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-pink-100 text-[#E91E63] font-bold text-xl mb-6">
                3
              </div>
              <h3 className="text-3xl font-bold text-gray-900 mb-4">
                Analiza datos y toma mejores decisiones
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed">
                Visualiza el sentimiento de tus clientes en tiempo real e identifica puntos críticos de mejora con métricas claras como NPS.
              </p>
            </div>
            <div className="mt-10 lg:mt-0 flex justify-center">
              <img 
                src={imgPaso3} 
                alt="Dashboard Oulalab" 
                className="rounded-2xl shadow-2xl border border-gray-100 w-full max-w-lg"
              />
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default ComoFunciona;
