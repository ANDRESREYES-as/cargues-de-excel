from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import ArchivoCalculo, ResultadoCalculo
import pandas as pd
from .excel_processor import (
    procesar_archivo_inventario,
    procesar_archivo_ventas,
    procesar_archivo_produccion,
    consolidar_resultados
)

def upload_files(request):
    """
    Vista para cargar los archivos Excel.
    """
    if request.method == 'POST':
        archivos = {
            'INV': request.FILES.get('archivo_inventario'),
            'VEN': request.FILES.get('archivo_ventas'),
            'PRO': request.FILES.get('archivo_produccion')
        }
        
        # Validar que se hayan cargado los tres archivos
        if not all(archivos.values()):
            messages.error(request, 'Debes cargar los tres archivos Excel')
            return redirect('upload_files')
        
        try:
            # Guardar archivos
            for tipo, archivo in archivos.items():
                ArchivoCalculo.objects.create(
                    archivo=archivo,
                    tipo_archivo=tipo
                )
            
            # Procesar archivos
            df_inv = pd.read_excel(archivos['INV'])
            df_ven = pd.read_excel(archivos['VEN'])
            df_pro = pd.read_excel(archivos['PRO'])
            
            # Procesar cada archivo
            inv_result = procesar_archivo_inventario(df_inv)
            ven_result = procesar_archivo_ventas(df_ven)
            pro_result = procesar_archivo_produccion(df_pro)
            
            # Consolidar resultados
            resultados = consolidar_resultados(inv_result, ven_result, pro_result)
            
            # Guardar nuevos resultados con la misma fecha
            from django.utils import timezone
            fecha_calculo = timezone.now()
            registros_guardados = 0
            nuevos_resultados = []
            
            for _, row in resultados.iterrows():
                nuevo_resultado = ResultadoCalculo(
                    referencia=row['Referencia'],
                    talla=row['Talla'],
                    ventas=row['Ventas'],
                    inventario=row['Inventario'],
                    produccion=row['Producción'],
                    total_disponible=row['Total Disponible'],
                    balance=row['Balance'],
                    fecha_calculo=fecha_calculo
                )
                nuevos_resultados.append(nuevo_resultado)
                registros_guardados += 1
            
            # Guardar todos los registros en una sola operación
            ResultadoCalculo.objects.bulk_create(nuevos_resultados)
            print(f"Se crearon {registros_guardados} registros con fecha {fecha_calculo}")
            
            messages.success(request, f'Archivos procesados correctamente. Se guardaron {registros_guardados} registros.')
            return redirect('ver_resultados')
            
        except Exception as e:
            messages.error(request, f'Error al procesar los archivos: {str(e)}')
            return redirect('upload_files')
    
    return render(request, 'excel_calculator/upload.html')

from django.http import HttpResponse
import pandas as pd
from io import BytesIO

def exportar_excel(request):
    """
    Vista para exportar los resultados a Excel en formato normal.
    """
    # Obtener la fecha del último cálculo
    ultimo_calculo = ResultadoCalculo.objects.order_by('-fecha_calculo').first()
    
    if ultimo_calculo:
        ultima_fecha = ultimo_calculo.fecha_calculo
        inicio_fecha = ultima_fecha.replace(microsecond=0)
        fin_fecha = inicio_fecha + timedelta(seconds=1)
        
        resultados = ResultadoCalculo.objects.filter(
            fecha_calculo__gte=inicio_fecha,
            fecha_calculo__lt=fin_fecha,
            balance__gt=0  # Solo resultados con balance positivo
        ).order_by('referencia', 'talla')
        
        # Convertir a DataFrame
        data = []
        for r in resultados:
            data.append({
                'Referencia': r.referencia,
                'Talla': r.talla,
                'Ventas Pendientes': float(r.ventas),
                'Inventario': float(r.inventario),
                'Producción': float(r.produccion),
                'Total Disponible': float(r.total_disponible),
                'Balance': float(r.balance)
            })
        
        df = pd.DataFrame(data)
        
        # Crear el archivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Resultados')
            worksheet = writer.sheets['Resultados']
            
            # Ajustar el ancho de las columnas
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).str.len().max(), len(col))
                worksheet.set_column(i, i, column_len + 2)
        
        # Preparar la respuesta
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=resultados_{inicio_fecha.strftime("%Y%m%d_%H%M")}.xlsx'
        return response
    
    return HttpResponse("No hay resultados para exportar", content_type='text/plain')

def exportar_excel_pivotado(request):
    """
    Vista para exportar los resultados a Excel en formato pivotado (tallas como columnas).
    """
    ultimo_calculo = ResultadoCalculo.objects.order_by('-fecha_calculo').first()
    
    if ultimo_calculo:
        ultima_fecha = ultimo_calculo.fecha_calculo
        inicio_fecha = ultima_fecha.replace(microsecond=0)
        fin_fecha = inicio_fecha + timedelta(seconds=1)
        
        resultados = ResultadoCalculo.objects.filter(
            fecha_calculo__gte=inicio_fecha,
            fecha_calculo__lt=fin_fecha,
            balance__gt=0
        ).order_by('referencia', 'talla')
        
        # Convertir a DataFrame
        data = []
        for r in resultados:
            data.append({
                'Referencia': r.referencia,
                'Talla': r.talla,
                'Valor': float(r.balance)  # Usamos el balance como valor
            })
        
        df = pd.DataFrame(data)
        
        # Crear pivot table
        df_pivot = df.pivot(
            index='Referencia',
            columns='Talla',
            values='Valor'
        ).fillna(0)  # Primero usamos 0 para los cálculos
        
        # Ordenar las columnas numéricamente
        tallas = sorted([col for col in df_pivot.columns if col.isdigit()], 
                       key=lambda x: int(x))
        otras_tallas = [col for col in df_pivot.columns if not col.isdigit()]
        df_pivot = df_pivot[tallas + otras_tallas]
        
        # Calcular el total primero mientras tenemos los ceros
        df_pivot['Total'] = df_pivot.sum(axis=1)
        
        # Reemplazar los ceros por espacios en blanco después de calcular el total
        df_pivot = df_pivot.replace(0, '')
        
        # Crear el archivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_pivot.to_excel(writer, sheet_name='Resultados')
            worksheet = writer.sheets['Resultados']
            
            # Ajustar el ancho de las columnas
            for i, col in enumerate(['Referencia'] + list(df_pivot.columns)):
                column_len = max(
                    df_pivot.index.astype(str).str.len().max() if i == 0 else len(str(col)),
                    len(col)
                )
                worksheet.set_column(i, i, column_len + 2)
        
        # Preparar la respuesta
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=resultados_pivotado_{inicio_fecha.strftime("%Y%m%d_%H%M")}.xlsx'
        return response
    
    return HttpResponse("No hay resultados para exportar", content_type='text/plain')

def ver_resultados(request):
    """
    Vista para ver los resultados del último cálculo.
    Solo muestra los resultados con balance positivo.
    """
    # Obtener la fecha del último cálculo
    ultimo_calculo = ResultadoCalculo.objects.order_by('-fecha_calculo').first()
    
    if ultimo_calculo:
        # Obtener todos los resultados de esa fecha
        ultima_fecha = ultimo_calculo.fecha_calculo
        # Redondear la fecha al segundo más cercano para evitar problemas de precisión
        inicio_fecha = ultima_fecha.replace(microsecond=0)
        fin_fecha = inicio_fecha + timedelta(seconds=1)
        
        # Filtrar por fecha y balance positivo
        resultados = ResultadoCalculo.objects.filter(
            fecha_calculo__gte=inicio_fecha,
            fecha_calculo__lt=fin_fecha,
            balance__gt=0  # Solo resultados con balance positivo
        ).order_by('referencia', 'talla')
        
        # Imprimir información de diagnóstico
        print(f"Fecha del último cálculo: {ultima_fecha}")
        print(f"Total de registros encontrados: {resultados.count()}")
        print("Primeros 5 registros con balance positivo:")
        for r in resultados[:5]:
            print(f"{r.referencia}-{r.talla}: Balance={r.balance}")
    else:
        resultados = ResultadoCalculo.objects.none()
        print("No se encontraron resultados")
    
    return render(request, 'excel_calculator/resultados.html', {
        'resultados': resultados,
        'fecha_calculo': ultimo_calculo.fecha_calculo if ultimo_calculo else None
    })
