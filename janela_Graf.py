from pyqtgraph.Qt import *
import numpy as np 
import sys
import pyqtgraph as pg 
print("PyQtGraph Version: ", pg.__version__)

def gerar_dados(x,amplitude, frequencia):
    seno= amplitude * np.sin(2 * np.pi * frequencia * x)
    ruido = np.random.uniform(
        low=-0.05,
        high=0.05,
        size=len(x)
    )
    return seno + ruido 
    
        


class JanelaOciloscopio(QtWidgets.QMainWindow):
    #Construtor da classe e declaracao de objetos
    contBotao1 = 0 # Contador para o botao 1 
    estiloBotoesZoom = """
    QPushButton {
        background-color: #b4452d;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #000000;
        padding: 10px;
    }
"""
    estiloBotoesEscala = """
    QPushButton {
        background-color: #7E8C54;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #000000;
        padding: 10px;
    }
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


    escalax =[-10, 10] # Escala do eixo x do grafico
    escalay = [-1.5, 1.5] # Escala do eixo y do grafico
    corGrafico = '#FF0000' # Cor do grafico
    
    def __init__(self): 
        super().__init__()# Construtor da classe pai 


        self.setWindowTitle("Ociloscopio")# Titulo da janela
        self.resize(1024, 640) # Tamanho da janela


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

        #Botoes 

        # Botao 1 - Zoom Out
        self.Zoomout = QtWidgets.QPushButton("Zoom Out") # Criacao do botao 1
        self.Zoomout.clicked.connect(self.Zoomout_clicado) # Conectar o clique do botao 1 a funcao botao1_clicado
        self.layout_lateral.addWidget(self.Zoomout) # Adicionar o botao 1 ao layout lateral
        self.Zoomout.setStyleSheet(self.estiloBotoesZoom) # Aplicar o estilo ao botao 1
        #Botao 2 - Zoom In
        self.Zoomin = QtWidgets.QPushButton("Zoom In") # Criacao do botao 2
        self.Zoomin.clicked.connect(self.Zoomin_clicado) # Conectar o clique do botao 2 a funcao botao2_clicado
        self.layout_lateral.addWidget(self.Zoomin) # Adicionar o botao 2 ao layout lateral
        self.Zoomin.setStyleSheet(self.estiloBotoesZoom) # Aplicar o estilo ao botao 2

        self.layout_lateral.addSpacing(20) # Adicionar um espaçamento entre os botões 3 e 4


        #Botao 3 - Resetar 
        self.Resetar = QtWidgets.QPushButton("Resetar") # Criacao do botao 3
        self.Resetar.clicked.connect(self.Resetar_clicado) # Conectar o clique do botao 3 a funcao ResetarZoom_clicado
        self.layout_lateral.addWidget(self.Resetar) # Adicionar o botao 3 ao layout lateral
        self.Resetar.setStyleSheet(self.estiloBotoeReset) # Aplicar o estilo ao botao 3
        
        self.layout_lateral.addSpacing(20) # Adicionar um espaçamento entre os botões 3 e 4

        #Botao 4 - Escala 
        self.EscalaPositiva = QtWidgets.QPushButton("Escala Positiva") # Criacao do botao 4
        self.EscalaPositiva.clicked.connect(self.EscalaPositiva_clicado) # Conectar o clique do botao 4 a funcao EscalaPositiva_clicado
        self.layout_lateral.addWidget(self.EscalaPositiva) # Adicionar o botao 4 ao layout lateral
        self.EscalaPositiva.setStyleSheet(self.estiloBotoesEscala) # Aplicar o estilo ao botao 4
        #Botao 5 - Escala Negativa
        self.EscalaNegativa = QtWidgets.QPushButton("Escala Negativa") #    Criacao do botao 5  
        self.EscalaNegativa.clicked.connect(self.EscalaNegativa_clicado) # Conectar o clique do botao 5 a funcao EscalaNegativa_clicado
        self.layout_lateral.addWidget(self.EscalaNegativa) # Adicionar o botao 5 ao layout lateral
        self.EscalaNegativa.setStyleSheet(self.estiloBotoesEscala) # Aplicar o estilo ao botao 5


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
        #Layout dos botoes 
        self.layout_lateral.addSpacing(20)
        

        #Seletor de cor do grafico 
        self.botao_cor = QtWidgets.QPushButton("Selecionar Cor do Grafico") # Criacao do botao para selecionar a cor do grafico
        self.botao_cor.clicked.connect(self.selecionar_cor_clicado) # Conectar o clique do botao a funcao selecionar_cor_clicado
        self.botao_cor.setStyleSheet(self.estiloBotaoCor) # Aplicar o estilo ao botao de cor
        self.caixa_texto_cor = QtWidgets.QColorDialog() # Criacao do seletor de cor
        self.layout_lateral.addWidget(self.botao_cor) # Adicionar o botao ao layout lateral

        
        self.layout_lateral.addStretch()

        #Proporcao do grafico e do painel lateral
        self.leyout.addWidget(self.grafico, 7) # Adicionar o grafico ao layout com proporcao 7
        self.leyout.addWidget(self.painel_lateral, 3) # Adicionar o painel lateral ao layout com proporcao 3


        self.configurar_grafico() # Configurar o grafico
        self.plotar_dados() # Plotar os dados no grafico



    def configurar_grafico(self):
        self.grafico.setLabel('left', 'Amplitude',units='mm') # eixo y do grafico  
        self.grafico.setLabel('bottom', 'Tempo', units='s') # eixo x do grafico
        self.grafico.showGrid(x=True, y=True) # Mostrar grid no grafico
        self.grafico.setRange(xRange=self.escalax, yRange=self.escalay) # Definir o range do grafico

    def plotar_dados(self):
        x = np.linspace(self.escalax[0], self.escalax[1], 1000)# Mostra no intervalo de -10 a 10 com 1000 pontos 
        y = gerar_dados(x,1,0.3) # Gerar os dados do seno (Mutavel, ira variar de acordo com o que se deseja plotar)

        self.grafico.plot(x, y, pen= self.corGrafico) # Plotar os dados no grafico com a cor vermelha



    def Zoomout_clicado(self):
        self.contBotao1 += 1
        print(f"Botao 1 clicado {self.contBotao1} vezes") # Funcao para o botao 1
        self.escalax = (self.escalax[0] * 1.1, self.escalax[1] * 1.1) # Aumentar a escala do eixo x em 10%
        self.escalay = (self.escalay[0] * 1.1, self.escalay[1] * 1.1) # Aumentar a escala do eixo y em 10%
        self.grafico.setRange(xRange=self.escalax, yRange=self.escalay) # Atualizar o range do grafico


    def Zoomin_clicado(self):
        print(f"Botao 2 clicado ") # Funcao para o botao 2
        self.escalax = (self.escalax[0] * 0.9, self.escalax[1] * 0.9) # Diminuir a escala do eixo x em 10%
        self.escalay = (self.escalay[0] * 0.9, self.escalay[1] * 0.9) # Diminuir a escala do eixo y em 10%
        self.grafico.setRange(xRange=self.escalax, yRange=self.escalay) # Atualizar o range do grafico
        
    def Resetar_clicado(self):
        print(f"Botao 3 clicado ") # Funcao para o botao 3
        self.escalax = (-10, 10) # Resetar a escala do eixo x
        self.escalay = (-1.5, 1.5) # Resetar a escala do eixo y
        self.grafico.setRange(xRange=self.escalax, yRange=self.escalay) # Atualizar o range do grafico
        self.grafico.clear() # Limpar o grafico para remover os dados antigos
        self.corGrafico = '#FF0000' # Resetar a cor do grafico para vermelho
        self.plotar_dados() # Replotar os dados com a escala resetada
        self.slider_escala.setValue(0) # Resetar o valor do slider para 0 após a ação

    def EscalaPositiva_clicado(self):
        print(f"Botao 4 clicado ") # Funcao para o botao 4
        self.escalax = (self.escalax[0]* 1.1, self.escalax[1]*1.1) # Aumentar a escala do eixo x em 10%
        self.grafico.setRange(xRange=self.escalax, yRange=self.escalay) # Atualizar o range do grafico
    def EscalaNegativa_clicado(self):
        print(f"Botao 5 clicado ") # Funcao para o botao 5
        self.escalax = (self.escalax[0]* 0.9, self.escalax[1]*0.9) # Diminuir a escala do eixo x em 10%
        self.grafico.setRange(xRange=self.escalax, yRange=self.escalay) # Atualizar o range do grafico


    def selecionar_cor_clicado(self):
        cor_selecionada = self.caixa_texto_cor.getColor() # Abrir o seletor de cor e obter a cor selecionada
        if cor_selecionada.isValid(): # Verificar se a cor selecionada é válida
            self.corGrafico = cor_selecionada
            self.grafico.clear() # Limpar o grafico para remover a cor antiga
            self.escalax=[-10,10]
            self.grafico.setRange(xRange=self.escalax, yRange=self.escalay) # Manter o range do grafico após a mudança de cor

            self.plotar_dados() # Replotar os dados com a nova cor do grafico

    def slider_escala_acao(self): 
        if self.slider_escala.value() - self.val_slider < 0: # Verificar se o valor do slider é positivo
            self.val_slider = self.slider_escala.value() # Atualizar o valor do slider
            self.escalax = (self.escalax[0]* 1.05, self.escalax[1] * 1.05) # Aumentar a escala do eixo x com base no valor do slider
        elif self.slider_escala.value() - self.val_slider > 0: # Verificar se o valor do slider é negativo
            self.val_slider = self.slider_escala.value() # Atualizar o valor do slider
            self.escalax = (self.escalax[0]* 0.95, self.escalax[1] * 0.95) # Diminuir a escala do eixo x com base no valor do slider
        self.grafico.setRange(xRange=self.escalax, yRange=self.escalay) # Atualizar o range do grafico
       


app = QtWidgets.QApplication(sys.argv) # Criacao da aplicacao com a sys

janela = JanelaOciloscopio() # Criacao da janela do osciloscopio
janela.show() # Mostrar a janela do osciloscopio

sys.exit(app.exec_()) # Executar a aplicacao