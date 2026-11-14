from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from unittest.mock import patch

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


class ConversacionApiTests(APITestCase):
    def test_list_only_returns_authenticated_personas_conversations(self):
        user = get_user_model().objects.create_user(username="ana")
        tipo_persona = TipoPersona.objects.create(
            rol="Cliente",
            descripcion="Cliente de API",
        )
        persona = Persona.objects.create(
            nombre="Ana",
            usuario="ana",
            contrasena="hash",
            direccion="Dirección",
            tipo_persona=tipo_persona,
        )
        otra_persona = Persona.objects.create(
            nombre="Bea",
            usuario="bea",
            contrasena="hash",
            direccion="Dirección",
            tipo_persona=tipo_persona,
        )
        Conversacion.objects.create(persona=persona, mensaje="De Ana")
        Conversacion.objects.create(persona=otra_persona, mensaje="De Bea")
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/ia/conversaciones/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["mensaje"], "De Ana")

    def test_create_associates_conversation_with_authenticated_persona(self):
        user = get_user_model().objects.create_user(username="ana")
        tipo_persona = TipoPersona.objects.create(
            rol="Cliente",
            descripcion="Cliente de API",
        )
        persona = Persona.objects.create(
            nombre="Ana",
            usuario="ana",
            contrasena="hash",
            direccion="Dirección",
            tipo_persona=tipo_persona,
        )
        self.client.force_authenticate(user=user)

        response = self.client.post("/api/ia/conversaciones/", {}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Conversacion.objects.get(pk=response.data["id"]).persona,
            persona,
        )

    def test_post_message_saves_user_and_assistant_messages(self):
        user = get_user_model().objects.create_user(username="ana")
        tipo_persona = TipoPersona.objects.create(
            rol="Cliente",
            descripcion="Cliente de API",
        )
        persona = Persona.objects.create(
            nombre="Ana",
            usuario="ana",
            contrasena="hash",
            direccion="Dirección",
            tipo_persona=tipo_persona,
        )
        conversacion = Conversacion.objects.create(persona=persona)
        self.client.force_authenticate(user=user)

        with patch(
            "ia.views.AsistenteIA.responder_pregunta",
            return_value={"respuesta": "Hay existencias.", "modelo": "test-model"},
        ) as responder:
            response = self.client.post(
                f"/api/ia/conversaciones/{conversacion.pk}/mensajes/",
                {"pregunta": "¿Hay existencias?"},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(conversacion.mensajes.values_list("rol", "contenido")),
            [("user", "¿Hay existencias?"), ("assistant", "Hay existencias.")],
        )
        conversacion.refresh_from_db()
        self.assertEqual(conversacion.mensaje, "¿Hay existencias?")
        responder.assert_called_once()
