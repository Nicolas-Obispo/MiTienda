import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const [profile, picker, pickerState, scheduleEditor, timeInput] = await Promise.all([
  readSource("../src/features/auth/pages/ProfilePage.jsx"),
  readSource("../src/shared/components/LocationPicker.jsx"),
  readSource("../src/shared/components/locationPickerState.js"),
  readSource("../src/features/availability/components/HorariosAtencionEditor.jsx"),
  readSource("../src/features/availability/components/HoraInput.jsx"),
]);

const administrationStart = profile.indexOf("{!showPerfilForm && showActivarEspacioInfo");
const administrationEnd = profile.indexOf("<AgendaGeneralModal", administrationStart);
const administration = profile.slice(administrationStart, administrationEnd);

test("alta y edicion comparten formulario tematizado y primitives", () => {
  assert.match(administration, /editingComercioId \? "Editar espacio" : "Crear espacio"/);
  assert.match(administration, /<Surface as="section" variant="elevated"/);
  assert.match(administration, /<Input\b/);
  assert.match(administration, /<Select\b/);
  assert.match(administration, /<Textarea\b/);
  assert.match(administration, /<Alert variant="danger" role="alert"/);
  assert.match(administration, /<Skeleton\b/);
});

test("submit, payload, validaciones y endpoints funcionales permanecen", () => {
  assert.match(profile, /onSubmit=\{handleCrearComercioSubmit\}/);
  assert.match(profile, /await crearComercio\(payload\)/);
  assert.match(profile, /await actualizarComercio\(editingComercioId, payload\)/);
  assert.match(profile, /const payload = \{\s*\.\.\.createForm/);
  assert.match(administration, /value=\{createForm\.provincia\}/);
  assert.match(administration, /value=\{createForm\.ciudad\}/);
  assert.match(profile, /direccion: createForm\.direccion\?\.trim\(\)/);
  assert.match(profile, /latitud:[\s\S]*Number\(createForm\.latitud\)/);
  assert.match(profile, /longitud:[\s\S]*Number\(createForm\.longitud\)/);
  assert.match(profile, /rubro_id: Number\(createForm\.rubro_id\)/);
  assert.match(profile, /especialidad_ids: createForm\.especialidad_ids/);
});

test("privacidad conserva default, control, ayuda y payload", () => {
  assert.match(profile, /mostrar_direccion_publicamente: true/);
  assert.match(administration, /checked=\{createForm\.mostrar_direccion_publicamente\}/);
  assert.match(administration, /mostrar_direccion_publicamente: event\.target\.checked/);
  assert.match(administration, /Mostrar mi dirección públicamente/);
  assert.match(administration, /las personas verán solamente tu ciudad/);
  assert.match(administration, /border-border-strong bg-surface text-interactive-primary/);
});

test("branding y uploads permanecen contenido del espacio", () => {
  assert.match(administration, /createForm\.portada_url/);
  assert.match(administration, /handlePortadaDrop/);
  assert.match(profile, /uploadImagen|handlePortadaFile/);
  assert.match(administration, /bg-black\/40/);
});

test("administracion conserva query, estados y acciones", () => {
  assert.match(profile, /useMisComercios\(/);
  assert.match(profile, /isLoadingComercios && misComercios\.length === 0/);
  assert.match(profile, /comerciosErrorVisible && misComercios\.length === 0/);
  assert.match(administration, /handleEditarComercio\(c\)/);
  assert.match(administration, /handleDesactivarComercio\(c\.id\)/);
  assert.match(administration, /handleReactivarComercio\(c\.id\)/);
  assert.match(administration, /<EstadoHorarioBadge/);
});

test("acciones migradas reutilizan Button e interactive-bubble", () => {
  assert.ok((administration.match(/<Button\b/g) || []).length >= 10);
  assert.match(administration, /variant="primary"/);
  assert.match(administration, /variant="secondary"/);
  assert.match(administration, /variant="warning"/);
  assert.match(administration, /variant="success"/);
  assert.doesNotMatch(administration, /interactive-bubble/);
});

test("LocationPicker migra shell sin reabrir su flujo", () => {
  assert.match(picker, /import \{ Alert, Button, Input, Surface \}/);
  assert.match(picker, /<MapContainer/);
  assert.match(picker, /buscarDirecciones\(/);
  assert.match(picker, /proponerDireccion\(/);
  assert.match(picker, /isCurrentOperation/);
  assert.match(picker, /confirmLocation\(draft\)/);
  assert.match(picker, /handleCancel/);
  assert.match(pickerState, /export function createLocationDraft/);
  assert.match(pickerState, /export function confirmLocation/);
});

test("editor de horarios directo reutiliza tokens y primitives sin tocar dominio", () => {
  assert.match(scheduleEditor, /<ActiveLayer/);
  assert.match(scheduleEditor, /useHorariosAtencion\(comercioId/);
  assert.match(scheduleEditor, /useReemplazarHorariosAtencionMutation\(\)/);
  assert.match(scheduleEditor, /<Button\b/);
  assert.match(scheduleEditor, /<Surface\b/);
  assert.match(scheduleEditor, /<Alert\b/);
  assert.match(scheduleEditor, /<Skeleton\b/);
  assert.doesNotMatch(scheduleEditor, /<button\b|interactive-bubble/);
  assert.match(timeInput, /role="combobox"/);
  assert.match(timeInput, /role="listbox"/);
  assert.match(timeInput, /<Button\b/);
});

test("superficies migradas no agregan tema manual ni colores fisicos", () => {
  const withoutMedia = administration
    .replace(/bg-black\/40/g, "")
    .replace(/bg-black\/70/g, "");

  for (const source of [withoutMedia, picker, scheduleEditor, timeInput]) {
    assert.doesNotMatch(source, /#[\da-f]{3,8}|\brgb\(|\brgba\(/i);
    assert.doesNotMatch(source, /(?:bg|text|border|ring|from|via|to)-(?:gray|slate|zinc|neutral|stone|white|black|red|green|emerald|orange|amber|yellow|blue|purple|pink)(?:\/|-\d|\b)/);
    assert.doesNotMatch(source, /resolvedTheme|data-theme|dark:|matchMedia\(|localStorage\./);
  }
});
