import { httpGet } from "@core";

export const LEGAL_DOCUMENT_TYPES = Object.freeze({
  terms: "terminos_condiciones",
  privacy: "politica_privacidad",
});

export async function getCurrentLegalDocuments() {
  const documents = await httpGet("/usuarios/documentos-vigentes");
  return Array.isArray(documents) ? documents : [];
}
