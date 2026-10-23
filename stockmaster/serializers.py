from rest_framework import serializers
from django.db import transaction

from .models import Categoria, TipoPersona, Persona, Venta, DetalleFactura, Articulo

class TipoPersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoPersona
        fields = '__all__'


class PersonaSerializer(serializers.ModelSerializer):
    tipo_persona = TipoPersonaSerializer(read_only=True)
    tipo_persona_id = serializers.PrimaryKeyRelatedField(
        source='tipo_persona',
        queryset=TipoPersona.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Persona
        fields = '__all__'


class DetalleVentaInputSerializer(serializers.Serializer):
    articulo_codigo = serializers.PrimaryKeyRelatedField(
        source='articulo',
        queryset=Articulo.objects.all(),
    )
    cantidad = serializers.IntegerField(min_value=1)
    precio_unitario = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)


class VentaSerializer(serializers.ModelSerializer):
    persona = PersonaSerializer(read_only=True)
    persona_id = serializers.PrimaryKeyRelatedField(
        source='persona',
        queryset=Persona.objects.all(),
        write_only=True,
    )
    detalles = DetalleVentaInputSerializer(many=True, required=False, write_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Venta
        fields = '__all__'

    @staticmethod
    def _guardar_detalles(venta, detalles_data):
        for detalle_data in detalles_data:
            DetalleFactura.objects.create(venta=venta, **detalle_data)
            
    
    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles', [])
        with transaction.atomic():
            venta = Venta.objects.create(**validated_data)
            self._guardar_detalles(venta, detalles_data)
            venta.calcularTotal()
        return venta


class DetalleFacturaSerializer(serializers.ModelSerializer):
    venta = serializers.PrimaryKeyRelatedField(read_only=True)
    venta_id = serializers.PrimaryKeyRelatedField(
        source='venta',
        queryset=Venta.objects.all(),
        write_only=True,
    )
    articulo = serializers.PrimaryKeyRelatedField(read_only=True)
    articulo_codigo = serializers.PrimaryKeyRelatedField(
        source='articulo',
        queryset=Articulo.objects.all(),
        write_only=True,
    )

    class Meta:
        model = DetalleFactura
        fields = '__all__'

class ArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Articulo
        fields = '__all__'

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'
