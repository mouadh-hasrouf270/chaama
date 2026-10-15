// Run ONLY against a disposable backend database with a trusted staff fixture.
// SMOKE_FRONTEND_URL, SMOKE_API_URL, SMOKE_CDP_URL, SMOKE_USERNAME and
// SMOKE_PASSWORD must be supplied. Uses Chrome CDP and Node's built-in WebSocket.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

const required = ['SMOKE_FRONTEND_URL', 'SMOKE_API_URL', 'SMOKE_CDP_URL', 'SMOKE_USERNAME', 'SMOKE_PASSWORD'];
for (const key of required) assert.ok(process.env[key], `Missing ${key}; use an isolated test database.`);
const origin = process.env.SMOKE_FRONTEND_URL;
const api = process.env.SMOKE_API_URL;
const target = await fetch(process.env.SMOKE_CDP_URL + '/json/new?about:blank', { method: 'PUT' }).then(r => r.json());
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(resolve => socket.addEventListener('open', resolve, { once: true }));
let sequence = 0;
const pending = new Map();
const exceptions = [];
socket.addEventListener('message', event => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(message.result);
  }
  if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails);
});
function command(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await command('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(expression, label) {
  const end = Date.now() + 15000;
  while (Date.now() < end) {
    if (await evaluate(expression)) return;
    await delay(100);
  }
  throw new Error(`${label}\n${await evaluate('document.body.innerText')}`);
}
async function navigate(route) {
  await command('Page.navigate', { url: origin + route });
  await until(`location.pathname === ${JSON.stringify(route)} && document.readyState === 'complete'`, route);
}
async function click(text) {
  await until(`[...document.querySelectorAll('button')].some(b => b.textContent.trim() === ${JSON.stringify(text)} && !b.disabled)`, `Button ready: ${text}`);
  await evaluate(`(() => {
    const button = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === ${JSON.stringify(text)});
    if (!button || button.disabled) throw new Error('Missing or disabled: ' + ${JSON.stringify(text)});
    button.click();
  })()`);
}
async function fill(selector, value) {
  await evaluate(`(() => {
    const el = document.querySelector(${JSON.stringify(selector)});
    if (!el) throw new Error('Missing input: ' + ${JSON.stringify(selector)});
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : el.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, ${JSON.stringify(value)});
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  })()`);
}
async function screenshot(name) {
  const directory = path.join(os.tmpdir(), 'ch2ma-booking-check', 'screenshots');
  await fs.mkdir(directory, { recursive: true });
  const result = await command('Page.captureScreenshot', { format: 'png' });
  await fs.writeFile(path.join(directory, name + '.png'), Buffer.from(result.data, 'base64'));
}
try {
  await command('Page.enable');
  await command('Runtime.enable');
  await command('DOM.enable');
  await command('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await navigate('/auth/login');
  await until('!!document.querySelector("input[type=password]")', 'Login form');
  await fill('input[type=text]', process.env.SMOKE_USERNAME);
  await fill('input[type=password]', process.env.SMOKE_PASSWORD);
  await click('Se connecter');
  await until('location.pathname === "/app"', 'Dashboard');
  await click('Nouveau client');
  await until('!!document.querySelector("dialog[open]")', 'Client modal opened from dashboard');
  const suffix = String(Date.now()).slice(-8);
  await fill('dialog input[name=first_name]', 'Browser');
  await fill('dialog input[name=last_name]', 'Office ' + suffix);
  await fill('dialog input[name=phone]', '+2136' + suffix);
  await fill('dialog input[name=email]', 'office@example.com');
  await click('Créer le client');
  await until('location.pathname.startsWith("/app/clients/") && document.body.innerText.includes("office@example.com")', 'Client persisted');
  await click('Modifier le client');
  await fill('dialog input[name=city]', 'Alger');
  await click('Enregistrer');
  await until('!document.querySelector("dialog[open]") && document.body.innerText.includes("Alger")', 'Client edit persisted');
  await evaluate(`[...document.querySelectorAll('a')].find(a => a.textContent === 'Nouveau dossier').click()`);
  await until('!!document.querySelector("input[name=title]")', 'New case form');
  await fill('input[name=title]', 'Browser Dossier ' + suffix);
  await fill('textarea[name=description]', 'Suivi initial du dossier.');
  await until(`[...document.querySelectorAll('button')].some(b => b.textContent === 'Créer le dossier' && !b.disabled)`, 'Client options loaded');
  await click('Créer le dossier');
  await until('location.pathname.startsWith("/app/matters/") && document.body.innerText.includes("Historique")', 'Case saved');
  const matterPath = await evaluate('location.pathname');
  await fill('textarea[name=description]', 'Pièces reçues, analyse en cours.');
  await click('Enregistrer le dossier');
  await until('document.body.innerText.includes("Informations du dossier modifiées")', 'Case edits recorded in history');
  await fill('select[name=status]', 'ACTIVE');
  await click('Changer le statut');
  await until('document.body.innerText.includes("Statut : OPEN → ACTIVE")', 'Case status persisted');
  const filePath = path.join(os.tmpdir(), 'ch2ma-booking-check', 'office-proof.png');
  await fs.writeFile(filePath, Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=', 'base64'));
  const input = await command('Runtime.evaluate', { expression: 'document.querySelector("input[type=file]")' });
  await command('DOM.setFileInputFiles', { objectId: input.result.objectId, files: [filePath] });
  await click('Ajouter le fichier');
  await until('document.body.innerText.includes("Document ajouté : office-proof.png")', 'File upload persisted');
  await click('Voir / télécharger');
  await until(`!!document.querySelector('img[alt="office-proof.png"]')`, 'Protected image preview');
  assert.ok(await evaluate('document.querySelector("a[download]").href.startsWith("blob:")'), 'Download uses authenticated blob, not public media');
  await screenshot('office-matter-documents');
  await evaluate(`[...document.querySelectorAll('a')].find(a => a.textContent === 'Factures du dossier').click()`);
  await until('location.pathname === "/app/billing"', 'Billing opened with matter filter');
  await click('Nouvelle facture');
  await until('!!document.querySelector("input[aria-label=description-0]")', 'Invoice form');
  await fill('input[aria-label=description-0]', 'Consultation et analyse');
  await fill('input[aria-label=quantity-0]', '2');
  await fill('input[aria-label=unit_price-0]', '1000.25');
  await fill('input[name=tax_rate]', '19');
  await until(`[...document.querySelectorAll('button')].some(b => b.textContent === 'Enregistrer le brouillon' && !b.disabled)`, 'Matter options loaded for invoice');
  await click('Enregistrer le brouillon');
  await until('document.body.innerText.includes("Émettre la facture")', 'Draft saved');
  await click('Émettre la facture');
  await until('document.body.innerText.includes("Enregistrer un règlement reçu")', 'Invoice issued');
  await fill('input[name=amount]', '1000');
  await click('Enregistrer le règlement');
  await until('document.body.innerText.includes("Partiellement réglée")', 'Partial payment persisted');
  await fill('input[name=amount]', '1380.60');
  await click('Enregistrer le règlement');
  await until('document.body.innerText.includes("Réglée") && !document.querySelector("input[name=amount]")', 'Invoice settled');
  await screenshot('office-paid-invoice');
  await evaluate(`(() => { const original = window.open.bind(window); window.open = (...args) => {
    const popup = original(...args); popup.print = () => { window.__printedInvoice = popup.document.documentElement.outerHTML; popup.close(); }; return popup;
  }; })()`);
  await click('Imprimer / enregistrer en PDF');
  assert.ok(await evaluate('window.__printedInvoice?.includes("Consultation et analyse")'), 'Printable invoice contains actual line items');
  await navigate(matterPath);
  await until('!!document.querySelector("select[name=status]")', 'Case reloaded');
  await fill('select[name=status]', 'CLOSED');
  await click('Changer le statut');
  await until('document.body.innerText.includes("Statut : ACTIVE → CLOSED")', 'Case closed');
  await fill('select[name=status]', 'ARCHIVED');
  await click('Changer le statut');
  await until('document.body.innerText.includes("Statut : CLOSED → ARCHIVED")', 'Settled case archived');
  assert.equal(await evaluate('!!document.querySelector("input[type=file]")'), false, 'Archived cases cannot upload');
  await command('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  assert.equal(await evaluate('document.documentElement.scrollWidth <= innerWidth'), true, 'Matter mobile layout does not overflow');
  await screenshot('office-matter-mobile');
  assert.deepEqual(exceptions, [], 'No runtime exceptions');
  console.log('PASS: dashboard client creation, client edit, case creation/edit/status/history, protected upload/preview, invoice issuance, partial/full payments, printable invoice, closure/archive and mobile layout.');
} finally {
  await command('Page.close');
  socket.close();
}
