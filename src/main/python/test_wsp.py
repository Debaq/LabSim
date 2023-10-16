import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout,QHBoxLayout, QWidget, QTextEdit, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QUrl, QTimer, QEvent
from test_chatbot import SimpleChatbot

class ChatWindow(QWidget):  # Cambia QMainWindow por QWidget aquí
    def __init__(self, parent=None):  # Añade parent=None para permitir la especificación del widget padre
        super().__init__(parent)  # Pasa el widget padre al inicializador


        # Inicializar los widgets
        self.browser = QWebEngineView()
        self.browser.setHtml("""
        <html>
        <head>
            <style>
                body { background-color: #e5ddd5; margin: 0; padding: 10px; font-family: Arial, sans-serif; }
                .message { margin: 5px 0; }
                .bot { text-align: left; }
                .mine { text-align: right; }
                .bubble { display: inline-block; border-radius: 7px; padding: 5px 10px; max-width: 70%; }
                .mine .bubble { background-color: #34b7f1; }
                .bot .bubble { background-color: #dcf8c6; }
            </style>
        </head>
        <body>
        </body>
        </html>
        """)
        
        self.input_area = QTextEdit(self)
        self.send_button = QPushButton("►", self)
        self.send_button.clicked.connect(self.send_message)

        # Dentro de __init__ de ChatWindow
        font_metrics = self.input_area.fontMetrics()
        line_spacing = font_metrics.lineSpacing()
        self.input_area.setMaximumHeight(line_spacing + 10)  # 10 es un pequeño margen
        self.input_area.textChanged.connect(self.adjust_input_height)
        self.input_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Diseño
        layout = QVBoxLayout()
        input_chat = QHBoxLayout()
        layout.addWidget(self.browser, 1)
        input_chat.addWidget(self.input_area, 0)
        input_chat.addWidget(self.send_button, 0)
        layout.addLayout(input_chat)

        container = QWidget()
        container.setLayout(layout)
        self.setLayout(layout)
        
        # Configurar ventana
        self.setWindowTitle("WhatsApp Style Chat with QWebEngineView")
        self.setGeometry(100, 100, 400, 600)

        self.input_area.installEventFilter(self)
        
        self.typing_timer = QTimer(self)
        self.typing_timer.timeout.connect(self.show_typing_effect)
        self.dot_count = 0
        self.bot = SimpleChatbot()
        self.last_message = ""
        
        
    def auto_reply(self):
        # Iniciar el efecto de "escribiendo..."
        self.typing_timer.start(500)  # Actualizar cada medio segundo


    def show_typing_effect(self):
        self.dot_count += 1
        dots = "." * (self.dot_count % 4)
        typing_message = f"Escribiendo{dots}"
        
        # Aquí reemplazamos el último mensaje (que es el efecto de escribiendo) con el nuevo efecto
        # Si es la primera vez, simplemente lo añadimos
        if self.dot_count == 1:
            self.append_message("Bot", typing_message, "bot")
        else:
            js_code = f"""
            var messages = document.getElementsByClassName('message');
            var lastMessage = messages[messages.length - 1];
            lastMessage.children[1].innerHTML = '{typing_message}';
            """
            self.browser.page().runJavaScript(js_code)

        # Después de 5 ciclos (2.5 segundos), removemos el mensaje de "Escribiendo..."
        # y mostramos el mensaje real, luego detenemos el temporizador
        if self.dot_count >= 1:
            js_code_remove_typing = """
            var messages = document.getElementsByClassName('message');
            var lastMessage = messages[messages.length - 1];
            lastMessage.remove();
            """
            self.browser.page().runJavaScript(js_code_remove_typing)
            
            self.typing_timer.stop()
            self.dot_count = 0
            #self.append_message("Bot", "¡Hola! Esta es una respuesta automática.", "bot")
            self.response_bot()



    def adjust_input_height(self):
        font_metrics = self.input_area.fontMetrics()
        line_spacing = font_metrics.lineSpacing()
        lines = len(self.input_area.toPlainText().split('\n'))
        if lines <= 3:  # Limitar a 3 líneas
            self.input_area.setMaximumHeight(line_spacing * lines + 10)
        else:
            self.input_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    
    def response_bot(self):
        message = self.last_message
        respuesta_bot = self.bot.obtener_respuesta(message)
        self.append_message("Bot", f"{respuesta_bot}", "bot")
        self.last_message = ""


    def send_message(self):
        message = self.input_area.toPlainText()
        if message:
            self.append_message("Yo", message, "mine")
            self.last_message=message
            self.input_area.clear()
            QTimer.singleShot(100, self.auto_reply)  # Pequeño retraso antes de empezar el efecto
            
    def append_message(self, sender, message, classtype):
        avatar_base64 = "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"
        if sender == "Yo":
            message_content = f"""
            <div class="message {classtype}">
                <div class='bubble'>{message}</div>
            </div>
            """
        else:
            message_content = f"""
            <div class="message {classtype}">
                <img src="data:image/png;base64,{avatar_base64}" style="width: 30px; height: 30px; border-radius: 50%; vertical-align: middle; margin-right: 5px;">
                <div class='bubble'>{message}</div>
            </div>
            """
        js_code = f"""
        var div = document.createElement("div");
        div.innerHTML = `{message_content}`;
        document.body.appendChild(div);
        setTimeout(function() {{ window.scrollTo(0, document.body.scrollHeight); }}, 0);
        """
        self.browser.page().runJavaScript(js_code)


    def eventFilter(self, source, event):
        if (source == self.input_area and event.type() == QEvent.KeyPress and event.key() in [Qt.Key_Return, Qt.Key_Enter] and not event.modifiers() & Qt.ShiftModifier):
            self.send_message()
            return True
        return super(ChatWindow, self).eventFilter(source, event)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = ChatWindow()
    window.show()

    sys.exit(app.exec())
