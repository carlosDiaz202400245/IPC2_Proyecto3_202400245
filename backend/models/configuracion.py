class RecursoConfiguracion:
    def __init__(self, id_recurso, cantidad):
        self.id_recurso = id_recurso
        self.cantidad = float(cantidad)

    def to_dict(self):
        return {
            'idRecurso': self.id_recurso,
            'cantidad': self.cantidad
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data['idRecurso'], data['cantidad'])


class Configuracion:
    def __init__(self, id_configuracion, nombre, descripcion, id_categoria):
        self.id = id_configuracion
        self.nombre = nombre
        self.descripcion = descripcion
        self.id_categoria = id_categoria
        self.recursos = []  # Lista de RecursoConfiguracion

    def agregar_recurso(self, recurso_config):
        self.recursos.append(recurso_config)

    def calcular_costo_hora(self, recursos_dict):
        """Calcular el costo por hora de esta configuración"""
        costo_total = 0.0
        for recurso_config in self.recursos:
            recurso = recursos_dict.get(recurso_config.id_recurso)
            if recurso:
                costo_total += recurso.valor_x_hora * recurso_config.cantidad
        return costo_total

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'idCategoria': self.id_categoria,
            'recursos': [recurso.to_dict() for recurso in self.recursos]
        }

    @classmethod
    def from_dict(cls, data):
        configuracion = cls(
            data['id'],
            data['nombre'],
            data['descripcion'],
            data['idCategoria']
        )
        for recurso_data in data.get('recursos', []):
            configuracion.agregar_recurso(RecursoConfiguracion.from_dict(recurso_data))
        return configuracion

    def __str__(self):
        return f"Configuración {self.id}: {self.nombre} (Categoría: {self.id_categoria})"