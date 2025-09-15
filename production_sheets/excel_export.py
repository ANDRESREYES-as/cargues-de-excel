import pandas as pd
from io import BytesIO
from datetime import datetime
from django.http import HttpResponse
from .size_utils import sort_sizes

def export_to_excel(production_sheets):
    try:
        # Crear un escritor de Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet in production_sheets:
                # Obtener los detalles de esta planilla
                details = sheet.productiondetail_set.all()
                
                # Usar todas las tallas posibles del sistema
                from .size_utils import TALLA_ORDER
                sizes = TALLA_ORDER
                
                # Asegurar que las columnas están en el orden correcto
                columns = ['OP', 'REF'] + sizes + ['TOTAL']
                
                # Crear DataFrame con los datos
                data = []
                for op_ref in set(details.values_list('op', 'ref')):
                    row = {'OP': op_ref[0], 'REF': op_ref[1]}
                    # Inicializar todas las tallas con 0
                    for size in sizes:
                        row[size] = 0
                    # Actualizar con las cantidades reales
                    size_quantities = details.filter(op=op_ref[0], ref=op_ref[1])
                    for detail in size_quantities:
                        row[detail.size] = detail.quantity
                    data.append(row)
                
                # Crear DataFrame con todas las columnas, incluso si no hay datos
                if not data:
                    data = [{
                        'OP': '',
                        'REF': '',
                        **{size: 0 for size in sizes},
                        'TOTAL': 0
                    }]

                df = pd.DataFrame(data)
                
                # Asegurarse de que todas las columnas existan
                for col in columns:
                    if col not in df.columns:
                        df[col] = 0
                
                # Calcular totales
                df['TOTAL'] = df[sizes].sum(axis=1)
                
                # Agregar fila de totales si hay datos
                if len(df) > 0:
                    totals = df[sizes + ['TOTAL']].sum()
                    totals['OP'] = 'TOTAL GENERAL'
                    totals['REF'] = ''
                    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
                
                # Reordenar las columnas según el orden definido
                df = df[columns]
                
                # Guardar en una hoja con el número de manifiesto
                sheet_name = f'Manifiesto_{sheet.manifest_number}'[:31]  # Excel limita nombres a 31 caracteres
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Ajustar el ancho de las columnas
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

        # Preparar la respuesta
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=planillas_produccion.xlsx'
        output.close()
        
        return response

    except Exception as e:
        # Asegurar que el output se cierre en caso de error
        if 'output' in locals():
            output.close()
        raise Exception(f"Error al exportar a Excel: {str(e)}")