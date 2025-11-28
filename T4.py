import sys
import cv2
import mediapipe as mp
import numpy as np
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap

# --- Funções de Cálculo do MediaPipe ---


# Inicializa o MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
# Ajuste 'min_detection_confidence' se a detecção estiver falhando
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def calcular_angulo(a, b, c):
    """Calcula o ângulo entre três pontos (landmarks)"""
    a = np.array(a)  # Primeiro ponto
    b = np.array(b)  # Ponto do meio (vértice)
    c = np.array(c)  # Terceiro ponto
    
    # Calcula os vetores
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
              np.arctan2(a[1] - b[1], a[0] - b[0])
    
    # Converte para graus
    angle = np.abs(radians * 180.0 / np.pi)
    
    # Garante que o ângulo esteja entre 0 e 180
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

# --- Classe Principal da Aplicação ---

class ContadorExercicioApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Carrega a interface do usuário (UI) a partir do arquivo
        uic.loadUi("tela_exercicio.ui", self)
        
        # Variáveis de estado
        self.cap = None
        self.timer = None
        self.camera_ligada = False
        self.exercicio_iniciado = False
        
        self.exercicio_selecionado = 0  # 1: Rosca, 2: Agachamento, 3: Polichinelo, 4: Abdominal
        self.meta_repeticoes = 0
        self.contador_repeticoes = 0
        self.estado_exercicio = None  # "subindo", "descendo", "baixo", etc.

        # Conectar os botões às suas funções
        self.btn_start_camera.clicked.connect(self.alternar_camera)
        self.btn_initial_position.clicked.connect(self.definir_posicao_inicial)
        self.btn_start_exercise.clicked.connect(self.alternar_exercicio)
        
        # Desabilitar botões de exercício até a câmera ligar
        self.btn_initial_position.setEnabled(False)
        self.btn_start_exercise.setEnabled(False)

    def alternar_camera(self):
        """Liga ou desliga a câmera."""
        if not self.camera_ligada:
            # Tenta ligar a câmera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                QMessageBox.critical(self, "Erro Câmera", "Não foi possível abrir a câmera.")
                return
            
            # Inicia o QTimer para atualizar os frames
            self.timer = QTimer()
            self.timer.timeout.connect(self.atualizar_frame)
            self.timer.start(30)  # Aprox. 33 FPS

            self.btn_start_camera.setText("DESLIGAR CÂMERA")
            self.btn_start_camera.setStyleSheet("background-color: rgb(200, 50, 50); color: white;")
            self.camera_ligada = True
            
            # Habilitar botões
            self.btn_initial_position.setEnabled(True)
            self.btn_start_exercise.setEnabled(True)
        else:
            # Desligar a câmera
            if self.timer:
                self.timer.stop()
            if self.cap:
                self.cap.release()
            
            self.camera_feed.clear()
            self.camera_feed.setText("CÂMERA DESLIGADA")
            self.btn_start_camera.setText("LIGAR CÂMERA")
            self.btn_start_camera.setStyleSheet("") # Reseta estilo
            self.camera_ligada = False
            
            # Se a câmera for desligada, para o exercício também
            if self.exercicio_iniciado:
                self.alternar_exercicio() 
                
            # Desabilitar botões
            self.btn_initial_position.setEnabled(False)
            self.btn_start_exercise.setEnabled(False)

    def definir_posicao_inicial(self):
        """Define (reseta) a contagem e o estado para o início."""
        if not self.camera_ligada:
            QMessageBox.warning(self, "Aviso", "Ligue a câmera primeiro.")
            return

        self.contador_repeticoes = 0
        
        # Define um estado inicial padrão (ex: braço/perna esticados)
        if self.exercicio_selecionado == 4: # Abdominal começa "deitado"
            self.estado_exercicio = "baixo"
        else: # Outros começam "em pé"
            self.estado_exercicio = "descendo" # Estado "baixo" ou "esticado"
        
        QMessageBox.information(self, "Posição Definida", 
                                "Posição inicial definida! O contador foi zerado. "
                                "Inicie o exercício.")

    def alternar_exercicio(self):
        """Inicia ou para a contagem do exercício."""
        if not self.camera_ligada:
            QMessageBox.critical(self, "Erro", "Ligue a câmera antes de iniciar o exercício.")
            return

        if not self.exercicio_iniciado:
            # --- Iniciar Exercício ---
            
            # 1. Identificar o exercício selecionado
            if self.radio_ex1.isChecked():
                self.exercicio_selecionado = 1  # Rosca Direta
            elif self.radio_ex2.isChecked():
                self.exercicio_selecionado = 2  # Agachamento
            elif self.radio_ex3.isChecked():
                self.exercicio_selecionado = 3  # Polichinelo
            elif self.radio_ex4.isChecked():
                self.exercicio_selecionado = 4  # Abdominal

            # 2. Ler meta de repetições
            self.meta_repeticoes = self.spin_repetitions.value()
            
            # 3. Resetar contador e estado
            self.contador_repeticoes = 0
            # Define o estado inicial correto para cada exercício
            if self.exercicio_selecionado == 4: # Abdominal começa "deitado"
                self.estado_exercicio = "baixo"
            else: # Outros começam "em pé"
                self.estado_exercicio = "descendo" # Estado "baixo" ou "esticado"
            
            # 4. Atualizar estado e UI
            self.exercicio_iniciado = True
            self.btn_start_exercise.setText("PARAR EXERCÍCIO")
            self.btn_start_exercise.setStyleSheet("background-color: rgb(200, 0, 0); color: white;")
            
            # Desabilitar controles enquanto se exercita
            self.group_exercicios.setEnabled(False)
            self.group_repeticoes.setEnabled(False)
            self.btn_initial_position.setEnabled(False)
            
        else:
            # --- Parar Exercício ---
            self.exercicio_iniciado = False
            self.btn_start_exercise.setText("INICIAR EXERCÍCIO")
            # Restaura o estilo original do .ui
            self.btn_start_exercise.setStyleSheet("background-color: rgb(4, 128, 56); color: white;")

            # Habilitar controles
            self.group_exercicios.setEnabled(True)
            self.group_repeticoes.setEnabled(True)
            self.btn_initial_position.setEnabled(True)

            QMessageBox.information(self, "Exercício Finalizado", 
                                    f"Parabéns! Você completou {self.contador_repeticoes} repetições.")

    def atualizar_frame(self):
        """Função principal chamada pelo Timer. Lê, processa e exibe o frame."""
        ret, frame = self.cap.read()
        if not ret:
            return
            
        # Redimensiona o frame para o tamanho do QLabel (camera_feed)
        frame = cv2.resize(frame, (self.camera_feed.width(), self.camera_feed.height()))
        
        # Inverte a imagem horizontalmente (efeito espelho)
        frame = cv2.flip(frame, 1)
        
        # Processamento MediaPipe
        imagem_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imagem_rgb.flags.writeable = False
        resultado = pose.process(imagem_rgb)
        imagem_rgb.flags.writeable = True
        frame_processado = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2BGR)

        # Lógica de contagem (apenas se o exercício estiver ativo)
        try:
            if self.exercicio_iniciado and resultado.pose_landmarks:
                landmarks = resultado.pose_landmarks.landmark
                
                # --- LÓGICA EXERCÍCIO 1: ROSCA DIRETA (Braço Direito) ---
                if self.exercicio_selecionado == 1:
                    # Obter coordenadas (Ombro, Cotovelo, Pulso)
                    ombro = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    cotovelo = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                                landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                    pulso = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                    
                    # Calcular ângulo do cotovelo
                    angulo = calcular_angulo(ombro, cotovelo, pulso)
                    
                    # Lógica de Contagem
                    if angulo > 160 and self.estado_exercicio == "subindo":
                        self.estado_exercicio = "descendo"
                    if angulo < 40 and self.estado_exercicio == "descendo":
                        self.estado_exercicio = "subindo"
                        self.contador_repeticoes += 1
                
                # --- LÓGICA EXERCÍCIO 2: AGACHAMENTO (Perna Direita) ---
                elif self.exercicio_selecionado == 2:
                    # Obter coordenadas (Quadril, Joelho, Tornozelo)
                    quadril = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                               landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    joelho = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                    tornozelo = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                                 landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]

                    # Calcular ângulo do joelho
                    angulo = calcular_angulo(quadril, joelho, tornozelo)

                    # Lógica de Contagem
                    if angulo > 170 and self.estado_exercicio == "subindo":
                        self.estado_exercicio = "descendo"
                    if angulo < 90 and self.estado_exercicio == "descendo":
                        self.estado_exercicio = "subindo"
                        self.contador_repeticoes += 1
                        
                # --- LÓGICA EXERCÍCIO 3: POLICHINELO (Braço Direito) ---
                elif self.exercicio_selecionado == 3:
                    # Obter coordenadas (Quadril, Ombro, Pulso)
                    # Mede o ângulo do braço em relação ao tronco
                    quadril = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                               landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    ombro = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    pulso = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                    
                    # Calcular ângulo do braço
                    angulo = calcular_angulo(quadril, ombro, pulso)
                    
                    # Lógica de Contagem (estado "descendo" = braços para baixo)
                    if angulo < 40 and self.estado_exercicio == "subindo":
                        self.estado_exercicio = "descendo" # Braços voltaram para baixo
                    if angulo > 140 and self.estado_exercicio == "descendo":
                        self.estado_exercicio = "subindo" # Braços levantaram
                        self.contador_repeticoes += 1
                        
                # --- LÓGICA EXERCÍCIO 4: ABDOMINAL (Lado Direito) ---
                elif self.exercicio_selecionado == 4:
                    # Obter coordenadas (Ombro, Quadril, Joelho)
                    # Mede o ângulo do tronco em relação à coxa
                    ombro = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    quadril = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                               landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    joelho = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]

                    # Calcular ângulo do quadril (flexão do tronco)
                    angulo = calcular_angulo(ombro, quadril, joelho)

                    # Lógica de Contagem (estado "baixo" = deitado)
                    if angulo > 150 and self.estado_exercicio == "subindo":
                        self.estado_exercicio = "baixo" # Deitou
                    if angulo < 90 and self.estado_exercicio == "baixo":
                        self.estado_exercicio = "subindo" # Subiu (contrai o abdômen)
                        self.contador_repeticoes += 1

        except Exception as e:
            # print(f"Erro ao processar landmarks: {e}") # Descomente para depurar
            pass # Continua mesmo se o corpo sair da tela

        # Desenhar os landmarks na imagem
        if resultado.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame_processado, 
                resultado.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
            )

        # Exibir contagem e estado na tela
        if self.exercicio_iniciado:
            # Caixa de status (Fundo preto semi-transparente)
            cv2.rectangle(frame_processado, (0, 0), (450, 70), (20, 20, 20), -1)
            
            # Texto REPETIÇÕES
            cv2.putText(frame_processado, 'REPETICOES', (15, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame_processado, str(self.contador_repeticoes), (20, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Texto ESTADO
            cv2.putText(frame_processado, 'ESTADO', (200, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Ajusta o nome do estado para Polichinelo/Abdominal
            estado_display = self.estado_exercicio
            if self.exercicio_selecionado == 3: # Polichinelo
                estado_display = "CIMA" if self.estado_exercicio == "subindo" else "BAIXO"
            elif self.exercicio_selecionado == 4: # Abdominal
                estado_display = "SUBIU" if self.estado_exercicio == "subindo" else "DEITADO"
            elif self.exercicio_selecionado == 1 or self.exercicio_selecionado == 2:
                estado_display = "CONTRAIDO" if self.estado_exercicio == "subindo" else "RELAXADO"

            cv2.putText(frame_processado, estado_display.upper(), (205, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Checar se atingiu a meta
            if self.contador_repeticoes >= self.meta_repeticoes:
                self.alternar_exercicio() # Para o exercício automaticamente

        # Exibir o frame processado na interface
        self.exibir_frame_na_tela(frame_processado)

    def exibir_frame_na_tela(self, frame):
        """Converte o frame (BGR) do OpenCV para QPixmap e exibe no QLabel 'camera_feed'."""
        # Converte o frame BGR para RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        # Calcula os bytes por linha
        bytes_per_line = ch * w
        # Cria a QImage
        img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        # Exibe a QImage no QLabel
        self.camera_feed.setPixmap(QPixmap.fromImage(img))

    def closeEvent(self, event):
        """Função chamada quando a janela é fechada."""
        # Garantir que a câmera seja liberada ao fechar
        if self.timer:
            self.timer.stop()
        if self.cap:
            self.cap.release()
        
        print("Câmera liberada. Encerrando aplicação.")
        # Libera o objeto 'pose' do MediaPipe
        pose.close() 
        event.accept()

# --- Execução da Aplicação ---
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    janela = ContadorExercicioApp()
    janela.show()
    sys.exit(app.exec_())