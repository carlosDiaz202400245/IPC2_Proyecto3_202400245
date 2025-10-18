from datetime import datetime

class Consumo:
    def __init__(self, tiempo, fecha_hora):
        self.tiempo = float(tiempo)  # Horas de consumo
        self.fecha_hora = fecha_hora  # String con fecha/hora

    def to_dict(self):
        return {
            'tiempo': self.tiempo,
            'fechahora': self.fecha_hora
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data['tiempo'], data['fechahora'])


class Instancia:
    def __init__(self, id_instancia, id_configuracion, nombre, fecha_inicio, nit_cliente):
        self.id = id_instancia
        self.id_configuracion = id_configuracion
        self.nombre = nombre
        self.fecha_inicio = fecha_inicio
        self.estado = "Vigente"  # "Vigente" o "Cancelada"
        self.fecha_final = None
        self.nit_cliente = nit_cliente
        self.consumos = []  # Lista de objetos Consumo

    def agregar_consumo(self, consumo):
        self.consumos.append(consumo)

    def cancelar(self, fecha_final):
        self.estado = "Cancelada"
        self.fecha_final = fecha_final

    def calcular_consumo_total(self):
        return sum(consumo.tiempo for consumo in self.consumos)

    def to_dict(self):
        data = {
            'id': self.id,
            'idConfiguracion': self.id_configuracion,
            'nombre': self.nombre,
            'fechaInicio': self.fecha_inicio,
            'estado': self.estado,
            'nitCliente': self.nit_cliente,
            'consumos': [consumo.to_dict() for consumo in self.consumos]
        }
        if self.fecha_final:
            data['fechaFinal'] = self.fecha_final
        return data

    @classmethod
    def from_dict(cls, data):
        instancia = cls(
            data['id'],
            data['idConfiguracion'],
            data['nombre'],
            data['fechaInicio'],
            data['nitCliente']
        )
        instancia.estado = data.get('estado', 'Vigente')
        instancia.fecha_final = data.get('fechaFinal')
        for consumo_data in data.get('consumos', []):
            instancia.agregar_consumo(Consumo.from_dict(consumo_data))
        return instancia

    def __str__(self):
        return f"Instancia {self.id}: {self.nombre} - {self.estado}"