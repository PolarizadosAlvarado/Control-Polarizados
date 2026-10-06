import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from io import BytesIO

# Importaciones para generación de PDF de Garantía
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Configuración de la página
st.set_page_config(page_title="Control de Polarizados", page_icon="🚗", layout="wide")

# --- CONEXIÓN A BASE DE DATOS ---
def conectar_db():
    conn = sqlite3.connect("polarizado_db.sqlite")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo_pelicula TEXT,
            stock REAL NOT NULL,
            precio_venta REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            vehiculo TEXT,
            cantidad REAL,
            total REAL,
            fecha TEXT,
            FOREIGN KEY(producto_id) REFERENCES productos(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT
        )
    ''')
    conn.commit()
    return conn

conectar_db()

# --- FUNCIÓN GENERADORA DE CARTA DE GARANTÍA (IDÉNTICA A TU FORMATO) ---
def generar_garantia_pdf(fecha_str, modelo_auto, cristales_desc, tonalidad_desc, anos_garantia=1):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter # 612 x 792 pt
    
    # Encabezado
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, 690, "Presente")
    c.drawString(380, 690, f"FECHA: {fecha_str}")
    
    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, 640, "CARTA DE GARANTIA")
    
    # A quien corresponda
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, 590, "AQUIEN CORRESPONDA:")
    
    # Detalle de la instalación
    texto_linea1 = f"CON RESPECTO A LA INSTALACION DE AUTOMOVIL MODELO: {modelo_auto.upper()}"
    texto_linea2 = f"{cristales_desc.upper()} ({tonalidad_desc.upper()})"
    
    c.drawString(70, 565, texto_linea1)
    c.drawString(70, 550, texto_linea2)
    
    # Tiempo de garantía
    c.setFont("Helvetica", 10)
    c.drawString(70, 515, "Con la ")
    c.setFont("Helvetica-Bold", 10)
    texto_garantia = f"GARANTIA ES DE {anos_garantia} AÑO" if anos_garantia == 1 else f"GARANTIA ES DE {anos_garantia} AÑOS"
    c.drawString(108, 515, texto_garantia)
    
    # Motivos de cobertura
    c.drawString(70, 485, "POR DESPRENDIMIEMTO, BURBUJAS O DECOLORACION")
    
    # Cláusula de burbujas
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(70, 455, "( EN CASO DE BURBUJAS LA GARANTIA APLICA SIEMPRE Y CUANDO TENGA UNA")
    c.drawString(70, 443, "CANTIDAD EXAGERADA Y AL IGUAL QUE SEAN VISIBLES A UNA DISTANCIA MINIMA")
    c.drawString(70, 431, "DE 1 METRO. )")
    
    # Despedida
    c.setFont("Helvetica", 10)
    c.drawString(70, 395, "SIN MAS POR EL MOMENTO QUEDO A SUS ORDENES")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, 355, "POLARIZADOS ALVARADO")
    
    # Contacto
    c.drawString(70, 305, "A T E N T A M E N T E")
    c.drawString(70, 265, "CONTACTO:")
    c.drawString(70, 240, "TELEFONO: 8129010370")
    c.drawString(70, 220, "CORREO: polarizadosalvarado@gmail.com")
    
    # Nota importante
    c.setFont("Helvetica-Bold", 9)
    c.drawString(70, 185, "NOTA: LA GARANTIAS SE TRABAJAN EN EL TALLER, CON PREVIA CITA")
    
    # Firma
    c.line(220, 135, 390, 135)
    c.setFont("Helvetica", 10)
    c.drawCentredString(305, 120, "POLARIZADOS ALVARADO")
    
    c.save()
    buffer.seek(0)
    return buffer

# --- TÍTULO Y NAVEGACIÓN ---
st.title("🚗 Control de Inventario y Ventas - Polarizados")

menu = st.sidebar.selectbox(
    "Navegación", 
    ["Registrar Venta", "Registrar Gasto", "Inventario / Stock", "Reportes y Balance"]
)

# --- OPCIÓN 1: REGISTRAR VENTA ---
if menu == "Registrar Venta":
    st.header("🛒 Registrar Nueva Venta / Servicio")
    
    conn = conectar_db()
    df_productos = pd.read_sql_query("SELECT id, nombre, stock, precio_venta FROM productos", conn)
    conn.close()
    
    if df_productos.empty:
        st.warning("⚠️ No hay productos en el inventario. Agrega productos en la pestaña 'Inventario / Stock'.")
    else:
        categoria_servicio = st.radio(
            "Tipo de Servicio:", 
            ["Paquete Automotriz", "Personalizado / 2 Tonos", "Arquitectónico (Residencial/Comercial)"], 
            horizontal=True
        )
        
        opciones_prod = {f"{row['nombre']} (Disp: {row['stock']}m)": row['id'] for _, row in df_productos.iterrows()}
        materiales_usados = []
        precio_sugerido = 0.0
        
        # Datos específicos para la carta de garantía
        modelo_auto = ""
        cristales_instalados = ""
        tonalidad_usada = ""
        anos_garantia = 1

        # --- CASO 1: PAQUETES AUTOMOTRICES ---
        if categoria_servicio == "Paquete Automotriz":
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                modelo_auto = st.text_input("Modelo del Vehículo:", placeholder="Ej. CHEVROLET AVEO")
            with col_a2:
                anos_garantia = st.number_input("Años de Garantía:", min_value=1, max_value=10, value=1)

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                paquete = st.selectbox(
                    "Selecciona el Paquete:",
                    ["Paquete Básico (Puertas Laterales, Aletas y Medallón)", "Paquete Completo (Parabrisas, Puertas Laterales, Aletas y Medallón)"]
                )
            
            if "Completo" in paquete:
                with col_p2:
                    det_parabrisas = st.radio("Detalle del Parabrisas:", ["Parabrisas Completo", "Solamente Franja / Parasol"], horizontal=True)
                cristales_instalados = f"Parabrisas ({det_parabrisas}), Puertas Laterales, Aletas y Medallón"
            else:
                with col_p2:
                    inc_franja = st.checkbox("¿Incluye Franja extra en Parabrisas?")
                cristales_instalados = "Puertas Laterales, Aletas y Medallón (Con Franja)" if inc_franja else "Puertas Laterales, Aletas y Medallón"

            st.subheader("Selección de Material y Tonalidad")
            es_dos_tonos = st.checkbox("¿Instalación en 2 Tonos (Combinado)?")

            if not es_dos_tonos:
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    p_sel = st.selectbox("Material:", list(opciones_prod.keys()))
                    p_id = opciones_prod[p_sel]
                    p_info = df_productos[df_productos['id'] == p_id].iloc[0]
                with col_m2:
                    tonalidad_usada = st.text_input("Tonalidad (%):", placeholder="Ej. 20% / 35%")

                cant_m = 3.0 if "Completo" in paquete else 2.5
                cant = st.number_input("Metros a descontar de inventario:", min_value=0.1, value=cant_m, step=0.5)
                precio_sugerido = p_info['precio_venta'] * cant
                materiales_usados = [(p_id, p_info['nombre'], cant, p_info['stock'])]
            else:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Tono 1 (Puertas / Medallón)**")
                    p1_sel = st.selectbox("Material 1:", list(opciones_prod.keys()), key="pk1")
                    p1_id = opciones_prod[p1_sel]
                    p1_info = df_productos[df_productos['id'] == p1_id].iloc[0]
                    t1 = st.text_input("Tonalidad Tono 1:", placeholder="Ej. 20%", key="t1")
                    m1 = st.number_input("Metros Tono 1:", min_value=0.1, value=2.0, step=0.5, key="m_pk1")

                with c2:
                    st.markdown("**Tono 2 (Parabrisas o Piloto/Copiloto)**")
                    p2_sel = st.selectbox("Material 2:", list(opciones_prod.keys()), key="pk2")
                    p2_id = opciones_prod[p2_sel]
                    p2_info = df_productos[df_productos['id'] == p2_id].iloc[0]
                    t2 = st.text_input("Tonalidad Tono 2:", placeholder="Ej. 35%", key="t2")
                    m2 = st.number_input("Metros Tono 2:", min_value=0.1, value=1.0, step=0.5, key="m_pk2")

                tonalidad_usada = f"{t1} y {t2}" if t1 and t2 else "2 Tonos Combinados"
                precio_sugerido = (p1_info['precio_venta'] * m1) + (p2_info['precio_venta'] * m2)
                materiales_usados = [
                    (p1_id, p1_info['nombre'], m1, p1_info['stock']),
                    (p2_id, p2_info['nombre'], m2, p2_info['stock'])
                ]

        # --- CASO 2: PERSONALIZADO ---
        elif categoria_servicio == "Personalizado / 2 Tonos":
            modelo_auto = st.text_input("Modelo / Datos del Vehículo:", placeholder="Ej. NISSAN SENTRA")
            cristales_instalados = st.text_input("Cristales Trabajados:", placeholder="Ej. Piloto y Copiloto")
            tonalidad_usada = st.text_input("Tonalidad (%):", placeholder="Ej. 15%")
            anos_garantia = st.number_input("Años de Garantía:", min_value=1, max_value=10, value=1)
            
            p_sel = st.selectbox("Material:", list(opciones_prod.keys()))
            p_id = opciones_prod[p_sel]
            p_info = df_productos[df_productos['id'] == p_id].iloc[0]
            cant = st.number_input("Metros Utilizados:", min_value=0.1, value=2.0, step=0.5)
            precio_sugerido = p_info['precio_venta'] * cant
            materiales_usados = [(p_id, p_info['nombre'], cant, p_info['stock'])]

        # --- CASO 3: ARQUITECTÓNICO ---
        else:
            subtipo = st.selectbox("Tipo de Inmueble:", ["Residencial / Casa", "Local Comercial", "Industrial / Oficinas"])
            direccion = st.text_input("Cliente / Dirección:", placeholder="Ej. Local 4 - Plaza Central")
            modelo_auto = f"[{subtipo}] {direccion}"
            cristales_instalados = "Ventanas / Cancel / Fachada"
            tonalidad_usada = st.text_input("Película / Tonalidad:", placeholder="Ej. Control Solar 20%")
            anos_garantia = st.number_input("Años de Garantía:", min_value=1, max_value=10, value=3)
            
            p_sel = st.selectbox("Material:", list(opciones_prod.keys()))
            p_id = opciones_prod[p_sel]
            p_info = df_productos[df_productos['id'] == p_id].iloc[0]
            cant = st.number_input("Metros de Rollo Utilizados:", min_value=0.1, value=5.0, step=1.0)
            precio_sugerido = p_info['precio_venta'] * cant
            materiales_usados = [(p_id, p_info['nombre'], cant, p_info['stock'])]

        # COBRO Y REGISTRO
        st.divider()
        usar_custom = st.checkbox(f"Modificar precio sugerido (${precio_sugerido:.2f})")
        total = st.number_input("Monto Total a Cobrar ($):", min_value=0.0, value=precio_sugerido) if usar_custom else precio_sugerido

        if st.button("✅ Confirmar Venta y Generar Garantía", type="primary"):
            stock_insuficiente = any(disp < c for _, _, c, disp in materiales_usados)

            if not modelo_auto.strip():
                st.warning("⚠ Por favor ingresa el modelo del vehículo o cliente.")
            elif stock_insuficiente:
                st.error("❌ Stock insuficiente en inventario para alguno de los materiales.")
            else:
                conn = conectar_db()
                cursor = conn.cursor()
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                fecha_corta = datetime.now().strftime("%d/%m/%Y")

                desc_servicio = f"{modelo_auto} - {cristales_instalados} ({tonalidad_usada})"
                for mat_id, nombre, cant, _ in materiales_usados:
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cant, mat_id))
                    subtotal = total / len(materiales_usados)
                    cursor.execute(
                        "INSERT INTO ventas (producto_id, vehiculo, cantidad, total, fecha) VALUES (?, ?, ?, ?, ?)",
                        (mat_id, desc_servicio, cant, subtotal, fecha_actual)
                    )

                conn.commit()
                conn.close()

                st.success(f"🎉 Venta registrada con éxito. Total: ${total:.2f}")

                # Generación automática del PDF de Garantía
                pdf_bytes = generar_garantia_pdf(
                    fecha_str=fecha_corta,
                    modelo_auto=modelo_auto,
                    cristales_desc=cristales_instalados,
                    tonalidad_desc=tonalidad_usada if tonalidad_usada else "Estándar",
                    anos_garantia=anos_garantia
                )

                st.download_button(
                    label="📄 Descargar Carta de Garantía (PDF)",
                    data=pdf_bytes,
                    file_name=f"Garantia_{modelo_auto.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

# --- OPCIÓN 2: REGISTRAR GASTO ---
elif menu == "Registrar Gasto":
    st.header("💸 Registrar Nuevo Gasto")
    col1, col2 = st.columns(2)
    with col1:
        concepto = st.text_input("Descripción del Gasto:", placeholder="Ej. Navajas Olfa, Luz, Herramientas")
        categoria = st.selectbox("Categoría:", ["Herramienta", "Material/Insumo", "Local", "Varios"])
    with col2:
        monto = st.number_input("Monto Gastado ($):", min_value=0.0, step=10.0)
        
    if st.button("💾 Guardar Gasto"):
        if concepto and monto > 0:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO gastos (concepto, categoria, monto, fecha) VALUES (?, ?, ?, ?)",
                           (concepto, categoria, monto, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            st.success(f"✅ Gasto de ${monto:.2f} registrado.")

# --- OPCIÓN 3: INVENTARIO / STOCK ---
elif menu == "Inventario / Stock":
    st.header("📦 Control de Inventario")
    tab1, tab2, tab3 = st.tabs(["Ver Inventario", "Agregar Producto", "Reabastecer / Borrar"])
    conn = conectar_db()
    with tab1:
        df_inv = pd.read_sql_query("SELECT id AS ID, nombre AS Producto, tipo_pelicula AS Tipo, stock AS 'Stock (m)', precio_venta AS 'Precio/m ($)' FROM productos", conn)
        st.dataframe(df_inv, use_container_width=True)
    with tab2:
        nom = st.text_input("Nombre del Producto:")
        tipo = st.text_input("Tipo / Tono:")
        stk = st.number_input("Stock Inicial (Metros):", min_value=0.0, step=5.0)
        prc = st.number_input("Precio Estimado por Metro ($):", min_value=0.0, step=50.0)
        if st.button("➕ Guardar"):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO productos (nombre, tipo_pelicula, stock, precio_venta) VALUES (?, ?, ?, ?)", (nom, tipo, stk, prc))
            conn.commit()
            st.success("✅ Producto agregado.")
            st.rerun()
    with tab3:
        df_prods = pd.read_sql_query("SELECT id, nombre FROM productos", conn)
        if not df_prods.empty:
            prod_map = {f"{row['nombre']} (ID: {row['id']})": row['id'] for _, row in df_prods.iterrows()}
            p_reab = st.selectbox("Producto:", list(prod_map.keys()))
            m_sumar = st.number_input("Metros a Sumar:", min_value=0.1, step=5.0)
            if st.button("📈 Reabastecer"):
                cursor = conn.cursor()
                cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (m_sumar, prod_map[p_reab]))
                conn.commit()
                st.success("✅ Stock actualizado.")
                st.rerun()
    conn.close()

# --- OPCIÓN 4: REPORTES Y BALANCE ---
elif menu == "Reportes y Balance":
    st.header("📊 Balance Financiero y Reportes")
    conn = conectar_db()
    df_ventas = pd.read_sql_query('''
        SELECT v.id AS ID, p.nombre AS Material, v.vehiculo AS 'Detalle Servicio', v.cantidad AS 'Metros (m)', v.total AS 'Total ($)', v.fecha AS Fecha 
        FROM ventas v JOIN productos p ON v.producto_id = p.id ORDER BY v.fecha DESC
    ''', conn)
    df_gastos = pd.read_sql_query("SELECT id AS ID, concepto AS Concepto, categoria AS Categoría, monto AS 'Monto ($)', fecha AS Fecha FROM gastos ORDER BY fecha DESC", conn)
    conn.close()
    
    t_v = df_ventas['Total ($)'].sum() if not df_ventas.empty else 0.0
    t_g = df_gastos['Monto ($)'].sum() if not df_gastos.empty else 0.0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Total Ingresos", f"${t_v:.2f}")
    c2.metric("💸 Total Gastos", f"${t_g:.2f}")
    c3.metric("📈 Ganancia Neta", f"${t_v - t_g:.2f}")
    st.divider()
    
    col_v, col_g = st.columns(2)
    with col_v:
        st.subheader("Historial de Ventas")
        st.dataframe(df_ventas, use_container_width=True)
    with col_g:
        st.subheader("Historial de Gastos")
        st.dataframe(df_gastos, use_container_width=True)
