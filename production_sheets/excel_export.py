import pandas as pd
from io import BytesIO
from datetime import datetime
from django.http import HttpResponse
from .size_utils import sort_sizes

def export_to_excel(production_sheets):
    # Crear un escritor de Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet in production_sheets:
            # Obtener los detalles de esta planilla
            details = sheet.productiondetail_set.all()
            
                    # Obtener todas las tallas únicas y ordenarlas según el orden predefinido
            sizes = sort_sizes(set(details.values_list('size', flat=True)))
            
            # Asegurar que las columnas están en el orden correcto
            columns = ['OP', 'REF'] + sizes + ['TOTAL']
            
            # Crear DataFrame con los datos
            data = []
            for op_ref in set(details.values_list('op', 'ref')):
                row = {'OP': op_ref[0], 'REF': op_ref[1]}
                size_quantities = details.filter(op=op_ref[0], ref=op_ref[1])
                for detail in size_quantities:
                    row[detail.size] = detail.quantity
                data.append(row)
            
            df = pd.DataFrame(data)
            
            # Calcular totales
            if not df.empty:
                size_columns = sizes  # Usar las tallas ordenadas
                df['TOTAL'] = df[size_columns].sum(axis=1)
                
                # Agregar fila de totales
                totals = df[size_columns + ['TOTAL']].sum()
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