import { useQuery } from "@tanstack/react-query";

import { getCurrentLegalDocuments } from "@features/legal/services/legalDocumentsService";

export function useLegalDocument(type) {
  const query = useQuery({
    queryKey: ["legal", "documents", "current"],
    queryFn: getCurrentLegalDocuments,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
  return {
    ...query,
    document: query.data?.find((item) => item.tipo === type) || null,
  };
}
