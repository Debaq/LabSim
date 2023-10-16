import spacy
import random

class SimpleChatbot:
    def __init__(self):
        self.nlp = spacy.load("es_core_news_md")


        self.INTENCIONES = {
                "saludo": ["hola", "buenas tardes", "que tal"],
                "estado":["Como se encuentra","Como esta","Como ha estado"],
                "nombre":["Como se llama","Cual es su nombre","Como se llama","Me indica su nombre","Me indica como se llama","Su nombre"],
                "edad": ["Cuál es su edad","Cuántos años tiene","Me indica su edad"], 
                "motivo": ["Por qué vino hoy","Porque vino aquí","Porque que esta aqui","Que le trae por aquí","Cual es el motivo de su consulta"],
                "evolución": ["Hace cuánto tiempo está con molestia","Desde cuando tiene molestias","Hace cuanto molesta","Hace cuanto","Hace cuanto que esto pasa"],
                "oído":["Por un oído o por ambos","Solo en un oido","En cual de los dos","En ambos oidos","En cual"],
                "supuración":["Le ha salido líquido o sangre de los oídos","Le ha salido liquido de los oidos","Le han sangrado los oidos","Le han supurado los oidos","Ha notado que sale liquido de sus oidos"],
                "tinnitus":["Escucha pitidos o ruidos en los oídos","Sufre de tinnitus","Siente pitidos en sus oidos","Escucha zumbidos en sus oidos","Siente que escucha pitidos en sus oidos"],
                "traumas":["Ha tenido golpes en la cabeza","Se ha golpeado la cabeza","Recuerda haberse golpeado la cabeza","Ha tenido accidentes que involucran golpes en la cabeza","Golpes en la cabeza"],
                "cirugía":["Ha tenido operaciones en la cabeza o cuello","Se ha realizado operaciones de cabeza cuello","Ha tenido operaciones en la cabeza"],
                "antecedentes":["Tiene familiares con problemas auditivos","Tiene familia con pérdida auditiva","En su familia hay personas con hipoacusia","Tiene familia con sordera","Tiene familia sorda"],
                "enfermedades":["Tiene enfermedades crónicas","Tiene enfermedades de base","padece de enfermedades como hipertensión, diabetes u otras"],
                "medicamentos":["Toma algún medicamento","Toma alguna pastilla","Toma algún fármaco con regularidad"], 
                "exposición":["Se encuentra expuesto a ruidos fuertes","Donde vive esta expuesto a mucho ruido","Donde estudia hay mucho ruido","En su vida cotidiana esta expuesto a ruidos fuertes"],
                "despedida": ["Adiós","Hasta luego","Chao","Nos vemos"], 
                "agradecimiento": ["Gracias", "Te agradezco", "Muchas gracias","Gracias por la ayuda"]}


        self.RESPUESTAS = {
                "saludo":["¡Hola!","Buenas tardes","Buenos dias"], 
                "estado":["Mas o menos","No muy bien"],
                "nombre":["Javiera","Matias","Nicol","Armando"], 
                "edad": ["7 años"], 
                "motivo":["Siento molestia en los oidos"], 
                "evolucion":["Hace una semana mas o menos"],
                "oido":["en el izquierdo"],
                "supuracion":["Si","en la noche dejo liquido en la cabecera"],
                "tinnitus":["Si, en el oído izquierdo","Si, un pitido en mi oido izquierdo","Si, un zumbido en el oido izquierdo"],
                "traumas":["No recuerdo","tutor a cargo responde que no"],
                "Cirugias":["Tutor indica que le sacaron las amigdalas hace un tiempo"],
                "antecedentes":["Tutor indica que no","Nadie","Mi abuelo quedo sordo por la edad"],
                "enfermedades":["No","Ninguna enfermedad indica el tutor"],
                "medicamentos":["no"],
                "exposicion":["Solo el ruido del colegio"],
                "despedida":["Hasta pronto","Hasta luego","Chao"],
                "agradecimiento":["Un gusto","Un placer","Gracias a usted"], 
                "default": ["Lo siento no entiendo","Puedes replantearlo","No estoy seguro de lo que me pregunta","Podrías explicarlo de nuevo", "Mis disculpas no comprendo","Podrías ser más claro"]}



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
