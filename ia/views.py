from django.db import transaction
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import Conversacion, Mensaje
from stockmaster.models import Persona
from .serializers import (
    PreguntaSerializer,
    MensajeSerializer,
    ConversacionSerializer,
)
from .asistente import AsistenteIA

class ConversacionViewSet(viewsets.ModelViewSet):

    serializer_class = ConversacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Cada usuario solamente consulta sus conversaciones.
        return (
            Conversacion.objects
            .filter(persona__usuario=self.request.user.get_username())
            .prefetch_related("mensajes")
            .order_by("-fecha_creacion")
        )

    def perform_create(self, serializer):
        persona = Persona.objects.filter(
            usuario=self.request.user.get_username()
        ).first()
        if persona is None:
            raise ValidationError(
                "No existe una persona asociada al nombre de usuario autenticado."
            )
        serializer.save(persona=persona)

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="mensajes",
    )
    def mensajes(self, request, pk=None):
        conversacion = self.get_object()
        # GET: consultar el historial.
        if request.method == "GET":
            mensajes = conversacion.mensajes.all()
            serializer = MensajeSerializer(
                mensajes,
                many=True,
            )
            return Response(serializer.data)

        # POST: enviar una pregunta.
        serializer = PreguntaSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)
        pregunta = serializer.validated_data["pregunta"]

        # Recuperar los últimos 10 mensajes anteriores.
        historial = list(
            conversacion.mensajes
            .order_by("-fecha_creacion", "-id")
            .values("rol", "contenido")[:10]
        )

        # El orden cronológico es importante para el modelo.
        historial.reverse()
        try:
            resultado = (
                AsistenteIA.responder_pregunta(
                    pregunta,
                    historial,
                )
            )

            respuesta = resultado["respuesta"]
            modelo = resultado["modelo"]

            # Guardar la pregunta y respuesta juntas.
            with transaction.atomic():

                Mensaje.objects.create(
                    conversacion=conversacion,
                    rol="user",
                    contenido=pregunta,
                )

                mensaje_asistente = Mensaje.objects.create(
                    conversacion=conversacion,
                    rol="assistant",
                    contenido=respuesta,
                )

                if conversacion.mensaje == "Nueva conversación":
                    conversacion.mensaje = pregunta[:1000]
                    conversacion.save(update_fields=["mensaje"])

            return Response(
                {
                    "conversacion": conversacion.id,
                    "pregunta": pregunta,
                    "respuesta": respuesta,
                    "modelo": modelo,
                    "mensaje_id": mensaje_asistente.id,
                },
                status=status.HTTP_200_OK,
            )

        except RuntimeError as error:

            return Response(
                {
                    "error": str(error),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
