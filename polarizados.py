import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

# Importaciones para PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

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

# --- FUNCIÓN PARA GENERAR EL PDF DE GARANTÍA ---
def generar_garantia_pdf(cliente_vehiculo, paquete_desc, material_desc, fecha, total_cobrado):
    """
    Superpone la información de la venta sobre la plantilla PDF o genera una elegante si no existe.
    """
    buffer_overlay = BytesIO()
    c = canvas.Canvas(buffer_overlay, pagesize=letter)
    
    # Coordenadas y texto a sobreescribir
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100, 680, f"FECHA: {fecha}")
    c.drawString(100, 660, f"CLIENTE / VEHÍCULO: {cliente_vehiculo}")
    c.drawString(100, 640, f"PAQUETE / SERVICIO: {paquete_desc}")
    c.drawString(100, 620, f"MATERIAL INSTALADO: {material_desc}")
    c.drawString(100, 600, f"IMPORTE TOTAL: ${total_cobrado:.2f}")
    c.setFont("Helvetica", 9)
    c.drawString(100, 570, "Garantía válida contra decoloración, desprendimiento o burbujas del adhesivo.")
    c.save()
    buffer_overlay.seek(0)

    # Si existe plantilla_garantia.pdf en GitHub, estampar sobre ella
    if os.path.exists("plantilla_garantia.pdf"):
        reader_base = PdfReader("plantilla_garantia.pdf")
        reader_overlay = PdfReader(buffer_overlay)
        writer = PdfWriter()

        page_base = reader_base.pages[0]
        page_base.merge_page(reader_overlay.pages[0])
        writer.add_page(page_base)

        buffer_final = BytesIO()
        writer.write(buffer_final)
        buffer_final.seek(0)
        return buffer_final
    else:
        # Retorna el generado básico si no se subió plantilla
        return buffer_overlay

# Título
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
        # Tipo de Servicio
        categoria_servicio = st.radio(
            "Tipo de Servicio:", 
            ["Paquete Automotriz", "Personalizado (1 Tono / 2 Tonos)", "Arquitectónico (Residencial/Comercial)"], 
            horizontal=True
        )
        
        opciones_prod = {f"{row['nombre']} (Disp: {row['stock']}m)": row['id'] for _, row in df_productos.iterrows()}
        materiales_usados = []
        precio_sugerido = 0.0
        cliente_info = ""
        detalle_paquete = ""

        # --- CASO 1: PAQUETES AUTOMOTRICES ---
        if categoria_servicio == "Paquete Automotriz":
            cliente_info = st.text_input("Datos del Vehículo / Cliente:", placeholder="Ej. Honda Civic 2021 - Juan Pérez")
            
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                paquete = st.selectbox(
                    "Selecciona el Paquete:",
                    ["Paquete Básico (4 Puertas + Aletas + Medallón)", "Paquete Completo (Parabrisas + 4 Puertas + Aletas + Medallón)"]
                )
            
            # Sub-opción para Parabrisas
            opcion_parabrisas = "N/A"
            if "Completo" in paquete:
                with col_p2:
                    opcion_parabrisas = st.radio("Detalle del Parabrisas:", ["Parabrisas Completo", "Solamente Franja / Parasol"], horizontal=True)
            else:
                with col_p2:
                    incluir_franja_extra = st.checkbox("¿Agregar Franja / Parasol extra?")
                    if incluir_franja_extra:
                        opcion_parabrisas = "Solamente Franja / Parasol"

            st.subheader("Materiales y Tonos")
            es_dos_tonos = st.checkbox("¿Instalación en 2 Tonos (combinado)?")

            if not es_dos_tonos:
                p_sel = st.selectbox("Material / Película:", list(opciones_prod.keys()))
                p_id = opciones_prod[p_sel]
                p_info = df_productos[df_productos['id'] == p_id].iloc[0]
                
                # Cálculo sugerido de metros según el paquete
                cant_metros = 3.0 if "Completo" in paquete else 2.5
                if opcion_parabrisas == "Solamente Franja / Parasol" and "Básico" in paquete:
                    cant_metros += 0.5
                
                cant = st.number_input("Metros totales a descontar:", min_value=0.1, value=cant_metros, step=0.5)
                precio_sugerido = p_info['precio_venta'] * cant
                materiales_usados = [(p_id, p_info['nombre'], cant, p_info['stock'])]
                detalle_paquete = f"{paquete} | Parabrisas: {opcion_parabrisas}"
            else:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Tono 1 (4 Puertas, Aletas y Medallón)**")
                    p1_sel = st.selectbox("Material Tono 1:", list(opciones_prod.keys()), key="pk1")
                    p1_id = opciones_prod[p1_sel]
                    p1_info = df_productos[df_productos['id'] == p1_id].iloc[0]
                    m1 = st.number_input("Metros Tono 1:", min_value=0.1, value=2.0, step=0.5, key="m_pk1")

                with c2:
                    st.markdown("**Tono 2 (Parabrisas o Piloto/Copiloto)**")
                    p2_sel = st.selectbox("Material Tono 2:", list(opciones_prod.keys()), key="pk2")
                    p2_id = opciones_prod[p2_sel]
                    p2_info = df_productos[df_productos['id'] == p2_id].iloc[0]
                    m2 = st.number_input("Metros Tono 2:", min_value=0.1, value=1.0 if "Completo" in paquete else 0.5, step=0.5, key="m_pk2")

                precio_sugerido = (p1_info['precio_venta'] * m1) + (p2_info['precio_venta'] * m2)
                materiales_usados = [
                    (p1_id, p1_info['nombre'], m1, p1_info['stock']),
                    (p2_id, p2_info['nombre'], m2, p2_info['stock'])
                ]
                detalle_paquete = f"{paquete} (2 Tonos) | Parabrisas: {opcion_parabrisas}"

        # --- CASO 2: PERSONALIZADO ---
        elif categoria_servicio == "Personalizado (1 Tono / 2 Tonos)":
            cliente_info = st.text_input("Datos del Vehículo / Cliente:", placeholder="Ej. Sedan Mazda 3")
            p_sel = st.selectbox("Material:", list(opciones_prod.keys()))
            p_id = opciones_prod[p_sel]
            p_info = df_productos[df_productos['id'] == p_id].iloc[0]
            cant = st.number_input("Metros Utilizados:", min_value=0.1, value=2.0, step=0.5)
            precio_sugerido = p_info['precio_venta'] * cant
            materiales_usados = [(p_id, p_info['nombre'], cant, p_info['stock'])]
            detalle_paquete = "Trabajo Personalizado"

        # --- CASO 3: ARQUITECTÓNICO ---
        else:
            subtipo = st.selectbox("Tipo de Inmueble:", ["Residencial / Casa", "Local Comercial", "Industrial / Oficinas"])
            direccion = st.text_input("Cliente / Dirección:", placeholder="Ej. Local 4 - Plaza Central")
            cliente_info = f"[{subtipo}] {direccion}"
            p_sel = st.selectbox("Material:", list(opciones_prod.keys()))
            p_id = opciones_prod[p_sel]
            p_info = df_productos[df_productos['id'] == p_id].iloc[0]
            cant = st.number_input("Metros de Rollo Utilizados:", min_value=0.1, value=5.0, step=1.0)
            precio_sugerido = p_info['precio_venta'] * cant
            materiales_usados = [(p_id, p_info['nombre'], cant, p_info['stock'])]
            detalle_paquete = f"Arquitectónico - {subtipo}"

        # COBRO Y REGISTRO
        st.divider()
        usar_custom = st.checkbox(f"Modificar precio sugerido (${precio_sugerido:.2f})")
        total = st.number_input("Monto Total a Cobrar ($):", min_value=0.0, value=precio_sugerido) if usar_custom else precio_sugerido

        if st.button("✅ Confirmar Venta y Generar Garantía", type="primary"):
            stock_insuficiente = any(disp < c for _, _, c, disp in materiales_usados)

            if not cliente_info.strip():
                st.warning("⚠ Por favor ingresa el nombre del cliente o datos del vehículo.")
            elif stock_insuficiente:
                st.error("❌ Stock insuficiente en inventario para alguno de los materiales.")
            else:
                conn = conectar_db()
                cursor = conn.cursor()
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                mat_nombres = []
                for mat_id, nombre, cant, _ in materiales_usados:
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cant, mat_id))
                    subtotal = total / len(materiales_usados)
                    desc_venta = f"{cliente_info} - {detalle_paquete}"
                    cursor.execute(
                        "INSERT INTO ventas (producto_id, vehiculo, cantidad, total, fecha) VALUES (?, ?, ?, ?, ?)",
                        (mat_id, desc_venta, cant, subtotal, fecha_actual)
                    )
                    mat_nombres.append(nombre)

                conn.commit()
                conn.close()

                st.success(f"🎉 Venta registrada con éxito. Total: ${total:.2f}")

                # Generación de la Carta de Garantía en PDF
                pdf_bytes = generar_garantia_pdf(
                    cliente_vehiculo=cliente_info,
                    paquete_desc=detalle_paquete,
                    material_desc=", ".join(mat_nombres),
                    fecha=fecha_actual[:10],
                    total_cobrado=total
                )

                st.download_button(
                    label="📄 Descargar Carta de Garantía (PDF)",
                    data=pdf_bytes,
                    file_name=f"Garantia_{cliente_info.replace(' ', '_')}.pdf",
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
