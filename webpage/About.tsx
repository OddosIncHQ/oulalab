function About() {
  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#f7f5f1",
        color: "#111111",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", sans-serif',
      }}
    >
      <section
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "100px 24px 80px",
        }}
      >
        <div style={{ maxWidth: "760px" }}>
          <p
            style={{
              fontSize: "12px",
              letterSpacing: "0.22em",
              textTransform: "uppercase",
              marginBottom: "24px",
              opacity: 0.65,
            }}
          >
            About OULALAB
          </p>

          <h1
            style={{
              fontSize: "clamp(42px, 8vw, 88px)",
              lineHeight: "0.95",
              fontWeight: 600,
              letterSpacing: "-0.04em",
              margin: 0,
              marginBottom: "28px",
            }}
          >
            Moda de alta gama,
            <br />
            reimaginada con inteligencia.
          </h1>

          <p
            style={{
              fontSize: "20px",
              lineHeight: 1.7,
              color: "#3b3b3b",
              margin: 0,
              maxWidth: "720px",
            }}
          >
            En OULALAB creemos que el futuro de la moda no está en acumular,
            sino en acceder de forma más inteligente, más flexible y más
            refinada.
          </p>
        </div>
      </section>

      <section
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "0 24px 90px",
        }}
      >
        <div
          style={{
            display: "grid",
            gap: "24px",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          }}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "28px",
              padding: "32px",
              boxShadow: "0 10px 30px rgba(0,0,0,0.04)",
            }}
          >
            <p
              style={{
                fontSize: "12px",
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                opacity: 0.55,
                marginBottom: "18px",
              }}
            >
              Visión
            </p>
            <p
              style={{
                fontSize: "22px",
                lineHeight: 1.5,
                margin: 0,
              }}
            >
              Redefinimos el acceso a la moda de lujo mediante tecnología,
              curaduría y una experiencia diseñada para una nueva generación.
            </p>
          </div>

          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "28px",
              padding: "32px",
              boxShadow: "0 10px 30px rgba(0,0,0,0.04)",
            }}
          >
            <p
              style={{
                fontSize: "12px",
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                opacity: 0.55,
                marginBottom: "18px",
              }}
            >
              Inteligencia
            </p>
            <p
              style={{
                fontSize: "22px",
                lineHeight: 1.5,
                margin: 0,
              }}
            >
              Usamos datos e inteligencia artificial para entender preferencias,
              optimizar inventario y hacer que cada prenda circule con precisión.
            </p>
          </div>

          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "28px",
              padding: "32px",
              boxShadow: "0 10px 30px rgba(0,0,0,0.04)",
            }}
          >
            <p
              style={{
                fontSize: "12px",
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                opacity: 0.55,
                marginBottom: "18px",
              }}
            >
              Experiencia
            </p>
            <p
              style={{
                fontSize: "22px",
                lineHeight: 1.5,
                margin: 0,
              }}
            >
              Un clóset rotativo de piezas premium, pensado para quienes valoran
              estilo, innovación y libertad por sobre la posesión tradicional.
            </p>
          </div>
        </div>
      </section>

      <section
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "0 24px 120px",
        }}
      >
        <div
          style={{
            backgroundColor: "#111111",
            color: "#f8f6f2",
            borderRadius: "36px",
            padding: "56px 32px",
          }}
        >
          <div style={{ maxWidth: "820px" }}>
            <p
              style={{
                fontSize: "12px",
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                opacity: 0.7,
                marginBottom: "20px",
              }}
            >
              Nuestra propuesta
            </p>

            <p
              style={{
                fontSize: "clamp(24px, 4vw, 40px)",
                lineHeight: 1.25,
                letterSpacing: "-0.03em",
                margin: 0,
                marginBottom: "28px",
                fontWeight: 500,
              }}
            >
              OULALAB opera en la intersección entre moda, logística y
              tecnología para construir una forma más sofisticada de vestir.
            </p>

            <p
              style={{
                fontSize: "18px",
                lineHeight: 1.8,
                color: "rgba(248,246,242,0.82)",
                margin: 0,
                maxWidth: "760px",
              }}
            >
              Cada prenda es parte de un sistema diseñado para aprender,
              adaptarse y evolucionar. Desde la selección hasta la entrega, cada
              detalle busca unir lujo, eficiencia y una nueva visión del acceso.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default About;
