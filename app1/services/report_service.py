from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter


def generar_pdf_recomendaciones(vehiculo, recomendaciones):
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    elements = []

    titulo = f"Reporte de Recomendaciones - {vehiculo.placa}"

    elements.append(Paragraph(titulo, styles["Title"]))

    elements.append(Spacer(1, 20))

    info = f"""
    <b>Vehículo:</b> {vehiculo.marca} {vehiculo.modelo}<br/>
    <b>Placa:</b> {vehiculo.placa}<br/>
    <b>Año:</b> {vehiculo.anio}
    """

    elements.append(Paragraph(info, styles["BodyText"]))

    elements.append(Spacer(1, 20))

    data = [["Fecha", "Tipo", "Mensaje", "Severidad", "Estado"]]

    for r in recomendaciones:
        data.append(
            [
                str(r.fecha_creacion.strftime("%Y-%m-%d")),
                r.tipo,
                r.mensaje,
                r.severidad,
                r.estado,
            ]
        )

    tabla = Table(data, repeatRows=1)

    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ]
        )
    )

    elements.append(tabla)

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf
