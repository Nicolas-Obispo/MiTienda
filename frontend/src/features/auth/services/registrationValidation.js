export const PASSWORD_MAX_UTF8_BYTES = 72;

export function evaluarPasswordRegistro(value) {
  return {
    longitud: value.length >= 8,
    mayuscula: /\p{Lu}/u.test(value),
    minuscula: /\p{Ll}/u.test(value),
    numero: /\p{Nd}/u.test(value),
    sinEspacios: value.length > 0 && !/\s/u.test(value),
    limiteBcrypt:
      value.length > 0 &&
      new TextEncoder().encode(value).length <= PASSWORD_MAX_UTF8_BYTES,
  };
}

export function passwordRegistroValida(value) {
  return Object.values(evaluarPasswordRegistro(value)).every(Boolean);
}
