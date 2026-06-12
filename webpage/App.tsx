import React, { useState, useEffect, useRef } from 'react';
import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  ArrowRight, 
  Menu, 
  X, 
  ShoppingBag, 
  Clock, 
  RefreshCw, 
  Star,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Mail,
  Linkedin,
  Rocket,
  Send,
  Languages
} from 'lucide-react';
import { CONTENT, PRICES } from './constants';
import { TeamMember, Currency } from './types';
import LogoObispo from './Logo_Obispo.png';
import LogoBlanco from './Logo_Blanco.png';

// Componentes modulares
import ComoFunciona from './components/ComoFunciona';
import Care from './components/Care'; 

// Videos para las secciones internas (.mp4)
import vidValue from './src/assets/vid-2.mp4';
import vidLaunch from './src/assets/vid-3.mp4';

type Language = 'es' | 'en' | 'pt';

// Helper para resetear el scroll al cambiar de ruta
const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
};

const UI_STRINGS = {
  es: {
    nav_works: 'Cómo funciona',
    nav_plans: 'Planes',
    nav_team: 'Equipo',
    nav_visit: 'Agenda una Visita al Showroom',
    nav_care: 'Cuidado de Prendas',
    hero_title: 'Bienvenido al futuro de la moda.',
    hero_cta: 'UNIRSE AQUI',
    hero_description: 'La primera Fashion Technology Company en Chile. Redefiniendo cómo vivimos el estilo.',
    intro_normal: 'normal',
    intro_title_1: 'Comprar es',
    intro_title_2: 'suscribirse es Oulalab.',
    intro_description: 'Oulalab busca cambiar el modelo de adquisición de ropa por un modelo de suscripción mensual, con fee mensual fijo, que permite acceder a cualquier marca y modelo de prenda.',
    deliver_title_1: 'Closet Infinito',
    deliver_desc_1: 'Tener miles de opciones que me hagan sentir única, a un solo click.',
    deliver_title_2: 'Outfit Infinito',
    deliver_desc_2: 'Mix que hagan match con quien necesito ser para esa ocasión especial.',
    deliver_title_3: 'Budget Infinito',
    deliver_desc_3: 'Acceso a las mejores marcas sin pensar en las lucas. Disfruta el lujo hoy.',
    pricing_subtitle: 'Elige tu estilo',
    pricing_title: '¿Por qué Oulalab?',
    plans_title: 'Planes de Suscripción',
    team_subtitle: 'Detrás de la marca',
    team_title: 'El Equipo Oulalab',
    team_description: 'Expertos líderes en industria, branding, operaciones y tecnología unidos para redefinir el futuro de la moda.',
    pricing_btn: 'Suscribirse',
    launch_countdown: 'Cuenta regresiva iniciada',
    launch_month: 'MAYO',
    launch_year: '2026',
    launch_description: 'El mes en que Oulalab redefine la forma en que vives la moda. El lanzamiento oficial está cerca.',
    launch_waitlist: 'Sé Oulalaber',
    launch_tag1: 'Estilo Infinito',
    launch_tag2: 'Lujo Sustentable',
    launch_tag3: 'Personal Stylist con IA', 
    waitlist_pretitle: 'Sé una de nuestras',
    waitlist_title: 'Oulalaber',
    waitlist_subtitle: 'Tu closet infinito está a un click',
    waitlist_name: 'Nombre completo',
    waitlist_email: 'Mail',
    waitlist_phone: 'Teléfono',
    waitlist_address: 'Comuna',
    waitlist_button: 'Inscríbete',
    waitlist_success: '¡Ya estás registrada!',
    waitlist_success_desc: 'Te contactaremos pronto',
    waitlist_close: 'Cerrar',
    footer_tagline: 'Empoderar a las mujeres redefiniendo a la moda como una fuente de confianza. La primera Fashion Technology Company de Chile.',
    footer_nav: 'Navegación',
    footer_home: 'Inicio',
    footer_plans: 'Planes de Suscripción',
    footer_team: 'El Equipo',
    footer_contact_title: 'Contacto',
    footer_rights: '© 2026 OULALAB CHILE SPA TODOS OS DERECHOS RESERVADOS.',
    read_more: 'LEER MÁS',
    collapse: 'CONTRAER'
  },
  en: {
    nav_works: 'How it works',
    nav_plans: 'Plans',
    nav_team: 'Team',
    nav_visit: 'Schedule a Showroom Visit',
    nav_care: 'Garment Care',
    hero_title: 'Welcome to the future of fashion.',
    hero_cta: 'JOIN HERE',
    hero_description: 'The first Fashion Technology Company in Chile. Redefining how we experience style.',
    intro_normal: 'normal',
    intro_title_1: 'Buying is',
    intro_title_2: 'subscribing is Oulalab.',
    intro_description: 'Oulalab aims to change the clothing acquisition model for a monthly subscription model, with a fixed monthly fee, which allows access to any brand and garment model.',
    deliver_title_1: 'Infinite Closet',
    deliver_desc_1: 'Thousands of options to make me feel unique, just a click away.',
    deliver_title_2: 'Infinite Outfit',
    deliver_desc_2: 'Mixes that match whoever I need to be for that special occasion.',
    deliver_title_3: 'Infinite Budget',
    deliver_desc_3: 'Access to the best brands without thinking about money. Enjoy luxury today.',
    pricing_subtitle: 'Choose your style',
    pricing_title: 'Why Oulalab?',
    plans_title: 'Subscription Plans',
    team_subtitle: 'Behind the brand',
    team_title: 'The Oulalab Team',
    team_description: 'Leading experts in industry, branding, operations, and technology united to redefine the future of fashion.',
    pricing_btn: 'Subscribe',
    launch_countdown: 'Countdown started',
    launch_month: 'MAY',
    launch_year: '2026',
    launch_description: 'The month Oulalab redefines the way you live fashion. The official launch is near.',
    launch_waitlist: 'Become a Oulalaber',
    launch_tag1: 'Infinite Style',
    launch_tag2: 'Sustainable Luxury',
    launch_tag3: 'AI Personal Stylist', 
    waitlist_pretitle: 'Be one of our',
    waitlist_title: 'Oulalaber',
    waitlist_subtitle: 'Your infinite closet is a click away',
    waitlist_name: 'Full Name',
    waitlist_email: 'Email',
    waitlist_phone: 'Phone Number',
    waitlist_address: 'Commune',
    waitlist_button: 'Subscribe Now!',
    waitlist_success: 'Registration succesful!',
    waitlist_success_desc: 'We\'ll contact you in soon.',
    waitlist_close: 'Close',
    footer_tagline: 'Empowering women by redefining fashion as a source of confidence. The first Fashion Technology Company in Chile.',
    footer_nav: 'Navigation',
    footer_home: 'Home',
    footer_plans: 'Subscription Plans',
    footer_team: 'The Team',
    footer_contact_title: 'Contact',
    footer_rights: '© 2026 OULALAB CHILE SPA ALL RIGHTS RESERVED.',
    read_more: 'READ MORE',
    collapse: 'COLLAPSE'
  },
  pt: {
    nav_works: 'Como funciona',
    nav_plans: 'Planos',
    nav_team: 'Equipe',
    nav_visit: 'Agende uma Visita ao Showroom',
    nav_care: 'Cuidados com a Roupa',
    hero_title: 'Bem-vindo ao futuro da moda.',
    hero_cta: 'ENTRAR AQUI',
    hero_description: 'A primeira Fashion Technology Company no Chile. Redefinindo como vivemos o estilo.',
    intro_normal: 'normal',
    intro_title_1: 'Comprar é',
    intro_title_2: 'assinar é Oulalab.',
    intro_description: 'Oulalab busca mudar o modelo de aquisição de roupas por um modelo de assinatura mensal, con taxa fixa, que permite acessar qualquer marca e modelo de peça.',
    deliver_title_1: 'Closet Infinito',
    deliver_desc_1: 'Ter milhares de opções para me sentir única, a um só clique.',
    deliver_title_2: 'Outfit Infinito',
    deliver_desc_2: 'Combinações que batem con quem eu preciso ser para aquela ocasião especial.',
    deliver_title_3: 'Budget Infinito',
    deliver_desc_3: 'Acesso às mejores marcas sem pensar no preço. Aproveite o luxo hoje.',
    pricing_subtitle: 'Escolha seu estilo',
    pricing_title: 'Por que Oulalab?',
    plans_title: 'Planos de Assinatura',
    team_subtitle: 'Por trás da marca',
    team_title: 'A Equipe Oulalab',
    team_description: 'Líderes especialistas em indústria, branding, operaciones e tecnología unidos para redefinir o futuro de la moda.',
    pricing_btn: 'Assinar',
    launch_countdown: 'Contagem regressiva iniciada',
    launch_month: 'MAIO',
    launch_year: '2026',
    launch_description: 'O mes em que a Oulalab redefine a forma como você vive a moda. O lançamento oficial está próximo.',
    launch_waitlist: 'Seja uma Oulalaber',
    launch_tag1: 'Estilo Infinito',
    launch_tag2: 'Luxo Sustentável',
    launch_tag3: 'Personal Stylist com IA', 
    waitlist_pretitle: 'Seja uma de nossas',
    waitlist_title: 'Oulalaber',
    waitlist_subtitle: 'Seu closet infinito está a um clique',
    waitlist_name: 'Nome completo',
    waitlist_email: 'Mail',
    waitlist_phone: 'Telefone',
    waitlist_address: 'Comuna',
    waitlist_button: 'Inscreva-se',
    waitlist_success: 'Já está registrada!',
    waitlist_success_desc: 'Entraremos em contato logo.',
    waitlist_close: 'Fechar',
    footer_tagline: 'Empoderando mulheres ao redefinir a moda como uma fonte de confianza. A primera Fashion Technology Company do Chile.',
    footer_nav: 'Navegação',
    footer_home: 'Início',
    footer_plans: 'Planos de Assinatura',
    footer_team: 'A Equipe',
    footer_contact_title: 'Contato',
    footer_rights: '© 2026 OULALAB CHILE SPA TODOS OS DIREITOS RESERVADOS.',
    read_more: 'LER MAIS',
    collapse: 'RECOLHER'
  }
};

// --- COMPONENTE: PÁGINA EXCLUSIVA PARA EL QR (NUEVO DISEÑO EXACTO) ---
const StandaloneWaitlist: React.FC<{ lang: Language }> = ({ lang }) => {
  const t = UI_STRINGS[lang];
  const [isSending, setIsSending] = useState(false);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 md:px-6 relative overflow-hidden bg-gray-500 font-sans">
      <div className="absolute inset-0 z-0">
        <img 
          src="https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&q=80&w=2000" 
          alt="Fashion background" 
          className="w-full h-full object-cover brightness-[0.3] scale-105"
        />
      </div>
      
      {/* Nuevo Contenedor Morado y Estrecho */}
      <div className="relative z-10 bg-[#2D132B] w-full max-w-[400px] rounded-[3rem] overflow-hidden shadow-2xl p-8 md:p-10 text-center animate-in zoom-in-95 duration-300 my-8">
        
        <div className="mb-10 mt-4">
          <p className="font-sans text-lg md:text-xl text-white font-medium mb-1">{t.waitlist_pretitle}</p>
          <h3 className="font-claven text-6xl md:text-7xl font-normal tracking-tight text-white leading-none mb-8">{t.waitlist_title}</h3>
          <p className="font-sans text-xl md:text-2xl text-white font-bold max-w-[250px] mx-auto leading-tight">{t.waitlist_subtitle}</p>
        </div>
        
        <form 
          className="flex flex-col space-y-4" 
          onSubmit={async (e) => {
            e.preventDefault();
            setIsSending(true);
            const form = e.currentTarget;
            const nombre = (form.elements.namedItem('nombre') as HTMLInputElement).value;
            const email = (form.elements.namedItem('email') as HTMLInputElement).value;
            const telefono = (form.elements.namedItem('telefono') as HTMLInputElement).value;
            const address = (form.elements.namedItem('address') as HTMLInputElement).value;
            try {
              // CONEXIÓN A GOOGLE SHEETS ENVIANDO "telefono" y "comuna"
              await fetch("https://script.google.com/a/macros/oulalab.com/s/AKfycbxsPYWEG9gysS5TjglG8MIlgoGNstE7g5iafbOjWu8qiV2pcNcjTsnccyfwAYLx7z9X/exec", {
                method: "POST", mode: 'no-cors', headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nombre, email, telefono, comuna: address })
              });
              alert(t.waitlist_success);
              form.reset();
            } catch (error) {
              alert("Error técnico. Intenta más tarde.");
            } finally {
              setIsSending(false);
            }
          }}
        >
          {/* Inputs redondos rosados apilados verticalmente */}
          <input name="nombre" type="text" className="w-full bg-[#F7E8F7] rounded-full px-6 py-4 font-medium text-gray-900 placeholder-gray-700 outline-none focus:ring-2 focus:ring-[#DF3265]" placeholder={t.waitlist_name} required />
          <input name="email" type="email" className="w-full bg-[#F7E8F7] rounded-full px-6 py-4 font-medium text-gray-900 placeholder-gray-700 outline-none focus:ring-2 focus:ring-[#DF3265]" placeholder={t.waitlist_email} required />
          <input name="telefono" type="tel" className="w-full bg-[#F7E8F7] rounded-full px-6 py-4 font-medium text-gray-900 placeholder-gray-700 outline-none focus:ring-2 focus:ring-[#DF3265]" placeholder={t.waitlist_phone} required />
          <input name="address" type="text" className="w-full bg-[#F7E8F7] rounded-full px-6 py-4 font-medium text-gray-900 placeholder-gray-700 outline-none focus:ring-2 focus:ring-[#DF3265]" placeholder={t.waitlist_address} required />

          {/* Botón Magenta */}
          <div className="pt-6 mb-2">
            <button type="submit" disabled={isSending} className="w-full bg-[#E61D64] text-white font-bold text-xl py-4 rounded-full hover:scale-105 transition-transform shadow-lg">
              {isSending ? "ENVIANDO..." : t.waitlist_button}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
// --- FIN DEL COMPONENTE QR ---


const App: React.FC = () => {
  const [lang, setLang] = useState<Language>('es');
  const [currency, setCurrency] = useState<Currency>('CLP');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isWaitlistOpen, setIsWaitlistOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [expandedTeamMember, setExpandedTeamMember] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  // Referencias para forzar la reproducción de los videos
  const videoRef1 = useRef<HTMLVideoElement>(null);
  const videoRef2 = useRef<HTMLVideoElement>(null);
  
  const LOGO_DARK = LogoObispo;   
  const LOGO_LIGHT = LogoBlanco;  
  const BRAND_LOGO_URL = scrolled ? LOGO_DARK : LOGO_LIGHT;
    
  const t = UI_STRINGS[lang];

  const navigate = useNavigate();
  const { pathname } = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Forzar reproducción de los videos al montar el componente
  useEffect(() => {
    const playVideo = (ref: React.RefObject<HTMLVideoElement>) => {
      if (ref.current) {
        ref.current.defaultMuted = true;
        ref.current.muted = true;
        ref.current.play().catch(error => console.log("Autoplay prevented:", error));
      }
    };
    playVideo(videoRef1);
    playVideo(videoRef2);
  }, [pathname]);

  const handleNav = (id: string) => {
    setIsMenuOpen(false);
    if (pathname !== '/') {
      navigate('/');
      setTimeout(() => {
        const element = document.getElementById(id);
        if (element) {
          const offset = 80;
          const elementPosition = element.getBoundingClientRect().top;
          const offsetPosition = elementPosition + window.pageYOffset - offset;
          window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
        }
      }, 150);
    } else {
      const element = document.getElementById(id);
      if (element) {
        const offset = 80;
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;
        window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
      }
    }
  };

  const isStandaloneWaitlist = pathname === '/unirse-aqui';

  return (
    <div className="min-h-screen bg-white text-gray-900 font-sans selection:bg-black selection:text-white overflow-x-hidden">
      <ScrollToTop />
      
      {/* Fixed Navigation Bar */}
      {!isStandaloneWaitlist && (
        <nav className={`fixed w-full z-50 transition-all duration-300 ${scrolled ? 'bg-white/95 backdrop-blur-lg shadow-lg py-3' : 'bg-transparent py-8'}`}>
          <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
            <Link to="/" className="flex items-center group cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
              <img 
                src={BRAND_LOGO_URL} 
                alt="Oulalab Logo" 
                className={`object-contain transition-all duration-500 group-hover:scale-105 ${scrolled ? 'h-16' : 'h-20 md:h-24 lg:h-32'}`}
              />
            </Link>

            <div className="hidden md:flex items-center space-x-6 lg:space-x-10">
              <button onClick={() => handleNav('how-it-works')} className={`text-sm font-bold uppercase tracking-widest hover:opacity-60 transition-colors ${scrolled ? 'text-black' : 'text-white'}`}>{t.nav_works}</button>
              <button onClick={() => handleNav('plans')} className={`text-sm font-bold uppercase tracking-widest hover:opacity-60 transition-colors ${scrolled ? 'text-black' : 'text-white'}`}>{t.nav_plans}</button>
              <button onClick={() => handleNav('team')} className={`text-sm font-bold uppercase tracking-widest hover:opacity-60 transition-colors ${scrolled ? 'text-black' : 'text-white'}`}>{t.nav_team}</button>
              
              <Link to="/care" className={`text-sm font-bold uppercase tracking-widest hover:opacity-60 transition-colors ${scrolled ? 'text-black' : 'text-white'}`}>
                {t.nav_care}
              </Link>

              <a 
                href="https://oulalab.odoo.com/agenda-una-visita/" 
                target="_blank" 
                rel="noopener noreferrer" 
                className={`text-[11px] lg:text-sm font-black uppercase tracking-widest px-4 py-2 border-2 rounded-full transition-all ${scrolled ? 'border-[#DF3265] text-[#DF3265] hover:bg-[#DF3265] hover:text-white' : 'border-white/40 text-white hover:bg-white hover:text-black'}`}
              >
                {t.nav_visit}
              </a>

              <div className="flex items-center space-x-2 ml-2 lg:ml-4">
                <div className="flex items-center bg-gray-100/20 backdrop-blur-md rounded-full p-1 border border-white/10">
                  {(['es', 'en', 'pt'] as Language[]).map((l) => (
                    <button
                      key={l}
                      onClick={() => setLang(l)}
                      className={`px-2 lg:px-3 py-1 text-[10px] font-black rounded-full transition-all uppercase ${lang === l ? 'bg-black text-white' : scrolled ? 'text-gray-400' : 'text-white/50'}`}
                    >
                      {l}
                    </button>
                  ))}
                </div>
                <div className="flex items-center bg-gray-100/20 backdrop-blur-md rounded-full p-1 border border-white/10">
                  {(['CLP', 'USD', 'EUR'] as Currency[]).map((c) => (
                    <button
                      key={c}
                      onClick={() => setCurrency(c)}
                      className={`px-2 lg:px-3 py-1 text-[10px] font-black rounded-full transition-all uppercase ${currency === c ? 'bg-black text-white' : scrolled ? 'text-gray-400' : 'text-white/50'}`}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button className={`md:hidden p-2 ${scrolled ? 'text-black' : 'text-white'}`} onClick={() => setIsMenuOpen(!isMenuOpen)}>
              {isMenuOpen ? <X size={32} /> : <Menu size={32} />}
            </button>
          </div>
        </nav>
      )}

      {/* Mobile Overlay Menu */}
      {isMenuOpen && !isStandaloneWaitlist && (
        <div className="fixed inset-0 z-[100] bg-white flex flex-col items-center justify-center space-y-6 md:space-y-8 animate-in fade-in duration-300 px-6 overflow-y-auto">
          <img src={LogoObispo} alt="Oulalab" className="h-16 md:h-20 mb-4" />
          <button onClick={() => handleNav('how-it-works')} className="text-2xl md:text-3xl font-black uppercase text-center w-full">{t.nav_works}</button>
          <button onClick={() => handleNav('plans')} className="text-2xl md:text-3xl font-black uppercase text-center w-full">{t.nav_plans}</button>
          <button onClick={() => handleNav('team')} className="text-2xl md:text-3xl font-black uppercase text-center w-full">{t.nav_team}</button>
          
          <Link to="/care" onClick={() => setIsMenuOpen(false)} className="text-2xl md:text-3xl font-black uppercase text-center w-full">
            {t.nav_care}
          </Link>

          <a 
            href="https://oulalab.odoo.com/agenda-una-visita/" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="text-2xl md:text-3xl font-black uppercase text-[#DF3265] text-center w-full leading-tight"
            onClick={() => setIsMenuOpen(false)}
          >
            {t.nav_visit}
          </a>
          
          <div className="flex flex-col space-y-6 pt-10 border-t w-1/2 items-center">
            <div className="flex space-x-4">
              {(['es', 'en', 'pt'] as Language[]).map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  className={`w-12 h-12 rounded-full font-black text-xs border-2 transition-all uppercase ${lang === l ? 'bg-black text-white border-black shadow-xl' : 'border-gray-200 text-gray-400'}`}
                >
                  {l}
                </button>
              ))}
            </div>
            <div className="flex space-x-4">
              {(['CLP', 'USD', 'EUR'] as Currency[]).map((c) => (
                <button
                  key={c}
                  onClick={() => setCurrency(c)}
                  className={`w-12 h-12 rounded-full font-black text-[10px] border-2 transition-all uppercase ${currency === c ? 'bg-black text-white border-black shadow-xl' : 'border-gray-200 text-gray-400'}`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
          <button onClick={() => setIsMenuOpen(false)} className="p-4 bg-gray-100 rounded-full text-black transition-transform active:scale-90"><X size={24} /></button>
        </div>
      )}

      {/* DEFINICIÓN DE RUTAS */}
      <Routes>
        {/* RUTA 1: HOME PAGE */}
        <Route path="/" element={
          <>
            {/* Main Hero Section */}
            <section className="relative h-screen flex items-center overflow-hidden pt-32 md:pt-40 lg:pt-20">
              <div className="absolute inset-0 z-0">
                <img 
                  src="https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&q=80&w=2000" 
                  alt="Fashion background" 
                  className="w-full h-full object-cover brightness-[0.85] scale-105"
                  style={{ animation: 'slow-zoom 20s ease-in-out infinite alternate' }}
                />
                <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/20"></div>
              </div>

              <div className="relative z-10 max-w-7xl mx-auto px-6 w-full">
                <div className="max-w-4xl">
                  <h1 className="font-claven text-5xl md:text-6xl lg:text-8xl xl:text-[9rem] text-white leading-[0.9] tracking-tighter mb-6 md:mb-8 font-black uppercase drop-shadow-xl">
                     {t.hero_title}
                  </h1>
                  
                  <p className="text-lg md:text-xl lg:text-2xl text-gray-100 mb-10 md:mb-12 leading-relaxed max-w-xl font-medium drop-shadow-md">
                    {t.hero_description}
                  </p>
                  
                  <div className="flex flex-col sm:flex-row gap-6">
                    <button 
                      onClick={() => setIsWaitlistOpen(true)}
                      className="group relative inline-flex items-center justify-center px-8 md:px-10 py-4 md:py-5 bg-[#DF3265] text-white font-black uppercase tracking-tighter hover:bg-white hover:text-black transition-all duration-300 shadow-2xl"
                    >
                      <span className="relative z-10 flex items-center text-center text-sm md:text-base">
                        {t.hero_cta} <ArrowRight className="ml-2 w-5 h-5 md:w-6 md:h-6 group-hover:translate-x-2 transition-transform" />
                      </span>
                    </button>
                  </div>
                </div>
              </div>

              <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-bounce cursor-pointer z-20" onClick={() => handleNav('value-prop')}>
                <ChevronDown className="text-white w-8 h-8 md:w-10 md:h-10 opacity-70" />
              </div>
            </section>

            {/* Intro Description Section (Value Prop) */}
            <section id="value-prop" className="py-20 md:py-32 bg-gray-50 scroll-mt-20">
              <div className="max-w-7xl mx-auto px-6">
                <div className="text-center mb-16 md:mb-24">
                  <span className="text-[10px] md:text-xs font-black tracking-widest uppercase text-gray-400 mb-4 md:mb-6 block">Concepto Oulalab</span>
                  <h2 className="font-claven text-4xl md:text-5xl lg:text-7xl font-black tracking-tighter uppercase">{t.pricing_title}</h2>
                </div>
                
                <div className="grid md:grid-cols-2 gap-12 md:gap-20 items-center">
                  <div className="relative group">
                    <div className="absolute -inset-4 md:-inset-6 bg-[#DF3265]/5 rounded-[3rem] transform -rotate-3 transition-transform group-hover:rotate-0"></div>
                    <div className="relative overflow-hidden rounded-[2rem] md:rounded-[2.5rem] shadow-2xl bg-black">
                      <video 
                        ref={videoRef1}
                        autoPlay={true} 
                        loop={true} 
                        muted={true} 
                        playsInline={true} 
                        preload="auto" 
                        className="w-full grayscale hover:grayscale-0 transition-all duration-1000 group-hover:scale-105"
                      >
                        <source src={vidValue} type="video/mp4" />
                      </video>
                    </div>
                  </div>
                  <div>
                    <h3 className="font-claven text-3xl md:text-4xl lg:text-5xl font-black tracking-tighter uppercase mb-8 md:mb-10 leading-[0.9]">
                      {t.intro_title_1} <span className="italic opacity-20">{t.intro_normal},</span><br />
                      {t.intro_title_2}
                    </h3>
                    <p className="text-base md:text-lg lg:text-xl text-gray-600 leading-relaxed mb-10 md:mb-12">
                      {t.intro_description}
                    </p>
                    <div className="grid grid-cols-1 gap-6 md:gap-8">
                      {[
                        { icon: ShoppingBag, title: t.deliver_title_1, desc: t.deliver_desc_1 },
                        { icon: RefreshCw, title: t.deliver_title_2, desc: t.deliver_desc_2 },
                        { icon: Clock, title: t.deliver_title_3, desc: t.deliver_desc_3 }
                      ].map((item, idx) => (
                        <div key={idx} className="flex items-start space-x-4 md:space-x-6 p-6 md:p-8 bg-white border border-gray-100 rounded-3xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-1">
                          <div className="p-3 md:p-4 bg-gray-50 rounded-2xl text-[#DF3265]">
                            <item.icon className="w-6 h-6 md:w-8 md:h-8" />
                          </div>
                          <div>
                            <h4 className="text-base md:text-lg font-black uppercase tracking-tighter mb-1 md:mb-2">{item.title}</h4>
                            <p className="text-sm md:text-base text-gray-500 leading-relaxed">{item.desc}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <div id="how-it-works" className="scroll-mt-20">
              <ComoFunciona lang={lang} />
            </div>

            {/* SECCIÓN DE PLANES */}
            <section id="plans" className="py-20 md:py-32 bg-white scroll-mt-20">
              <div className="max-w-7xl mx-auto px-6 text-center">
                <span className="text-[10px] md:text-xs font-black tracking-widest uppercase text-gray-400 mb-4 md:mb-6 block">{t.pricing_subtitle}</span>
                <h2 className="font-claven text-4xl md:text-5xl lg:text-7xl font-black tracking-tighter uppercase mb-12 md:mb-20">{t.plans_title}</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-10">
                  {CONTENT[lang].pricing.map((plan) => {
                    const price = PRICES[currency][plan.id];
                    return (
                      <div key={plan.id} className={`relative flex flex-col p-8 md:p-10 lg:p-12 bg-white border-2 rounded-[3rem] md:rounded-[3.5rem] transition-all duration-500 group ${plan.id === 'premium' ? 'border-black shadow-2xl scale-105 z-10' : 'border-gray-100 hover:border-black hover:shadow-xl'}`}>
                        {plan.id === 'premium' && (
                          <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-black text-white px-6 md:px-8 py-3 md:py-4 rounded-[2rem] text-[10px] md:text-[11px] font-black tracking-[0.2em] uppercase whitespace-nowrap shadow-xl">
                            OULALAB CHOICE
                          </div>
                        )}
                        <h3 className="text-2xl md:text-3xl font-black uppercase tracking-tighter mb-4 text-center">{plan.name}</h3>
                        
                        <div className="flex flex-col items-center justify-center mb-8 md:mb-10 text-center min-h-[80px] md:min-h-[100px]">
                          {plan.id === 'premium' ? (
                            <>
                              <span className="text-4xl md:text-5xl lg:text-7xl font-black tracking-tighter leading-none">{price}</span>
                              <div className="mt-2 flex items-center justify-center space-x-2 text-gray-400">
                                <span className="text-xl md:text-2xl font-light opacity-30">/</span>
                                <span className="text-[9px] md:text-[10px] font-black tracking-[0.2em] uppercase">{plan.frequency}</span>
                              </div>
                            </>
                          ) : (
                            <span className="text-xl md:text-2xl lg:text-3xl font-black tracking-widest text-gray-300 uppercase">Coming Soon</span>
                          )}
                        </div>

                        <div className="space-y-4 flex-grow text-left">
                          {plan.features.map((feature, i) => (
                            <div key={i} className="flex items-start space-x-3 text-xs md:text-sm font-bold">
                              <CheckCircle2 size={16} className="text-black shrink-0 mt-0.5 md:w-[18px] md:h-[18px]" />
                              <span className="text-gray-600 group-hover:text-black transition-colors">{feature}</span>
                            </div>
                          ))}
                          <div className="pt-6 border-t border-gray-100 mt-6">
                            <p className="text-[9px] md:text-[10px] font-black uppercase tracking-widest text-black/30 mb-1">{plan.limit}</p>
                            <p className="text-[10px] md:text-xs italic font-bold text-gray-400">{plan.swap}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>

            {/* Founders / Team Section */}
            <section id="team" className="py-20 md:py-32 bg-gray-50 scroll-mt-20">
              <div className="max-w-7xl mx-auto px-6">
                <div className="max-w-3xl mb-16 md:mb-20">
                  <span className="text-[10px] md:text-xs font-black tracking-widest uppercase text-gray-400 mb-4 md:mb-6 block">{t.team_subtitle}</span>
                  <h2 className="font-claven text-4xl md:text-5xl lg:text-7xl font-black tracking-tighter uppercase mb-6 md:mb-8 leading-none">{t.team_title}</h2>
                  <p className="text-lg md:text-xl lg:text-2xl text-gray-500 font-medium italic border-l-4 border-[#DF3265] pl-6 md:pl-8">{t.team_description}</p>
                </div>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 md:gap-10">
                  {CONTENT[lang].team.map((member: TeamMember, idx: number) => {
                    const isExpanded = expandedTeamMember === member.name;
                    return (
                      <div key={idx} className="bg-white p-8 md:p-10 rounded-[2.5rem] md:rounded-[3rem] border border-gray-100 shadow-sm hover:shadow-2xl transition-all duration-500 flex flex-col group">
                        <div className="flex items-center space-x-6 md:space-x-8 mb-8 md:mb-10">
                          <div className="relative">
                            <img src={member.image} alt={member.name} className="relative w-24 h-24 md:w-28 md:h-28 rounded-[1.5rem] md:rounded-[2rem] object-cover grayscale transition-all duration-700 group-hover:grayscale-0 group-hover:rotate-3 shadow-xl" />
                            <div className="absolute -bottom-2 -right-2 md:-bottom-3 md:-right-3 bg-[#DF3265] text-white p-2 md:p-3 rounded-xl md:rounded-2xl shadow-xl"><Star size={16} fill="white" className="md:w-5 md:h-5" /></div>
                          </div>
                          <div>
                            <h3 className="text-xl md:text-2xl font-black uppercase mb-1">{member.name}</h3>
                            <p className="text-black/30 font-black text-[10px] md:text-xs tracking-widest uppercase">{member.role}</p>
                          </div>
                        </div>
                        <div className="mb-8 flex-grow">
                          <div className={`relative transition-all duration-500 ${isExpanded ? '' : 'max-h-24 md:max-h-32 overflow-hidden'}`}>
                            <p className="text-gray-600 text-xs md:text-sm leading-[1.8] font-medium">{member.description}</p>
                          </div>
                          <button onClick={() => setExpandedTeamMember(isExpanded ? null : member.name)} className="mt-4 flex items-center text-[9px] md:text-[10px] font-black tracking-widest uppercase text-black hover:text-[#DF3265]">
                            {isExpanded ? t.collapse : t.read_more} {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          </button>
                        </div>
                        <div className="pt-6 md:pt-8 border-t border-gray-100 flex items-center justify-between">
                          <p className="italic font-black text-black/70 text-xs md:text-sm leading-tight max-w-[70%]">"{member.quote}"</p>
                          <div className="flex space-x-3 md:space-x-4">
                            <a href={`mailto:${member.email}`} className="p-2 md:p-3 bg-gray-50 hover:bg-[#DF3265] hover:text-white rounded-xl md:rounded-2xl transition-all shadow-sm"><Mail size={16} className="md:w-5 md:h-5" /></a>
                            <a href={`https://${member.linkedin}`} target="_blank" rel="noopener noreferrer" className="p-2 md:p-3 bg-gray-50 hover:bg-[#DF3265] hover:text-white rounded-xl md:rounded-2xl transition-all shadow-sm"><Linkedin size={16} className="md:w-5 md:h-5" /></a>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>

            <section className="py-24 md:py-40 bg-black text-white relative overflow-hidden">
              <div className="absolute inset-0 z-0">
                <video 
                  ref={videoRef2}
                  autoPlay={true} 
                  loop={true} 
                  muted={true} 
                  playsInline={true} 
                  preload="auto" 
                  className="w-full h-full object-cover opacity-50 scale-110"
                >
                  <source src={vidLaunch} type="video/mp4" />
                </video>
              </div>
              <div className="relative z-10 max-w-7xl mx-auto px-6 text-center">
                <div className="inline-flex items-center space-x-2 md:space-x-3 border border-white/20 px-4 md:px-6 py-2 md:py-3 rounded-full mb-8 md:mb-12 backdrop-blur-md bg-white/5">
                  <Rocket className="text-[#DF3265] w-4 h-4 md:w-5 md:h-5 animate-bounce" />
                  <span className="text-white text-[10px] md:text-xs font-black tracking-[0.3em] uppercase">{t.launch_countdown}</span>
                </div>
                <h2 className="font-claven text-6xl md:text-8xl lg:text-[11rem] font-black italic tracking-tighter uppercase mb-8 md:mb-10 leading-[0.8] text-white">
                  {t.launch_month} <span className="text-white/10">{t.launch_year}</span>
                </h2>
                <p className="text-lg md:text-2xl lg:text-3xl text-gray-200 leading-relaxed mb-12 md:mb-16 max-w-3xl mx-auto font-medium">
                  {t.launch_description}
                </p>
                <button 
                  onClick={() => setIsWaitlistOpen(true)}
                  className="inline-flex items-center px-10 md:px-16 py-5 md:py-8 bg-[#DF3265] text-white font-black uppercase tracking-tighter text-base md:text-xl hover:scale-110 transition-all shadow-[0_0_50px_rgba(223,50,101,0.4)]"
                >
                  {t.launch_waitlist} <Send className="ml-3 w-5 h-5 md:ml-4 md:w-6 md:h-6" />
                </button>
              </div>
            </section>
          </>
        } />
        
        {/* RUTA 2: CUIDADOS */}
        <Route path="/care" element={<Care lang={lang} />} />

        {/* RUTA 3: EXCLUSIVA CÓDIGO QR */}
        <Route path="/unirse-aqui" element={<StandaloneWaitlist lang={lang} />} />
      </Routes>

      {/* FOOTER (Oculto en StandaloneWaitlist) */}
      {!isStandaloneWaitlist && (
        <footer className="py-20 md:py-32 bg-white border-t border-gray-100">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-12 md:gap-20 mb-16 md:mb-32">
              <div className="col-span-1 md:col-span-2">
                <div className="flex items-center mb-8 md:mb-12 cursor-pointer" onClick={() => { navigate('/'); setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 100); }}>
                  <img src={LogoObispo} alt="Oulalab Logo" className="h-12 md:h-16 w-auto object-contain transition-transform hover:scale-105" />
                </div>
                <p className="text-gray-500 font-bold text-lg md:text-xl leading-relaxed max-w-md italic opacity-80">{t.footer_tagline}</p>
              </div>
              
              <div>
                <h4 className="font-black uppercase tracking-widest text-[10px] md:text-xs mb-6 md:mb-10 text-black/30">{t.footer_nav}</h4>
                <ul className="space-y-4 md:space-y-6 font-black text-black text-xs md:text-sm uppercase tracking-tighter">
                  <li><Link to="/" onClick={() => window.scrollTo(0,0)} className="hover:text-[#DF3265] transition-colors">{t.footer_home}</Link></li>
                  <li><button onClick={() => handleNav('how-it-works')} className="hover:text-[#DF3265] transition-colors">{t.nav_works}</button></li>
                  <li><Link to="/care" onClick={() => window.scrollTo(0,0)} className="hover:text-[#DF3265] transition-colors uppercase">{t.nav_care}</Link></li>
                  <li>
                    <a href="https://oulalab.odoo.com/agenda-una-visita/" target="_blank" rel="noopener noreferrer" className="text-[#DF3265] hover:opacity-70 transition-opacity">
                      {t.nav_visit}
                    </a>
                  </li>
                  <li><button onClick={() => handleNav('plans')} className="hover:text-[#DF3265] transition-colors uppercase">{t.footer_plans}</button></li>
                  <li><button onClick={() => handleNav('team')} className="hover:text-[#DF3265] transition-colors uppercase">{t.footer_team}</button></li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-black uppercase tracking-widest text-[10px] md:text-xs mb-6 md:mb-10 text-black/30">{t.footer_contact_title}</h4>
                <ul className="space-y-4 md:space-y-6 font-black text-black text-xs md:text-sm uppercase tracking-tighter">
                  <li><a href="mailto:hola@oulalab.com" className="hover:text-[#DF3265] transition-colors">hola@oulalab.com</a></li>
                  <li><a href="#" className="hover:text-[#DF3265] transition-colors">LinkedIn</a></li>
                </ul>
              </div>
            </div>
            
            <div className="pt-10 md:pt-16 border-t border-gray-100 flex flex-col md:flex-row justify-between items-center gap-6 md:gap-10">
              <p className="text-[9px] md:text-[10px] font-black uppercase tracking-[0.4em] text-black/20 text-center md:text-left">
                {t.footer_rights}
              </p>
              <div className="flex items-center space-x-4 md:space-x-6">
                <div className="flex items-center space-x-2 text-black/20">
                  <Languages size={14} className="md:w-4 md:h-4" />
                  <span className="text-[9px] md:text-[10px] font-black uppercase tracking-widest">Global Fashion Network</span>
                </div>
                <div className="w-6 md:w-10 h-1 text-black/10"></div>
                <p className="text-[9px] md:text-[10px] font-black uppercase tracking-widest text-black/40">EST. 2025 | CHILE</p>
              </div>
            </div>
          </div>
        </footer>
      )}

      {/* WAITLIST MODAL PARA EL HOME (NUEVO DISEÑO EXACTO) */}
      {isWaitlistOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center px-4 md:px-6">
          <div className="absolute inset-0 bg-black/95 backdrop-blur-xl animate-in fade-in duration-500" onClick={() => setIsWaitlistOpen(false)}></div>
          
          <div className="relative z-10 bg-[#2D132B] w-full max-w-[400px] rounded-[3rem] overflow-hidden shadow-2xl p-8 md:p-10 text-center animate-in zoom-in-95 duration-300">
            <button className="absolute top-6 right-6 p-2 text-white/50 hover:text-white transition-colors" onClick={() => setIsWaitlistOpen(false)}>
              <X size={24} />
            </button>

            <div className="mb-10 mt-4">
              <p className="font-sans text-lg md:text-xl text-white font-medium mb-1">{t.waitlist_pretitle}</p>
              <h3 className="font-claven text-6xl md:text-7xl font-normal tracking-tight text-white leading-none mb-8">{t.waitlist_title}</h3>
              <p className="font-sans text-xl md:text-2xl text-white font-bold max-w-[250px] mx-auto leading-tight">{t.waitlist_subtitle}</p>
            </div>
            
            <form 
              className="flex flex-col space-y-4" 
              onSubmit={async (e) => {
                e.preventDefault();
                setIsSending(true);
                const form = e.currentTarget;
                const nombre = (form.elements.namedItem('nombre') as HTMLInputElement).value;
                const email = (form.elements.namedItem('email') as HTMLInputElement).value;
                const telefono = (form.elements.namedItem('telefono') as HTMLInputElement).value;
                const address = (form.elements.namedItem('address') as HTMLInputElement).value;
                try {
                  // CONEXIÓN A GOOGLE SHEETS ENVIANDO "comuna" y "telefono"
                  await fetch("https://script.google.com/macros/s/AKfycbwKGfjuGtQNGMheUmvvH3qOAqxbEluDC6m_8jnphhQINUnInnR597AT1ytoMpSZ6W-e/exec", {
                    method: "POST", mode: 'no-cors', headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ nombre, email, telefono, comuna: address })
                  });
                  alert(t.waitlist_success);
                  setIsWaitlistOpen(false);
                } catch (error) {
                  alert("Error técnico. Intenta más tarde.");
                } finally {
                  setIsSending(false);
                }
              }}
            >
              <input name="nombre" type="text" className="w-full bg-[#F7E8F7] rounded-full px-6 py-4 font-medium text-gray-900 placeholder-gray-700 outline-none focus:ring-2 focus:ring-[#DF3265]" placeholder={t.waitlist_name} required />
              <input name="email" type="email" className="w-full bg-[#F7E8F7] rounded-full px-6 py-4 font-medium text-gray-900 placeholder-gray-700 outline-none focus:ring-2 focus:ring-[#DF3265]" placeholder={t.waitlist_email} required />
              <input name="telefono" type="tel" className="w-full bg-[#F7E8F7] rounded-full px-6 py-4 font-medium text-gray-900 placeholder-gray-700 outline-none focus:ring-2 focus:ring-[#DF3265]" placeholder={t.waitlist_phone} required />
              <input name="address" type="text" className="w-full bg-[#F7E8F7] rounded-full px-6 py-4 font-medium text-gray-900 placeholder-gray-700 outline-none focus:ring-2 focus:ring-[#DF3265]" placeholder={t.waitlist_address} required />

              <div className="pt-6 mb-2">
                <button type="submit" disabled={isSending} className="w-full bg-[#E61D64] text-white font-bold text-xl py-4 rounded-full hover:scale-105 transition-transform shadow-lg">
                  {isSending ? "ENVIANDO..." : t.waitlist_button}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
