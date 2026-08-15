import LegalDocumentLayout from "@features/legal/components/LegalDocumentLayout";
import { LEGAL_DOCUMENT_TYPES } from "@features/legal/services/legalDocumentsService";

function Section({ title, children }) {
  return (
    <section>
      <h2 className="mb-2 text-lg font-semibold text-primary">{title}</h2>
      {children}
    </section>
  );
}

export default function PrivacyPolicyPage() {
  return (
    <LegalDocumentLayout type={LEGAL_DOCUMENT_TYPES.privacy} title="Política de Privacidad">
      <Section title="1. Responsable">
        <p>La identificación legal completa del responsable del tratamiento, su domicilio y el canal de privacidad están pendientes de definición institucional y deben completarse antes de habilitar esta versión en producción.</p>
      </Section>
      <Section title="2. Datos tratados">
        <p>FeedGo trata datos de cuenta y perfil, evidencia de aceptación, información y contenido de espacios, interacciones sociales, denuncias, datos operativos de seguridad, consultas y eventos de búsqueda, y datos geográficos cuando se utilizan funciones de ubicación.</p>
      </Section>
      <Section title="3. Registro y perfil">
        <p>Para crear una cuenta se tratan email, credenciales protegidas y los datos de perfil incorporados durante el uso. La creación registra separadamente la aceptación de Términos y Política con usuario, tipo, versión, fecha, canal y mecanismo.</p>
      </Section>
      <Section title="4. Espacios y contenidos">
        <p>Los propietarios pueden aportar nombre, descripción, imágenes, contactos, rubros, publicaciones, horarios y ubicación. Los contenidos destinados a difusión se muestran conforme a la configuración y permisos aplicables.</p>
      </Section>
      <Section title="5. Ubicación dinámica del usuario">
        <p>Con permiso del navegador, FeedGo obtiene temporalmente coordenadas, precisión y momento técnico para determinar territorio, ordenar cercanía y calcular distancias. Se mantienen en memoria de sesión, sin historial de desplazamientos, seguimiento permanente ni geolocalización en segundo plano.</p>
      </Section>
      <Section title="6. Alternativa manual y revocación">
        <p>La ubicación puede rechazarse o revocarse desde el navegador. FeedGo sigue funcionando mediante selección manual de provincia y ciudad; una ciudad del perfil se presenta únicamente como referencia elegida y no como GPS actual.</p>
      </Section>
      <Section title="7. Ubicación persistida del espacio">
        <p>Provincia, ciudad, dirección y coordenadas confirmadas se conservan para pertenencia territorial, Search, Discovery y funciones geográficas. Esta ubicación pertenece al espacio y nunca se reemplaza con la posición dinámica de quien busca.</p>
      </Section>
      <Section title="8. Dirección pública y privada">
        <p>El propietario controla la publicación del domicilio. Si es público pueden mostrarse dirección, coordenadas derivadas, distancia, mapa y “Cómo llegar”. Si es privado, la API pública omite esos datos y muestra solo la ciudad, aunque FeedGo mantenga la ubicación para búsqueda local.</p>
      </Section>
      <Section title="9. Búsqueda, Discovery y distancia">
        <p>El territorio determina candidatos y la posición vigente puede aportar cercanía. Los espacios privados pueden utilizar una banda geográfica interna no expuesta; no se devuelve al cliente su distancia, score ni coordenadas.</p>
      </Section>
      <Section title="10. Geocoding y proveedores">
        <p>Las búsquedas de dirección envían al proveedor la consulta y contexto territorial necesarios; el reverse geocoding envía coordenadas. Actualmente FeedGo utiliza Geoapify mediante backend, sin enviar usuario, email, IDs internos ni credenciales de FeedGo. Geoapify procesa además metadatos técnicos de red conforme a sus propias condiciones.</p>
      </Section>
      <Section title="11. Mapas y atribución">
        <p>La cartografía utiliza OpenStreetMap y la interfaz muestra las atribuciones exigidas. El proveedor puede ser sustituido sin cambiar el contrato funcional del dominio.</p>
      </Section>
      <Section title="12. Logs y analítica">
        <p>FeedGo mantiene logs operativos y métricas necesarias para seguridad, diagnóstico y funcionamiento. SearchEvent registra consulta y contexto territorial normalizado, alcance y resultados, pero no coordenadas precisas ni domicilios privados.</p>
      </Section>
      <Section title="13. Conservación">
        <p>La ubicación dinámica se conserva solo en memoria. Los datos de cuenta, espacios y evidencias se mantienen mientras resulten necesarios para el servicio, obligaciones y seguridad. Los plazos concretos y procedimientos operativos deben formalizarse antes del lanzamiento.</p>
      </Section>
      <Section title="14. Seguridad y destinatarios">
        <p>Se aplican validaciones, ownership, proyecciones públicas, control de credenciales, rate limiting y minimización. Los datos se comunican a proveedores únicamente en la medida necesaria para prestar cada función o cumplir obligaciones aplicables.</p>
      </Section>
      <Section title="15. Derechos">
        <p>Las personas pueden solicitar acceso, rectificación, actualización y supresión conforme a la normativa aplicable. El canal formal y el procedimiento de ejercicio deben publicarse antes de activar productivamente esta versión.</p>
      </Section>
      <Section title="16. Cambios de versión">
        <p>Los cambios materiales se evaluarán para informar o solicitar reaceptación. La evidencia histórica conserva la versión efectivamente aceptada y no autoriza automáticamente tratamientos futuros incompatibles.</p>
      </Section>
    </LegalDocumentLayout>
  );
}
