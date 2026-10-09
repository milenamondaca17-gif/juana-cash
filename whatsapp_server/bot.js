// JUANA CASH — Bot de comandos via WhatsApp
// Las credenciales van en C:\JuanaCash\whatsapp\bot_config.json (no en git)
const Anthropic = require('@anthropic-ai/sdk');
const path      = require('path');
const fs        = require('fs');

module.exports = function initBot(client, enviarMensaje, BACKEND_PORT, http) {

    const configPath = path.join('C:\\JuanaCash\\whatsapp', 'bot_config.json');
    let config;
    try {
        config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    } catch(e) {
        console.log('⚠️  Bot desactivado: no se encontró bot_config.json en C:\\JuanaCash\\whatsapp\\');
        return;
    }

    const BOT_API_KEY         = config.api_key;
    const NUMEROS_AUTORIZADOS = config.numeros_autorizados || [];

    if (!BOT_API_KEY || BOT_API_KEY === 'PONER_API_KEY_AQUI') {
        console.log('⚠️  Bot desactivado: completá la api_key en bot_config.json');
        return;
    }

    const anthropic = new Anthropic({ apiKey: BOT_API_KEY });

    // Cache de productos para búsqueda fuzzy local
    let productosCache = null;
    let cacheTs = 0;
    const CACHE_TTL = 5 * 60 * 1000;

    async function getProductos() {
        if (productosCache && Date.now() - cacheTs < CACHE_TTL) return productosCache;
        const r = await api('GET', '/productos/');
        productosCache = r.data || [];
        cacheTs = Date.now();
        return productosCache;
    }

    // Similaridad por palabras clave (0 a 1)
    function similaridad(query, nombre) {
        const norm = s => s.toLowerCase()
            .replace(/[áàä]/g,'a').replace(/[éèë]/g,'e').replace(/[íìï]/g,'i')
            .replace(/[óòö]/g,'o').replace(/[úùü]/g,'u')
            .replace(/[^a-z0-9]/g,' ').replace(/\s+/g,' ').trim();
        const q = norm(query);
        const n = norm(nombre);
        if (q === n) return 1;
        if (n.includes(q) || q.includes(n)) return 0.9;
        const wq = q.split(' ').filter(w => w.length > 1);
        const wn = n.split(' ').filter(w => w.length > 1);
        if (wq.length === 0) return 0;
        const matches = wq.filter(w => wn.some(x => x.includes(w) || w.includes(x)));
        return matches.length / wq.length;
    }

    // Historial de conversación por usuario (en memoria, se limpia si pasan 20 min sin actividad)
    const conversaciones  = new Map();
    const ultimaActividad = new Map();
    const TIMEOUT_MS = 20 * 60 * 1000;
    const MAX_TURNOS = 10; // máximo de intercambios guardados por usuario

    function getHistorial(remitente) {
        const ahora = Date.now();
        const ultima = ultimaActividad.get(remitente) || 0;
        if (ahora - ultima > TIMEOUT_MS) conversaciones.delete(remitente);
        ultimaActividad.set(remitente, ahora);
        return conversaciones.get(remitente) || [];
    }

    function setHistorial(remitente, historial) {
        // Guardar solo texto (sin media/tool_calls) para no acumular tokens
        conversaciones.set(remitente, historial.slice(-(MAX_TURNOS * 2)));
    }

    function api(method, ruta, body = null) {
        return new Promise((resolve, reject) => {
            const data = body ? JSON.stringify(body) : null;
            const opts = {
                hostname: '127.0.0.1', port: BACKEND_PORT, path: ruta, method,
                headers: { 'Content-Type': 'application/json' }
            };
            if (data) opts.headers['Content-Length'] = Buffer.byteLength(data);
            const req = http.request(opts, (res) => {
                let d = '';
                res.on('data', c => d += c);
                res.on('end', () => {
                    try { resolve({ status: res.statusCode, data: JSON.parse(d) }); }
                    catch(e) { reject(e); }
                });
            });
            req.on('error', reject);
            if (data) req.write(data);
            req.end();
        });
    }

    const TOOLS = [
        {
            name: "ver_ventas_hoy",
            description: "Resumen de ventas del día: total, tickets y desglose por método de pago",
            input_schema: { type: "object", properties: {} }
        },
        {
            name: "ver_ventas_fecha",
            description: "Ventas de una fecha específica",
            input_schema: {
                type: "object",
                properties: { fecha: { type: "string", description: "Fecha YYYY-MM-DD" } },
                required: ["fecha"]
            }
        },
        {
            name: "ver_caja_actual",
            description: "Estado del turno activo: efectivo esperado, ventas y gastos",
            input_schema: { type: "object", properties: {} }
        },
        {
            name: "buscar_producto",
            description: "Buscar productos por nombre: devuelve id, nombre y precio actual",
            input_schema: {
                type: "object",
                properties: { nombre: { type: "string", description: "Nombre o parte del nombre" } },
                required: ["nombre"]
            }
        },
        {
            name: "cambiar_precio",
            description: "Cambiar el precio de un producto. Primero usar buscar_producto para confirmar el ID.",
            input_schema: {
                type: "object",
                properties: {
                    producto_id:  { type: "number", description: "ID del producto" },
                    nuevo_precio: { type: "number", description: "Nuevo precio en pesos" }
                },
                required: ["producto_id", "nuevo_precio"]
            }
        },
        {
            name: "ver_deuda_cliente",
            description: "Deuda de un cliente por nombre",
            input_schema: {
                type: "object",
                properties: { nombre: { type: "string", description: "Nombre del cliente" } },
                required: ["nombre"]
            }
        },
        {
            name: "listar_deudores",
            description: "Clientes con deuda, ordenados de mayor a menor",
            input_schema: {
                type: "object",
                properties: { top: { type: "number", description: "Cantidad, default 10" } }
            }
        },
        {
            name: "registrar_gasto",
            description: "Registrar un gasto (proveedor, servicio, compra)",
            input_schema: {
                type: "object",
                properties: {
                    monto:       { type: "number", description: "Monto en pesos" },
                    descripcion: { type: "string", description: "Descripción" }
                },
                required: ["monto", "descripcion"]
            }
        },
        {
            name: "ver_gastos_hoy",
            description: "Gastos del día con total",
            input_schema: { type: "object", properties: {} }
        },
        {
            name: "enviar_difusion_wa",
            description: "Enviar mensaje a todos los contactos WA del negocio",
            input_schema: {
                type: "object",
                properties: { mensaje: { type: "string", description: "Texto a enviar" } },
                required: ["mensaje"]
            }
        }
    ];

    async function ejecutar(nombre, params) {
        switch(nombre) {
            case "ver_ventas_hoy": {
                const r = await api('GET', `/caja/resumen-rapido?usuario_id=1`);
                const d = r.data.hoy || {};
                return { total: d.total||0, tickets: d.cantidad||0, efectivo: d.efectivo||0,
                         debito: d.debito||0, tarjeta: d.tarjeta||0, qr_mp: d.mercadopago_qr||0,
                         transferencia: d.transferencia||0, fiado: d.fiado||0 };
            }
            case "ver_ventas_fecha": {
                const r = await api('GET', `/ventas/por-fecha?fecha=${params.fecha}`);
                const v = r.data || [];
                return { fecha: params.fecha, tickets: v.length,
                         total: v.reduce((s,x) => s+x.total, 0),
                         anuladas: v.filter(x => x.estado==='anulada').length };
            }
            case "ver_caja_actual": {
                const r = await api('GET', `/caja/resumen-rapido?usuario_id=1`);
                return r.data;
            }
            case "buscar_producto": {
                const todos = await getProductos();
                const resultados = todos
                    .map(p => ({ id:p.id, nombre:p.nombre, precio:p.precio, sim: similaridad(params.nombre, p.nombre) }))
                    .filter(p => p.sim >= 0.5)
                    .sort((a,b) => b.sim - a.sim)
                    .slice(0, 5)
                    .map(p => ({ id:p.id, nombre:p.nombre, precio:p.precio, coincidencia: Math.round(p.sim*100)+'%' }));
                console.log(`🔍 buscar "${params.nombre}" → ${resultados.map(p=>p.nombre+'('+p.coincidencia+')').join(', ')||'sin resultados'}`);
                return resultados;
            }
            case "cambiar_precio": {
                const r = await api('POST', `/productos/${params.producto_id}/cambiar-precio`,
                    { precio: params.nuevo_precio, usuario: 'bot-wa' });
                return r.data;
            }
            case "ver_deuda_cliente": {
                const r = await api('GET', `/clientes/`);
                const q = params.nombre.toLowerCase();
                return (r.data||[]).filter(c => c.nombre.toLowerCase().includes(q))
                    .slice(0,5).map(c => ({ nombre:c.nombre, deuda:c.deuda_actual, tel:c.telefono||'-' }));
            }
            case "listar_deudores": {
                const r = await api('GET', `/clientes/`);
                return (r.data||[]).filter(c => parseFloat(c.deuda_actual)>0)
                    .sort((a,b) => parseFloat(b.deuda_actual)-parseFloat(a.deuda_actual))
                    .slice(0, params.top||10).map(c => ({ nombre:c.nombre, deuda:c.deuda_actual }));
            }
            case "registrar_gasto": {
                const r = await api('POST', `/gastos/`,
                    { descripcion:params.descripcion, monto:params.monto, categoria:'general', usuario_id:1 });
                return r.data;
            }
            case "ver_gastos_hoy": {
                const r = await api('GET', `/gastos/hoy`);
                const g = r.data||[];
                return { total: g.reduce((s,x)=>s+parseFloat(x.monto),0),
                         gastos: g.slice(0,15).map(x=>({ desc:x.descripcion, monto:x.monto })) };
            }
            case "enviar_difusion_wa": {
                const r = await api('GET', `/clientes/contactos-wa`);
                const contactos = (r.data||[]).filter(c=>c.telefono);
                let enviados=0, errores=0;
                for (const c of contactos) {
                    try { await enviarMensaje(c.telefono, params.mensaje); enviados++;
                          await new Promise(res=>setTimeout(res,2000)); }
                    catch(_) { errores++; }
                }
                return { enviados, errores, total:contactos.length };
            }
            default: return { error: `Herramienta no implementada: ${nombre}` };
        }
    }

    async function procesarMensaje(texto, mediaData, historial) {
        const ahora    = new Date();
        const fechaHoy = ahora.toISOString().split('T')[0];
        const horaStr  = ahora.toLocaleString('es-AR', {
            timeZone:'America/Argentina/San_Juan', dateStyle:'short', timeStyle:'short'
        });

        const system = `Sos el asistente de gestión del almacén "Autoservicio San Valentín" (sistema Juana Cash).
Hablás directamente con el dueño (Lucas) o su familia para ayudarlos a gestionar el negocio.

DATOS DEL NEGOCIO:
- Dirección: Di Paola 480 esquina Misiones
- Horario: lunes a sábado 09:30-13:30 y 18:00-22:00 / domingos 09:30-14:00
- Rubros: almacén general, carnicería, lácteos, panadería, insumos de telefonía
- Formas de pago: efectivo, Mercado Pago, QR, débito, crédito, transferencia
- Cajeras: Fernanda (turno mañana), Natalia (turno tarde)
- Fiado: solo a clientes registrados en la base de datos

CONVERSACIÓN:
Tenés memoria de los mensajes anteriores. Si el usuario dice un número solo, es el precio del producto que estaban hablando. Si dice "ese" o "ese producto", se refiere al último producto mencionado. Mantené el contexto sin pedir que repitan información.

ACCIONES:
- Consultar ventas, caja, precios, deudas y registrar gastos con las herramientas disponibles.
- Para cambiar un precio: buscás el producto, confirmás el ID y aplicás el cambio.
- Si el usuario ya dijo el producto antes y ahora solo manda el precio, hacé el cambio directamente.

ACTUALIZACIÓN DE PRECIOS POR IMAGEN O PDF:
Cuando recibís una foto o PDF de lista de precios de proveedor:
1. Leés todos los productos y precios visibles.
2. Por cada producto, buscás con buscar_producto. La herramienta ya hace el matching fuzzy y devuelve el porcentaje de coincidencia.
3. Si el primer resultado tiene coincidencia >= 70%, actualizás el precio con cambiar_precio SIN pedir confirmación.
4. Si coincidencia < 70% o no hay resultados, lo anotás como "no encontrado".
5. Si el usuario indicó margen (ej: "30% de ganancia"): precio_venta = precio_proveedor * (1 + margen/100), redondeado al peso.
6. Si NO indicó margen, actualizás con el precio exacto de la lista.
7. Al terminar, resumís: cuántos actualizaste y cuáles no encontraste.

Usás español rioplatense, sos conciso y usás emojis. Sin mencionar stock.
Fecha/hora actual: ${horaStr}. Hoy es: ${fechaHoy}. Los montos son en pesos argentinos.`;

        let userContent;
        if (mediaData) {
            const mediaBlock = mediaData.mimetype === 'application/pdf'
                ? { type:'document', source:{ type:'base64', media_type:'application/pdf', data:mediaData.data } }
                : { type:'image',    source:{ type:'base64', media_type:mediaData.mimetype,  data:mediaData.data } };
            userContent = [
                mediaBlock,
                { type:'text', text: texto || 'Actualizá los precios con los de esta lista.' }
            ];
        } else {
            userContent = texto;
        }

        // Construir mensajes con historial previo
        const messages = [...historial, { role:'user', content:userContent }];

        let resp = await anthropic.messages.create({
            model:'claude-haiku-4-5-20251001', max_tokens:4096, system, tools:TOOLS, messages
        });

        while (resp.stop_reason === 'tool_use') {
            const uses = resp.content.filter(b=>b.type==='tool_use');
            const results = [];
            for (const t of uses) {
                let result;
                try   { result = await ejecutar(t.name, t.input); }
                catch (e) { result = { error:e.message }; }
                results.push({ type:'tool_result', tool_use_id:t.id, content:JSON.stringify(result) });
            }
            messages.push({ role:'assistant', content:resp.content });
            messages.push({ role:'user', content:results });
            resp = await anthropic.messages.create({
                model:'claude-haiku-4-5-20251001', max_tokens:4096, system, tools:TOOLS, messages
            });
        }

        const bloque = resp.content.find(b=>b.type==='text');
        const respuesta = bloque ? bloque.text : '❌ Sin respuesta';

        // Guardar solo texto en el historial (sin media ni tool_calls para no acumular tokens)
        const historialNuevo = [
            ...historial,
            { role:'user',      content: mediaData ? (texto || '[imagen/PDF]') : texto },
            { role:'assistant', content: respuesta }
        ];

        return { respuesta, historialNuevo };
    }

    client.on('message', async (msg) => {
        if (msg.fromMe) return;
        let remitente;
        try {
            const contact = await msg.getContact();
            remitente = contact.number || msg.from.split('@')[0];
        } catch(e) {
            remitente = msg.from.split('@')[0];
        }
        console.log(`[DEBUG] remitente=${remitente}`);
        if (!NUMEROS_AUTORIZADOS.includes(remitente)) return;
        const texto = (msg.body||'').trim();
        if (!texto && !msg.hasMedia) return;
        console.log(`\n🤖 [BOT] ${remitente}: "${texto || '[archivo]'}"`);

        let mediaData = null;
        if (msg.hasMedia) {
            try {
                const media = await msg.downloadMedia();
                if (media && media.mimetype) {
                    if (media.mimetype.startsWith('image/') || media.mimetype === 'application/pdf') {
                        mediaData = { mimetype: media.mimetype, data: media.data };
                        console.log(`📎 [BOT] Archivo recibido (${media.mimetype})`);
                    }
                }
            } catch(e) {
                console.error('⚠️ [BOT] Error descargando archivo:', e.message);
            }
        }

        const historial = getHistorial(remitente);

        try {
            const chat = await msg.getChat();
            await chat.sendStateTyping();
            const { respuesta, historialNuevo } = await procesarMensaje(texto, mediaData, historial);
            setHistorial(remitente, historialNuevo);
            await msg.reply(respuesta);
            console.log(`✅ [BOT] Respuesta enviada\n`);
        } catch(e) {
            console.error('❌ [BOT] Error:', e.message);
            try { await msg.reply(`❌ Error: ${e.message}`); } catch(_) {}
        }
    });

    console.log(`🤖 Bot activo — ${NUMEROS_AUTORIZADOS.length} número(s) autorizado(s)`);
};
