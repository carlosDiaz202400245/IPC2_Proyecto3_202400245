class Categoria:
    def __init__(self, id_categoria, nombre, descripcion, carga_trabajo):
        self.id = id_categoria
        self.nombre = nombre
        self.descripcion = descripcion
        self.carga_trabajo = carga_trabajo
        self.configuraciones = []  # Lista de objetos Configuracion

    def agregar_configuracion(self, configuracion):
        self.configuraciones.append(configuracion)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'cargaTrabajo': self.carga_trabajo,
            'configuraciones': [config.to_dict() for config in self.configuraciones]
        }

    @classmethod
    def from_dict(cls, data):
        categoria = cls(
            data['id'],
            data['nombre'],
            data['descripcion'],
            data['cargaTrabajo']
        )
        # Las configuraciones las pienso después jdskjs
        return categoria

    def __str__(self):
        return f"Categoría {self.id}: {self.nombre} - {self.carga_trabajo}"