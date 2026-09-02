export async function crearComercioConHorariosDraft({
  crear,
  guardarHorarios,
  payload,
  horariosConfigurados,
  franjas,
}) {
  const comercio = await crear(payload);

  if (!horariosConfigurados) {
    return { comercio, horariosError: null };
  }

  try {
    await guardarHorarios({
      comercioId: comercio.id,
      franjas,
    });
    return { comercio, horariosError: null };
  } catch (horariosError) {
    return { comercio, horariosError };
  }
}

export function reintentarHorariosDeComercio({
  guardarHorarios,
  comercioId,
  franjas,
}) {
  return guardarHorarios({ comercioId, franjas });
}
