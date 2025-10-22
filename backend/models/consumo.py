class Consumo:
    def __init__(self, tiempo, fecha_hora):
        self.tiempo = float(tiempo)
        self.fecha_hora = fecha_hora

    def to_dict(self):
        return {
            'tiempo': self.tiempo,
            'fechahora': self.fecha_hora
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data['tiempo'], data['fechahora'])