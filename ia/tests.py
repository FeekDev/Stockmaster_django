from django.test import TestCase

from stockmaster.models import Persona, TipoPersona

from .models import Conversacion


class ConversacionPersonaTests(TestCase):
    def test_conversacion_se_relaciona_con_persona(self):
        tipo_persona = TipoPersona.objects.create(
            rol="Cliente",
            descripcion="Cliente de prueba",
        )
        persona = Persona.objects.create(
            nombre="Ana",
            usuario="ana",
            contrasena="hash",
            direccion="Dirección de prueba",
            tipo_persona=tipo_persona,
        )

        conversacion = Conversacion.objects.create(persona=persona)

        self.assertEqual(conversacion.persona, persona)
        self.assertEqual(persona.conversaciones.get(), conversacion)
