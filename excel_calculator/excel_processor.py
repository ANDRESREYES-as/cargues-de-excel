import pandas as pd

def procesar_archivo_inventario(df):
    """
    Procesa el archivo de inventario.
    Solo considera registros del depósito PT y productos que inician con PA.
    """
    # Crear una copia y asegurarse de que la columna Producto sea string
    df = df.copy()
    df['Producto'] = df['Producto'].astype(str)
    
    # Filtrar depósitos PT y 98, y productos que empiezan con PA //(df['Deposito'] == 'PT') |
    
    df_filtered = df[
        ((df['Deposito'] == '98') | (df['Direccion'] == 'CALIDAD')) &  
        (df['Producto'].str.startswith('PA'))
    ].copy()

    # Extraer referencia y talla
    df_filtered['Producto_Clean'] = df_filtered['Producto'].str.strip()
    df_filtered['Talla'] = df_filtered['Producto_Clean'].str.extract(r'(\d{3})$').fillna('')
    
    # Para referencias que terminan en 3 dígitos
    df_filtered['Referencia'] = df_filtered.apply(
        lambda x: x['Producto_Clean'][:-3] if x['Talla'] != '' else x['Producto_Clean'],
        axis=1
    )
    
    # Agrupar por referencia y talla, sumar saldos
    resultado = df_filtered.groupby(['Referencia', 'Talla'])['Saldo Actual'].sum().reset_index()
    resultado = resultado.rename(columns={'Saldo Actual': 'Inventario'})
    
    return resultado

def procesar_archivo_ventas(df):
    """
    Procesa el archivo de ventas.
    Solo considera productos que inician con PA y suma la cantidad pendiente por producto.
    """
    try:
        # Imprimir información de diagnóstico
        print(f"Total de registros en archivo de ventas: {len(df)}")
        
        # Crear una copia y asegurarse de que la columna Producto sea string
        df = df.copy()
        df['Producto'] = df['Producto'].astype(str)
        
        # Filtrar solo productos que empiezan con PA
        df_filtered = df[df['Producto'].str.startswith('PA')].copy()
        print(f"Registros de productos PA encontrados: {len(df_filtered)}")
        
        # Extraer referencia y talla
        df_filtered['Producto_Clean'] = df_filtered['Producto'].str.strip()
        df_filtered['Talla'] = df_filtered['Producto_Clean'].str.extract(r'(\d{3})$').fillna('')
        
        # Para referencias que terminan en 3 dígitos
        df_filtered['Referencia'] = df_filtered.apply(
            lambda x: x['Producto_Clean'][:-3] if x['Talla'] != '' else x['Producto_Clean'],
            axis=1
        )
        
        # Mostrar algunas filas de ejemplo
        print("\nEjemplos de productos procesados:")
        print(df_filtered[['Producto', 'Referencia', 'Talla', 'Cant.Pendiente']].head())
        
        # Agrupar por referencia y talla, sumar cantidades
        resultado = df_filtered.groupby(['Referencia', 'Talla'])['Cant.Pendiente'].sum().reset_index()
        resultado = resultado.rename(columns={'Cant.Pendiente': 'Ventas'})
        
        print(f"\nTotal de resultados agrupados: {len(resultado)}")
        print("\nPrimeros registros del resultado:")
        print(resultado.head())
        
        return resultado
    except Exception as e:
        print(f"Error al procesar archivo de ventas: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['Referencia', 'Talla', 'Ventas'])

def procesar_archivo_produccion(df):
    """
    Procesa el archivo de producción.
    Solo considera productos que inician con PA y suma el saldo por entregar.
    """
    # Crear una copia y manejar diferentes nombres de columnas
    df = df.copy()
    if 'PRODUC.' in df.columns:
        producto_col = 'PRODUC.'
    else:
        producto_col = 'Producto'
    
    # Asegurarse de que la columna Producto sea string
    df[producto_col] = df[producto_col].astype(str)
    
    # Filtrar solo productos que empiezan con PA
    df_filtered = df[df[producto_col].str.startswith('PA')].copy()
    
    # Extraer referencia y talla
    df_filtered['Producto_Clean'] = df_filtered[producto_col].str.strip()
    df_filtered['Talla'] = df_filtered['Producto_Clean'].str.extract(r'(\d{3})$').fillna('')
    df_filtered['Referencia'] = df_filtered.apply(
        lambda x: x['Producto_Clean'][:-3] if x['Talla'] != '' else x['Producto_Clean'],
        axis=1
    )
    
    # Agrupar por referencia y talla, sumar saldos
    resultado = df_filtered.groupby(['Referencia', 'Talla'])['SALDO P ENTREGAR'].sum().reset_index()
    resultado = resultado.rename(columns={'SALDO P ENTREGAR': 'Producción'})
    
    return resultado

def consolidar_resultados(inv_df, ven_df, prod_df):
    """
    Consolida los resultados de los tres archivos en un solo DataFrame y calcula el balance.
    Usa las ventas como base para mostrar todos los productos PA que tienen ventas.
    """
    # Usar ventas como base
    resultado = ven_df.copy()
    
    # Merge con inventario
    resultado = resultado.merge(
        inv_df[['Referencia', 'Talla', 'Inventario']],
        on=['Referencia', 'Talla'],
        how='left'
    )
    
    # Merge con producción
    resultado = resultado.merge(
        prod_df[['Referencia', 'Talla', 'Producción']],
        on=['Referencia', 'Talla'],
        how='left'
    )
    
    # Llenar valores nulos con 0
    resultado = resultado.fillna(0)
    
    # Calcular el balance
    resultado['Total Disponible'] = resultado['Inventario'] + resultado['Producción']
    resultado['Balance'] = resultado['Ventas'] - resultado['Total Disponible']
    
    # Ordenar las columnas
    columnas = [
        'Referencia',
        'Talla',
        'Ventas',
        'Inventario',
        'Producción',
        'Total Disponible',
        'Balance'
    ]
    resultado = resultado[columnas]
    
    # Ordenar por Referencia y Talla
    resultado = resultado.sort_values(['Referencia', 'Talla'])
    
    return resultado