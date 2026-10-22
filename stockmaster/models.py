from decimal import Decimal

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Sum

class TipoPersona(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    rol = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return self.rol


class Persona(models.Model):
    id_persona = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    usuario = models.CharField(max_length=150, unique=True)
    contrasena = models.CharField(max_length=128)
    direccion = models.CharField(max_length=255)
    tipo_persona = models.ForeignKey(
        TipoPersona,
        on_delete=models.PROTECT,
    )

    def set_contrasena(self, contrasena):
        self.contrasena = make_password(contrasena)

    def verificar_contrasena(self, contrasena):
        return check_password(contrasena, self.contrasena)

    @classmethod
    def iniciarSesion(cls, usuario, contrasena):
        persona = cls.objects.filter(usuario=usuario).first()
        return persona is not None and persona.verificar_contrasena(contrasena)

    @classmethod
    def registrarse(cls, nombre, usuario, contrasena, direccion, tipo_persona):
        if cls.objects.filter(usuario=usuario).exists():
            return False

        persona = cls(
            nombre=nombre,
            usuario=usuario,
            direccion=direccion,
            tipo_persona=tipo_persona,
        )
        persona.set_contrasena(contrasena)
        persona.save()
        return True

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.descripcion


class Articulo(models.Model):
    codigo = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=150)
    precio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    stock = models.PositiveIntegerField(default=0)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="articulos",
    )

    def actualizarStock(self, cantidad):
        nuevo_stock = self.stock + cantidad
        if nuevo_stock < 0:
            raise ValidationError("El stock no puede quedar por debajo de cero.")
        self.stock = nuevo_stock
        self.save(update_fields=["stock"])

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    persona = models.ForeignKey(
        Persona,
        on_delete=models.PROTECT,
    )
    fecha = models.DateTimeField(auto_now_add=True)
    descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
    )
    total = models.DecimalField(
            max_digits=12,
            decimal_places=2,
            default=Decimal("0.00"),
        )

class DetalleFactura(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    articulo = models.ForeignKey(
        Articulo,
        on_delete=models.PROTECT,
        related_name="detalles_venta",
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
