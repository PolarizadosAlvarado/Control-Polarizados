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
        # Formato para el selector
        opciones_prod = {f"{row['nombre']} (Disp: {row['stock']}m)": row['id'] for _, row in df_productos.iterrows()}
        prod_seleccionado = st.selectbox("Selecciona el Material:", list(opciones_prod.keys()))
        prod_id = opciones_prod[prod_seleccionado]
        
        # Obtener datos del producto seleccionado
        prod_info = df_productos[df_productos['id'] == prod_id].iloc[0]
        
        vehiculo = st.text_input("Datos del Vehículo / Cliente:", placeholder="Ej. Sedan Corolla 2020")
        cantidad = st.number_input("Metros Utilizados:", min_value=0.1, value=2.5, step=0.5)
        
        precio_sugerido = prod_info['precio_venta'] * cantidad
        usar_custom = st.checkbox(f"Modificar precio sugerido (${precio_sugerido:.2f})")
        
        if usar_custom:
            total = st.number_input("Monto Total a Cobrar ($):", min_value=0.0, value=precio_sugerido)
        else:
            total = precio_sugerido
            
        if st.button("✅ Confirmar Venta", type="primary"):
            if prod_info['stock'] < cantidad:
                st.error(f"❌ Stock insuficiente. Solo quedan {prod_info['stock']:.2f}m disponibles.")
            elif not vehiculo:
                st.warning("⚠️️ Por favor ingresa los datos del vehículo o cliente.")
            else:
                conn = conectar_db()
                cursor = conn.cursor()
                # Descontar stock
                cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cantidad, prod_id))
                # Registrar venta
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO ventas (producto_id, vehiculo, cantidad, total, fecha) VALUES (?, ?, ?, ?, ?)",
                               (prod_id, vehiculo, cantidad, total, fecha_actual))
                conn.commit()
                conn.close()
                st.success(f"🎉 Venta registrada con éxito ({cantidad:.2f} m). Total: ${total:.2f}")
                st.rerun()

# --- OPCIÓN 2: REGISTRAR GASTO ---
elif menu == "Registrar Gasto":
    st.header("💸 Registrar Nuevo Gasto")
    
    col1, col2 = st.columns(2)
    with col1:
        concepto = st.text_input("Descripción del Gasto:", placeholder="Ej. Navajas Olfa, Luz, Pistola de calor")
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
        nom = st.text_input("Nombre del Producto:", placeholder="Ej. Rollo Nanocerámico 20%")
        tipo = st.text_input("Tipo / Tono:", placeholder="Ej. 20%, Carbón, Nanocerámico")
        stk = st.number_input("Stock Inicial (Metros):", min_value=0.0, step=5.0)
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
        SELECT v.id AS ID, p.nombre AS Material, v.vehiculo AS Cliente, v.cantidad AS 'Metros (m)', v.total AS 'Total ($)', v.fecha AS Fecha 
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
    c3.metric("📈 Ganancia Neta", f"${ganancia_neta:.2f}", delta_color="normal")
    
    st.divider()
    
    col_v, col_g = st.columns(2)
    with col_v:
        st.subheader("Historial de Ventas")
        st.dataframe(df_ventas, use_container_width=True)
    with col_g:
        st.subheader("Historial de Gastos")
        st.dataframe(df_gastos, use_container_width=True)