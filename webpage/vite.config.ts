import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Carga las variables de entorno del archivo .env o de los Secretos de GitHub
  const env = loadEnv(mode, '.', '');
  
  return {
    // Al usar dominio propio (www.oulalab.com), la base debe ser la raíz '/'
    base: '/', 
    
    server: {
      port: 3000,
      host: '0.0.0.0',
    },
    
    plugins: [react()],
    
    define: {
      // Estas líneas permiten que tu código acceda a la API KEY de Gemini
      // configurada en los Secrets de GitHub Actions
      'process.env.GEMINI_API_KEY': JSON.stringify(env.VITE_GEMINI_API_KEY || env.GEMINI_API_KEY),
      'process.env.API_KEY': JSON.stringify(env.VITE_GEMINI_API_KEY || env.GEMINI_API_KEY)
    },
    
    resolve: {
      alias: {
        // Mantiene la referencia '@' hacia la carpeta actual para los imports
        '@': path.resolve(__dirname, '.'),
      }
    }
  };
});
