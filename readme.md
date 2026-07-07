# Osciloscópio Digital com ESP32

Osciloscópio didático de baixo custo: um **ESP32** captura o sinal analógico e envia os dados pela porta serial para uma interface gráfica em **Python (PyQtGraph)** que roda no computador, exibindo a forma de onda com base de tempo real e controles de escala, amplitude e offset. Um circuito de condicionamento na entrada permite medir sinais bipolares de até ±10 V.

---

## Visão geral

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
│  Circuito de │     │    ESP32     │     │   PC (Python)        │
│ condiciona-  │ --> │  aquisição   │ --> │  janela_Graf.py      │
│ mento        │     │  do sinal    │ USB │  PyQtGraph           │
│ (±10V→0-3.3V)│     │  (ADC)       │     │  Osciloscópio na tela│
└──────────────┘     └──────────────┘     └──────────────────────┘
```

1. **Condicionamento analógico** — uma rede resistiva + buffer traduz o sinal bipolar de ±10 V para a faixa 0–3,3 V que o ADC do ESP32 aceita (ver seção do esquemático abaixo);
2. **Aquisição** — o ESP32 amostra o sinal condicionado, monta frames de 256 amostras e os envia pela serial junto com o tempo real de coleta de cada frame;
3. **Interface (`janela_Graf.py`)** — recebe os frames pela porta serial e plota a forma de onda com eixo de tempo calibrado pelo tempo real reportado na aquisição, com controles de escala, amplitude, offset e cor.

---

## Circuito de condicionamento de sinal (esquemático)
![squemático do circuito de condicionamento no LTspice](<ProjetoMicro/Imagens/Circuito.png>)


O ADC do ESP32 só aceita tensões entre **0 e 3,3 V**, mas o objetivo é medir sinais bipolares de até **±10 V**. O circuito acima (simulado no LTspice) resolve isso com uma rede de três resistores que faz, ao mesmo tempo, **atenuação** e **deslocamento de nível (offset)**:

| Componente | Valor | Função |
|---|---|---|
| `Vin` | SINE(0 10 1k) | Sinal de teste: senoide de ±10 V a 1 kHz |
| `R2` | 100 kΩ | Liga o sinal de entrada ao nó `Vmap` (atenuação) |
| `R1` | 33 kΩ | Liga a referência de 3,3 V (`Vesp32`) ao nó `Vmap` (injeta o offset) |
| `R3` | 49,2 kΩ | Liga `Vmap` ao GND (fecha o divisor) |
| `U1` | Op-amp (5 V) | Buffer (seguidor de tensão) entre `Vmap` e a saída `Vfinal` |

### A matemática do nó Vmap

Os três resistores se encontram no nó `Vmap`. Por superposição (teorema de Millman), a tensão nesse nó é a média das fontes ponderada pelas condutâncias:

```
Vmap = (Vin/R2 + 3,3/R1 + 0/R3) / (1/R2 + 1/R1 + 1/R3)
Vmap ≈ 0,165 · Vin + 1,65
```

Testando os extremos:

- `Vin = +10 V` → `Vmap ≈ 3,3 V` (fundo de escala do ADC)
- `Vin = 0 V`   → `Vmap = 1,65 V` (exatamente o meio da escala)
- `Vin = −10 V` → `Vmap ≈ 0 V` (zero do ADC)

Ou seja: a faixa completa de **−10 V a +10 V é mapeada linearmente em 0 a 3,3 V**, sem cortar nenhuma parte do sinal. Os valores de R1 e R3 foram escolhidos justamente para que o ganho (≈1/6) e o offset (1,65 V) fechem essa conta.

### Por que o buffer (U1)?

A impedância equivalente do nó `Vmap` é `100k ∥ 33k ∥ 49,2k ≈ 16,5 kΩ` — alta demais para o ADC do ESP32, que usa um circuito de amostragem (sample-and-hold) que "rouba" corrente do nó a cada conversão e distorceria a leitura. O op-amp `U1`, ligado como **seguidor de tensão** (saída realimentada na entrada inversora), copia `Vmap` para `Vfinal` com impedância de saída baixíssima, entregando ao ADC um sinal firme.

> **Nota prática:** como o op-amp é alimentado com 5 V e precisa entregar de 0 a 3,3 V na saída, use um modelo **rail-to-rail** (ex.: MCP6002, TLV2372) na montagem real.

---

## Simulação no LTspice (gráfico)
![Resultado da simulação transiente](<ProjetoMicro/Imagens/Grafico_exemplo_conversao.png>)

Resultado da diretiva `.tran 0 5m` (5 ms de simulação = 5 ciclos do sinal de 1 kHz):

- **Curva verde — `V(vin)`**: o sinal original, oscilando entre **−10 V e +10 V**;
- **Curva vermelha — `V(vfinal)`**: a saída do condicionador, oscilando entre **0 e 3,3 V**, centrada em 1,65 V, com a mesma frequência e fase do sinal original — só que "encolhida e levantada" para caber na janela do ADC;
- **Curva azul — `V(vmap)`**: está na legenda mas não aparece separada no gráfico porque fica **exatamente embaixo da vermelha**: como o buffer tem ganho 1, `Vfinal = Vmap` e as duas curvas se sobrepõem perfeitamente.

A simulação confirma o comportamento esperado: nos picos de +10 V do sinal verde, a vermelha toca 3,3 V; nos vales de −10 V, toca 0 V. Nenhum trecho satura ou é cortado.

---

## Comunicação serial

O script Python espera receber, a 115200 baud, frames no seguinte formato:

```
_Update:<tempo_de_coleta_em_segundos>   ← marcador de início + base de tempo
<amostra 0>                              ← 256 linhas, um inteiro 0–4095 por linha
<amostra 1>
...
<amostra 255>
```

- O marcador `_Update:` indica o início de um frame novo e carrega o **tempo real de coleta** das 256 amostras (medido no ESP32, sem incluir o tempo de transmissão);
- Cada amostra é o valor bruto do ADC de 12 bits (0–4095), convertido para tensão (0–3,3 V) no lado do PC;
- Linhas não numéricas (mensagens de boot/erro do ESP32) são ignoradas automaticamente pelo parser.

---

## Interface Python (`janela_Graf.py`)

Interface gráfica em **PyQt + PyQtGraph** que funciona como a tela do osciloscópio:

### Base de tempo real

O coração da sincronização é o **`dt`** — o espaçamento entre amostras. Ele é recalculado a cada frame a partir do tempo recebido no marcador:

```python
dt_ms = (tempo_coleta_s * 1000) / N
```

Cada ponto é plotado em `x = i · dt_ms`, então o eixo X reflete o **tempo real** em que as amostras foram capturadas — se a taxa de amostragem do ESP32 mudar, o gráfico se ajusta sozinho no frame seguinte.

### Controles disponíveis

- **Slider de escala (eixo X)**: fatores multiplicativos sobre a duração real do frame (2×, 1×, 0,5×, 0,25×, 0,125×) — zoom out/in na janela de tempo;
- **Slider de amplitude (eixo Y)**: ajusta o topo da janela vertical em steps, "esticando" a onda sem alterar os dados;
- **Slider de offset**: desloca a curva verticalmente;
- **Seletor de cor** da curva;
- **Botão Resetar**: volta todas as escalas ao padrão e ressincroniza com o próximo frame;
- **Medições em tempo real**: média do sinal e tensão pico a pico (Vpp), calculadas a cada frame.

### Sincronização de frames

O parser da serial acumula bytes num buffer, monta linha por linha e só começa a guardar amostras **depois** de ver um marcador `_Update` — isso evita plotar frames "pela metade" quando o programa conecta no meio de uma transmissão.

---

## Como executar

```bash
pip install pyqtgraph pyserial numpy PyQt5
```

Ajuste a porta serial no início do script (`/dev/cu.usbserial-0001` no macOS; no Windows algo como `COM3`; no Linux `/dev/ttyUSB0`) e rode:

```bash
python janela_Graf.py
```

Com o ESP32 conectado via USB e enviando frames, a forma de onda aparece na tela automaticamente.

---

## Estrutura do repositório

```
ProjetoMicro/
├── janela_Graf.py      # Interface gráfica do osciloscópio (PyQtGraph)
├── docs/
│   ├── esquematico.png # Circuito de condicionamento (LTspice)
│   └── simulacao.png   # Resultado da simulação transiente
└── README.md
```