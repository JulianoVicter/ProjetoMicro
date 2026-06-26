from pyqtgraph.Qt import *
import numpy as np
import sys
import pyqtgraph as pg
import serial


print("PyQtGraph Version: ", pg.__version__)
print(">>> RODANDO janela_Graf_esp32.py (conversao ADC->tensao 0..3.3 V ATIVA) <<<")

# ---- Calibracao do ADC (ESP32, 12 bits) ----
V_REF = 3.3
ADC_MAX = 4095


def calcula_media(val):
    return sum(val) / len(val)


class JanelaOciloscopio(QtWidgets.QMainWindow):
    # Construtor da classe e declaracao de objetos
    contBotao1 = 0  # Contador para o botao 1
    estiloSliderAmplitude = """
        QSlider {
            background-color: #b4452d;
            border: 2px solid #000000;
            padding: 6px;
        }

        QSlider::groove:horizontal {
            background: #b4452d;
            border: 2px solid #000000;
            height: 8px;
            border-radius: 0px;
        }

        QSlider::handle:horizontal {
            background: white;
            border: 2px solid #000000;
            width: 18px;
            height: 18px;
            margin-top: -7px;
            margin-bottom: -7px;
            border-radius: 0px;
        }

        QSlider::sub-page:horizontal {
            background: white;
            border: 1px solid #000000;
        }

        QSlider::add-page:horizontal {
            background: #7a2e1d;
            border: 1px solid #000000;
        }
        """
    estiloTextoAmplitude = """
            background-color: #b4452d;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #000000;
        padding: 6px;
        qproperty-alignment: AlignCenter;
        """
    estiloBotoeReset = """
    QPushButton {
        background-color: #000080;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #000000;
        padding: 10px;
    }
"""
    estiloBotaoCor = """
    QPushButton {
        background-color:#ff8838 ;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #000000;
        padding: 10px;
    }
"""
    estiloTextoEscala = """
            background-color: green;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #000000;
        padding: 6px;
        qproperty-alignment: AlignCenter;
        """
    estiloSlider = """
        QSlider {
            background-color: green;
            border: 2px solid #000000;
            padding: 6px;
        }

        QSlider::groove:horizontal {
            background: green;
            border: 2px solid #000000;
            height: 8px;
            border-radius: 0px;
        }

        QSlider::handle:horizontal {
            background: white;
            border: 2px solid #000000;
            width: 18px;
            height: 18px;
            margin-top: -7px;
            margin-bottom: -7px;
            border-radius: 0px;
        }

        QSlider::sub-page:horizontal {
            background: white;
            border: 1px solid #000000;
        }

        QSlider::add-page:horizontal {
            background: #006400;
            border: 1px solid #000000;
        }
        """
    estiloTextoMedia = """
        background-color: DarkCyan;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #000000;
        padding: 6px;
        qproperty-alignment: AlignCenter;
        """
    estiloSliderDeslocamento = """
        QSlider {
            background-color: #5e3a87;
            border: 2px solid #000000;
            padding: 6px;
        }

        QSlider::groove:vertical {
            background: #5e3a87;
            border: 2px solid #000000;
            width: 8px;
            border-radius: 0px;
        }

        QSlider::handle:vertical {
            background: white;
            border: 2px solid #000000;
            width: 18px;
            height: 18px;
            margin-left: -7px;
            margin-right: -7px;
            border-radius: 0px;
        }

        QSlider::sub-page:vertical {
            background: #3a2456;
            border: 1px solid #000000;
        }

        QSlider::add-page:vertical {
            background: white;
            border: 1px solid #000000;
        }
        """

    corGrafico = '#FF0000'   # Cor do grafico
    media = 0

    # baud 115200 (igual ao firmware). Ajuste a porta com 'ls /dev/cu.*'
    porta = serial.Serial(port='/dev/cu.usbserial-0001', baudrate=115200, timeout=0.1)

    def __init__(self):
        super().__init__()  # Construtor da classe pai

        # Defs da tela
        self.setWindowTitle("Ociloscopio")  # Titulo da janela
        self.resize(1080, 640)  # Tamanho da janela

        # Wiget principal da janela
        self.widget_central = QtWidgets.QWidget()  # Criacao do widget central da janela
        self.setCentralWidget(self.widget_central)  # Setar o widget central na janela

        # Leyout horizontal
        self.leyout = QtWidgets.QHBoxLayout()  # Criacao do layout horizontal
        self.widget_central.setLayout(self.leyout)  # Setar o layout no widget central

        # Grafico
        self.grafico = pg.PlotWidget()  # Criacao do grafico

        # Area ao lado
        self.painel_lateral = QtWidgets.QWidget()  # Criacao do painel lateral

        self.layout_lateral = QtWidgets.QVBoxLayout()  # Criacao do layout vertical para o painel lateral
        self.painel_lateral.setLayout(self.layout_lateral)  # Setar o layout no painel lateral

        self.painel_horizontal = QtWidgets.QWidget()
        self.layout_horizontal = QtWidgets.QVBoxLayout()
        self.painel_horizontal.setLayout(self.layout_horizontal)

        # ================= BASE DE TEMPO (eixo X) =================
        # fs = taxa de amostragem REAL do ADC no firmware (Hz). dt_ms e derivado dela
        # e e FIXO: nao depende de nenhum slider. E o que mantem o eixo X sincronizado
        # com o sinal real (mexer na escala nao muda o espacamento das amostras).
        self.fs = 1000.0                   # Hz  <-- TROCAR pela taxa real do ESP32
        self.dt_ms = 1000.0 / self.fs      # ms entre amostras (FIXO)
        self.n_div = 10                    # numero de divisoes horizontais visiveis
        self.ms_por_div = 25               # escala de tempo inicial (ms/div)

        # ================= AQUISICAO (frame a frame) =================
        self._buf = ''                     # pedaco de linha incompleta entre ticks
        self.N = 256                       # amostras por pacote (igual ao firmware)
        self.frame = []                    # acumula o pacote em andamento
        self.largura_pacote = self.N * self.dt_ms   # duracao total de 1 pacote (ms)

        # ================= AMPLITUDE (eixo Y) =================
        # Exibicao em steps: a base fica ANCORADA no 0 e o TOPO desce em steps.
        # Topo menor -> a mesma onda ocupa mais altura da tela -> "estica pra cima".
        # Isso NAO toca nos dados plotados, so muda a janela de visualizacao (setYRange).
        self.y_min = 0.0                            # base ancorada no zero (nao muda)
        self.escalas_topo = [V_REF, 2.0, 1.0, 0.5]  # topo do eixo Y (V); menor = mais esticado
        self.idx_amplitude = 0                      # comeca no topo 3.3 V (onda no fundo)

        # Curva criada uma vez. Depois so atualizamos com setData.
        self.curva = self.grafico.plot([], [], pen=self.corGrafico)

        # Timer que dispara a leitura periodicamente
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.receber_serial)
        self.timer.start(20)   # 20 ms -> ~50 ciclos de leitura por segundo

        # ===================== BOTOES / SLIDERS =====================

        # Botao - Resetar
        self.Resetar = QtWidgets.QPushButton("Resetar")
        self.Resetar.clicked.connect(self.Resetar_clicado)
        self.layout_lateral.addWidget(self.Resetar)
        self.Resetar.setStyleSheet(self.estiloBotoeReset)

        self.layout_lateral.addSpacing(20)

        # Slider Amplitude (escala vertical em steps)
        self.texto_amplitude = QtWidgets.QLabel("Slider Amplitude")
        self.texto_amplitude.setStyleSheet(self.estiloTextoAmplitude)
        self.layout_lateral.addWidget(self.texto_amplitude)

        self.slider_amplitude = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_amplitude.setMinimum(0)                               # indice na lista
        self.slider_amplitude.setMaximum(len(self.escalas_topo) - 1)      # ultimo indice
        self.slider_amplitude.setSingleStep(1)
        self.slider_amplitude.setValue(0)
        self.slider_amplitude.setStyleSheet(self.estiloSliderAmplitude)

        self.layout_lateral.addWidget(self.slider_amplitude)
        self.slider_amplitude.valueChanged.connect(self.slider_amplitude_acao)
        self.val_slider_amplitude = self.slider_amplitude.value()

        self.layout_lateral.addSpacing(20)

        # Slider offset (desloca a janela vertical pra cima/baixo)
        self.slider_offset = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.slider_offset.setMaximum(100)
        self.slider_offset.setMinimum(-100)
        self.slider_offset.setStyleSheet(self.estiloSliderDeslocamento)
        self.layout_horizontal.addWidget(self.slider_offset)

        self.slider_offset.valueChanged.connect(self.slider_offset_acao)

        self.layout_horizontal.addStretch()

        # Slider escala X (escala de tempo, ms/div)
        self.texto_slider = QtWidgets.QLabel("Slider da Escala")
        self.texto_slider.setStyleSheet(self.estiloTextoEscala)
        self.layout_lateral.addWidget(self.texto_slider)

        self.slider_escala = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_escala.setMinimum(1)      # 1 ms/div minimo
        self.slider_escala.setMaximum(50)     # 50 ms/div maximo
        self.slider_escala.setSingleStep(1)
        self.slider_escala.setValue(self.ms_por_div)
        self.slider_escala.setStyleSheet(self.estiloSlider)

        self.layout_lateral.addWidget(self.slider_escala)
        self.slider_escala.valueChanged.connect(self.slider_escala_acao)
        self.val_slider = self.slider_escala.value()

        self.layout_lateral.addSpacing(20)

        # Seletor de cor do grafico
        self.botao_cor = QtWidgets.QPushButton("Selecionar Cor do Grafico")
        self.botao_cor.clicked.connect(self.selecionar_cor_clicado)
        self.botao_cor.setStyleSheet(self.estiloBotaoCor)
        self.caixa_texto_cor = QtWidgets.QColorDialog()
        self.layout_lateral.addWidget(self.botao_cor)

        self.layout_lateral.addSpacing(20)

        # Media do grafico
        self.media_graf = QtWidgets.QLabel(f"Media do grafico: {self.media}")
        self.media_graf.setStyleSheet(self.estiloTextoMedia)
        self.layout_lateral.addWidget(self.media_graf)

        self.layout_lateral.addStretch()

        # Proporcao do grafico e do painel lateral
        self.leyout.addWidget(self.grafico, 7)
        self.leyout.addWidget(self.painel_lateral, 2)
        self.leyout.addWidget(self.painel_horizontal, 1)

        self.configurar_grafico()  # Configurar o grafico
        self.atualizar_grafico()   # define escala X/Y antes do primeiro tick

    def configurar_grafico(self):
        self.grafico.setLabel('left', 'Amplitude', units='V')  # eixo y do grafico
        self.grafico.setLabel('bottom', 'Tempo', units='ms')   # eixo x do grafico
        self.grafico.showGrid(x=True, y=True)  # Mostrar grid no grafico
        self.grafico.enableAutoRange(axis='y', enable=False)  # impede o pyqtgraph de reescalar o Y sozinho
        self.grafico.enableAutoRange(axis='x', enable=False)  # idem no X

    def Resetar_clicado(self):
        self.slider_escala.setValue(25)      # 25 ms/div
        self.slider_amplitude.setValue(0)    # idx 0 = topo 3.3 V (sem esticar)
        self.slider_offset.setValue(0)
        self.frame = []
        self.curva.setData([], [])
        self.corGrafico = '#FF0000'
        self.curva.setPen(self.corGrafico)

    def selecionar_cor_clicado(self):
        cor = self.caixa_texto_cor.getColor()
        if cor.isValid():
            self.corGrafico = cor
            self.curva.setPen(self.corGrafico)   # so troca a caneta, sem replotar

    def atualizar_eixo_y(self):
        # Escala vertical em steps. So mexe na EXIBICAO (setYRange), nunca nos dados.
        # base ancorada no 0; topo desce conforme o slider sobe -> onda estica pra cima.
        self.idx_amplitude = self.slider_amplitude.value()
        y_topo = self.escalas_topo[self.idx_amplitude]

        # offset desloca a janela inteira pra cima/baixo (pan). Em 0, base fica no zero.
        # Se a direcao parecer invertida, troque o sinal de 'desloc'.
        val_off = self.slider_offset.value()
        desloc = (val_off / 100.0) * y_topo

        self.grafico.setYRange(self.y_min + desloc, y_topo + desloc, padding=0)

        # feedback do valor atual no proprio rotulo do slider
        self.texto_amplitude.setText(f"Amplitude: topo {y_topo} V")

    def atualizar_grafico(self):
        # --- Eixo X (escala de tempo em ms/div) ---
        self.ms_por_div = self.slider_escala.value()         # valor do slider = ms/div
        largura_ms = self.n_div * self.ms_por_div            # janela total = n_div * (ms/div)

        self.grafico.setXRange(0, largura_ms, padding=0)

        # trava o grid: 1 linha por divisao, cada uma valendo ms_por_div
        eixo_x = self.grafico.getAxis('bottom')
        ticks = [(d * self.ms_por_div, str(d * self.ms_por_div)) for d in range(self.n_div + 1)]
        eixo_x.setTicks([ticks])
        self.texto_slider.setText(f"Escala: {self.ms_por_div} ms/div")

        # --- Eixo Y (amplitude) ---
        self.atualizar_eixo_y()

    def slider_escala_acao(self):
        self.atualizar_grafico()

    def slider_amplitude_acao(self):
        self.atualizar_grafico()

    def slider_offset_acao(self):
        self.atualizar_grafico()

    def receber_serial(self):
        n = self.porta.in_waiting
        if n:
            self._buf += self.porta.read(n).decode('ascii', errors='ignore')

        partes = self._buf.split('\n')
        self._buf = partes.pop()        # ultimo pedaco = linha incompleta, volta pro buffer

        for linha in partes:
            linha = linha.strip()       # tira o \r do \r\n

            if linha.isdigit():
                bruto = int(linha)
                if 0 <= bruto <= 4095:
                    self.frame.append(bruto)
                    if len(self.frame) >= self.N:
                        y = [(b / ADC_MAX) * V_REF for b in self.frame]
                        x = [i * self.dt_ms for i in range(len(self.frame))]
                        self.curva.setData(x, y)
                        self.media = calcula_media(y)
                        self.media_graf.setText(f"Media do grafico: {self.media:.4f} V")
                        self.frame = []
            else:
                if '_Update' in linha and self.frame:
                    self.frame = []     # ressincroniza no marcador do GxEPD2


app = QtWidgets.QApplication(sys.argv)  # Criacao da aplicacao com a sys

janela = JanelaOciloscopio()  # Criacao da janela do osciloscopio
janela.show()  # Mostrar a janela do osciloscopio

sys.exit(app.exec_())  # Executar a aplicacao