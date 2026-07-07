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


val_offset_global = 0

def calcula_media(val):
    return sum(val) / len(val)


class JanelaOciloscopio(QtWidgets.QMainWindow):
    # Construtor da classe e declaracao de objetos
    contBotao1 = 0  # Contador para o botao 1
    estiloSliderAmplitude = """
        QSlider {
            background-color: #D9A79A;
            border: 2px solid #6B4A42;
            border-radius: 10px;
            padding: 6px;
        }

        QSlider::groove:horizontal {
            background: #D9A79A;
            border: 2px solid #6B4A42;
            height: 8px;
            border-radius: 4px;
        }

        QSlider::handle:horizontal {
            background: white;
            border: 2px solid #6B4A42;
            width: 18px;
            height: 18px;
            margin-top: -7px;
            margin-bottom: -7px;
            border-radius: 9px;
        }

        QSlider::sub-page:horizontal {
            background: white;
            border: 1px solid #6B4A42;
            border-radius: 4px;
        }

        QSlider::add-page:horizontal {
            background: #C08E7E;
            border: 1px solid #6B4A42;
            border-radius: 4px;
        }
        """
    estiloTextoAmplitude = """
            background-color: #D9A79A;
        color: #4A2F28;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #6B4A42;
        border-radius: 10px;
        padding: 6px;
        qproperty-alignment: AlignCenter;
        """
    estiloBotoeReset = """
    QPushButton {
        background-color: #A8B7D4;
        color: #24304A;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #5A6C8C;
        border-radius: 10px;
        padding: 10px;
    }
"""
    estiloBotaoCor = """
    QPushButton {
        background-color: #F5C9A3;
        color: #6B4423;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #C98F5C;
        border-radius: 10px;
        padding: 10px;
    }
"""
    estiloTextoEscala = """
            background-color: #A9CBA5;
        color: #2E4A2C;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #6F9A6A;
        border-radius: 10px;
        padding: 6px;
        qproperty-alignment: AlignCenter;
        """
    estiloSlider = """
        QSlider {
            background-color: #A9CBA5;
            border: 2px solid #6F9A6A;
            border-radius: 10px;
            padding: 6px;
        }

        QSlider::groove:horizontal {
            background: #A9CBA5;
            border: 2px solid #6F9A6A;
            height: 8px;
            border-radius: 4px;
        }

        QSlider::handle:horizontal {
            background: white;
            border: 2px solid #6F9A6A;
            width: 18px;
            height: 18px;
            margin-top: -7px;
            margin-bottom: -7px;
            border-radius: 9px;
        }

        QSlider::sub-page:horizontal {
            background: white;
            border: 1px solid #6F9A6A;
            border-radius: 4px;
        }

        QSlider::add-page:horizontal {
            background: #8CB786;
            border: 1px solid #6F9A6A;
            border-radius: 4px;
        }
        """
    estiloTextoMedia = """
        background-color: #A8D3D3;
        color: #244A4A;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #6EA3A3;
        border-radius: 10px;
        padding: 6px;
        qproperty-alignment: AlignCenter;
        """
    estiloSliderDeslocamento = """
        QSlider {
            background-color: #C3AFDA;
            border: 2px solid #8A6FA8;
            border-radius: 10px;
            padding: 6px;
        }

        QSlider::groove:vertical {
            background: #C3AFDA;
            border: 2px solid #8A6FA8;
            width: 8px;
            border-radius: 4px;
        }

        QSlider::handle:vertical {
            background: white;
            border: 2px solid #8A6FA8;
            width: 18px;
            height: 18px;
            margin-left: -7px;
            margin-right: -7px;
            border-radius: 9px;
        }

        QSlider::sub-page:vertical {
            background: #A98FC4;
            border: 1px solid #8A6FA8;
            border-radius: 4px;
        }

        QSlider::add-page:vertical {
            background: white;
            border: 1px solid #8A6FA8;
            border-radius: 4px;
        }
        """
    estiloTextoOffset = """
            background-color: #C3AFDA;
        color: #3F2E52;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #8A6FA8;
        border-radius: 10px;
        padding: 6px;
        qproperty-alignment: AlignCenter;
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
        # OBS: o firmware comeca em 20000 Hz (taxaAtual) e ajusta dinamicamente
        # entre 5000 e 50000 Hz. Enquanto a taxa nao for enviada junto do frame,
        # 20000.0 e a melhor aproximacao.
        self.fs = 20000.0                  # Hz  (taxa inicial do firmware)
        self.dt_ms = 1000.0 / self.fs      # ms entre amostras (FIXO)
        self.n_div = 10                    # numero de divisoes horizontais visiveis
        self.ms_por_div = 25               # escala de tempo inicial (ms/div)
        passo_freq = 1  # ms/div, distancia entre cada step (ajuste pra controlar o range)
        self.escalas_freq = [
            5 + 4*passo_freq,
            5 + 3*passo_freq,
            5 + 2*passo_freq,
            5 + 1*passo_freq,
            5,
            5 - 1*passo_freq,
            5 - 2*passo_freq,
            5 - 3*passo_freq,
            5 - 4*passo_freq,
        ]  # ms/div; simetrico em torno de 5
        self.idx_freq = 0

        # ================= AQUISICAO (frame a frame) =================
        self._buf = ''                     # pedaco de linha incompleta entre ticks
        self.N = 256                       # amostras por pacote (igual ao firmware)
        self.frame = []                    # acumula o pacote em andamento
        self.sincronizado = False          # so acumula amostras depois do 1o '_Update'
        self.largura_pacote = self.N * self.dt_ms   # duracao total de 1 pacote (ms)

        # ================= AMPLITUDE (eixo Y) =================
        # Exibicao em steps: a base fica ANCORADA no 0 e o TOPO desce em steps.
        # Topo menor -> a mesma onda ocupa mais altura da tela -> "estica pra cima".
        # Isso NAO toca nos dados plotados, so muda a janela de visualizacao (setYRange).
        self.y_min = 0.0                            # base ancorada no zero (nao muda)
        step = 0.5
        self.escalas_topo = [
            V_REF + 4*step + 0.1,
            V_REF + 3*step + 0.1,
            V_REF + 2*step + 0.1,
            V_REF + 1*step + 0.1,
            V_REF + 0.1,
            V_REF - 1*step + 0.1,
            V_REF - 2*step + 0.1,
            V_REF - 3*step + 0.1,
            V_REF - 4*step + 0.1,
        ]  # topo do eixo Y (V); simetrico em torno de V_REF, +0.1 so visual, menor = mais esticado
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

        self.layout_lateral.addSpacing(10)

        # Slider Amplitude (escala vertical em steps)
        self.texto_amplitude = QtWidgets.QLabel("Slider Amplitude")
        self.texto_amplitude.setStyleSheet(self.estiloTextoAmplitude)
        self.layout_lateral.addWidget(self.texto_amplitude)

        self.slider_amplitude = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_amplitude.setMinimum(0)                               # indice na lista
        self.slider_amplitude.setMaximum(len(self.escalas_topo) - 1)      # ultimo indice
        self.slider_amplitude.setSingleStep(1)
        self.slider_amplitude.setValue(4)
        self.slider_amplitude.setStyleSheet(self.estiloSliderAmplitude)

        self.layout_lateral.addWidget(self.slider_amplitude)
        self.slider_amplitude.valueChanged.connect(self.slider_amplitude_acao)
        self.val_slider_amplitude = self.slider_amplitude.value()

        self.layout_lateral.addSpacing(10)
        # Slider escala X (escala de tempo, ms/div)
        self.texto_slider = QtWidgets.QLabel("Slider da Escala")
        self.texto_slider.setStyleSheet(self.estiloTextoEscala)
        self.layout_lateral.addWidget(self.texto_slider)

        self.slider_escala = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_escala.setMinimum(0)      
        self.slider_escala.setMaximum(len(self.escalas_freq)-1)    
        self.slider_escala.setSingleStep(1)
        self.slider_escala.setValue(4)
        self.slider_escala.setStyleSheet(self.estiloSlider)

        self.layout_lateral.addWidget(self.slider_escala)
        self.slider_escala.valueChanged.connect(self.slider_escala_acao)
        self.val_slider = self.slider_escala.value()

        self.layout_lateral.addSpacing(10)

        # Slider offset (desloca a janela vertical pra cima/baixo)
        self.slider_offset = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.slider_offset.setMaximum(10)
        self.slider_offset.setMinimum(-10)
        self.slider_offset.setStyleSheet(self.estiloSliderDeslocamento)
        self.layout_horizontal.addWidget(self.slider_offset)

        self.slider_offset.valueChanged.connect(self.slider_offset_acao)
        self.texto_offset = QtWidgets.QLabel(f"Offset: {self.slider_offset.value()}")
        self.texto_offset.setStyleSheet(self.estiloTextoOffset)
        self.layout_horizontal.addWidget(self.texto_offset)


        self.layout_horizontal.addStretch()

        

        # Seletor de cor do grafico
        self.botao_cor = QtWidgets.QPushButton("Selecionar Cor do Grafico")
        self.botao_cor.clicked.connect(self.selecionar_cor_clicado)
        self.botao_cor.setStyleSheet(self.estiloBotaoCor)
        self.caixa_texto_cor = QtWidgets.QColorDialog()
        self.layout_lateral.addWidget(self.botao_cor)

        self.layout_lateral.addSpacing(10)

        # Media do grafico
        self.media_graf = QtWidgets.QLabel(f"Media do grafico: {self.media}")
        self.media_graf.setStyleSheet(self.estiloTextoMedia)
        self.layout_lateral.addWidget(self.media_graf)
        # Pico a pico do grafico
        self.vpp_graf = QtWidgets.QLabel("Pico a pico: 0.0000 V")
        self.vpp_graf.setStyleSheet(self.estiloTextoMedia)
        self.layout_lateral.addWidget(self.vpp_graf)

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
        self.slider_escala.setValue(4)     
        self.slider_amplitude.setValue(4)    
        self.slider_offset.setValue(0)
        self.frame = []
        self.sincronizado = False            # espera o proximo '_Update' pra recomecar
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

        desloc =0  #y_topo

        self.grafico.setYRange(self.y_min + desloc, y_topo + desloc, padding=0)

        # feedback do valor atual no proprio rotulo do slider
        self.texto_amplitude.setText(f"Amplitude: topo {y_topo-0.1:.1f} V")

    def atualizar_grafico(self):
        # --- Eixo X (escala de tempo em ms/div) ---
        self.idx_freq= self.slider_escala.value()         # valor do slider = ms/div
        largura_ms = self.escalas_freq[self.idx_freq]            # janela total = n_div * (ms/div)

        self.grafico.setXRange(0, largura_ms, padding=0)

        # trava o grid: 1 linha por divisao, cada uma valendo ms_por_div
        eixo_x = self.grafico.getAxis('bottom')
        ticks = [(d * self.ms_por_div, str(d * self.ms_por_div)) for d in range(self.n_div + 1)]
        eixo_x.setTicks([ticks])
        self.texto_slider.setText(f"Escala: {largura_ms} ms/div")

        # --- Eixo Y (amplitude) ---
        self.atualizar_eixo_y()

    def slider_escala_acao(self):
        self.atualizar_grafico()

    def slider_amplitude_acao(self):
        self.atualizar_grafico()

    def slider_offset_acao(self):
        self.atualizar_grafico()
        global val_offset_global
        val_offset_global = self.slider_offset.value()
        self.texto_offset.setText(f"Offset: {val_offset_global}")

    def receber_serial(self):
        """So le/parseia a serial e monta o frame. Nao mexe no grafico.

        Protocolo do firmware (enviarFrameSerial):
            _Update            <- marcador de INICIO de frame
            <amostra 0>        <- 256 linhas, um inteiro 0..4095 por linha
            ...
            <amostra 255>
        Linhas de boot/erro do ESP32 (nao numericas) sao ignoradas.
        """
        n = self.porta.in_waiting
        if n:
            self._buf += self.porta.read(n).decode('ascii', errors='ignore')

        partes = self._buf.split('\n')
        self._buf = partes.pop()        # ultimo pedaco = linha incompleta, volta pro buffer

        for linha in partes:
            linha = linha.strip()       # tira o \r do \r\n

            # '_Update' agora marca o INICIO de um frame novo:
            # descarta qualquer resto parcial e libera a acumulacao.
            if '_Update' in linha:
                self.frame = []
                self.sincronizado = True
                continue

            # ignora amostras enquanto nao viu o primeiro '_Update'
            # (evita plotar um frame que comecou pela metade ao conectar)
            if not self.sincronizado:
                continue

            if linha.isdigit():
                bruto = int(linha)
                if 0 <= bruto <= 4095:
                    self.frame.append(bruto)
                    if len(self.frame) >= self.N:
                        self.plotar_frame(self.frame)
                        self.frame = []
                        self.sincronizado = False   # espera o proximo '_Update'
            # linhas de boot/erro do ESP32 caem aqui e sao ignoradasx   

    def plotar_frame(self, frame):
        """Recebe um frame pronto (N amostras) e atualiza curva + media."""
        y=[]
        for b in frame:
            tensao = ((b / ADC_MAX) * V_REF) + val_offset_global 
            y.append(tensao)
        #y = [(b / ADC_MAX) * V_REF for b in frame]  # converte ADC->tensao 0..3.3 V
        x = [i * self.dt_ms for i in range(len(frame))]

        vmax= max(y) 
        vmin= min(y)
        vpp = vmax - vmin 
        self.vpp_graf.setText(f"Pico a pico: {vpp:.2f} V")
        self.curva.setData(x, y)
        self.media = calcula_media(y)
        self.media_graf.setText(f"Media do grafico: {self.media:.2f} V")


app = QtWidgets.QApplication(sys.argv)  # Criacao da aplicacao com a sys

janela = JanelaOciloscopio()  # Criacao da janela do osciloscopio
janela.show()  # Mostrar a janela do osciloscopio

sys.exit(app.exec_())  # Executar a aplicacao