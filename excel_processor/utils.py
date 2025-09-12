def validar_formato_excel(ws):
    """
    Valida que el archivo Excel tenga las columnas requeridas.
    Retorna (bool, str) - (es_valido, mensaje_error)
    """
    # Lista de columnas requeridas (nombres exactos)
    COLUMNAS_REQUERIDAS = [
        'Nro.Ord.Prod',
        'PRODUC.',
        'CANT. ORIGINAL',
        'SALDO P ENTREGAR',
        'Ctd.Producid',
        'Observacion',
        'FC.PREVISTA',
        'concat',
        'anterior',
        'nuevo',
        'iny'
    ]
    
    # Obtener los nombres de las columnas del Excel (primera fila)
    columnas_excel = [str(cell.value).strip() if cell.value else '' for cell in ws[1]]
    
    # Verificar cada columna requerida
    columnas_faltantes = []
    for columna in COLUMNAS_REQUERIDAS:
        if columna not in columnas_excel:
            columnas_faltantes.append(columna)
    
    if columnas_faltantes:
        mensaje = (
            f"El archivo Excel no tiene el formato correcto.\n\n"
            f"Columnas que debe tener el archivo:\n"
            f"- {', '.join(COLUMNAS_REQUERIDAS)}\n\n"
            f"Columnas faltantes:\n"
            f"- {', '.join(columnas_faltantes)}\n\n"
            f"Nota: El campo 'Cant. Produc' se generará automáticamente durante el procesamiento."
        )
        return False, mensaje
    
    return True, "Formato válido"