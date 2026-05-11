const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const qrcode = require('qrcode-terminal');

const app = express();
app.use(express.json());

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
    console.log('\n✅ WhatsApp conectado y listo para enviar tickets!');
    console.log('🚀 Servidor corriendo en puerto 3001');
    console.log('\nNo cierres esta ventana.\n');
});

client.on('disconnected', (reason) => {
    clientReady = false;
    console.log('\n⚠️  WhatsApp desconectado:', reason);
    console.log('Reconectando...\n');
    client.initialize();
});

// Endpoint para enviar mensaje
app.post('/send', async (req, res) => {
    if (!clientReady) {
        return res.status(503).json({ ok: false, error: 'WhatsApp no está conectado todavía' });
    }

    const { phone, message } = req.body;
    if (!phone || !message) {
        return res.status(400).json({ ok: false, error: 'Faltan datos: phone y message son requeridos' });
    }

    try {
        // Formatear número argentino
        let tel = phone.toString().replace(/\D/g, '');
        if (tel.startsWith('0')) tel = tel.substring(1);
        if (!tel.startsWith('54')) tel = '54' + tel;
        // Agregar 9 para celulares argentinos si no está
        if (tel.length === 12 && tel[2] !== '9') {
            tel = tel.substring(0, 2) + '9' + tel.substring(2);
        }

        const chatId = tel + '@c.us';
        await client.sendMessage(chatId, message);
        console.log(`📤 Ticket enviado a ${tel}`);
        res.json({ ok: true, mensaje: 'Ticket enviado correctamente' });
    } catch (error) {
        console.error('Error al enviar:', error.message);
        res.status(500).json({ ok: false, error: error.message });
    }
});

// Endpoint para verificar estado
app.get('/status', (req, res) => {
    res.json({
        ok: clientReady,
        estado: clientReady ? 'conectado' : 'desconectado'
    });
});

const PORT = 3001;
app.listen(PORT, '127.0.0.1', () => {
    console.log('\n============================================');
    console.log('   JUANA CASH - SERVIDOR WHATSAPP');
    console.log('============================================');
    console.log('\nIniciando conexión con WhatsApp...');
    console.log('Aguardá el QR para escanear.\n');
});

client.initialize();
