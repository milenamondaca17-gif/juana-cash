// JUANA CASH — Bot de comandos via WhatsApp
// Las credenciales van en C:\JuanaCash\whatsapp\bot_config.json (no en git)
const Anthropic = require('@anthropic-ai/sdk');
const path      = require('path');
const fs        = require('fs');

module.exports = function initBot(client, enviarMensaje, BACKEND_PORT, http) {

    // Leer configuración local (nunca va al repositorio)
    const configPath = path.join('C:\\JuanaCash\\whatsapp', 'bot_config.json');
    let config;
    try {
        config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    } catch(e) {
        console.log('⚠️  Bot desactivado: no se encontró bot_config.json en C:\\JuanaCash\\whatsapp\\');
        console.log('   Creá ese archivo con api_key y numeros_autorizados para activar el bot.');
        return;
    }

    const BOT_API_KEY          = config.api_key;
    const NUMEROS_AUTORIZADOS  = config.numeros_autorizados || [];

    if (!BOT_API_KEY || BOT_API_KEY === 'PONER_API_KEY_AQUI') {
        console.log('⚠️  Bot desactivado: completá la api_key en bot_config.json');
        return;
    }

    const anthropic = new Anthropic({ apiKey: BOT_API_KEY });

    // Petición HTTP al backend
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

    // Herramientas disponibles para Claude
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
            description: "Buscar productos por nombre: precio, stock e ID",
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
            name: "ver_stock_bajo",
            description: "Productos con stock bajo o agotado",
            input_schema: {
                type: "object",
                properties: { minimo: { type: "number", description: "Stock mínimo, default 5" } }
            }
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
                const r = await api('GET', `/productos/buscar?q=${encodeURIComponent(params.nombre)}`);
                return (r.data||[]).slice(0,6).map(p => ({ id:p.id, nombre:p.nombre, precio:p.precio, stock:p.stock_actual }));
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
            case "ver_stock_bajo": {
                const r = await api('GET', `/productos/`);
                const min = params.minimo !== undefined ? params.minimo : 5;
                return (r.data||[]).filter(p=>parseFloat(p.stock_actual)<=min)
                    .sort((a,b)=>parseFloat(a.stock_actual)-parseFloat(b.stock_actual))
                    .slice(0,15).map(p=>({ nombre:p.nombre, stock:p.stock_actual, precio:p.precio }));
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

    async function procesarMensaje(texto) {
        const ahora   = new Date();
        const fechaHoy = ahora.toISOString().split('T')[0];
        const horaStr  = ahora.toLocaleString('es-AR', {
            timeZone:'America/Argentina/San_Juan', dateStyle:'short', timeStyle:'short'
        });
        const system = `Sos el asistente de gestión del almacén "Autoservicio San Valentín" (sistema Juana Cash).
Hablás directamente con el dueño o su familia para ayudarlos a gestionar el negocio.
Podés consultar ventas, caja, precios, stock, deudas de clientes y registrar gastos usando las herramientas disponibles.
Cuando el dueño pregunta algo del negocio, usás las herramientas para obtener datos reales del sistema.
Si el dueño pregunta algo que no podés resolver con las herramientas (como horarios, empleados, etc.), lo decís claramente.
Usás español rioplatense, sos conciso y usás emojis para facilitar la lectura en WhatsApp.
Para cambiar un precio: primero buscás el producto para confirmar el nombre y el ID, luego aplicás el cambio.
Fecha/hora actual: ${horaStr}. Hoy es: ${fechaHoy}. Los montos son en pesos argentinos.`;

        const messages = [{ role:'user', content:texto }];
        let resp = await anthropic.messages.create({
            model:'claude-haiku-4-5-20251001', max_tokens:1024, system, tools:TOOLS, messages
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
                model:'claude-haiku-4-5-20251001', max_tokens:1024, system, tools:TOOLS, messages
            });
        }
        const bloque = resp.content.find(b=>b.type==='text');
        return bloque ? bloque.text : '❌ Sin respuesta';
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
        if (!texto) return;
        console.log(`\n🤖 [BOT] ${remitente}: "${texto}"`);
        try {
            const chat = await msg.getChat();
            await chat.sendStateTyping();
            const respuesta = await procesarMensaje(texto);
            await msg.reply(respuesta);
            console.log(`✅ [BOT] Respuesta enviada\n`);
        } catch(e) {
            console.error('❌ [BOT] Error:', e.message);
            try { await msg.reply(`❌ Error: ${e.message}`); } catch(_) {}
        }
    });

    console.log(`🤖 Bot activo — ${NUMEROS_AUTORIZADOS.length} número(s) autorizado(s)`);
};
