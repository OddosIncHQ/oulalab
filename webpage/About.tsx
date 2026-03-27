import React from 'react';

const About: React.FC = () => {
  return (
    <div className="min-h-screen bg-white text-gray-900 font-sans selection:bg-black selection:text-white overflow-x-hidden">
      <section className="pt-40 pb-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="max-w-5xl">
            <span className="text-xs font-black tracking-widest uppercase text-gray-400 mb-6 block">
              About
            </span>

            <h1 className="text-5xl sm:text-7xl md:text-8xl lg:text-[9rem] font-black tracking-tighter uppercase leading-[0.9] mb-10">
              OULALAB
            </h1>

            <p className="text-2xl md:text-3xl text-gray-500 leading-relaxed font-medium italic max-w-4xl border-l-4 border-black pl-8">
              En OULALAB creemos que el futuro de la moda no está en acumular,
              sino en acceder de forma más inteligente, flexible y sofisticada.
            </p>
          </div>
        </div>
      </section>

      <section className="pb-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-10 rounded-[3rem] border border-gray-100 shadow-sm hover:shadow-2xl transition-all duration-500 hover:-translate-y-1">
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-black/30 mb-6">
                Visión
              </p>
              <h3 className="text-3xl font-black uppercase tracking-tighter mb-6 leading-none">
                Moda de alta gama,
                <br />
                redefinida.
              </h3>
              <p className="text-gray-600 text-base leading-[1.9] font-medium">
                Redefinimos la forma en que las personas acceden a la moda de
                lujo a través de una experiencia impulsada por tecnología,
                curaduría y diseño.
              </p>
            </div>

            <div className="bg-white p-10 rounded-[3rem] border border-gray-100 shadow-sm hover:shadow-2xl transition-all duration-500 hover:-translate-y-1">
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-black/30 mb-6">
                Inteligencia
              </p>
              <h3 className="text-3xl font-black uppercase tracking-tighter mb-6 leading-none">
                Datos e IA
                <br />
                con propósito.
              </h3>
              <p className="text-gray-600 text-base leading-[1.9] font-medium">
                Utilizamos datos e inteligencia artificial para entender
                preferencias, optimizar inventario y hacer que cada prenda
                circule con mayor precisión y eficiencia.
              </p>
            </div>

            <div className="bg-white p-10 rounded-[3rem] border border-gray-100 shadow-sm hover:shadow-2xl transition-all duration-500 hover:-translate-y-1">
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-black/30 mb-6">
                Modelo
              </p>
              <h3 className="text-3xl font-black uppercase tracking-tighter mb-6 leading-none">
                Acceso por sobre
                <br />
                posesión.
              </h3>
              <p className="text-gray-600 text-base leading-[1.9] font-medium">
                Un clóset rotativo de piezas premium para una nueva generación
                que valora libertad, innovación y estilo sin depender de la
                compra tradicional.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-32 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-20 items-center">
            <div className="relative group">
              <div className="absolute -inset-6 bg-black/5 rounded-[3rem] transform -rotate-3 transition-transform group-hover:rotate-0"></div>
              <div className="relative overflow-hidden rounded-[2.5rem] shadow-2xl">
                <img
                  src="https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&q=80&w=1200"
                  alt="Luxury fashion"
                  className="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-1000 scale-100 group-hover:scale-105"
                />
              </div>
            </div>

            <div>
              <span className="text-xs font-black tracking-widest uppercase text-gray-400 mb-6 block">
                Nuestra propuesta
              </span>

              <h2 className="text-4xl sm:text-6xl md:text-7xl font-black tracking-tighter uppercase mb-10 leading-[0.9]">
                Tecnología,
                <br />
                logística
                <br />
                y estilo.
              </h2>

              <p className="text-xl text-gray-600 leading-relaxed mb-8 font-medium">
                OULALAB opera en la intersección entre moda, tecnología y
                operación para construir una experiencia más refinada, eficiente
                y contemporánea.
              </p>

              <p className="text-xl text-gray-600 leading-relaxed font-medium">
                Cada prenda forma parte de un sistema diseñado para aprender,
                adaptarse y evolucionar, uniendo lujo, precisión y una nueva
                visión del acceso.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-40 bg-black text-white relative overflow-hidden">
        <div className="absolute top-0 right-0 w-1/3 h-full bg-white/5 skew-x-[-20deg] translate-x-1/2"></div>
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <span className="text-[10px] font-black tracking-[0.3em] uppercase text-white/40 mb-8 block">
            Oulalab Manifesto
          </span>

          <h2 className="text-4xl sm:text-6xl md:text-8xl lg:text-[8rem] font-black italic tracking-tighter uppercase mb-10 leading-[0.85]">
            Esto no es
            <br />
            solo moda.
          </h2>

          <p className="text-2xl md:text-3xl text-gray-400 leading-relaxed max-w-4xl mx-auto font-medium">
            Es un nuevo sistema para vestir. Más inteligente. Más flexible. Más
            alineado con la forma en que queremos vivir el lujo hoy.
          </p>
        </div>
      </section>
    </div>
  );
};

export default About;
