import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

# Importaciones para generación de PDF de Garantía
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

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

# --- FUNCIÓN GENERADORA DE CARTA DE GARANTÍA (CON COMPATIBILIDAD FLEXIBLE DE IMÁGENES) ---
def generar_garantia_pdf(fecha_str, modelo_auto, cristales_desc, tonalidad_desc, anos_garantia=1):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter # 612 x 792 pt
    
    # --- LOGO EN EL ENCABEZADO ---
    logo_cargado = False
    posibles_logos = ["logo.png", "logo.jpg", "logo.jpeg", "Logo.png", "LOGO.png", "Logo.jpg"]
    for nombre_logo in posibles_logos:
        if os.path.exists(nombre_logo):
            c.drawImage(nombre_logo, 360, 680, width=180, preserveAspectRatio=True, mask='auto')
            logo_cargado = True
            break

    # Si no encuentra ninguna imagen en el servidor, dibuja el encabezado alternativo
    if not logo_cargado:
        c.setFillColor(HexColor("#E65100"))
        c.setFont("Helvetica-Bold", 16)
        c.drawRightString(540, 725, "POLARIZADO")
        c.setFillColor(HexColor("#000000"))
        c.setFont("Helvetica-Bold", 13)
        c.drawRightString(540, 710, "A L V A R A D O")
        c.setLineWidth(1.5)
        c.setStrokeColor(HexColor("#000000"))
        c.line(380, 705, 540, 705)

    # Texto 'Presente' y Fecha
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, 690, "Presente")
    c.drawString(380, 675, f"FECHA: {fecha_str}")
    
    # --- TÍTULO ---
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, 630, "CARTA DE GARANTIA")
    
    # --- A QUIEN CORRESPONDA ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, 580, "AQUIEN CORRESPONDA:")
    
    # Detalle de la instalación (Sin incluir nombre del cliente)
    texto_linea1 = f"CON RESPECTO A LA INSTALACION DE AUTOMOVIL MODELO: {modelo_auto.upper()}"
    texto_linea2 = f"{cristales_desc.upper()} ({tonalidad_desc.upper()})"
    
    c.drawString(70, 555, texto_linea1)
    c.drawString(70, 540, texto_linea2)
    
    # Tiempo de garantía
    c.setFont("Helvetica", 10)
    c.drawString(70, 505, "Con la ")
    c.setFont("Helvetica-Bold", 10)
    texto_garantia = f"GARANTIA ES DE {anos_garantia} AÑO" if anos_garantia == 1 else f"GARANTIA ES DE {anos_garantia} AÑOS"
    c.drawString(108, 505, texto_garantia)
    
    # Cobertura
    c.drawString(70, 475, "POR DESPRENDIMIEMTO, BURBUJAS O DECOLORACION")
    
    # Cláusula de burbujas
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(70, 445, "( EN CASO DE BURBUJAS LA GARANTIA APLICA SIEMPRE Y CUANDO TENGA UNA")
    c.drawString(70, 433, "CANTIDAD EXAGERADA Y AL IGUAL QUE SEAN VISIBLES A UNA DISTANCIA MINIMA")
    c.drawString(70, 421, "DE 1 METRO. )")
    
    # Despedida
    c.setFont("Helvetica", 10)
    c.drawString(70, 385, "SIN MAS POR EL MOMENTO QUEDO A SUS ORDENES")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, 345, "POLARIZADOS ALVARADO")
    
    # Contacto
    c.drawString(70, 295, "A T E N T A M E N T E")
    c.drawString(70, 255, "CONTACTO:")
    c.drawString(70, 230, "TELEFONO: 8129010370")
    c.drawString(70, 210, "CORREO: polarizadosalvarado@gmail.com")
    
    # Nota
    c.setFont("Helvetica-Bold", 9)
    c.drawString(70, 175, "NOTA: LA GARANTIAS SE TRABAJAN EN EL TALLER, CON PREVIA CITA")
    
    # --- FIRMA DIGITAL EN EL PIE DE PÁGINA ---
    posibles_firmas = ["firma.png", "firma.jpg", "firma.jpeg", "Firma.png", "FIRMA.png", "Firma.jpg"]
    for nombre_firma in posibles_firmas:
        if os.path.exists(nombre_firma):
            c.drawImage(nombre_firma, 230, 125, width=150, preserveAspectRatio=True, mask='auto')
            break
        
    c.setLineWidth(1)
    c.line(220, 125, 390, 125)
    c.setFont("Helvetica", 10)
    c.drawCentredString(305, 110, "POLARIZADOS ALVARADO")
    
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
        
        modelo_auto = ""
        cristales_instalados = ""
        tonalidad_usada = ""
        anos_garantia = 1

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
                    p1_sel
