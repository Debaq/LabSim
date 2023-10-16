import spacy
import random

class SimpleChatbot:
    def __init__(self):
        self.nlp = spacy.load("es_core_news_md")
        self.INTENCIONES = {
            "saludo": ["hola", "buenas", "saludos", "qué tal"],
            "despedida": ["adiós", "hasta luego", "chao", "nos vemos"],
            "agradecimiento": ["gracias", "te agradezco", "muchas gracias"]
        }
        self.RESPUESTAS = {
            "saludo": ["¡Hola! ¿Cómo puedo ayudarte?", "¡Buenas! ¿En qué te puedo asistir?", "¡Hola! ¿Qué necesitas?"],
            "despedida": ["¡Hasta luego! Espero haber sido de ayuda.", "¡Adiós! Cuídate.", "¡Hasta la próxima!"],
            "agradecimiento": ["¡De nada! Estoy aquí para ayudar.", "No hay de qué.", "¡Fue un placer ayudarte!"],
            "default": ["Lo siento, no entiendo. ¿Puedes reformular?", "No estoy seguro de lo que me estás pidiendo. ¿Podrías explicar un poco más?", "Mis disculpas, no comprendo. ¿Podrías ser más claro?"]
        }
    
    def cambiar_diccionarios(self, intenciones=None, respuestas=None):
        if intenciones:
            self.INTENCIONES = intenciones
        if respuestas:
            self.RESPUESTAS = respuestas
    
    def determinar_intencion(self, texto_usuario):
        doc_usuario = self.nlp(texto_usuario)

        mejor_intencion = None
        mejor_similitud = -1

        for intencion, frases in self.INTENCIONES.items():
            for frase in frases:
                doc_frase = self.nlp(frase)
                similitud = doc_usuario.similarity(doc_frase)
                if similitud > mejor_similitud:
                    mejor_similitud = similitud
                    mejor_intencion = intencion

        if mejor_similitud > 0.7:  # Puedes ajustar este umbral según lo necesites.
            return mejor_intencion
        else:
            return None
    
    def obtener_respuesta(self, entrada):
        intencion = self.determinar_intencion(entrada)
        posibles_respuestas = self.RESPUESTAS.get(intencion, self.RESPUESTAS["default"])
        return random.choice(posibles_respuestas)

# Ejemplo de uso:
#chatbot = SimpleChatbot()
#entrada_usuario = input("Tú: ")
#respuesta_bot = chatbot.obtener_respuesta(entrada_usuario)
#print(f"Bot: {respuesta_bot}")
