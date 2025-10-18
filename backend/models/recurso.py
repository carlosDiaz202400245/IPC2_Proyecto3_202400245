class Recurso:
    def __init__(self, id_recurso, nombre, abreviatura, metrica, tipo, valor_x_hora):
        self.id = id_recurso
        self.nombre = nombre
        self.abreviatura = abreviatura
        self.metrica = metrica
        self.tipo = tipo  # "Hardware" o "Software"
        self.valor_x_hora = float(valor_x_hora)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'abreviatura': self.abreviatura,
            'metrica': self.metrica,
            'tipo': self.tipo,
            'valorXhora': self.valor_x_hora
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data['id'],
            data['nombre'],
            data['abreviatura'],
            data['metrica'],
            data['tipo'],
            data['valorXhora']
        )

    def __str__(self):
        return f"Recurso {self.id}: {self.nombre} ({self.abreviatura}) - {self.tipo}"