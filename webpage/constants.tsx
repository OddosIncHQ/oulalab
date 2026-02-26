
import { PricingPlan, TeamMember, Currency } from './types';

export const PRICES: Record<Currency, Record<string, string>> = {
  CLP: {
    'try-on': '$49.900',
    'premium': '$128.000',
    'luxury': '$249.000'
  },
  USD: {
    'try-on': '$55',
    'premium': '$145',
    'luxury': '$280'
  },
  EUR: {
    'try-on': '€50',
    'premium': '€135',
    'luxury': '€260'
  }
};

export const CONTENT = {
  es: {
    pricing: [
      {
        id: 'try-on',
        name: 'Try On',
        frequency: 'SEMANAL',
        features: ['Acceso al catálogo premium', 'Limpieza incluida', 'Envío prioritario'],
        limit: 'HASTA 2 PRENDAS POR SEMANA',
        swap: 'Ideal para eventos puntuales'
      },
      {
        id: 'premium',
        name: 'Premium',
        frequency: 'MENSUAL',
        features: ['Suscripción flexible', 'Acceso a todas las marcas', 'Seguro de prenda básico'],
        limit: 'HASTA 10 PRENDAS POR MES',
        swap: 'Swap al día 15 del mes'
      },
      {
        id: 'luxury',
        name: 'Luxury',
        frequency: 'MENSUAL',
        features: ['Curaduría VIP', 'Personal Shopper dedicado', 'Acceso anticipado a colecciones'],
        limit: 'HASTA 16 PRENDAS POR MES',
        swap: 'Swap al día 15 del mes'
      }
    ],
    team: [
      {
        name: 'Andy Klawer',
        role: 'COO',
        title: 'COO by Oulalab',
        experience: '17 AÑOS DE EXPERIENCIA EN PRODUCCIÓN DE MODA EN ASIA',
        description: 'Líder en procesos industriales a gran escala, ha trabajado de cerca con fábricas, proveedores y las marcas globales. Este recorrido le otorgó un conocimiento profundo de la cadena de suministro textil y de los desafíos medioambientales que enfrenta la industria. Su enfoque práctico y visionario lo llevó a impulsar soluciones que reducen el impacto ambiental sin comprometer la calidad ni la estética.',
        quote: 'Haz que suceda.',
        image: 'https://i.imgur.com/oOpfrDY.jpeg',
        email: 'andres@oulalab.com',
        linkedin: 'linkedin.com/in/andrés-klawer-75842b67'
      },
      {
        name: 'Gaby Badagnani',
        role: 'CMO',
        title: 'CMO by Oulalab',
        experience: '25 AÑOS EN EMPRESAS INTERNACIONALES DE CONSULTORÍA DE MARCA',
        description: 'Con amplia trayectoria liderando las consultoras de branding más importantes del mundo, ha ayudado a marcas en múltiples categorías en toda América y Europa a crear sus estrategias de marca y marketing. Además, es profesor de branding en la UDD y la UC, Presidente del Board de los Best Branding Awards en Latam y conferencista internacional.',
        quote: 'Construyendo marcas que la gente ame.',
        image: 'https://i.imgur.com/AxJAdZi.jpeg',
        email: 'gabriel@oulalab.com',
        linkedin: 'linkedin.com/in/gabriel-badagnani-59961918'
      },
      {
        name: 'Maca Loy',
        role: 'CCO',
        title: 'CCO by Oulalab',
        experience: '10+ AÑOS COMBINANDO ENFOQUES DE DISEÑO CON ESTILO',
        description: 'Creativa estratégica con ADN en moda y una visión de marca afilada, ha desarrollado una sensibilidad estética ligada al lujo y las tendencias globales. Responsable del diseño y curatoría de colecciones femeninas y juveniles en líderes de retail chileno y como DC de empresas internacionales. Es líder natural para formar equipos con enfoque creativo y estratégico y con una ejecución de clase mundial.',
        quote: 'Detrás de cada gran mujer hay otra gran mujer.',
        image: 'https://i.imgur.com/OJjZdZt.jpeg',
        email: 'macarena@oulalab.com',
        linkedin: 'linkedin.com/in/mmloy'
      },
      {
        name: 'Javi Contreras',
        role: 'CEO',
        title: 'CEO by Oulalab',
        experience: '25 AÑOS DE EXPERIENCIA EN IMPUESTOS M&A',
        description: 'Hoy lidera el equipo de impuestos de EY siendo líder de industria. Con un MBA de la Universidad Adolfo Ibáñez y una certificación como directora del IDDC, complementadas con programas de liderazgo estratégico en Babson College destaca su habilidad para innovar, adaptar estrategias y liderar equipos de alto desempeño. En los últimos dos años ha desarrollado soluciones tecnológicas en el ámbito de impuestos posicionándolas en el mercado local.',
        quote: 'Si vienes a la fiesta, tienes que bailar.',
        image: 'https://i.imgur.com/3hyDj6t.jpeg',
        email: 'javiera@oulalab.com',
        linkedin: 'linkedin.com/in/m-javiera-conteras'
      },
      {
        name: 'Angel Izurieta',
        role: 'CIO',
        title: 'CIO by Oulalab',
        experience: '25 AÑOS TRANSFORMANDO EMPRESAS A TRAVÉS DE LA TECNOLOGÍA',
        description: 'Actualmente es el Gerente General de Google Cloud en Chile y ha estado vinculado al mundo de Tecnología por más de 25 años en distintos roles en Accenture y EY. Inversionista Angel en varias startups y limited Partner en dos VCs que lo hacen conocedor del ecosistema digital.',
        quote: 'Nunca dejes de aprender porque la vida nunca deja de enseñar.',
        image: 'https://i.imgur.com/K8Dk9yH.jpeg',
        email: 'angel@oulalab.com',
        linkedin: 'linkedin.com/in/angel-izurieta-6a29811'
      },
      {
        name: 'Mauri Loy',
        role: 'CLO',
        title: 'CLO by Oulalab',
        experience: '20 AÑOS EN ESTRUCTURACIÓN DE NEGOCIOS Y M&A',
        description: 'Abogado con más de 20 años de experiencia en el ámbito jurídico y fiscal, especializado en estructuración de inversiones, litigios fiscales, reorganizaciones corporativas, y M&A. Fundador de Letonja & Loy abogados y de SoothSayer, una empresa pionera en Compliance Risk Analytics en Chile, implementando el primer algoritmo de riesgo impositivo en la región. Excelentes habilidades en la creación y gestión de equipos complejos.',
        quote: 'No le tengo miedo a nada, tengo dos hijas.',
        image: 'https://i.imgur.com/OhaBIqp.jpeg',
        email: 'mauricio@oulalab.com',
        linkedin: 'linkedin.com/in/mauricio-loy-b96a91127'
      }
    ]
  },
  en: {
    pricing: [
      {
        id: 'try-on',
        name: 'Try On',
        frequency: 'WEEKLY',
        features: ['Access to premium catalog', 'Cleaning included', 'Priority shipping'],
        limit: 'UP TO 2 ITEMS PER WEEK',
        swap: 'Ideal for occasional events'
      },
      {
        id: 'premium',
        name: 'Premium',
        frequency: 'MONTHLY',
        features: ['Flexible subscription', 'Access to all brands', 'Basic garment insurance'],
        limit: 'UP TO 10 ITEMS PER MONTH',
        swap: 'Swap on the 15th of the month'
      },
      {
        id: 'luxury',
        name: 'Luxury',
        frequency: 'MONTHLY',
        features: ['VIP curation', 'Dedicated Personal Shopper', 'Early access to collections'],
        limit: 'UP TO 16 ITEMS PER MONTH',
        swap: 'Swap on the 15th of the month'
      }
    ],
    team: [
      {
        name: 'Andy Klawer',
        role: 'COO',
        title: 'COO by Oulalab',
        experience: '17 YEARS EXPERIENCE IN FASHION PRODUCTION IN ASIA',
        description: 'Leader in large-scale industrial processes, he has worked closely with factories, suppliers, and global brands. This journey gave him a deep understanding of the textile supply chain and the environmental challenges facing the industry. His practical and visionary approach led him to drive solutions that reduce environmental impact without compromising quality or aesthetics.',
        quote: 'Make it happens.',
        image: 'https://i.imgur.com/oOpfrDY.jpeg',
        email: 'andres@oulalab.com',
        linkedin: 'linkedin.com/in/andrés-klawer-75842b67'
      },
      {
        name: 'Gaby Badagnani',
        role: 'CMO',
        title: 'CMO by Oulalab',
        experience: '25 YEAR INTERNATIONAL BRAND CONSULTING COMPANIES',
        description: 'With a vast track record leading the world\'s most important branding consultancies, he has helped brands in multiple categories across America and Europe create their brand and marketing strategies. Furthermore, he is a professor of branding at UDD and UC, Chairman of the Board of the Best Branding Awards in Latam, and an international speaker.',
        quote: 'Building brands to people love.',
        image: 'https://i.imgur.com/AxJAdZi.jpeg',
        email: 'gabriel@oulalab.com',
        linkedin: 'linkedin.com/in/gabriel-badagnani-59961918'
      },
      {
        name: 'Maca Loy',
        role: 'CCO',
        title: 'CCO by Oulalab',
        experience: '10+ YEARS OF FASHIONABLY BLENDING DESIGN APPROACHES',
        description: 'Strategic creative with a fashion DNA and a sharp brand vision, she has developed an aesthetic sensitivity linked to luxury and global trends. Responsible for the design and curation of women\'s and youth collections in Chilean retail leaders and as DC for international companies. She is a natural leader for building teams with a creative and strategic focus and world-class execution.',
        quote: 'Behind every great woman is another great woman.',
        image: 'https://i.imgur.com/OJjZdZt.jpeg',
        email: 'macarena@oulalab.com',
        linkedin: 'linkedin.com/in/mmloy'
      },
      {
        name: 'Javi Contreras',
        role: 'CEO',
        title: 'CEO by Oulalab',
        experience: '25 YEAR EXPERIENCE IN M&A TAX',
        description: 'Currently leads the tax team at EY as an industry leader. With an MBA from Adolfo Ibáñez University and certification as an IDDC director, complemented by strategic leadership programs at Babson College, she stands out for her ability to innovate, adapt strategies, and lead high-performance teams. In the last two years, she has developed technological solutions in the tax field, positioning them in the local market.',
        quote: 'If you come to the party you have to dance.',
        image: 'https://i.imgur.com/3hyDj6t.jpeg',
        email: 'javiera@oulalab.com',
        linkedin: 'linkedin.com/in/m-javiera-conteras'
      },
      {
        name: 'Angel Izurieta',
        role: 'CIO',
        title: 'CIO by Oulalab',
        experience: '25 YEARS TRANSFORMING COMPANIES THROUGH TECHNOLOGY',
        description: 'Currently the General Manager of Google Cloud in Chile, he has been linked to the technology world for more than 25 years in various roles at Accenture and EY. Angel investor in several startups and limited partner in two VCs, making him an expert in the digital ecosystem.',
        quote: 'Never stop learning because life never stops teaching.',
        image: 'https://i.imgur.com/K8Dk9yH.jpeg',
        email: 'angel@oulalab.com',
        linkedin: 'linkedin.com/in/angel-izurieta-6a29811'
      },
      {
        name: 'Mauri Loy',
        role: 'CLO',
        title: 'CLO by Oulalab',
        experience: '20 YEARS IN BUSINESS STRUCTURING AND M&A',
        description: 'Lawyer with more than 20 years of experience in the legal and tax field, specializing in investment structuring, tax litigation, corporate reorganizations, and M&A. Founder of Letonja & Loy lawyers and SoothSayer, a pioneer company in Compliance Risk Analytics in Chile, implementing the first tax risk algorithm in the region. Excellent skills in creating and managing complex teams.',
        quote: 'I\'m not afraid of anything, I have two daughters.',
        image: 'https://i.imgur.com/OhaBIqp.jpeg',
        email: 'mauricio@oulalab.com',
        linkedin: 'linkedin.com/in/mauricio-loy-b96a91127'
      }
    ]
  },
  pt: {
    pricing: [
      {
        id: 'try-on',
        name: 'Try On',
        frequency: 'SEMANAL',
        features: ['Acesso ao catálogo premium', 'Lavagem incluída', 'Entrega prioritária'],
        limit: 'ATÉ 2 PEÇAS POR SEMANA',
        swap: 'Ideal para eventos ocasionais'
      },
      {
        id: 'premium',
        name: 'Premium',
        frequency: 'MENSAL',
        features: ['Assinatura flexível', 'Acesso a todas as marcas', 'Seguro de peça básico'],
        limit: 'ATÉ 10 PEÇAS POR MÊS',
        swap: 'Troca no dia 15 do mês'
      },
      {
        id: 'luxury',
        name: 'Luxury',
        frequency: 'MENSAL',
        features: ['Curadoria VIP', 'Personal Shopper dedicado', 'Acesso antecipado a coleções'],
        limit: 'ATÉ 16 PEÇAS POR MÊS',
        swap: 'Troca no dia 15 do mês'
      }
    ],
    team: [
      {
        name: 'Andy Klawer',
        role: 'COO',
        title: 'COO da Oulalab',
        experience: '17 ANOS DE EXPERIÊNCIA EM PRODUÇÃO DE MODA NA ÁSIA',
        description: 'Líder em processos industriais de grande escala, trabalhou de perto com fábricas, fornecedores e marcas globais. Esta jornada deu a ele uma compreensão profunda da cadeia de suprimentos têxtil e dos desafios ambientais que a indústria enfrenta. Sua abordagem prática e visionária o levou a impulsionar soluções que reduzem o impacto ambiental sem comprometer a qualidade ou a estética.',
        quote: 'Faça acontecer.',
        image: 'https://i.imgur.com/oOpfrDY.jpeg',
        email: 'andres@oulalab.com',
        linkedin: 'linkedin.com/in/andrés-klawer-75842b67'
      },
      {
        name: 'Gaby Badagnani',
        role: 'CMO',
        title: 'CMO da Oulalab',
        experience: '25 ANOS EM EMPRESAS INTERNACIONAIS DE CONSULTORIA DE MARCA',
        description: 'Com uma vasta trajetória liderando as consultorias de branding mais importantes do mundo, ajudou marcas em múltiplas categorias em toda a América e Europa a criar suas estratégias de marca e marketing. Além disso, é professor de branding na UDD e UC, Presidente do Conselho dos Best Branding Awards na América Latina e palestrante internacional.',
        quote: 'Construindo marcas que as pessoas amem.',
        image: 'https://i.imgur.com/AxJAdZi.jpeg',
        email: 'gabriel@oulalab.com',
        linkedin: 'linkedin.com/in/gabriel-badagnani-59961918'
      },
      {
        name: 'Maca Loy',
        role: 'CCO',
        title: 'CCO da Oulalab',
        experience: '10+ ANOS UNINDO DESIGN E ESTILO COM ESTRATÉGIA',
        description: 'Criativa estratégica com DNA em moda e uma visão de marca aguçada, desenvolveu uma sensibilidade estética ligada ao luxo e às tendências globais. Responsável pelo design e curadoria de coleções femininas e juvenis em líderes do varejo chileno e como DC de empresas internacionais. É uma líder natural para formar equipes com foco criativo e estratégico e execução de classe mundial.',
        quote: 'Atrás de cada grande mulher há outra grande mulher.',
        image: 'https://i.imgur.com/OJjZdZt.jpeg',
        email: 'macarena@oulalab.com',
        linkedin: 'linkedin.com/in/mmloy'
      },
      {
        name: 'Javi Contreras',
        role: 'CEO',
        title: 'CEO da Oulalab',
        experience: '25 ANOS DE EXPERIÊNCIA EM TRIBUTÁRIO M&A',
        description: 'Atualmente lidera a equipe tributária da EY como líder da indústria. Com um MBA pela Universidade Adolfo Ibáñez e certificação como diretora do IDDC, complementada por programas de liderança estratégica no Babson College, destaca-se por sua habilidade em inovar, adaptar estratégias e liderar equipes de alto desempenho.',
        quote: 'Se você vem para a festa, tem que dançar.',
        image: 'https://i.imgur.com/3hyDj6t.jpeg',
        email: 'javiera@oulalab.com',
        linkedin: 'linkedin.com/in/m-javiera-conteras'
      },
      {
        name: 'Angel Izurieta',
        role: 'CIO',
        title: 'CIO da Oulalab',
        experience: '25 ANOS TRANSFORMANDO EMPRESAS ATRAVÉS DA TECNOLOGÍA',
        description: 'Atualmente é Gerente Geral do Google Cloud no Chile e está vinculado ao mundo da tecnologia há mais de 25 anos em diferentes funções na Accenture e EY. Investidor anjo em várias startups e limited partner em dois VCs.',
        quote: 'Nunca pare de aprender porque a vida nunca para de ensinar.',
        image: 'https://i.imgur.com/K8Dk9yH.jpeg',
        email: 'angel@oulalab.com',
        linkedin: 'linkedin.com/in/angel-izurieta-6a29811'
      },
      {
        name: 'Mauri Loy',
        role: 'CLO',
        title: 'CLO da Oulalab',
        experience: '20 ANOS EM ESTRUTURAÇÃO DE NEGÓCIOS E M&A',
        description: 'Advogado with more than 20 years of experience in the legal and tax field, specializing in investment structuring, tax litigation, corporate reorganizations, and M&A. Founder of Letonja & Loy lawyers and SoothSayer, a pioneer company in Compliance Risk Analytics in Chile, implementing the first tax risk algorithm in the region. Excellent skills in creating and managing complex teams.',
        quote: 'Não tenho medo de nada, tenho duas filhas.',
        image: 'https://i.imgur.com/OhaBIqp.jpeg',
        email: 'mauricio@oulalab.com',
        linkedin: 'linkedin.com/in/mauricio-loy-b96a91127'
      }
    ]
  }
};