from rest_framework import serializers
from .models import Conversacion, Mensaje

class PreguntaSerializer(serializers.ModelSerializer):
    pregunta = serializers.CharField(
        min_length=1, max_length=1000, required=True, 
        trim_whitespace=True
    )

class MensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensaje
        fields = ['id', 'conversacion', 
                  'contenido', 'fecha_creacion', 'rol']
        read_only_fields = fields 

class  ConversacionSerializer(serializers.ModelSerializer):
    mensajes = MensajeSerializer(many=True, read_only=True)

    class Meta:
        model = Conversacion
        fields = ['id', 'mensaje', 
                  'fecha_creacion', 'fecha_actualizacion',
                    'mensajes']
        read_only_fields = fields      