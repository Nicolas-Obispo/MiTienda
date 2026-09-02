import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  crearComercioConHorariosDraft,
  reintentarHorariosDeComercio,
} from "../src/features/availability/services/horarios_draft_flow.js";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [profile, editor] = await Promise.all([
  readSource("../src/features/auth/pages/ProfilePage.jsx"),
  readSource("../src/features/availability/components/HorariosAtencionEditor.jsx"),
]);

test("crea primero y persiste despues el mismo draft con el id devuelto", async () => {
  const operaciones = [];
  const franjas = [
    { dia_semana: 1, hora_apertura: "09:00", hora_cierre: "18:00" },
  ];

  const resultado = await crearComercioConHorariosDraft({
    crear: async (payload) => {
      operaciones.push(["POST", payload]);
      return { id: 77, nombre: payload.nombre };
    },
    guardarHorarios: async (variables) => {
      operaciones.push(["PUT", variables]);
    },
    payload: { nombre: "Espacio" },
    horariosConfigurados: true,
    franjas,
  });

  assert.deepEqual(operaciones, [
    ["POST", { nombre: "Espacio" }],
    ["PUT", { comercioId: 77, franjas }],
  ]);
  assert.equal(resultado.comercio.id, 77);
  assert.equal(resultado.horariosError, null);
});

test("sin draft configurado no ejecuta PUT", async () => {
  let puts = 0;
  await crearComercioConHorariosDraft({
    crear: async () => ({ id: 10 }),
    guardarHorarios: async () => {
      puts += 1;
    },
    payload: {},
    horariosConfigurados: false,
    franjas: [],
  });
  assert.equal(puts, 0);
});

test("fallo de horarios conserva el comercio y el reintento no repite POST", async () => {
  let posts = 0;
  let puts = 0;
  const errorPut = new Error("sin conexion");
  const guardarHorarios = async () => {
    puts += 1;
    if (puts === 1) throw errorPut;
  };

  const resultado = await crearComercioConHorariosDraft({
    crear: async () => {
      posts += 1;
      return { id: 91 };
    },
    guardarHorarios,
    payload: {},
    horariosConfigurados: true,
    franjas: [],
  });

  assert.equal(resultado.comercio.id, 91);
  assert.equal(resultado.horariosError, errorPut);

  await reintentarHorariosDeComercio({
    guardarHorarios,
    comercioId: resultado.comercio.id,
    franjas: [],
  });

  assert.equal(posts, 1);
  assert.equal(puts, 2);
});

test("el mismo editor separa draft local y persistencia existente", () => {
  assert.match(editor, /mode = "persisted"/);
  assert.match(editor, /const isDraft = mode === "draft"/);
  assert.match(editor, /enabled: !isDraft && Boolean\(comercioId\)/);
  assert.match(editor, /if \(isDraft\) \{[\s\S]*onSaveDraft\?\.\(payloadFranjas\)[\s\S]*return;/);
  assert.match(editor, /await reemplazarMutation\.mutateAsync\(\{[\s\S]*comercioId,[\s\S]*franjas: payloadFranjas/);
  assert.equal((editor.match(/function validarFranjas\(/g) || []).length, 1);
});

test("draft guardado vive en ProfilePage y cancelar no lo sobrescribe", () => {
  assert.match(profile, /const \[horariosDraft, setHorariosDraft\] = useState\(\[\]\)/);
  assert.match(profile, /const \[horariosDraftConfigurado, setHorariosDraftConfigurado\] = useState\(false\)/);
  assert.match(profile, /initialFranjas=\{horariosDraft\}/);
  assert.match(profile, /onSaveDraft=\{\(franjas\) => \{[\s\S]*setHorariosDraft\(franjas\)[\s\S]*setHorariosDraftConfigurado\(true\)/);

  const cancelar = editor.slice(
    editor.indexOf("function cancelarEdicion"),
    editor.indexOf("async function guardarHorarios")
  );
  assert.doesNotMatch(cancelar, /onSaveDraft/);
});

test("el formulario conserva el orden visual aprobado", () => {
  const form = profile.slice(
    profile.indexOf("<form onSubmit={handleCrearComercioSubmit}"),
    profile.indexOf("</form>", profile.indexOf("<form onSubmit={handleCrearComercioSubmit}"))
  );
  const markers = [
    ">Portada<",
    'htmlFor="espacio-nombre"',
    'htmlFor="espacio-rubro"',
    'htmlFor="espacio-especialidad"',
    'htmlFor="espacio-descripcion"',
    "Horarios de atención",
    'htmlFor="espacio-whatsapp"',
    'htmlFor="espacio-instagram"',
    'htmlFor="espacio-provincia"',
    'htmlFor="espacio-ciudad"',
    'htmlFor="espacio-direccion"',
    "Ubicación del espacio",
    "Mostrar mi dirección públicamente",
    'type="submit"',
  ];
  let previous = -1;
  for (const marker of markers) {
    const current = form.indexOf(marker);
    assert.ok(current > previous, `${marker} debe respetar el orden`);
    previous = current;
  }
});

test("edicion mantiene modo persisted y el error parcial tiene retry exclusivo", () => {
  assert.match(profile, /mode=\{editingComercioId \? "persisted" : "draft"\}/);
  assert.match(profile, /if \(comercioCreadoPendienteHorarios\) \{[\s\S]*reintentarHorariosDeComercio/);
  assert.match(
    profile,
    /El espacio fue creado, pero no se pudieron guardar sus horarios\./
  );
});
