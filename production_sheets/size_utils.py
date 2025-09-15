TALLA_ORDER = [
    '034', '035', '036', '037', '375', '038', '385', '039', '395',
    '040', '405', '041', '415', '042', '425', '043', '435','044',
    '045', '046', '047', '048', '600', '700', '750', '800','850',
    '900', '950', '100', '105', '110', '115', '120', '130'
]

def is_valid_size(size):
    """
    Verifica si una talla es válida según el formato esperado.
    Una talla válida debe ser:
    - Una cadena de 3 caracteres
    - Contener solo números
    
    Args:
        size (str): La talla a validar
    
    Returns:
        bool: True si la talla es válida, False en caso contrario
    """
    try:
        # Verificar que sea una cadena de 3 caracteres
        if not isinstance(size, str) or len(size) != 3:
            return False
        
        # Verificar que todos los caracteres sean números
        int(size)
        return True
    except ValueError:
        return False

def sort_sizes(sizes):
    """
    Ordena las tallas según el orden predefinido.
    Las tallas inválidas o no reconocidas se añadirán al final.
    
    Args:
        sizes (list): Lista de tallas a ordenar
    
    Returns:
        tuple: (tallas_ordenadas, tallas_invalidas)
            - tallas_ordenadas: Lista de tallas ordenadas según TALLA_ORDER
            - tallas_invalidas: Lista de tallas que no cumplen con el formato esperado
    """
    valid_sizes = []
    invalid_sizes = []
    
    # Separar tallas válidas e inválidas
    for size in sizes:
        if is_valid_size(size):
            valid_sizes.append(size)
        else:
            invalid_sizes.append(size)
    
    # Crear un diccionario con las posiciones para ordenar
    order_dict = {size: idx for idx, size in enumerate(TALLA_ORDER)}
    
    # Ordenar las tallas válidas usando el orden predefinido
    # Las tallas válidas pero no en TALLA_ORDER irán después de las conocidas
    known_sizes = []
    unknown_sizes = []
    
    for size in valid_sizes:
        if size in order_dict:
            known_sizes.append(size)
        else:
            unknown_sizes.append(size)
    
    # Ordenar tallas conocidas según TALLA_ORDER
    sorted_known = sorted(known_sizes, key=lambda x: order_dict[x])
    # Ordenar tallas desconocidas alfabéticamente
    sorted_unknown = sorted(unknown_sizes)
    # Ordenar tallas inválidas alfabéticamente
    sorted_invalid = sorted(invalid_sizes)
    
    # Combinar todas las tallas en el orden correcto
    final_sizes = sorted_known + sorted_unknown + sorted_invalid
    
    return final_sizes, sorted_invalid