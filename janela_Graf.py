from pyqtgraph.Qt import *
import numpy as np 
import sys
import pyqtgraph as pg 
import serial


print("PyQtGraph Version: ", pg.__version__)

def gera_dados(t, tipo, amplitude, frequencia):
    # Simula UMA leitura do serial: o valor da onda no instante t
    if tipo == 'seno':
        valor = amplitude * np.sin(2 * np.pi * frequencia * t)
    elif tipo == 'cosseno':
        valor = amplitude * np.cos(2 * np.pi * frequencia * t)
    elif tipo == 'quadrada':
        valor = amplitude * np.sign(np.sin(2 * np.pi * frequencia * t))
    elif tipo == 'triangular':
        fase = frequencia * t - np.floor(frequencia * t + 0.5)
        valor = amplitude * (2 * np.abs(2 * fase) - 1)
    elif tipo == 'dente_serra':
        valor = amplitude * 2 * (frequencia * t - np.floor(0.5 + frequencia * t))
    else:
        valor = 0.0

    ruido = np.random.uniform(-0.05, 0.05)  # sem 'size' -> retorna UM float só
    return valor + ruido

def calcula_media(val):
    return sum(val)/len(val)



class JanelaOciloscopio(QtWidgets.QMainWindow):
    #Construtor da classe e declaracao de objetos
    contBotao1 = 0 # Contador para o botao 1 
    estiloSliderAmplitude  = """
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
    
    escalax =[-10, 10] # Escala do eixo x do grafico
    escalay = [-1.5, 1.5] # Escala do eixo y do grafico
    # Larguras/alturas BASE (referencia fixa, nunca muda)
    base_meia_largura = 10   # eixo X: [-10, 10]
    base_meia_altura  = 1.5  # eixo Y: [-1.5, 1.5] 
    largura_janela = 10.0   # segundos visiveis no X
    fator_desloc = 0 
    corGrafico = '#FF0000' # Cor do grafico
    media =0 


    porta = serial.Serial(port='/dev/cu.usbserial-1130',baudrate=9600,timeout=0.1)


    def __init__(self): 
        super().__init__()# Construtor da classe pai 

        #Defs da tela
        self.setWindowTitle("Ociloscopio")# Titulo da janela
        self.resize(1080, 640) # Tamanho da janela


        #Wiget principal da janela
        self.widget_central = QtWidgets.QWidget() # Criacao do widget central da janela
        self.setCentralWidget(self.widget_central) # Setar o widget central na janela

        #Leyout horizontal 
        self.leyout = QtWidgets.QHBoxLayout() # Criacao do layout horizontal
        self.widget_central.setLayout(self.leyout) # Setar o layout no widget central

        #Grafico
        self.grafico = pg.PlotWidget() # Criacao do grafico

        #Area ao lado 
        self.painel_lateral = QtWidgets.QWidget() # Criacao do painel lateral

        self.layout_lateral = QtWidgets.QVBoxLayout() # Criacao do layout vertical para o painel lateral
        self.painel_lateral.setLayout(self.layout_lateral) # Setar o layout no painel lateral

        self.painel_horizontal = QtWidgets.QWidget()
        self.layout_horizontal =QtWidgets.QVBoxLayout()
        self.painel_horizontal.setLayout(self.layout_horizontal)


#aquisicao da funcao matematica 
        self.tipo_onda = 'seno'   # qual onda "receber"
        self.t = 0.0     # tempo atual (s)
        self.dt = 0.02    # passo de tempo por amostra (s)
        self.max_pontos = 1000    # janela rolante: quantas amostras manter
        self.buffer_x = []      # tempos recebidos
        self.buffer_y = []      # valores recebidos

        # Curva criada uma vez. Depois so atualizamos com setData.
        self.curva = self.grafico.plot([], [], pen=self.corGrafico)

        # Timer que dispara a leitura periodicamente
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.receber_serial)
        self.timer.start(20)   # 20 ms -> ~50 leituras por segundo
    


        #Botoes 

        #Botao 3 - Resetar 
        self.Resetar = QtWidgets.QPushButton("Resetar") # Criacao do botao 3
        self.Resetar.clicked.connect(self.Resetar_clicado) # Conectar o clique do botao 3 a funcao ResetarZoom_clicado
        self.layout_lateral.addWidget(self.Resetar) # Adicionar o botao 3 ao layout lateral
        self.Resetar.setStyleSheet(self.estiloBotoeReset) # Aplicar o estilo ao botao 3
        
        self.layout_lateral.addSpacing(20) # Adicionar um espaçamento entre os botões 3 e 4

      
        #Slider Amplitude
        self.texto_amplitude  = QtWidgets.QLabel("Slider Amplitude")
        self.texto_amplitude.setStyleSheet(self.estiloTextoAmplitude)
        self.layout_lateral.addWidget(self.texto_amplitude)

        self.slider_amplitude= QtWidgets.QSlider(QtCore.Qt.Horizontal) # Criacao do slider de amplitude (zoom vertical)
        self.slider_amplitude.setMinimum(-100) # Valor minimo do slider
        self.slider_amplitude.setMaximum(100) # Valor maximo do slider
        self.slider_amplitude.setStyleSheet(self.estiloSliderAmplitude)


        self.layout_lateral.addWidget(self.slider_amplitude)
        self.slider_amplitude.valueChanged.connect(self.slider_amplitude_acao) # Conectar a mudança de valor do slider
        self.val_slider_amplitude = self.slider_amplitude.value() # Valor do slider de amplitude

        self.layout_lateral.addSpacing(20)

        #Slider offset
        self.slider_offset = QtWidgets.QSlider(QtCore.Qt.Vertical) # Criacao do slider
        self.slider_offset.setMaximum(100)
        self.slider_offset.setMinimum(-100)
        self.slider_offset.setStyleSheet(self.estiloSliderDeslocamento)
        self.layout_horizontal.addWidget(self.slider_offset)

        self.slider_offset.valueChanged.connect(self.slider_offset_acao)
        self.fator_desloc = self.slider_offset.value()

        self.layout_horizontal.addStretch()




        #Slider escala x 
        self.texto_slider = QtWidgets.QLabel("Slider da Escala")
        self.texto_slider.setStyleSheet(self.estiloTextoEscala)
        self.layout_lateral.addWidget(self.texto_slider)

        self.slider_escala= QtWidgets.QSlider(QtCore.Qt.Horizontal) # Criacao do slider para a escala do eixo x
        self.slider_escala.setMinimum(-100) # Valor minimo do slider
        self.slider_escala.setMaximum(100) # Valor maximo do slider
        self.slider_escala.setStyleSheet(self.estiloSlider)


        self.layout_lateral.addWidget(self.slider_escala)
        self.slider_escala.valueChanged.connect(self.slider_escala_acao) # Conectar a mudança de valor do slider a funcao slider_escala
        self.val_slider = self.slider_escala.value() # Valor do slider para a escala do eixo x

        self.layout_lateral.addSpacing(20)
        

        

        #Seletor de cor do grafico 
        self.botao_cor = QtWidgets.QPushButton("Selecionar Cor do Grafico") # Criacao do botao para selecionar a cor do grafico
        self.botao_cor.clicked.connect(self.selecionar_cor_clicado) # Conectar o clique do botao a funcao selecionar_cor_clicado
        self.botao_cor.setStyleSheet(self.estiloBotaoCor) # Aplicar o estilo ao botao de cor
        self.caixa_texto_cor = QtWidgets.QColorDialog() # Criacao do seletor de cor
        self.layout_lateral.addWidget(self.botao_cor) # Adicionar o botao ao layout lateral

        self.layout_lateral.addSpacing(20)

        #Media do grafico 
        
        self.media_graf = QtWidgets.QLabel(f"Media do grafico: {self.media}")
        self.media_graf.setStyleSheet(self.estiloTextoMedia)
        self.layout_lateral.addWidget(self.media_graf)

        self.layout_lateral.addStretch()

        #Proporcao do grafico e do painel lateral
        self.leyout.addWidget(self.grafico, 7) # Adicionar o grafico ao layout com proporcao 7
        self.leyout.addWidget(self.painel_lateral, 2) # Adicionar o painel lateral ao layout com proporcao 3
        self.leyout.addWidget(self.painel_horizontal,1)


        self.configurar_grafico() # Configurar o grafico
        self.atualizar_grafico()

    

    def configurar_grafico(self):
        self.grafico.setLabel('left', 'Amplitude',units='mm') # eixo y do grafico  
        self.grafico.setLabel('bottom', 'Tempo', units='s') # eixo x do grafico
        self.grafico.showGrid(x=True, y=True) # Mostrar grid no grafico
        self.grafico.setRange(xRange=self.escalax, yRange=self.escalay) # Definir o range do grafico


    def Resetar_clicado(self):
        self.slider_escala.setValue(0)
        self.slider_amplitude.setValue(0)
        self.slider_offset.setValue(0)
        self.buffer_x.clear()
        self.buffer_y.clear()
        self.t = 0.0
        self.corGrafico = '#FF0000'
        self.curva.setPen(self.corGrafico)

    def selecionar_cor_clicado(self):
        cor = self.caixa_texto_cor.getColor()
        if cor.isValid():
            self.corGrafico = cor
            self.curva.setPen(self.corGrafico)   # so troca a caneta, sem replotar


    def atualizar_eixo_y(self):
        meia_altura = self.base_meia_altura * (1.02 ** (-self.slider_amplitude.value()))
        self.grafico.setYRange(-meia_altura,meia_altura, padding=0)

    def atualizar_grafico(self):
        val_escala = self.slider_escala.value()

        fator_escala = 0.95 ** (val_escala)

        # Largura da janela no tempo (X comeca em 0)
        self.largura_janela = (2 * self.base_meia_largura) * fator_escala

        self.grafico.setXRange(0, self.largura_janela, padding=0)
        self.atualizar_eixo_y()   # Y vem da fonte unica

    def slider_escala_acao(self):
        self.atualizar_grafico()

    def slider_amplitude_acao(self):
        self.atualizar_grafico()

    def slider_offset_acao(self):
        self.atualizar_grafico()

    def receber_serial(self):
        #valor = gera_dados(self.t, self.tipo_onda, 1, 3) +self.slider_offset.value()
        
        valor= float(self.porta.readline().decode('utf-8', errors='ignore').strip()) +(self.slider_offset.value()/10)


        # Chegou na borda direita? Limpa e recomeca do zero.
        if self.t > self.largura_janela:
            self.buffer_x.clear()
            self.buffer_y.clear()
            self.t = 0.0

        self.buffer_x.append(self.t)
        self.buffer_y.append(valor )

        self.t += self.dt

        self.curva.setData(self.buffer_x, self.buffer_y)
        #self.fator_desloc = self.slider_offset.value()/10

        if self.buffer_y:
            self.media = calcula_media(self.buffer_y)
            self.media_graf.setText(f"Media do grafico: {self.media:.4f}")
            if abs(self.media - self.fator_desloc) > 0.5: #nao fica tremendo 
                #self.fator_desloc = self.media

                self.atualizar_eixo_y()   # mesma conta, um lugar so
        else: 
            self.atualizar_grafico()




app = QtWidgets.QApplication(sys.argv) # Criacao da aplicacao com a sys

janela = JanelaOciloscopio() # Criacao da janela do osciloscopio
janela.show() # Mostrar a janela do osciloscopio

sys.exit(app.exec_()) # Executar a aplicacao