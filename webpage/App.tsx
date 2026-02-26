
import React, { useState, useEffect } from 'react';
import { 
  ArrowRight, 
  Menu, 
  X, 
  ShoppingBag, 
  Clock, 
  RefreshCw, 
  Sparkles, 
  Star,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Mail,
  Linkedin,
  Rocket,
  Send,
  Languages,
  DollarSign
} from 'lucide-react';
import { CONTENT, PRICES } from './constants';
import { TeamMember, Currency } from './types';

// --- Types ---
type Language = 'es' | 'en' | 'pt';

// --- Translations ---
const UI_STRINGS = {
  es: {
    nav_works: 'Cómo funciona',
    nav_plans: 'Planes',
    nav_team: 'Equipo',
    hero_title: 'Bienvenido al futuro de la moda.',
    hero_cta: 'UNIRSE A LA LISTA DE ESPERA',
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
    pricing_title: '¿Cómo funciona?',
    plans_title: 'Planes de Suscripción',
    team_subtitle: 'Detrás de la marca',
    team_title: 'El Equipo Oulalab',
    team_description: 'Expertos líderes en industria, branding, operaciones y tecnología unidos para redefinir el futuro de la moda.',
    pricing_btn: 'Suscribirse',
    launch_countdown: 'Cuenta regresiva iniciada',
    launch_month: 'MARZO',
    launch_year: '2025',
    launch_description: 'El mes en que Oulalab redefine la forma en que vives la moda. El lanzamiento oficial está cerca.',
    launch_waitlist: 'Unirse a la lista de espera',
    launch_tag1: 'Estilo Infinito',
    launch_tag2: 'Lujo Sustentable',
    launch_tag3: 'Personal Shopper con IA',
    waitlist_title: 'Únete a la lista de espera',
    waitlist_subtitle: 'Sé la primera en vivir la experiencia del clóset de tus sueños este marzo.',
    waitlist_name: 'Nombre Completo',
    waitlist_email: 'Correo Electrónico',
    waitlist_phone: 'Telefono',
    waitlist_address: 'Dirección',
    waitlist_button: 'ASEGURAR MI LUGAR',
    waitlist_success: '¡Ya estás en la lista!',
    waitlist_success_desc: 'Te contactaremos en marzo con acceso anticipado exclusivo.',
    waitlist_close: 'Cerrar',
    footer_tagline: 'Empoderar a las mujeres redefiniendo a la moda como una fuente de confianza. La primera Fashion Technology Company de Chile.',
    footer_nav: 'Navegación',
    footer_home: 'Inicio',
    footer_plans: 'Planes de Suscripción',
    footer_team: 'El Equipo',
    footer_contact_title: 'Contacto',
    footer_rights: '© 2025 OULALAB S.A. TODOS OS DERECHOS RESERVADOS.',
    read_more: 'LEER MÁS',
    collapse: 'CONTRAER'
  },
  en: {
    nav_works: 'How it works',
    nav_plans: 'Plans',
    nav_team: 'Team',
    hero_title: 'Welcome to the future of fashion.',
    hero_cta: 'JOIN THE WAITLIST',
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
    pricing_title: 'How does it work?',
    plans_title: 'Subscription Plans',
    team_subtitle: 'Behind the brand',
    team_title: 'The Oulalab Team',
    team_description: 'Leading experts in industry, branding, operations, and technology united to redefine the future of fashion.',
    pricing_btn: 'Subscribe',
    launch_countdown: 'Countdown started',
    launch_month: 'MARCH',
    launch_year: '2025',
    launch_description: 'The month Oulalab redefines the way you live fashion. The official launch is near.',
    launch_waitlist: 'Join the waitlist',
    launch_tag1: 'Infinite Style',
    launch_tag2: 'Sustainable Luxury',
    launch_tag3: 'AI Personal Shopper',
    waitlist_title: 'Join the waitlist',
    waitlist_subtitle: 'Be the first to experience the closet of your dreams this March.',
    waitlist_name: 'Full Name',
    waitlist_email: 'Email Address',
    waitlist_phone: 'Phone Number',
    waitlist_address: 'Address',
    waitlist_button: 'SECURE MY SPOT',
    waitlist_success: 'You\'re on the list!',
    waitlist_success_desc: 'We\'ll contact you in March with exclusive early access.',
    waitlist_close: 'Close',
    footer_tagline: 'Empowering women by redefining fashion as a source of confidence. The first Fashion Technology Company in Chile.',
    footer_nav: 'Navigation',
    footer_home: 'Home',
    footer_plans: 'Subscription Plans',
    footer_team: 'The Team',
    footer_contact_title: 'Contact',
    footer_rights: '© 2025 OULALAB S.A. ALL RIGHTS RESERVED.',
    read_more: 'READ MORE',
    collapse: 'COLLAPSE'
  },
  pt: {
    nav_works: 'Como funciona',
    nav_plans: 'Planos',
    nav_team: 'Equipe',
    hero_title: 'Bem-vindo ao futuro da moda.',
    hero_cta: 'ENTRAR NA LISTA DE ESPERA',
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
    deliver_desc_3: 'Acesso às melhores marcas sem pensar no preço. Aproveite o luxo hoje.',
    pricing_subtitle: 'Escolha seu estilo',
    pricing_title: 'Como funciona?',
    plans_title: 'Planos de Assinatura',
    team_subtitle: 'Por trás da marca',
    team_title: 'A Equipe Oulalab',
    team_description: 'Líderes especialistas em indústria, branding, operações e tecnologia unidos para redefinir o futuro de la moda.',
    pricing_btn: 'Assinar',
    launch_countdown: 'Contagem regressiva iniciada',
    launch_month: 'MARÇO',
    launch_year: '2025',
    launch_description: 'O mes em que a Oulalab redefine a forma como você vive a moda. O lançamento oficial está próximo.',
    launch_waitlist: 'Entrar na lista de espera',
    launch_tag1: 'Estilo Infinito',
    launch_tag2: 'Luxo Sustentável',
    launch_tag3: 'Personal Shopper con IA',
    waitlist_title: 'Entre na lista de espera',
    waitlist_subtitle: 'Seja a primeira a viver a experiência do closet dos seus sonhos em março.',
    waitlist_name: 'Nome Completo',
    waitlist_email: 'E-mail',
    waitlist_phone: 'Telefone',
    waitlist_address: 'Endereço',
    waitlist_button: 'GARANTIR MEU LUGAR',
    waitlist_success: 'Você está na lista!',
    waitlist_success_desc: 'Entraremos em contato em março con acesso antecipado exclusivo.',
    waitlist_close: 'Fechar',
    footer_tagline: 'Empoderando mulheres ao redefinir a moda como uma fonte de confiança. A primera Fashion Technology Company do Chile.',
    footer_nav: 'Navegação',
    footer_home: 'Início',
    footer_plans: 'Planos de Assinatura',
    footer_team: 'A Equipe',
    footer_contact_title: 'Contato',
    footer_rights: '© 2025 OULALAB S.A. TODOS OS DIREITOS RESERVADOS.',
    read_more: 'LER MAIS',
    collapse: 'RECOLHER'
  }
};

const App: React.FC = () => {
  const [lang, setLang] = useState<Language>('es');
  const [currency, setCurrency] = useState<Currency>('CLP');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isWaitlistOpen, setIsWaitlistOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [expandedTeamMember, setExpandedTeamMember] = useState<string | null>(null);

  const BRAND_LOGO_URL = "https://i.imgur.com/4FHPaMb.png";
  const t = UI_STRINGS[lang];

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      const offset = 80;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - offset;
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
    setIsMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 font-sans selection:bg-black selection:text-white overflow-x-hidden">
      {/* Fixed Navigation Bar */}
      <nav className={`fixed w-full z-50 transition-all duration-300 ${scrolled ? 'bg-white/95 backdrop-blur-lg shadow-lg py-3' : 'bg-transparent py-8'}`}>
        <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
          <div className="flex items-center group cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <img 
              src={BRAND_LOGO_URL} 
              alt="Oulalab Logo" 
              className={`object-contain transition-all duration-500 group-hover:scale-105 mix-blend-multiply ${scrolled ? 'h-12' : 'h-16 md:h-24'}`}
            />
          </div>

          <div className="hidden md:flex items-center space-x-6 lg:space-x-10">
            <button onClick={() => scrollToSection('how-it-works')} className="text-sm font-bold uppercase tracking-widest hover:text-black/60 transition-colors">{t.nav_works}</button>
            <button onClick={() => scrollToSection('plans')} className="text-sm font-bold uppercase tracking-widest hover:text-black/60 transition-colors">{t.nav_plans}</button>
            <button onClick={() => scrollToSection('team')} className="text-sm font-bold uppercase tracking-widest hover:text-black/60 transition-colors">{t.nav_team}</button>
            
            <div className="flex items-center space-x-2 ml-4">
              {/* Language Switcher */}
              <div className="flex items-center bg-gray-100/50 rounded-full p-1 border border-black/5">
                {(['es', 'en', 'pt'] as Language[]).map((l) => (
                  <button
                    key={l}
                    onClick={() => setLang(l)}
                    className={`px-3 py-1 text-[10px] font-black rounded-full transition-all uppercase tracking-tighter ${lang === l ? 'bg-black text-white shadow-md' : 'text-gray-400 hover:text-black'}`}
                  >
                    {l}
                  </button>
                ))}
              </div>

              {/* Currency Switcher */}
              <div className="flex items-center bg-gray-100/50 rounded-full p-1 border border-black/5">
                {(['CLP', 'USD', 'EUR'] as Currency[]).map((c) => (
                  <button
                    key={c}
                    onClick={() => setCurrency(c)}
                    className={`px-3 py-1 text-[10px] font-black rounded-full transition-all uppercase tracking-tighter ${currency === c ? 'bg-black text-white shadow-md' : 'text-gray-400 hover:text-black'}`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <button className="md:hidden p-2 text-black" onClick={() => setIsMenuOpen(!isMenuOpen)}>
            {isMenuOpen ? <X size={32} /> : <Menu size={32} />}
          </button>
        </div>
      </nav>

      {/* Mobile Overlay Menu */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-40 bg-white flex flex-col items-center justify-center space-y-10 animate-in fade-in slide-in-from-top duration-300 overflow-y-auto pt-20">
          <img src={BRAND_LOGO_URL} alt="Oulalab" className="h-20 mb-6 mix-blend-multiply" />
          <button onClick={() => scrollToSection('how-it-works')} className="text-3xl font-black uppercase tracking-tighter">{t.nav_works}</button>
          <button onClick={() => scrollToSection('plans')} className="text-3xl font-black uppercase tracking-tighter">{t.nav_plans}</button>
          <button onClick={() => scrollToSection('team')} className="text-3xl font-black uppercase tracking-tighter">{t.nav_team}</button>
          
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
        </div>
      )}

      {/* Main Hero Section */}
      <section className="relative h-screen flex items-center overflow-hidden pt-20">
        <div className="absolute inset-0 z-0">
          <img 
            src="https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&q=80&w=2000" 
            alt="Fashion background" 
            className="w-full h-full object-cover brightness-[0.5] scale-105"
            style={{ animation: 'slow-zoom 20s ease-in-out infinite alternate' }}
          />
          <div className="absolute inset-0 bg-gradient-to-r from-black via-black/30 to-transparent"></div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 w-full">
          <div className="max-w-4xl">
            <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-[7rem] text-white leading-[1] tracking-tight mb-8 font-claven">
               {t.hero_title}
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-300 mb-12 leading-relaxed max-w-xl font-medium">
              {t.hero_description}
            </p>
            
            <div className="flex flex-col sm:flex-row gap-6">
              <button 
                onClick={() => setIsWaitlistOpen(true)}
                className="group relative inline-flex items-center justify-center px-10 py-5 bg-white text-black font-black uppercase tracking-tighter hover:bg-black hover:text-white transition-all duration-300 overflow-hidden shadow-2xl"
              >
                <span className="relative z-10 flex items-center text-center">
                  {t.hero_cta} <ArrowRight className="ml-2 w-6 h-6 group-hover:translate-x-2 transition-transform" />
                </span>
              </button>
              
              <button 
                onClick={() => scrollToSection('how-it-works')}
                className="inline-flex items-center justify-center px-10 py-5 border-2 border-white/30 text-white font-black uppercase tracking-tighter hover:bg-white/10 transition-all backdrop-blur-sm"
              >
                {t.nav_works}
              </button>
            </div>
          </div>
        </div>

        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-bounce cursor-pointer z-20" onClick={() => scrollToSection('how-it-works')}>
          <ChevronDown className="text-white w-10 h-10 opacity-70" />
        </div>
      </section>

      {/* Intro Description Section (How it Works) */}
      <section id="how-it-works" className="py-32 bg-gray-50 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-24">
            <span className="text-xs font-black tracking-widest uppercase text-gray-400 mb-6 block">{t.nav_works}</span>
            <h2 className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tighter uppercase">{t.pricing_title}</h2>
          </div>
          
          <div className="grid md:grid-cols-2 gap-20 items-center">
            <div className="relative group">
              <div className="absolute -inset-6 bg-black/5 rounded-[3rem] transform -rotate-3 transition-transform group-hover:rotate-0"></div>
              <div className="relative overflow-hidden rounded-[2.5rem] shadow-2xl">
                <img 
                  src="https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&q=80&w=1000" 
                  alt="Modern fashion" 
                  className="w-full grayscale hover:grayscale-0 transition-all duration-1000 scale-100 group-hover:scale-105"
                />
              </div>
            </div>
            <div>
              <h3 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black tracking-tighter uppercase mb-10 leading-[0.9]">
                {t.intro_title_1} <span className="italic opacity-20">{t.intro_normal},</span><br />
                {t.intro_title_2}
              </h3>
              <p className="text-xl text-gray-600 leading-relaxed mb-12">
                {t.intro_description}
              </p>
              <div className="grid grid-cols-1 gap-8">
                {[
                  { icon: ShoppingBag, title: t.deliver_title_1, desc: t.deliver_desc_1 },
                  { icon: RefreshCw, title: t.deliver_title_2, desc: t.deliver_desc_2 },
                  { icon: Clock, title: t.deliver_title_3, desc: t.deliver_desc_3 }
                ].map((item, idx) => (
                  <div key={idx} className="flex items-start space-x-6 p-8 bg-white border border-gray-100 rounded-3xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-1">
                    <div className="p-4 bg-gray-50 rounded-2xl text-black">
                      <item.icon className="w-8 h-8" />
                    </div>
                    <div>
                      <h4 className="text-lg font-black uppercase tracking-tighter mb-2">{item.title}</h4>
                      <p className="text-gray-500 text-base leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Subscription Plans Section */}
      <section id="plans" className="py-32 bg-white scroll-mt-20">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <span className="text-xs font-black tracking-widest uppercase text-gray-400 mb-6 block">{t.pricing_subtitle}</span>
          <h2 className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tighter uppercase mb-20">{t.plans_title}</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-10">
            {CONTENT[lang].pricing.map((plan) => {
              const price = PRICES[currency][plan.id];
              return (
                <div key={plan.id} className={`relative flex flex-col p-8 md:p-6 lg:p-10 xl:p-12 bg-white border-2 rounded-[3.5rem] transition-all duration-500 group ${plan.id === 'premium' ? 'border-black shadow-2xl scale-105 z-10' : 'border-gray-100 hover:border-black hover:shadow-xl'}`}>
                  {plan.id === 'premium' && (
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-black text-white px-8 py-4 rounded-[2rem] text-[11px] font-black tracking-[0.2em] uppercase whitespace-nowrap shadow-xl">
                      OULALAB CHOICE
                    </div>
                  )}
                  
                  <h3 className="text-3xl md:text-2xl lg:text-4xl font-black uppercase tracking-tighter mb-4 text-center">{plan.name}</h3>
                  
                  <div className="flex flex-col items-center justify-center mb-10 text-center">
                    <span className="text-4xl sm:text-5xl md:text-2xl lg:text-4xl xl:text-7xl font-black tracking-tighter leading-none">{price}</span>
                    <div className="mt-2 flex items-center justify-center space-x-2 text-gray-400">
                      <span className="text-2xl font-light opacity-30">/</span>
                      <span className="text-[10px] sm:text-xs font-black tracking-[0.2em] uppercase">{plan.frequency}</span>
                    </div>
                  </div>

                  <div className="space-y-4 flex-grow text-left">
                    {plan.features.map((feature, i) => (
                      <div key={i} className="flex items-start space-x-3 text-sm font-bold">
                        <CheckCircle2 size={18} className="text-black shrink-0 mt-0.5" />
                        <span className="text-gray-600 group-hover:text-black transition-colors">{feature}</span>
                      </div>
                    ))}
                    <div className="pt-6 border-t border-gray-100 mt-6">
                      <p className="text-[10px] font-black uppercase tracking-widest text-black/30 mb-1">{plan.limit}</p>
                      <p className="text-xs italic font-bold text-gray-400">{plan.swap}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Founders / Team Section */}
      <section id="team" className="py-32 bg-gray-50 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-20 gap-8">
            <div className="max-w-3xl">
              <span className="text-xs font-black tracking-widest uppercase text-gray-400 mb-6 block">{t.team_subtitle}</span>
              <h2 className="text-6xl md:text-8xl font-black tracking-tighter uppercase mb-8 leading-none">{t.team_title}</h2>
              <p className="text-2xl text-gray-500 font-medium leading-relaxed italic border-l-4 border-black pl-8">{t.team_description}</p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-10">
            {CONTENT[lang].team.map((member: TeamMember, idx: number) => {
              const isExpanded = expandedTeamMember === member.name;
              return (
                <div key={idx} className="bg-white p-10 rounded-[3rem] border border-gray-100 shadow-sm hover:shadow-2xl transition-all duration-500 overflow-hidden flex flex-col group">
                  <div className="flex items-center space-x-8 mb-10">
                    <div className="relative">
                      <div className="absolute -inset-2 bg-black scale-0 group-hover:scale-100 rounded-3xl transition-transform duration-500"></div>
                      <img src={member.image} alt={member.name} className="relative w-28 h-28 rounded-[2rem] object-cover grayscale transition-all duration-700 group-hover:grayscale-0 group-hover:rotate-3 shadow-xl" />
                      <div className="absolute -bottom-3 -right-3 bg-black text-white p-3 rounded-2xl shadow-xl group-hover:scale-110 transition-transform">
                        <Star size={20} fill="white" />
                      </div>
                    </div>
                    <div>
                      <h3 className="text-2xl font-black uppercase tracking-tighter mb-1">{member.name}</h3>
                      <p className="text-black/30 font-black text-xs tracking-widest uppercase">{member.role}</p>
                    </div>
                  </div>
                  
                  <div className="mb-8 space-y-6">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-black/30 leading-relaxed bg-gray-50 p-4 rounded-xl border border-black/5">
                      {member.experience}
                    </p>
                    <div className={`relative transition-all duration-500 ${isExpanded ? '' : 'max-h-32 overflow-hidden'}`}>
                      <p className="text-gray-600 text-sm leading-[1.8] font-medium">
                        {member.description}
                      </p>
                      {!isExpanded && <div className="absolute bottom-0 inset-x-0 h-12 bg-gradient-t-t from-white to-transparent"></div>}
                    </div>
                    <button 
                      onClick={() => setExpandedTeamMember(isExpanded ? null : member.name)}
                      className="flex items-center text-[10px] font-black tracking-widest uppercase text-black hover:opacity-50 transition-opacity"
                    >
                      {isExpanded ? t.collapse : t.read_more} 
                      {isExpanded ? <ChevronUp size={16} className="ml-2" /> : <ChevronDown size={16} className="ml-2" />}
                    </button>
                  </div>

                  <div className="mt-auto pt-8 border-t border-gray-100 flex items-center justify-between">
                    <p className="italic font-black text-black/70 text-sm leading-tight max-w-[70%]">"{member.quote}"</p>
                    <div className="flex space-x-4">
                      <a href={`mailto:${member.email}`} className="p-3 bg-gray-50 hover:bg-black hover:text-white rounded-2xl transition-all shadow-sm"><Mail size={20} /></a>
                      <a href={`https://${member.linkedin}`} target="_blank" rel="noopener noreferrer" className="p-3 bg-gray-50 hover:bg-black hover:text-white rounded-2xl transition-all shadow-sm"><Linkedin size={20} /></a>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Launch Countdown CTA Section */}
      <section className="py-40 bg-black text-white relative overflow-hidden">
        <div className="absolute top-0 right-0 w-1/3 h-full bg-white/5 skew-x-[-20deg] translate-x-1/2"></div>
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <div className="inline-flex items-center space-x-3 border border-white/20 px-6 py-3 rounded-full mb-12 backdrop-blur-md">
            <Rocket className="text-white w-5 h-5 animate-bounce" />
            <span className="text-white text-xs font-black tracking-[0.3em] uppercase">{t.launch_countdown}</span>
          </div>
          <h2 className="text-5xl sm:text-7xl md:text-9xl lg:text-[10rem] xl:text-[12rem] font-black italic tracking-tighter uppercase mb-10 leading-[0.8]">
            {t.launch_month} <span className="text-white/10">{t.launch_year}</span>
          </h2>
          <p className="text-2xl md:text-3xl text-gray-400 leading-relaxed mb-16 max-w-3xl mx-auto font-medium">
            {t.launch_description}
          </p>
          <button 
            onClick={() => setIsWaitlistOpen(true)}
            className="inline-flex items-center px-16 py-8 bg-white text-black font-black uppercase tracking-tighter text-xl hover:scale-110 active:scale-95 transition-all shadow-[0_0_50px_rgba(255,255,255,0.3)]"
          >
            {t.launch_waitlist} <Send className="ml-4 w-6 h-6" />
          </button>
        </div>
      </section>

      {/* Site Footer */}
      <footer className="py-32 bg-white border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-20 mb-32">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center mb-12 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
                <img 
                  src={BRAND_LOGO_URL} 
                  alt="Oulalab Logo" 
                  className="h-16 w-auto object-contain transition-transform hover:scale-105 mix-blend-multiply"
                />
              </div>
              <p className="text-gray-500 font-bold text-xl leading-relaxed max-w-md italic opacity-80">
                {t.footer_tagline}
              </p>
            </div>
            
            <div>
              <h4 className="font-black uppercase tracking-widest text-xs mb-10 text-black/30">{t.footer_nav}</h4>
              <ul className="space-y-6 font-black text-black text-sm uppercase tracking-tighter">
                <li><button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="hover:opacity-40 transition-opacity">{t.footer_home}</button></li>
                <li><button onClick={() => scrollToSection('how-it-works')} className="hover:opacity-40 transition-opacity">{t.nav_works}</button></li>
                <li><button onClick={() => scrollToSection('plans')} className="hover:opacity-40 transition-opacity">{t.footer_plans}</button></li>
                <li><button onClick={() => scrollToSection('team')} className="hover:opacity-40 transition-opacity">{t.footer_team}</button></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-black uppercase tracking-widest text-xs mb-10 text-black/30">{t.footer_contact_title}</h4>
              <ul className="space-y-6 font-black text-black text-sm uppercase tracking-tighter">
                <li><a href="mailto:hola@oulalab.com" className="hover:opacity-40 transition-opacity">hola@oulalab.com</a></li>
                <li><a href="#" className="hover:opacity-40 transition-opacity">LinkedIn</a></li>
                <li className="flex items-center space-x-3 pt-4 opacity-50">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-[10px] tracking-widest uppercase">Global Operations in Chile</span>
                </li>
              </ul>
            </div>
          </div>
          
          <div className="pt-16 border-t border-gray-100 flex flex-col md:flex-row justify-between items-center gap-10">
            <p className="text-[10px] font-black uppercase tracking-[0.4em] text-black/20">
              {t.footer_rights}
            </p>
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2 text-black/20">
                <Languages size={16} />
                <span className="text-[10px] font-black uppercase tracking-widest">Global Fashion Network</span>
              </div>
              <div className="w-10 h-1 text-black/10"></div>
              <p className="text-[10px] font-black uppercase tracking-widest text-black/40">EST. 2025</p>
            </div>
          </div>
        </div>
      </footer>

      {/* Waitlist Registration Modal */}
      {isWaitlistOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center px-6">
          <div className="absolute inset-0 bg-black/95 backdrop-blur-xl animate-in fade-in duration-500" onClick={() => setIsWaitlistOpen(false)}></div>
          <div className="relative bg-white w-full max-w-2xl rounded-[4rem] overflow-hidden shadow-[0_0_100px_rgba(255,255,255,0.1)] animate-in zoom-in-95 duration-300">
            <button className="absolute top-10 right-10 p-4 hover:bg-gray-100 rounded-full transition-all active:scale-90 z-10" onClick={() => setIsWaitlistOpen(false)}>
              <X size={32} />
            </button>
            
            <div className="p-16 md:p-24">
              <div className="text-center mb-16">
                <img src={BRAND_LOGO_URL} alt="Oulalab" className="h-16 mx-auto mb-12 mix-blend-multiply" />
                <h3 className="text-5xl font-black uppercase tracking-tighter mb-6 leading-none">{t.waitlist_title}</h3>
                <p className="text-xl text-gray-500 font-medium leading-relaxed italic">{t.waitlist_subtitle}</p>
              </div>
              
              <form className="space-y-8" onSubmit={(e) => {
                e.preventDefault();
                alert(t.waitlist_success);
                setIsWaitlistOpen(false);
              }}>
                <div className="grid md:grid-cols-2 gap-8">
                  <div>
                    <label className="text-[10px] font-black uppercase tracking-[0.3em] text-black/20 mb-4 block">{t.waitlist_name}</label>
                    <input type="text" className="w-full bg-gray-50 border-b-2 border-transparent focus:border-black rounded-2xl px-8 py-6 font-bold text-lg outline-none transition-all placeholder:text-black/10" placeholder="Jane Doe" required />
                  </div>
                  <div>
                    <label className="text-[10px] font-black uppercase tracking-[0.3em] text-black/20 mb-4 block">{t.waitlist_email}</label>
                    <input type="email" className="w-full bg-gray-50 border-b-2 border-transparent focus:border-black rounded-2xl px-8 py-6 font-bold text-lg outline-none transition-all placeholder:text-black/10" placeholder="jane@oulalab.com" required />
                  </div>
                </div>
                <button type="submit" className="w-full bg-black text-white font-black uppercase tracking-[0.2em] py-8 rounded-[2rem] hover:scale-[1.02] active:scale-95 transition-all shadow-2xl text-lg">
                  {t.waitlist_button}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;