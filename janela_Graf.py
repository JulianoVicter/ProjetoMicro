from pyqtgraph.Qt import *
import numpy as np
import sys
import pyqtgraph as pg
import serial
import struct


print("PyQtGraph Version: ", pg.__version__)

# ---- Formato do pacote binario vindo do ESP32 ----
HEADER_FMT = '<Hff'                            # quantidadeAmostras (uint16), taxaReal (float), frequenciaDetectada (float)
HEADER_SIZE = struct.calcsize(HEADER_FMT)      # 10 bytes
N_AMOSTRAS = 256
TAMANHO_PACOTE = HEADER_SIZE + N_AMOSTRAS * 2  # 10 + 512 = 522 bytes

# ---- Calibracao do ADC ----
V_REF = 3.3        # tensao de referencia do ADC
ADC_MAX = 4095     # ADC de 12 bits -> 0..4095


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

    escalax = [-10, 10]  # Escala do eixo x do grafico
    escalay = [-1.5, 1.5]  # Escala do eixo y do grafico
    # Larguras/alturas BASE (referencia fixa, nunca muda)
    base_meia_largura = 10   # eixo X
    base_meia_altura = 1.5   # eixo Y: [-1.5, 1.5]
    largura_janela = 10.0    # segundos visiveis no X
    corGrafico = '#FF0000'   # Cor do grafico
    media = 0
    taxa_real = 1000.0       # taxa de amostragem (Hz); default ate chegar o 1o pacote

    porta = serial.Serial(port='/dev/cu.usbserial-0001', baudrate=9600, timeout=0.1)

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

        # ---- Aquisicao por pacotes binarios ----
        # Curva criada uma vez. Depois so atualizamos com setData.
        self.curva = self.grafico.plot([], [], pen=self.corGrafico)

        # Timer que dispara a leitura periodicamente
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.receber_serial)
        self.timer.start(20)   # 20 ms -> tenta ler um pacote a cada ciclo

        # Botoes

        # Botao 3 - Resetar
        self.Resetar = QtWidgets.QPushButton("Resetar")  # Criacao do botao 3
        self.Resetar.clicked.connect(self.Resetar_clicado)  # Conectar o clique do botao 3
        self.layout_lateral.addWidget(self.Resetar)  # Adicionar o botao 3 ao layout lateral
        self.Resetar.setStyleSheet(self.estiloBotoeReset)  # Aplicar o estilo ao botao 3

        self.layout_lateral.addSpacing(20)  # Espacamento

        # Slider Amplitude
        self.texto_amplitude = QtWidgets.QLabel("Slider Amplitude")
        self.texto_amplitude.setStyleSheet(self.estiloTextoAmplitude)
        self.layout_lateral.addWidget(self.texto_amplitude)

        self.slider_amplitude = QtWidgets.QSlider(QtCore.Qt.Horizontal)  # Slider de amplitude (zoom vertical)
        self.slider_amplitude.setMinimum(-100)  # Valor minimo do slider
        self.slider_amplitude.setMaximum(100)  # Valor maximo do slider
        self.slider_amplitude.setStyleSheet(self.estiloSliderAmplitude)

        self.layout_lateral.addWidget(self.slider_amplitude)
        self.slider_amplitude.valueChanged.connect(self.slider_amplitude_acao)  # Conectar mudanca de valor
        self.val_slider_amplitude = self.slider_amplitude.value()  # Valor do slider de amplitude

        self.layout_lateral.addSpacing(20)

        # Slider offset
        self.slider_offset = QtWidgets.QSlider(QtCore.Qt.Vertical)  # Criacao do slider
        self.slider_offset.setMaximum(100)
        self.slider_offset.setMinimum(-100)
        self.slider_offset.setStyleSheet(self.estiloSliderDeslocamento)
        self.layout_horizontal.addWidget(self.slider_offset)

        self.slider_offset.valueChanged.connect(self.slider_offset_acao)
        

        self.slider_offset.valueChanged.connect(self.slider_offset_acao)

        # Caixa de texto com o valor do offset
        self.texto_offset = QtWidgets.QLabel("Offset: 0.0 V")
        self.texto_offset.setStyleSheet(self.estiloTextoMedia)
        self.layout_horizontal.addWidget(self.texto_offset)

        self.layout_horizontal.addStretch()

        # Slider escala x
        self.texto_slider = QtWidgets.QLabel("Slider da Escala")
        self.texto_slider.setStyleSheet(self.estiloTextoEscala)
        self.layout_lateral.addWidget(self.texto_slider)

        self.slider_escala = QtWidgets.QSlider(QtCore.Qt.Horizontal)  # Slider para a escala do eixo x
        self.slider_escala.setMinimum(-100)  # Valor minimo do slider
        self.slider_escala.setMaximum(100)  # Valor maximo do slider
        self.slider_escala.setStyleSheet(self.estiloSlider)

        self.layout_lateral.addWidget(self.slider_escala)
        self.slider_escala.valueChanged.connect(self.slider_escala_acao)  # Conectar mudanca de valor
        self.val_slider = self.slider_escala.value()  # Valor do slider para a escala do eixo x

        self.layout_lateral.addSpacing(20)

        # Seletor de cor do grafico
        self.botao_cor = QtWidgets.QPushButton("Selecionar Cor do Grafico")  # Botao para selecionar cor
        self.botao_cor.clicked.connect(self.selecionar_cor_clicado)  # Conectar o clique
        self.botao_cor.setStyleSheet(self.estiloBotaoCor)  # Aplicar o estilo
        self.caixa_texto_cor = QtWidgets.QColorDialog()  # Criacao do seletor de cor
        self.layout_lateral.addWidget(self.botao_cor)  # Adicionar o botao ao layout lateral

        self.layout_lateral.addSpacing(20)

        # Media do grafico
        self.media_graf = QtWidgets.QLabel(f"Media do grafico: {self.media}")
        self.media_graf.setStyleSheet(self.estiloTextoMedia)
        self.layout_lateral.addWidget(self.media_graf)

        self.layout_lateral.addSpacing(20)

        # Frequencia detectada (vem do header do pacote)
        self.freq_label = QtWidgets.QLabel("Frequencia: 0.0 Hz")
        self.freq_label.setStyleSheet(self.estiloTextoMedia)
        self.layout_lateral.addWidget(self.freq_label)

        self.layout_lateral.addStretch()

        # Proporcao do grafico e do painel lateral
        self.leyout.addWidget(self.grafico, 7)  # Grafico com proporcao 7
        self.leyout.addWidget(self.painel_lateral, 2)  # Painel lateral com proporcao 2
        self.leyout.addWidget(self.painel_horizontal, 1)

        self.configurar_grafico()  # Configurar o grafico
        self.atualizar_grafico()

    def configurar_grafico(self):
        self.grafico.setLabel('left', 'Amplitude', units='V')  # eixo y do grafico
        self.grafico.setLabel('bottom', 'Tempo', units='s')    # eixo x do grafico
        self.grafico.showGrid(x=True, y=True)  # Mostrar grid no grafico
        self.grafico.setRange(xRange=self.escalax, yRange=self.escalay)  # Range inicial

    def Resetar_clicado(self):
        self.slider_escala.setValue(0)
        self.slider_amplitude.setValue(0)
        self.slider_offset.setValue(0)
        self.corGrafico = '#FF0000'
        self.curva.setPen(self.corGrafico)
        self.curva.setData([], [])

    def selecionar_cor_clicado(self):
        cor = self.caixa_texto_cor.getColor()
        if cor.isValid():
            self.corGrafico = cor
            self.curva.setPen(self.corGrafico)   # so troca a caneta, sem replotar

    def atualizar_eixo_y(self):
        meia_altura = self.base_meia_altura * (1.02 ** (-self.slider_amplitude.value()))
        self.grafico.setYRange(-meia_altura, meia_altura, padding=0)

    def atualizar_grafico(self):
        val_escala = self.slider_escala.value()
        fator_escala = 0.95 ** val_escala

        # Janela natural do eixo X = duracao de um pacote = N_AMOSTRAS / taxa de amostragem
        if self.taxa_real > 0:
            janela_base = N_AMOSTRAS / self.taxa_real
        else:
            janela_base = 1.0

        self.largura_janela = janela_base * fator_escala
        self.grafico.setXRange(0, self.largura_janela, padding=0)
        self.atualizar_eixo_y()   # Y vem da fonte unica

    def slider_escala_acao(self):
        self.atualizar_grafico()

    def slider_amplitude_acao(self):
        self.atualizar_grafico()

    def slider_offset_acao(self):
        self.texto_offset.setText(f"Offset: {self.slider_offset.value() / 10.0:.1f} V")

        self.atualizar_grafico()

    def receber_serial(self):
        # So processa quando ja chegou um pacote inteiro
        if self.porta.in_waiting < TAMANHO_PACOTE:
            return

        dados = self.porta.read(TAMANHO_PACOTE)
        if len(dados) < TAMANHO_PACOTE:
            return

        quantidade, taxa_real, freq_detectada = struct.unpack(HEADER_FMT, dados[:HEADER_SIZE])
        quantidade = min(quantidade, N_AMOSTRAS)   # protege contra header corrompido

        amostras = np.frombuffer(dados[HEADER_SIZE:], dtype='<u2').astype(float)[:quantidade]

        # ADC bruto (0..4095) -> tensao centrada em zero + offset manual do slider
        y = (amostras / ADC_MAX) * V_REF - (V_REF / 2.0) + (self.slider_offset.value() / 10.0)

        # Se a taxa de amostragem mudou, reajusta a janela do eixo X
        if taxa_real > 0 and abs(taxa_real - self.taxa_real) > 1.0:
            self.taxa_real = taxa_real
            self.atualizar_grafico()

        # Eixo X em segundos, reconstruido a partir da taxa de amostragem
        if self.taxa_real > 0:
            x = np.arange(len(y)) / self.taxa_real
        else:
            x = np.arange(len(y))

        self.curva.setData(x, y)

        self.freq_label.setText(f"Frequencia: {freq_detectada:.1f} Hz")

        if len(y):
            self.media = float(np.mean(y))
            self.media_graf.setText(f"Media do grafico: {self.media:.4f}")


app = QtWidgets.QApplication(sys.argv)  # Criacao da aplicacao com a sys

janela = JanelaOciloscopio()  # Criacao da janela do osciloscopio
janela.show()  # Mostrar a janela do osciloscopio

sys.exit(app.exec_())  # Executar a aplicacao