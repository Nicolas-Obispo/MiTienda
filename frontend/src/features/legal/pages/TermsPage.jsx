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

export default function TermsPage() {
  return (
    <LegalDocumentLayout type={LEGAL_DOCUMENT_TYPES.terms} title="Términos y Condiciones">
      <Section title="1. Alcance">
        <p>Estos términos regulan el acceso y uso de FeedGo, una plataforma local para explorar espacios, contenidos y servicios, y para que sus propietarios administren su presencia pública.</p>
      </Section>
      <Section title="2. Responsable e información institucional">
        <p>La identificación legal completa del responsable, domicilio y canal formal se encuentran pendientes de definición institucional y deberán incorporarse antes de la activación productiva de esta versión.</p>
      </Section>
      <Section title="3. Uso sin cuenta y registro">
        <p>FeedGo permite un modo Explorar sin registro. Para utilizar funciones asociadas a una cuenta se requiere información válida, aceptación separada de estos Términos y de la Política de Privacidad, y cumplimiento de los requisitos del registro.</p>
      </Section>
      <Section title="4. Cuenta y seguridad">
        <p>La persona usuaria debe proteger sus credenciales, suministrar información veraz y comunicar usos no autorizados cuando exista un canal habilitado. No debe intentar vulnerar permisos, privacidad, disponibilidad o integridad del servicio.</p>
      </Section>
      <Section title="5. Espacios y contenido">
        <p>Quien crea un espacio declara que puede administrarlo y es responsable por la veracidad, actualización y licitud de su información y contenido. FeedGo puede aplicar moderación, desactivación o restricciones conforme a sus controles vigentes.</p>
      </Section>
      <Section title="6. Ubicación de los espacios">
        <p>Los espacios nuevos deben declarar provincia, ciudad, dirección y coordenadas confirmadas. FeedGo utiliza esa ubicación para búsqueda local y funciones geográficas. La ubicación interna y la publicación del domicilio son decisiones independientes.</p>
      </Section>
      <Section title="7. Dirección pública o privada">
        <p>La dirección se publica por defecto en nuevas altas, con un control visible para desactivarla. Si permanece pública pueden mostrarse dirección, mapa, distancia y “Cómo llegar”. Si se mantiene privada, FeedGo conserva internamente la ubicación y muestra públicamente solo la ciudad.</p>
      </Section>
      <Section title="8. Ubicación de quien busca">
        <p>Las funciones cercanas pueden solicitar permiso técnico del navegador. La aceptación de estos documentos no concede ese permiso. Rechazarlo no elimina la cuenta y permite utilizar una selección territorial manual.</p>
      </Section>
      <Section title="9. Servicios externos">
        <p>FeedGo puede utilizar proveedores reemplazables para geocoding y mapas. Actualmente el geocoding se integra mediante Geoapify desde el backend y la cartografía utiliza datos de OpenStreetMap con la atribución correspondiente.</p>
      </Section>
      <Section title="10. Disponibilidad y cambios">
        <p>El servicio puede experimentar mantenimiento, errores o cambios compatibles con su evolución. FeedGo no garantiza disponibilidad ininterrumpida ni resultados perfectos de búsqueda, geocoding o información aportada por terceros.</p>
      </Section>
      <Section title="11. Conductas prohibidas">
        <p>No se permite suplantar identidades, publicar contenido ilícito, obtener datos privados, abusar de endpoints o proveedores, manipular resultados, introducir código malicioso ni utilizar la plataforma para dañar a otras personas.</p>
      </Section>
      <Section title="12. Privacidad y derechos">
        <p>El tratamiento de datos se explica separadamente en la Política de Privacidad. Las solicitudes sobre datos se atenderán mediante el canal formal que debe quedar definido antes del lanzamiento.</p>
      </Section>
      <Section title="13. Versiones y reaceptación">
        <p>La versión aceptada queda registrada. Los cambios materiales podrán requerir información adicional o una nueva aceptación; una aceptación anterior no cubre indefinidamente finalidades futuras incompatibles.</p>
      </Section>
    </LegalDocumentLayout>
  );
}
