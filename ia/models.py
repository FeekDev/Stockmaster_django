from django.db import models

# Create your models here.
class Conversacion(models.Model):
    persona = models.ForeignKey(
        "stockmaster.Persona",
        on_delete=models.CASCADE,
        related_name="conversaciones",
    )
    mensaje = models.TextField(max_length=1000, default="Nueva conversación")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversación de {self.persona.nombre} - {self.mensaje}"


class Mensaje(models.Model):
    ROLE_CHOICES = [
        ("user", "Usuario"),
        ("assistant", "Asistente"),
    ]
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name="mensajes")
    contenido = models.TextField(max_length=1000)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    rol = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
class Meta:
        ordering = ["fecha_creacion", "id"]
        