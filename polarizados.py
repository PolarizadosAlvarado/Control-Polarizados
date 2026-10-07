import os
from reportlab.lib.colors import HexColor

# --- FUNCIÓN GENERADORA DE CARTA DE GARANTÍA (SIN NOMBRE DEL CLIENTE) ---
def generar_garantia_pdf(fecha_str, modelo_auto, cristales_desc, tonalidad_desc, anos_garantia=1):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter # 612 x 792 pt
    
    # --- LOGO Y ENCABEZADO ---
    if os.path.exists("logo.png"):
        c.drawImage("logo.png", 360, 680, width=180, preserveAspectRatio=True, mask='auto')
    elif os.path.exists("logo.jpg"):
        c.drawImage("logo.jpg", 360, 680, width=180, preserveAspectRatio=True, mask='auto')
    else:
        # Diseño vectorial alternativo de Polarizados Alvarado
        c.setFillColor(HexColor("#E65100")) # Naranja
        c.setFont("Helvetica-Bold", 16)
        c.drawRightString(540, 725, "POLARIZADO")
        c.setFillColor(HexColor("#000000")) # Negro
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
    
    # Detalle exclusivo del Vehículo y Cristales (Sin Nombre del Cliente)
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
    
    # Motivos de cobertura
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
    
    # Datos de Contacto
    c.drawString(70, 295, "A T E N T A M E N T E")
    c.drawString(70, 255, "CONTACTO:")
    c.drawString(70, 230, "TELEFONO: 8129010370")
    c.drawString(70, 210, "CORREO: polarizadosalvarado@gmail.com")
    
    # Nota importante
    c.setFont("Helvetica-Bold", 9)
    c.drawString(70, 175, "NOTA: LA GARANTIAS SE TRABAJAN EN EL TALLER, CON PREVIA CITA")
    
    # --- FIRMA DIGITAL ---
    if os.path.exists("firma.png"):
        c.drawImage("firma.png", 230, 125, width=150, preserveAspectRatio=True, mask='auto')
    elif os.path.exists("firma.jpg"):
        c.drawImage("firma.jpg", 230, 125, width=150, preserveAspectRatio=True, mask='auto')
        
    c.setLineWidth(1)
    c.line(220, 125, 390, 125)
    c.setFont("Helvetica", 10)
    c.drawCentredString(305, 110, "POLARIZADOS ALVARADO")
    
    c.save()
    buffer.seek(0)
    return buffer
