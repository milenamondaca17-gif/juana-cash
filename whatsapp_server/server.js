const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const qrcode = require('qrcode-terminal');
const http = require('http');

const app = express();
app.use(express.json());

// ── Configuración reporte diario ──────────────────────────────────────────────
const REPORTE_HORA    = 22;
const REPORTE_MINUTO  = 20;
const REPORTE_TELEFONO = "2634670678";
const BACKEND_PORT    = 8000;
// ─────────────────────────────────────────────────────────────────────────────

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    }
});

let clientReady = false;

client.on('qr', (qr) => {
    console.clear();
    console.log('============================================');
    console.log('   JUANA CASH - SERVIDOR WHATSAPP');
    console.log('============================================');
    console.log('\n📱 ESCANEA ESTE QR CON EL CELULAR DEL NEGOCIO:\n');
    qrcode.generate(qr, { small: true });
    console.log('\nAbrí WhatsApp > Dispositivos vinculados > Vincular dispositivo\n');
});

client.on('authenticated', () => {
    console.log('\n✅ WhatsApp autenticado correctamente!\n');
});

client.on('ready', () => {
    clientReady = true;
    console.clear();
    console.log('============================================');
    console.log('   JUANA CASH - SERVIDOR WHATSAPP');
    console.log('============================================');
    console.log('\n✅ WhatsApp conectado y listo!');
    console.log('🚀 Servidor corriendo en puerto 3001');
    console.log(`📊 Reporte diario: ${REPORTE_HORA}:${String(REPORTE_MINUTO).padStart(2,'0')} hs`);
    console.log('\nNo cierres esta ventana.\n');
    iniciarScheduler();
});

client.on('disconnected', (reason) => {
    clientReady = false;
    console.log('\n⚠️  WhatsApp desconectado:', reason);
    console.log('Reconectando...\n');
    client.initialize();
});

// ── Formatear número argentino ────────────────────────────────────────────────
function formatearTel(phone) {
    let tel = phone.toString().replace(/\D/g, '');
    if (tel.startsWith('0')) tel = tel.substring(1);
    if (!tel.startsWith('54')) tel = '54' + tel;
    if (tel.length === 12 && tel[2] !== '9') {
        tel = tel.substring(0, 2) + '9' + tel.substring(2);
    }
    return tel;
}

// ── Enviar mensaje ────────────────────────────────────────────────────────────
async function enviarMensaje(phone, message) {
    const tel = formatearTel(phone);
    const chatId = tel + '@c.us';
    await client.sendMessage(chatId, message);
    console.log(`📤 Mensaje enviado a ${tel}`);
}

// ── Consultar backend ─────────────────────────────────────────────────────────
function consultarBackend(path) {
    return new Promise((resolve, reject) => {
        http.get(`http://127.0.0.1:${BACKEND_PORT}${path}`, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch(e) { reject(e); }
            });
        }).on('error', reject);
    });
}

// ── Formatear precio argentino ────────────────────────────────────────────────
function p(v) {
    return '$' + parseFloat(v).toLocaleString('es-AR', {maximumFractionDigits: 0});
}

// ── Generar y enviar reporte diario ──────────────────────────────────────────
async function enviarReporteDiario() {
    console.log('\n📊 Generando reporte diario...');
    try {
        const resumen = await consultarBackend('/caja/resumen-rapido?usuario_id=1');
        const hoy = resumen.hoy;
        const ayer = resumen.ayer;
        const mes = resumen.mes;

        const ahora = new Date();
        const fecha = ahora.toLocaleDateString('es-AR', {
            weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric'
        });

        const delta = resumen.delta_pct;
        const deltaStr = delta > 0 ? `📈 +${delta}% vs ayer` :
                         delta < 0 ? `📉 ${delta}% vs ayer` : `➡️ Igual que ayer`;

        const msg = [
            `📊 *RESUMEN DEL DÍA - JUANA CASH*`,
            `📅 ${fecha}`,
            ``,
            `💰 *VENTAS HOY*`,
            `Total vendido:    ${p(hoy.total)}`,
            `Cantidad tickets: ${hoy.cantidad}`,
            `Ticket promedio:  ${p(hoy.ticket_promedio)}`,
            `${deltaStr}`,
            ``,
            `💳 *POR MÉTODO*`,
            hoy.efectivo       > 0 ? `💵 Efectivo:       ${p(hoy.efectivo)}`       : null,
            hoy.debito         > 0 ? `🏧 Débito:         ${p(hoy.debito)}`         : null,
            hoy.tarjeta        > 0 ? `💳 Tarjeta:        ${p(hoy.tarjeta)}`        : null,
            hoy.mercadopago_qr > 0 ? `📱 QR/MP:          ${p(hoy.mercadopago_qr)}` : null,
            hoy.transferencia  > 0 ? `🏦 Transf.:        ${p(hoy.transferencia)}`  : null,
            hoy.fiado          > 0 ? `💸 Fiado:          ${p(hoy.fiado)}`          : null,
            ``,
            `📆 *ESTE MES*`,
            `Total mes:        ${p(mes.total)}`,
            `Tickets mes:      ${mes.cantidad}`,
            ``,
            `━━━━━━━━━━━━━━━━━━━━`,
            `_Juana Cash 🧾_`,
        ].filter(l => l !== null).join('\n');

        await enviarMensaje(REPORTE_TELEFONO, msg);
        console.log('✅ Reporte diario enviado correctamente\n');
    } catch (e) {
        console.error('❌ Error al generar reporte:', e.message);
    }
}

// ── Scheduler: revisa cada minuto si es hora del reporte ─────────────────────
let reporteEnviadoHoy = null;

function iniciarScheduler() {
    setInterval(() => {
        if (!clientReady) return;
        const ahora = new Date();
        const hoy = ahora.toDateString();
        if (ahora.getHours() === REPORTE_HORA &&
            ahora.getMinutes() === REPORTE_MINUTO &&
            reporteEnviadoHoy !== hoy) {
            reporteEnviadoHoy = hoy;
            enviarReporteDiario();
        }
    }, 60 * 1000);
}

// ── Endpoints HTTP ────────────────────────────────────────────────────────────
app.post('/send', async (req, res) => {
    if (!clientReady)
        return res.status(503).json({ ok: false, error: 'WhatsApp no está conectado' });

    const { phone, message } = req.body;
    if (!phone || !message)
        return res.status(400).json({ ok: false, error: 'Faltan datos' });

    try {
        await enviarMensaje(phone, message);
        res.json({ ok: true, mensaje: 'Ticket enviado correctamente' });
    } catch (error) {
        console.error('Error al enviar:', error.message);
        res.status(500).json({ ok: false, error: error.message });
    }
});

app.get('/status', (req, res) => {
    res.json({ ok: clientReady, estado: clientReady ? 'conectado' : 'desconectado' });
});

// Endpoint para probar el reporte manualmente
app.get('/reporte', async (req, res) => {
    if (!clientReady)
        return res.status(503).json({ ok: false, error: 'WhatsApp no está conectado' });
    await enviarReporteDiario();
    res.json({ ok: true, mensaje: 'Reporte enviado' });
});

const PORT = 3001;
app.listen(PORT, '127.0.0.1', () => {
    console.log('\n============================================');
    console.log('   JUANA CASH - SERVIDOR WHATSAPP');
    console.log('============================================');
    console.log('\nIniciando conexión con WhatsApp...\n');
});

client.initialize();
