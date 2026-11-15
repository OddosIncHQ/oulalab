import React, { useState } from 'react';
import { Diamond, Crown, Star } from 'lucide-react';

const Planes: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'subscription' | 'single'>('subscription');

  return (
    <section className="py-20 md:py-32 bg-gray-50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16 md:mb-24">
          <span className="text-[#DF3265] font-black tracking-[0.3em] uppercase text-[10px] md:text-xs mb-4 md:mb-6 block">
            Tu Clóset, a tu Manera
          </span>
          {/* Título en Claven Responsivo (Mismo escalado que el resto) */}
          <h2 className="font-claven text-4xl md:text-5xl lg:text-7xl font-black tracking-tighter uppercase mb-8 md:mb-12">
            La Experiencia
          </h2>
          
          <div className="inline-flex flex-col sm:flex-row bg-white p-2 rounded-3xl sm:rounded-full shadow-lg border border-gray-100 gap-2 sm:gap-0">
            <button 
              onClick={() => setActiveTab('subscription')}
              className={`px-6 md:px-8 py-3 md:py-4 rounded-2xl sm:rounded-full font-black text-[10px] md:text-xs lg:text-sm uppercase tracking-widest transition-all duration-300 ${activeTab === 'subscription' ? 'bg-black text-white shadow-xl' : 'text-gray-400 hover:text-black'}`}
            >
              Membresía Mensual
            </button>
            <button 
              onClick={() => setActiveTab('single')}
              className={`px-6 md:px-8 py-3 md:py-4 rounded-2xl sm:rounded-full font-black text-[10px] md:text-xs lg:text-sm uppercase tracking-widest transition-all duration-300 ${activeTab === 'single' ? 'bg-black text-white shadow-xl' : 'text-gray-400 hover:text-black'}`}
            >
              Alquiler Único
            </button>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-10 md:gap-16 items-center">
          <div className={`transition-all duration-700 transform ${activeTab === 'subscription' ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10 hidden'}`}>
            {/* Títulos interiores en Claven Responsivo */}
            <h3 className="font-claven text-3xl md:text-4xl lg:text-5xl font-black uppercase tracking-tighter mb-4 md:mb-6">El Poder de la Suscripción</h3>
            <p className="text-base md:text-lg lg:text-xl text-gray-600 mb-8 leading-relaxed">
              La forma más inteligente de mantener tu clóset siempre fresco. Por una tarifa mensual fija, accede a una rotación constante de prendas premium sin el compromiso de compra.
            </p>
            <ul className="space-y-4 md:space-y-6">
              {[
                { icon: Star, text: 'Rotación mensual de prendas de diseñador' },
                { icon: Crown, text: 'Limpieza profesional en seco incluida' },
                { icon: Diamond, text: 'Seguro de daños menores sin costo extra' }
              ].map((item, i) => (
                <li key={i} className="flex items-center space-x-4 bg-white p-4 md:p-6 rounded-2xl shadow-sm border border-gray-50">
                  <div className="p-2 md:p-3 bg-[#DF3265]/10 text-[#DF3265] rounded-xl"><item.icon size={20} className="md:w-6 md:h-6" /></div>
                  <span className="font-bold text-gray-800 text-xs md:text-sm lg:text-base">{item.text}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className={`transition-all duration-700 transform ${activeTab === 'single' ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10 hidden'}`}>
            {/* Títulos interiores en Claven Responsivo */}
            <h3 className="font-claven text-3xl md:text-4xl lg:text-5xl font-black uppercase tracking-tighter mb-4 md:mb-6">Para Ocasiones Especiales</h3>
            <p className="text-base md:text-lg lg:text-xl text-gray-600 mb-8 leading-relaxed">
              ¿Tienes una boda, gala o evento corporativo? Alquila una pieza espectacular (vestidos, accesorios, bolsos) solo por los días que la necesites.
            </p>
            <ul className="space-y-4 md:space-y-6">
              {[
                { icon: Star, text: 'Reserva hasta con 3 meses de anticipación' },
                { icon: Crown, text: 'Alquiler por 4, 8 o 12 días' },
                { icon: Diamond, text: 'Prueba de talla en nuestro Showroom' }
              ].map((item, i) => (
                <li key={i} className="flex items-center space-x-4 bg-white p-4 md:p-6 rounded-2xl shadow-sm border border-gray-50">
                  <div className="p-2 md:p-3 bg-black/5 text-black rounded-xl"><item.icon size={20} className="md:w-6 md:h-6" /></div>
                  <span className="font-bold text-gray-800 text-xs md:text-sm lg:text-base">{item.text}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="relative h-[300px] md:h-[400px] lg:h-[600px] rounded-[2rem] md:rounded-[3rem] overflow-hidden group mt-6 lg:mt-0">
            <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors duration-700 z-10"></div>
            <img 
              src={activeTab === 'subscription' 
                ? "https://images.unsplash.com/photo-1532453288672-3a27e9be9efd?auto=format&fit=crop&q=80&w=1000"
                : "https://images.unsplash.com/photo-1566206091558-7f218b696731?auto=format&fit=crop&q=80&w=1000"} 
              alt="Estilo Oulalab" 
              className="absolute inset-0 w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default Planes;
