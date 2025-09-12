TALLA_ORDER = [
    '034', '035', '036', '037', '038', '039', '395',
    '040', '405', '041', '042', '425', '043', '435',
    '044', '045', '046', '047', '750', '800'
]

def sort_sizes(sizes):
    """
    Ordena las tallas según el orden predefinido.
    Si aparece una talla nueva, se añadirá al final.
    """
    # Crear un diccionario con las posiciones para ordenar
    order_dict = {size: idx for idx, size in enumerate(TALLA_ORDER)}
    
    # Ordenar las tallas usando el orden predefinido
    sorted_sizes = sorted(sizes, key=lambda x: order_dict.get(x, len(TALLA_ORDER)))
    
    return sorted_sizes