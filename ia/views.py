from django.db import transaction
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import Conversacion, Mensaje
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
            .filter(usuario=self.request.user)
            .prefetch_related("mensajes")
            .order_by("-fecha_actualizacion")
        )

    def perform_create(self, serializer):
        serializer.save(
            usuario=self.request.user
        )

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
                    rol="USUARIO",
                    contenido=pregunta,
                )

                mensaje_asistente = Mensaje.objects.create(
                    conversacion=conversacion,
                    rol="ASISTENTE",
                    contenido=respuesta,
                )

                # Actualizar el título en el primer mensaje.
                if conversacion.titulo == "Nueva conversación":
                    conversacion.titulo = pregunta[:150]
                conversacion.fecha_actualizacion = timezone.now()

                conversacion.save(
                    update_fields=[
                        "titulo",
                        "fecha_actualizacion",
                    ]
                )

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
