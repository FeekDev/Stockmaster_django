from decimal import Decimal
from django.test import SimpleTestCase
from django.db import models
from unittest.mock import Mock, PropertyMock, patch

from .models import Articulo, DetalleFactura, Persona, TipoPersona, Venta
from .serializers import (
    DetalleFacturaSerializer,
    PersonaSerializer,
    TipoPersonaSerializer,
    VentaSerializer,
)


class PersonaSerializerTests(SimpleTestCase):
    def test_tipo_persona_is_nested_in_output_and_id_is_writable(self):
        tipo_persona = TipoPersona(
            id_tipo=1,
            rol='Administrador',
            descripcion='Acceso total',
        )
        persona = Persona(
            id_persona=1,
            nombre='Usuario',
            usuario='usuario',
            contrasena='hash',
            direccion='Dirección',
            tipo_persona=tipo_persona,
        )
        serializer = PersonaSerializer(persona)
        id_field = serializer.fields['tipo_persona_id']

        self.assertTrue(serializer.fields['tipo_persona'].read_only)
        self.assertTrue(id_field.write_only)
        self.assertEqual(id_field.source, 'tipo_persona')
        self.assertIs(id_field.get_queryset().model, TipoPersona)
        self.assertEqual(
            dict(serializer.data['tipo_persona']),
            dict(TipoPersonaSerializer(tipo_persona).data),
        )
        self.assertNotIn('tipo_persona_id', serializer.data)

    def test_tipo_persona_id_resolves_to_related_model(self):
        tipo_persona = TipoPersona(id_tipo=1, rol='Admin', descripcion='Full')
        field = PersonaSerializer().fields['tipo_persona_id']

        with patch.object(field, 'get_queryset', return_value=Mock(get=Mock(return_value=tipo_persona))):
            self.assertIs(field.to_internal_value(1), tipo_persona)


class VentaSerializerTests(SimpleTestCase):
    def test_persona_is_nested_in_output_and_id_is_writable(self):
        tipo_persona = TipoPersona(id_tipo=1, rol='Admin', descripcion='Full')
        persona = Persona(
            id_persona=1,
            nombre='Usuario',
            usuario='usuario',
            contrasena='hash',
            direccion='Dirección',
            tipo_persona=tipo_persona,
        )
        venta = Venta(id_venta=1, persona=persona)
        serializer = VentaSerializer(venta)
        id_field = serializer.fields['persona_id']

        self.assertTrue(serializer.fields['persona'].read_only)
        self.assertTrue(id_field.write_only)
        self.assertEqual(id_field.source, 'persona')
        self.assertIs(id_field.get_queryset().model, Persona)
        self.assertEqual(
            dict(serializer.data['persona']),
            dict(PersonaSerializer(persona).data),
        )
        self.assertNotIn('persona_id', serializer.data)
        self.assertTrue(serializer.fields['total'].read_only)
        self.assertEqual(serializer.data['total'], '0.00')

    def test_persona_id_resolves_to_related_model(self):
        persona = Persona(
            id_persona=1,
            nombre='Usuario',
            usuario='usuario',
            contrasena='hash',
            direccion='Dirección',
            tipo_persona=TipoPersona(id_tipo=1, rol='Admin', descripcion='Full'),
        )
        field = VentaSerializer().fields['persona_id']

        with patch.object(field, 'get_queryset', return_value=Mock(get=Mock(return_value=persona))):
            self.assertIs(field.to_internal_value(1), persona)

    def test_create_saves_nested_details_and_recalculates_total(self):
        persona = Persona(id_persona=1)
        articulo = Articulo(codigo='A1')
        venta = Mock()
        detalles = [{'articulo': articulo, 'cantidad': 2, 'precio_unitario': Decimal('10.00')}]
        serializer = VentaSerializer()

        with patch('stockmaster.serializers.transaction.atomic'):
            with patch.object(Venta.objects, 'create', return_value=venta) as create_venta:
                with patch.object(VentaSerializer, '_guardar_detalles') as guardar_detalles:
                    result = serializer.create(
                        {'persona': persona, 'detalles': detalles}
                    )

        self.assertIs(result, venta)
        create_venta.assert_called_once_with(persona=persona)
        guardar_detalles.assert_called_once_with(venta, detalles)
        venta.calcularTotal.assert_called_once_with()


class VentaTotalTests(SimpleTestCase):
    def test_calcular_total_applies_discount_to_detail_subtotals(self):
        venta = Venta(pk=1, descuento=Decimal('10.00'))
        detalles = Mock()
        detalles.aggregate.return_value = {'total': Decimal('50.00')}

        with patch.object(Venta, 'detalles', new_callable=PropertyMock, return_value=detalles):
            with patch.object(models.Model, 'save') as base_save:
                total = venta.calcularTotal()

        self.assertEqual(total, Decimal('45.00'))
        base_save.assert_called_once_with(update_fields=['total'])

    def test_saving_venta_recalculates_total(self):
        venta = Venta(pk=1, persona_id=1)

        with patch.object(models.Model, 'save') as base_save:
            with patch.object(Venta, 'calcularTotal') as calcular_total:
                venta.save()

        base_save.assert_called_once()
        calcular_total.assert_called_once_with()

    def test_saving_detail_recalculates_venta_total(self):
        venta = Mock()
        detalle = DetalleFactura(
            venta_id=1,
            articulo_id='A1',
            cantidad=2,
            precio_unitario='10.00',
        )
        detalle._state.fields_cache['venta'] = venta

        with patch.object(models.Model, 'save'):
            with patch.object(DetalleFactura, 'calcularSubtotal'):
                detalle.save()

        venta.calcularTotal.assert_called_once_with()

    def test_deleting_detail_recalculates_venta_total(self):
        venta = Mock()
        detalle = DetalleFactura(
            pk=1,
            venta_id=1,
            articulo_id='A1',
            cantidad=2,
            precio_unitario='10.00',
        )
        detalle._state.fields_cache['venta'] = venta

        with patch.object(models.Model, 'delete', return_value=(1, {})):
            detalle.delete()

        venta.calcularTotal.assert_called_once_with()


class DetalleFacturaSerializerTests(SimpleTestCase):
    def test_detail_accepts_sale_and_article_ids(self):
        venta = Venta(pk=5, persona_id=1)
        articulo = Articulo(codigo='A1', nombre='Artículo', precio=Decimal('12.50'), stock=3)
        serializer = DetalleFacturaSerializer()
        venta_field = serializer.fields['venta_id']
        articulo_field = serializer.fields['articulo_codigo']

        self.assertTrue(venta_field.write_only)
        self.assertEqual(venta_field.source, 'venta')
        self.assertTrue(articulo_field.write_only)
        self.assertEqual(articulo_field.source, 'articulo')

        with patch.object(venta_field, 'get_queryset', return_value=Mock(get=Mock(return_value=venta))):
            self.assertIs(venta_field.to_internal_value(5), venta)
        with patch.object(
            articulo_field,
            'get_queryset',
            return_value=Mock(get=Mock(return_value=articulo)),
        ):
            self.assertIs(articulo_field.to_internal_value('A1'), articulo)

    def test_detail_endpoint_is_registered(self):
        from django.urls import reverse

        self.assertEqual(reverse('detallefactura-list'), '/api/detalle-factura/')
