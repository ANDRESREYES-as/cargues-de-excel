from django.shortcuts import render, redirect
from django.contrib import messages
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
            
            # Guardar resultados
            for _, row in resultados.iterrows():
                ResultadoCalculo.objects.create(
                    producto=row['Producto'],
                    ventas=row['Ventas'],
                    inventario=row['Inventario'],
                    produccion=row['Producción'],
                    total_disponible=row['Total Disponible'],
                    balance=row['Balance']
                )
            
            messages.success(request, 'Archivos procesados correctamente')
            return redirect('ver_resultados')
            
        except Exception as e:
            messages.error(request, f'Error al procesar los archivos: {str(e)}')
            return redirect('upload_files')
    
    return render(request, 'excel_calculator/upload.html')

def ver_resultados(request):
    """
    Vista para ver los resultados del cálculo.
    """
    resultados = ResultadoCalculo.objects.all()
    return render(request, 'excel_calculator/resultados.html', {
        'resultados': resultados
    })
