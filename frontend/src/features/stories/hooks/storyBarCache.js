export function reconcileStoriesBarAfterDeletion(items, comercioId) {
  if (!Array.isArray(items)) return items;

  return items.flatMap((item) => {
    if (Number(item?.comercioId) !== Number(comercioId)) return [item];

    const cantidad = Math.max(0, Number(item?.cantidad || 0) - 1);
    const pendientes = Math.min(
      cantidad,
      Math.max(0, Number(item?.pendientes || 0) - 1)
    );

    return cantidad === 0 ? [] : [{ ...item, cantidad, pendientes }];
  });
}
