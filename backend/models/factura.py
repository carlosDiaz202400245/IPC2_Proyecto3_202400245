class DetalleFactura:
    def __init__(self, id_instancia, tiempo_total, monto):
        self.id_instancia = id_instancia
        self.tiempo_total = float(tiempo_total)
        self.monto = float(monto)

    def to_dict(self):
        return {
            'idInstancia': self.id_instancia,
            'tiempoTotal': self.tiempo_total,
            'monto': self.monto
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data['idInstancia'], data['tiempoTotal'], data['monto'])


class Factura:
    def __init__(self, id_factura, nit_cliente, fecha_emision, periodo):
        self.id = id_factura
        self.nit_cliente = nit_cliente
        self.fecha_emision = fecha_emision
        self.periodo = periodo
        self.monto_total = 0.0
        self.detalles = []  # Lista de DetalleFactura

    def agregar_detalle(self, detalle):
        self.detalles.append(detalle)
        self.monto_total += detalle.monto

    def to_dict(self):
        return {
            'id': self.id,
            'nitCliente': self.nit_cliente,
            'fechaEmision': self.fecha_emision,
            'periodo': self.periodo,
            'montoTotal': self.monto_total,
            'detalles': [detalle.to_dict() for detalle in self.detalles]
        }

    @classmethod
    def from_dict(cls, data):
        factura = cls(
            data['id'],
            data['nitCliente'],
            data['fechaEmision'],
            data['periodo']
        )
        factura.monto_total = data.get('montoTotal', 0.0)
        for detalle_data in data.get('detalles', []):
            factura.agregar_detalle(DetalleFactura.from_dict(detalle_data))
        return factura

    def __str__(self):
        return f"Factura {self.id}: {self.nit_cliente} - ${self.monto_total:.2f}"