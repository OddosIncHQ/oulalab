import React, { useState } from 'react';
import { Play, X } from 'lucide-react';

// 1. Importación actualizada con la extensión .MOV (o .mov si lo renombraste)
import videoTutorial from '../src/assets/tutorial-registro.MOV'; 

const Planes: React.FC = () => {
  const [isVideoOpen, setIsVideoOpen] = useState(false);

  return (
    <section id="planes" className="py-24 bg-gray-50 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        
        {/* Cabecera de la sección */}
        <div className="text-center mb-16">
          <h2 className="text-base font-black text-[#DF3265] tracking-widest uppercase mb-4">
            Membresías
          </h2>
          <p className="text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl mb-6">
            Elige la rotación perfecta para tu estilo
          </p>
          
          {/* BOTÓN PARA ABRIR VIDEO */}
          <button 
            onClick={() => setIsVideoOpen(true)}
            className="inline-flex items-center space-x-3 bg-white border border-gray-200 px-6 py-3 rounded-full shadow-sm hover:shadow-md hover:border-[#DF3265] transition-all duration-300 group"
          >
            <div className="bg-[#F7E8F7] p-2 rounded-full text-[#DF3265] group-hover:bg-[#DF3265] group-hover:text-white transition-colors">
              <Play size={18} fill="currentColor" />
            </div>
            <span className="text-sm font-bold text-gray-700 uppercase tracking-wider">
              Mira cómo suscribirte en 30 segundos
            </span>
          </button>
        </div>

        {/* AQUÍ IRÍA TU GRUPO DE TARJETAS DE PLANES (LUXURY, PREMIUM, ETC.) */}
        <div className="grid md:grid-cols-3 gap-8">
            {/* Ejemplo de tarjeta de plan */}
            <div className="bg-white p-8 rounded-[2.5rem] border border-gray-100 shadow-xl">
                {/* Contenido del plan... */}
            </div>
            {/* ... otros planes */}
        </div>
      </div>

      {/* MODAL DEL VIDEO */}
      {isVideoOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/90 backdrop-blur-sm transition-all">
          <div className="relative w-full max-w-sm bg-black rounded-3xl overflow-hidden shadow-2xl">
            
            {/* Botón Cerrar */}
            <button 
              onClick={() => setIsVideoOpen(false)}
              className="absolute top-4 right-4 z-10 bg-white/10 hover:bg-white/20 text-white p-2 rounded-full transition-colors"
            >
              <X size={24} />
            </button>

            {/* 2. Etiqueta de Video actualizada para soportar .MOV */}
            <video 
              controls 
              autoPlay 
              playsInline
              className="w-full h-auto max-h-[80vh] object-contain"
            >
              <source src={videoTutorial} type="video/quicktime" />
              Tu navegador no soporta la reproducción de este video.
            </video>
          </div>

          {/* Área fuera del video para cerrar al hacer clic */}
          <div 
            className="absolute inset-0 -z-10" 
            onClick={() => setIsVideoOpen(false)}
          ></div>
        </div>
      )}
    </section>
  );
};

export default Planes;
