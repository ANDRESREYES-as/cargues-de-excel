import pandas as pd

def procesar_archivo_inventario(df):
    """
    Procesa el archivo de inventario.
    Solo considera registros del depósito PT y productos que inician con PA.
    """
    # Filtrar solo depósito PT y productos que empiezan con PA
    df_filtered = df[
        (df['Deposito'] == 'PT') & 
        (df['Producto'].str.startswith('PA'))
    ]
    
    # Agrupar por producto y sumar saldos
    resultado = df_filtered.groupby('Producto')['Saldo Actual'].sum().reset_index()
    return resultado

def procesar_archivo_ventas(df):
    """
    Procesa el archivo de ventas.
    Solo considera productos que inician con PA y suma la cantidad pendiente por producto.
    """
    try:
        # Asegurarse de que la columna Producto sea string
        df['Producto'] = df['Producto'].astype(str)
        
        # Filtrar solo productos que empiezan con PA
        df_filtered = df[df['Producto'].str.startswith('PA')]
        
        # Agrupar por producto y sumar cantidades pendientes
        resultado = df_filtered.groupby('Producto')['Cant.Pendiente'].sum().reset_index()
        return resultado
    except Exception as e:
        print(f"Error al procesar archivo de ventas: {str(e)}")
        # Devolver DataFrame vacío con las columnas correctas
        return pd.DataFrame(columns=['Producto', 'Cant.Pendiente'])

def procesar_archivo_produccion(df):
    """
    Procesa el archivo de producción.
    Solo considera productos que inician con PA y suma el saldo por entregar.
    """
    # Renombrar columna PRODUC. a Producto para consistencia
    df = df.rename(columns={'PRODUC.': 'Producto'})
    
    # Filtrar solo productos que empiezan con PA
    df_filtered = df[df['Producto'].str.startswith('PA')]
    
    # Agrupar por producto y sumar saldos por entregar
    resultado = df_filtered.groupby('Producto')['SALDO P ENTREGAR'].sum().reset_index()
    return resultado

def consolidar_resultados(inv_df, ven_df, prod_df):
    """
    Consolida los resultados de los tres archivos en un solo DataFrame y calcula el balance.
    Solo incluye productos que empiezan con PA.
    
    El proceso es:
    1. Usa el DataFrame de ventas como base
    2. Agrega las columnas de inventario y producción
    3. Calcula el balance final (Ventas - (Inventario + Producción))
    """
    # Preparar DataFrames con las columnas necesarias
    ventas = ven_df[ven_df['Producto'].str.startswith('PA')].copy()
    ventas = ventas.rename(columns={'Cant.Pendiente': 'Ventas'})
    inventario = inv_df.rename(columns={'Saldo Actual': 'Inventario'})
    produccion = prod_df.rename(columns={'SALDO P ENTREGAR': 'Producción'})
    
    # Usar ventas como base y hacer merge con los otros DataFrames
    resultado = ventas.copy()
    
    # Merge con inventario
    resultado = resultado.merge(
        inventario[['Producto', 'Inventario']],
        on='Producto',
        how='left'
    )
    
    # Merge con producción (ajustando el nombre de la columna PRODUC. si es necesario)
    if 'PRODUC.' in prod_df.columns:
        produccion = produccion.rename(columns={'PRODUC.': 'Producto'})
    resultado = resultado.merge(
        produccion[['Producto', 'Producción']],
        on='Producto',
        how='left'
    )
    
    # Llenar valores nulos con 0
    resultado = resultado.fillna(0)
    
    # Calcular el balance
    resultado['Total Disponible'] = resultado['Inventario'] + resultado['Producción']
    resultado['Balance'] = resultado['Ventas'] - resultado['Total Disponible']
    
    # Ordenar las columnas
    columnas = [
        'Producto',
        'Ventas',
        'Inventario',
        'Producción',
        'Total Disponible',
        'Balance'
    ]
    resultado = resultado[columnas]
    
    return resultado