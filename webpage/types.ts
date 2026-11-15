
export type Currency = 'CLP' | 'USD' | 'EUR';

export interface PricingPlan {
  id: string;
  name: string;
  frequency: string;
  features: string[];
  limit: string;
  swap: string;
}

export interface TeamMember {
  name: string;
  role: string;
  title: string;
  experience: string;
  description: string;
  quote: string;
  image: string;
  email: string;
  linkedin: string;
}