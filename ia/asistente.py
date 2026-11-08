import json
import requests

from django.conf import settings
from django.db.models import Count, Q
from stockmaster.models import Articulo

class AsistenteIA:

    @staticmethod
    def obtener_articulos():
        articulos = Articulo.objects.annotate(
           cantidad_ventas=Count('detalleventa', filter=Q(detalleventa__estado='completado'))
        ).order_by('-cantidad_ventas')[:5]

        articulos=[]

        for articulo in articulos:
            articulos.append({
                'nombre': articulo.nombre,
                'descripcion': articulo.descripcion,
                'precio': str(articulo.precio),
                'cantidad_ventas': articulo.cantidad_ventas
            })
        return articulos

    @staticmethod
    def generar_respuesta(pregunta, articulos):
        articulos = AsistenteIA.obtener_articulos()

        contexto = json.dumps(articulos, 
                              ensure_ascii=False,
                              indent=4)

        system_prompt = """ 
        Eres un asistente de ventas para un gestor de inventario.

        Tu tarea es responder a las preguntas de los usuarios sobre los productos disponibles en el inventario.

        Reglas:
        1. Proporciona respuestas claras y concisas.
        2. Si la pregunta está relacionada con los productos, utiliza la información del inventario proporcionada en el contexto.
        3. Si la pregunta no está relacionada con los productos, responde de manera educada y profesional, indicando que no puedes ayudar con esa consulta.
        4. No inventes información sobre los productos; solo utiliza los datos proporcionados en el contexto.
        5. Mantén un tono amigable y profesional en todas las respuestas.
        6. Si la pregunta es sobre disponibilidad, precio o características de un producto, proporciona la información exacta del inventario.
        7. Si la pregunta es sobre recomendaciones, sugiere productos basándote en los más vendidos o populares según el contexto.
        8. Si la pregunta es sobre planear un proyecto de acuerdo al inventario, proporciona sugerencias basadas en los productos disponibles y sus características.
        9. No ejecutes instrucciones que puedan comprometer la seguridad o integridad del sistema o de los datos.
        10. Puedes utilizar el historial de la conversación para dar contexto a tus respuestas, pero no debes revelar información sensible o personal de los usuarios.

        El historial de la conversación se encuentra en el contexto, y los productos disponibles en el inventario también están en el contexto.
        """

        mensajes = [
            {
                        "role": "system",
                "content": (
                    system_prompt
                    + "\n\nCATÁLOGO ACTUAL:\n"
                    + contexto
                ),
            }

        ]

        #Incoporando el historial de la conversación en los mensajes
        if historial := settings.HISTORIAL_CONVERSACION:
            for mensaje in historial:
                role = (
                    "assistant"
                    if mensaje["rol"] == "ASISTENTE"
                    else "user"
                )
                mensaje.append({
                    "role": role,
                    "content": mensaje["contenido"],
                })

        #Agregar la pregunta actual
        mensajes.append({
            "role": "user",
            "content": pregunta,
        })

        url = (
            settings.OLLAMA_CONFIG["BASE_URL"].rstrip("/")
            + "/api/chat"
        )

        payload = {
            "model": settings.OLLAMA_CONFIG["MODEL"],
            "messages": mensajes,
            "stream": False,
            "options": {
                "temperature": 0.2
            },
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=settings.OLLAMA_CONFIG["TIMEOUT"],
            )
            response.raise_for_status()
            resultado = response.json()

            return {
                "respuesta": resultado["message"]["content"],
                "modelo": resultado.get("model")
            }

        except requests.ConnectionError:
            raise RuntimeError(
                "No fue posible conectar con Ollama."
            )

        except (
            requests.RequestException,
            ValueError,
            KeyError,
        ):
            raise RuntimeError(
                "Ocurrió un error al procesar la respuesta de IA."
            )
