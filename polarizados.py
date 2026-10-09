import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import os
import json

# Importaciones para Google Sheets
import gspread
from google.oauth2.service_account import Credentials

# Importaciones para generación de PDF de Garantía
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# Configuración de la página
st.set_page_config(page_title="Control de Polarizados", page_icon="🚗", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def conectar_gsheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Manejo de Secrets en Streamlit Cloud
    if "gcp_service_account" in st.secrets:
        sec = st.secrets["gcp_service_account"]
        creds_dict = dict(sec) if not isinstance(sec, str) else json.loads(sec)
        
        # Corrección para formatear la private_key de Google
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    elif os.path.exists("credentials.json"):
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    else:
        st.error("❌ No se encontraron las credenciales de Google Sheets en Secrets.")
        st.stop()
        
    client = gspread.authorize(creds)
    sheet = client.open("Control_Polarizados_DB")
    return sheet

def obtener_df(sheet_name):
    sh = conectar_gsheets()
    worksheet = sh.worksheet(sheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data), worksheet

# --- FUNCIÓN GENERADORA DE CARTA DE GARANTÍA ---
def generar_garantia_pdf(fecha_str, modelo_auto, cristales_desc, tonalidad_desc, anos_garantia=1):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter # 612 x 792 pt
    
    # LOGO EN ENCABEZADO
    logo_cargado = False
    posibles_logos = ["logo.png", "logo.jpg", "logo.jpeg", "Logo.png", "LOGO.png", "Logo.jpg"]
    for nombre_logo in posibles_logos:
        if os.path.exists(nombre_logo):
            c.drawImage(nombre_logo, 360, 680, width=180, preserveAspectRatio=True, mask='auto')
            logo_cargado = True
            break

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

    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, 690, "Presente")
    c.drawString(380, 675, f"FECHA: {fecha_str}")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, 630, "CARTA DE GARANTIA")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, 580, "AQUIEN CORRESPONDA:")
    
    texto_linea1 = f"CON RESPECTO A LA INSTALACION DE AUTOMOVIL MODELO: {modelo_auto.upper()}"
    texto_linea2 = f"{cristales_desc.upper()} ({tonalidad_desc.upper()})"
    
    c.drawString(70, 555, texto_linea1)
    c.drawString(70, 540, texto_linea2)
    
    c.setFont("Helvetica", 10)
    c.drawString(70, 505, "Con la ")
    c.setFont("Helvetica-Bold", 10)
    texto_garantia = f"GARANTIA ES DE {anos_garantia} AÑO" if anos_garantia == 1 else f"GARANTIA ES DE {anos_garantia} AÑOS"
    c.drawString(108, 505, texto_garantia)
    
    c.drawString(70, 475, "POR DESPRENDIMIEMTO, BURBUJAS O DECOLORACION")
    
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(70, 445, "( EN CASO DE BURBUJAS LA GARANTIA APLICA SIEMPRE Y CUANDO TENGA UNA")
    c.drawString(70, 433, "CANTIDAD EXAGERADA Y AL IGUAL QUE SEAN VISIBLES A UNA DISTANCIA MINIMA")
    c.drawString(70, 421, "DE 1 METRO. )")
    
    c.setFont("Helvetica", 10)
    c.drawString(70, 385, "SIN MAS POR EL MOMENTO QUEDO A SUS ORDENES")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, 345, "POLARIZADOS ALVARADO")
    
    c.drawString(70, 295, "A T E N T A M E N T E")
    c.drawString(70, 255, "CONTACTO:")
    c.drawString(70, 230, "TELEFONO: 8129010370")
    c.drawString(70, 210, "CORREO: polarizadosalvarado@gmail.com")
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(70, 175, "NOTA: LA GARANTIAS SE TRABAJAN EN EL TALLER, CON PREVIA CITA")
    
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

# --- NAVEGACIÓN ---
st.title("🚗 Control de Inventario y Ventas - Polarizados")

menu = st.sidebar.selectbox(
    "Navegación", 
    ["Registrar Venta", "Registrar Gasto", "Inventario / Stock", "Reportes y Balance"]
)

# --- OPCIÓN 1: REGISTRAR VENTA ---
if menu == "Registrar Venta":
    st.header("🛒 Registrar Nueva Venta / Servicio")
    
    df_productos, ws_productos = obtener_df("productos")
    
    if df_productos.empty:
        st.warning("⚠️ No hay productos en el inventario. Agrega productos en 'Inventario / Stock'.")
    else:
        categoria_servicio = st.radio(
            "Tipo de Servicio:", 
            ["Paquete Automotriz Completo/Básico", "Pieza / Ventana Individual", "Personalizado / 2 Tonos", "Arquitectónico (Residencial/Comercial)"], 
            horizontal=True
        )
        
        opciones_prod = {f"{row['nombre']} (Disp: {row['stock']}m)": row['id'] for _, row in df_productos.iterrows()}
        materiales_usados = []
        precio_sugerido = 0.0
        
        modelo_auto = ""
        cristales_instalados = ""
        tonalidad_usada = ""
        anos_garantia = 1

        if categoria_servicio == "Paquete Automotriz Completo/Básico":
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
            
            tono_parabrisas = ""
            if "Completo" in paquete:
                with col_p2:
                    det_parabrisas = st.radio("Detalle del Parabrisas:", ["Parabrisas Completo", "Solamente Franja / Parasol"], horizontal=True)
                    tono_parabrisas = st.text_input("Tonalidad Parabrisas (%):", placeholder="Ej. 35% o 50%", key="t_parab")
                cristales_instalados = f"Parabrisas ({det_parabrisas}), Puertas Laterales, Aletas y Medallón"
            else:
                with col_p2:
                    inc_franja = st.checkbox("¿Incluye Franja extra en Parabrisas?")
                    if inc_franja:
                        tono_parabrisas = st.text_input("Tonalidad Franja Parabrisas (%):", placeholder="Ej. 5%", key="t_franja")
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
                    tono_general = st.text_input("Tonalidad Puertas/Medallón (%):", placeholder="Ej. 20%")

                if tono_parabrisas.strip():
                    tonalidad_usada = f"Parabrisas: {tono_parabrisas} / Laterales y Medallón: {tono_general}"
                else:
                    tonalidad_usada = tono_general

                cant_m = 3.0 if "Completo" in paquete else 2.5
                cant = st.number_input("Metros a descontar de inventario:", min_value=0.1, value=cant_m, step=0.5)
                precio_sugerido = float(p_info['precio_venta']) * cant
                materiales_usados = [(p_id, p_info['nombre'], cant, float(p_info['stock']))]
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
                if tono_parabrisas.strip():
                    tonalidad_usada += f" (Parabrisas: {tono_parabrisas})"

                precio_sugerido = (float(p1_info['precio_venta']) * m1) + (float(p2_info['precio_venta']) * m2)
                materiales_usados = [
                    (p1_id, p1_info['nombre'], m1, float(p1_info['stock'])),
                    (p2_id, p2_info['nombre'], m2, float(p2_info['stock']))
                ]

        elif categoria_servicio == "Pieza / Ventana Individual":
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                modelo_auto = st.text_input("Modelo del Vehículo:", placeholder="Ej. NISSAN MARCH")
            with col_v2:
                anos_garantia = st.number_input("Años de Garantía:", min_value=1, max_value=10, value=1)

            st.markdown("**Selecciona las Ventanas / Piezas a Polarizar:**")
            
            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                v_piloto = st.checkbox("Ventana Piloto")
                v_copiloto = st.checkbox("Ventana Copiloto")
            with c_p2:
                v_pas_izq = st.checkbox("Pasajero Trasero Izquierdo")
                v_pas_der = st.checkbox("Pasajero Trasero Derecho")
            with c_p3:
                v_medallon = st.checkbox("Medallón")
                v_aletas = st.checkbox("Aletas / Esquinas")
                v_parabrisas_ind = st.checkbox("Parabrisas Completo / Franja")

            piezas_seleccionadas = []
            if v_piloto: piezas_seleccionadas.append("Ventana Piloto")
            if v_copiloto: piezas_seleccionadas.append("Ventana Copiloto")
            if v_pas_izq: piezas_seleccionadas.append("Pasajero Trasero Izquierdo")
            if v_pas_der: piezas_seleccionadas.append("Pasajero Trasero Derecho")
            if v_medallon: piezas_seleccionadas.append("Medallón")
            if v_aletas: piezas_seleccionadas.append("Aletas")
            if v_parabrisas_ind: piezas_seleccionadas.append("Parabrisas")

            cristales_instalados = ", ".join(piezas_seleccionadas) if piezas_seleccionadas else "Pieza Individual"

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                p_sel = st.selectbox("Material:", list(opciones_prod.keys()))
                p_id = opciones_prod[p_sel]
                p_info = df_productos[df_productos['id'] == p_id].iloc[0]
            with col_m2:
                tonalidad_usada = st.text_input("Tonalidad (%):", placeholder="Ej. 20%")

            m_sugeridos = max(0.5, len(piezas_seleccionadas) * 0.5)
            cant = st.number_input("Metros a descontar de inventario:", min_value=0.1, value=m_sugeridos, step=0.5)
            precio_sugerido = float(p_info['precio_venta']) * cant
            materiales_usados = [(p_id, p_info['nombre'], cant, float(p_info['stock']))]

        elif categoria_servicio == "Personalizado / 2 Tonos":
            modelo_auto = st.text_input("Modelo / Datos del Vehículo:", placeholder="Ej. NISSAN SENTRA")
            cristales_instalados = st.text_input("Cristales Trabajados:", placeholder="Ej. Piloto y Copiloto")
            tonalidad_usada = st.text_input("Tonalidad (%):", placeholder="Ej. 15%")
            anos_garantia = st.number_input("Años de Garantía:", min_value=1, max_value=10, value=1)
            
            p_sel = st.selectbox("Material:", list(opciones_prod.keys()))
            p_id = opciones_prod[p_sel]
            p_info = df_productos[df_productos['id'] == p_id].iloc[0]
            cant = st.number_input("Metros Utilizados:", min_value=0.1, value=2.0, step=0.5)
            precio_sugerido = float(p_info['precio_venta']) * cant
            materiales_usados = [(p_id, p_info['nombre'], cant, float(p_info['stock']))]

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
            precio_sugerido = float(p_info['precio_venta']) * cant
            materiales_usados = [(p_id, p_info['nombre'], cant, float(p_info['stock']))]

        st.divider()
        usar_custom = st.checkbox(f"Modificar precio sugerido (${precio_sugerido:.2f})")
        total = st.number_input("Monto Total a Cobrar ($):", min_value=0.0, value=precio_sugerido) if usar_custom else precio_sugerido

        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("✅ Confirmar Venta y Generar Garantía", type="primary", use_container_width=True):
                stock_insuficiente = any(disp < c for _, _, c, disp in materiales_usados)

                if not modelo_auto.strip():
                    st.warning("⚠ Por favor ingresa el modelo del vehículo o datos del inmueble.")
                elif stock_insuficiente:
                    st.error("❌ Stock insuficiente en inventario para alguno de los materiales.")
                else:
                    _, ws_ventas = obtener_df("ventas")
                    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    fecha_corta = datetime.now().strftime("%d/%m/%Y")
                    desc_servicio = f"{modelo_auto} - {cristales_instalados} ({tonalidad_usada})"

                    # Actualizar Stock y Guardar en Google Sheets
                    for mat_id, nombre, cant, _ in materiales_usados:
                        cell = ws_productos.find(str(mat_id))
                        row_num = cell.row
                        stock_actual = float(ws_productos.cell(row_num, 4).value)
                        nuevo_stock = stock_actual - cant
                        ws_productos.update_cell(row_num, 4, nuevo_stock)

                        num_ventas = len(ws_ventas.get_all_records()) + 1
                        subtotal = total / len(materiales_usados)
                        ws_ventas.append_row([num_ventas, mat_id, desc_servicio, cant, subtotal, fecha_actual])

                    st.session_state["pdf_garantia"] = generar_garantia_pdf(
                        fecha_str=fecha_corta,
                        modelo_auto=modelo_auto,
                        cristales_desc=cristales_instalados,
                        tonalidad_desc=tonalidad_usada if tonalidad_usada else "Estándar",
                        anos_garantia=anos_garantia
                    )
                    st.session_state["nombre_garantia"] = f"Garantia_{modelo_auto.replace(' ', '_')}.pdf"
                    st.success(f
