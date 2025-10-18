class Cliente:
    def __init__(self, nit, nombre, usuario, clave, direccion, correo_electronico):
        self.nit = nit
        self.nombre = nombre
        self.usuario = usuario
        self.clave = clave
        self.direccion = direccion
        self.correo_electronico = correo_electronico
        self.instancias = []  # Lista de objetos Instancia

    def agregar_instancia(self, instancia):
        self.instancias.append(instancia)

    def to_dict(self):
        return {
            'nit': self.nit,
            'nombre': self.nombre,
            'usuario': self.usuario,
            'clave': self.clave,
            'direccion': self.direccion,
            'correoElectronico': self.correo_electronico,
            'instancias': [instancia.to_dict() for instancia in self.instancias]
        }

    @classmethod
    def from_dict(cls, data):
        cliente = cls(
            data['nit'],
            data['nombre'],
            data['usuario'],
            data['clave'],
            data['direccion'],
            data['correoElectronico']
        )
        # Las instancias se agregarán después
        return cliente

    def __str__(self):
        return f"Cliente {self.nit}: {self.nombre}"