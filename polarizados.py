import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Control de Polarizados", page_icon="🚗", layout="wide")

# Conexión a la base de datos
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

# Inicializar BD
conectar_db()

# Título Principal
st.title("🚗 Control de Inventario y Ventas - Polarizados")

# Menú Lateral
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
        # Categoría del servicio
        categoria_servicio = st.radio(
            "Tipo de Servicio:", 
            ["Automotriz (1 Tono)", "Automotriz (2 Tonos)", "Arquitectónico (Residencial / Comercial / Industrial)"], 
            horizontal=True
        )
        
        # Mapeo de productos
        opciones_prod = {f"{row['nombre']} (Disp: {row['stock']}m)": row['id'] for _, row in df_productos.iterrows()}
        
        materiales_usados = []
        precio_sugerido = 0.0
        cliente_info = ""

        # --- CASO 1: AUTOMOTRIZ 1 TONO ---
        if categoria_servicio == "Automotriz (1 Tono)":
            cliente_info = st.text_input("Datos del Vehículo / Cliente:", placeholder="Ej. Sedan Corolla 2020")
            
            col1, col2 = st.columns(2)
            with col1:
                prod_sel = st.selectbox("Selecciona el Material:", list(opciones_prod.keys()))
                prod_id = opciones_prod[prod_sel]
                prod_info = df_productos[df_productos['id'] == prod_id].iloc[0]
            with col2:
                cantidad = st.number_input("Metros Utilizados (m):", min_value=0.1, value=2.5, step=0.5)
            
            precio_sugerido = prod_info['precio_venta'] * cantidad
            materiales_usados = [(prod_id, prod_info['nombre'], cantidad, prod_info['stock'])]

        # --- CASO 2: AUTOMOTRIZ 2 TONOS ---
        elif categoria_servicio == "Automotriz (2 Tonos)":
            cliente_info = st.text_input("Datos del Vehículo / Cliente:", placeholder="Ej. SUV Sportage 2022")
            st.subheader("Configuración de 2 Tonos")
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown("**Tono 1 (Medios / Traseros)**")
                p1_sel = st.selectbox("Material 1:", list(opciones_prod.keys()), key="p1")
                p1_id = opciones_prod[p1_sel]
                p1_info = df_productos[df_productos['id'] == p1_id].iloc[0]
                m1 = st.number_input("Metros Tono 1:", min_value=0.1, value=1.5, step=0.5, key="m1")

            with col_t2:
                st.markdown("**Tono 2 (Piloto / Copiloto)**")
                p2_sel = st.selectbox("Material 2:", list(opciones_prod.keys()), key="p2")
                p2_id = opciones_prod[p2_sel]
                p2_info = df_productos[df_productos['id'] == p2_id].iloc[0]
                m2 = st.number_input("Metros Tono 2:", min_value=0.1, value=1.0, step=0.5, key="m2")

            precio_sugerido = (p1_info['precio_venta'] * m1) + (p2_info['precio_venta'] * m2)
            materiales_usados = [
                (p1_id, p1_info['nombre'], m1, p1_info['stock']),
                (p2_id, p2_info['nombre'], m2, p2_info['stock'])
            ]

        # --- CASO 3: ARQUITECTÓNICO ---
        else:
            subtipo = st.selectbox("Clasificación del Inmueble:", ["Residencial / Casa", "Local Comercial", "Industrial / Oficinas"])
            direccion_cliente = st.text_input("Nombre de Cliente / Dirección o Empresa:", placeholder="Ej. Casa Habitación - San Nicolás / Bodega NAVE 4")
            cliente_info = f"[{subtipo}] {direccion_cliente}"
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                prod_sel = st.selectbox("Material / Película Instalada:", list(opciones_prod.keys()))
                prod_id = opciones_prod[prod_sel]
                prod_info = df_productos[df_productos['id'] == prod_id].iloc[0]
            with col_a2:
                cantidad = st.number_input("Metros Utilizados de Rollo (m):", min_value=0.1, value=5.0, step=1.0)
                m2_instalados = st.number_input("Superficie Cubierta (m² opcional):", min_value=0.0, value=0.0, step=1.0)

            precio_sugerido = prod_info['precio_venta'] * cantidad
            materiales_usados = [(prod_id, prod_info['nombre'], cantidad, prod_info['stock'])]

        # --- COBRO Y CONFIRMACIÓN ---
        st.divider()
        usar_custom = st.checkbox(f"Modificar precio sugerido (${precio_sugerido:.2f})")
        if usar_custom:
            total = st.number_input("Monto Total a Cobrar ($):", min_value=0.0, value=precio_sugerido)
        else:
            total = precio_sugerido

        if st.button("✅ Confirmar Venta", type="primary"):
            stock_insuficiente = False
            for mat_id, nombre, cant, stock_disp in materiales_usados:
                if stock_disp < cant:
                    st.error(f"❌ Stock insuficiente de {nombre}. Solicitado: {cant}m, Disponible: {stock_disp:.2f}m")
                    stock_insuficiente = True

            if not cliente_info.strip():
                st.warning("⚠ Por favor ingresa la información del cliente, vehículo o ubicación.")
            elif not stock_insuficiente:
                conn = conectar_db()
                cursor = conn.cursor()
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                for mat_id, nombre, cant, _ in materiales_usados:
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cant, mat_id))
                    subtotal = (total / len(materiales_usados)) if len(materiales_usados) > 1 else total
                    cursor.execute(
                        "INSERT INTO ventas (producto_id, vehiculo, cantidad, total, fecha) VALUES (?, ?, ?, ?, ?)",
                        (mat_id, cliente_info, cant, subtotal, fecha_actual)
                    )

                conn.commit()
                conn.close()
                st.success(f"🎉 Instalación registrada con éxito. Total cobrado: ${total:.2f}")
                st.rerun()

# --- OPCIÓN 2: REGISTRAR GASTO ---
elif menu == "Registrar Gasto":
    st.header("💸 Registrar Nuevo Gasto")
    
    col1, col2 = st.columns(2)
    with col1:
        concepto = st.text_input("Descripción del Gasto:", placeholder="Ej. Navajas Olfa, Luz, Escalera, ANDAMIOS")
        categoria = st.selectbox("Categoría:", ["Herramienta", "Material/Insumo", "Local", "Varios"])
    with col2:
        monto = st.number_input("Monto Gastado ($):", min_value=0.0, step=10.0)
        
    if st.button("💾 Guardar Gasto"):
        if not concepto or monto <= 0:
            st.warning("⚠️ Completa la descripción y asegúrate de que el monto sea mayor a 0.")
        else:
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO gastos (concepto, categoria, monto, fecha) VALUES (?, ?, ?, ?)",
                           (concepto, categoria, monto, fecha_actual))
            conn.commit()
            conn.close()
            st.success(f"✅ Gasto de ${monto:.2f} registrado correctamente.")

# --- OPCIÓN 3: INVENTARIO / STOCK ---
elif menu == "Inventario / Stock":
    st.header("📦 Control de Inventario")
    
    tab1, tab2, tab3 = st.tabs(["Ver Inventario", "Agregar Producto", "Reabastecer / Borrar"])
    
    conn = conectar_db()
    
    with tab1:
        df_inv = pd.read_sql_query("SELECT id AS ID, nombre AS Producto, tipo_pelicula AS Tipo, stock AS 'Stock (m)', precio_venta AS 'Precio/m ($)' FROM productos", conn)
        st.dataframe(df_inv, use_container_width=True)
        
    with tab2:
        st.subheader("Agregar Nuevo Material")
        nom = st.text_input("Nombre del Producto:", placeholder="Ej. Espejo Plata / Nanocerámico 20%")
        tipo = st.text_input("Tipo / Tono / Uso:", placeholder="Ej. Control Solar, Seguridad, 5%, 20%")
        stk = st.number_input("Stock Inicial (Metros de Rollo):", min_value=0.0, step=5.0)
        prc = st.number_input("Precio Estimado por Metro/Servicio ($):", min_value=0.0, step=50.0)
        
        if st.button("➕ Guardar en Inventario"):
            if nom:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO productos (nombre, tipo_pelicula, stock, precio_venta) VALUES (?, ?, ?, ?)",
                               (nom, tipo, stk, prc))
                conn.commit()
                st.success("✅ Producto agregado correctamente.")
                st.rerun()
            else:
                st.warning("⚠️ El nombre del producto es obligatorio.")

    with tab3:
        col_reab, col_del = st.columns(2)
        
        with col_reab:
            st.subheader("Reabastecer Stock")
            df_prods = pd.read_sql_query("SELECT id, nombre FROM productos", conn)
            if not df_prods.empty:
                prod_map = {f"{row['nombre']} (ID: {row['id']})": row['id'] for _, row in df_prods.iterrows()}
                p_reab = st.selectbox("Seleccionar Producto:", list(prod_map.keys()))
                m_sumar = st.number_input("Metros a Sumar:", min_value=0.1, step=5.0)
                if st.button("📈 Actualizar Stock"):
                    cursor = conn.cursor()
                    cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (m_sumar, prod_map[p_reab]))
                    conn.commit()
                    st.success("✅ Stock actualizado correctamente.")
                    st.rerun()

        with col_del:
            st.subheader("Borrar Producto")
            if not df_prods.empty:
                p_del = st.selectbox("Producto a Eliminar:", list(prod_map.keys()), key="del_select")
                if st.button("🗑️ Eliminar Producto", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM productos WHERE id = ?", (prod_map[p_del],))
                    conn.commit()
                    st.warning("🗑️ Producto eliminado.")
                    st.rerun()

    conn.close()

# --- OPCIÓN 4: REPORTES Y BALANCE ---
elif menu == "Reportes y Balance":
    st.header("📊 Balance Financiero y Reportes")
    
    conn = conectar_db()
    
    df_ventas = pd.read_sql_query('''
        SELECT v.id AS ID, p.nombre AS Material, v.vehiculo AS 'Cliente / Proyecto', v.cantidad AS 'Metros (m)', v.total AS 'Total ($)', v.fecha AS Fecha 
        FROM ventas v JOIN productos p ON v.producto_id = p.id ORDER BY v.fecha DESC
    ''', conn)
    
    df_gastos = pd.read_sql_query("SELECT id AS ID, concepto AS Concepto, categoria AS Categoría, monto AS 'Monto ($)', fecha AS Fecha FROM gastos ORDER BY fecha DESC", conn)
    
    conn.close()
    
    total_ventas = df_ventas['Total ($)'].sum() if not df_ventas.empty else 0.0
    total_gastos = df_gastos['Monto ($)'].sum() if not df_gastos.empty else 0.0
    ganancia_neta = total_ventas - total_gastos
    
    # Tarjetas Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Total Ingresos", f"${total_ventas:.2f}")
    c2.metric("💸 Total Gastos", f"${total_gastos:.2f}")
    c3.metric("📈 Ganancia Neta", f"${ganancia_neta:.2f}")
    
    st.divider()
    
    col_v, col_g = st.columns(2)
    with col_v:
        st.subheader("Historial de Ventas")
        st.dataframe(df_ventas, use_container_width=True)
    with col_g:
        st.subheader("Historial de Gastos")
        st.dataframe(df_gastos, use_container_width=True)
