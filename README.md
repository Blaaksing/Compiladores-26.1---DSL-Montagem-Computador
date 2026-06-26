# Compiladores-26.1---DSL-Montagem-Computador
Este repositório contém o projeto de uma DSL para montagem de computador, baseado na descrição da configuração do computador. O programa irá informar caso a máquina apresente inconsistências desde a escolha dos componentes da montagem, até o formato do gabinete e capacidade máxima da fonte.

---

### Equipe:
> Sergio Henrique
> 
> Sing Silva
> 
> Tales Paiva

---

### Motivação

A motivação do trabalho se dá através da dificuldade que reside na busca de peças de computador uma a uma. E aí há outro problema, que é saber se as peças são compatíveis entre si.

E à medida que vai se juntando os componentes, a pessoa além de se preocupar com preço, também precisa ficar alerta com outros detalhes, como por exemplo: consumo energético das peças, capacidade máxima da fonte, formato de gabinete, tipos de memória, soquetes de placa mãe...

Isso gera uma complexidade desnecessária, mas que poderia ser contornada com uma simples ferramenta que informa qual o componente que está causando invalidez na montagem. Caso contrário, a montagem é válida.

Em tempos em que as peças de computador estão caras, é importante ter cuidado na hora de montar. Sabendo disso, desenvolvemos um programa que avalia se uma determinada configuração é válida e ela também informa se uma configuração é inconsistente, além de informar onde que está a inconsistência na lista de montagem.

---

## Descrição informal da linguagem

Um programa descreve **um** computador, dentro de um bloco `computador <Nome> { ... }`.
Dentro do bloco você declara os componentes:

| Componente      | Sintaxe                                              | Exemplo                          |
| --------------- | --------------------------------------------------- | -------------------------------- |
| Processador     | `processador <Modelo> [<Geração>]`                  | `processador Ryzen5 5600X`       |
| Placa-mãe       | `placa_mae <Modelo>`                                 | `placa_mae B550`                 |
| Memória RAM     | `memoria <Cap> <GB\|TB> <TipoDDR> [<freq>MHz]`       | `memoria 16 GB DDR4 3200MHz`     |
| Armazenamento   | `armazenamento <SSD\|HDD> <Cap> <GB\|TB>`            | `armazenamento SSD 1 TB`         |
| Fonte           | `fonte <Potência> W`                                 | `fonte 650 W`                    |
| Placa de vídeo  | `placa_video <Modelo> [<VRAM>GB]`                    | `placa_video RTX3060 12GB`       |
| Gabinete        | `gabinete <Formato>`                                 | `gabinete ATX`                   |

Os campos entre `[...]` são **opcionais**. É permitido declarar **mais de um**
armazenamento.

### Componentes obrigatórios

Toda configuração precisa ter, no mínimo: **processador**, **placa-mãe**,
**memória RAM**, **pelo menos um armazenamento** e **fonte**. Placa de vídeo e
gabinete são opcionais.

### Validações semânticas (o "diferencial" da linguagem)

Além de verificar a sintaxe, o compilador roda uma **análise semântica** que
checa as regras do mundo real:

1. **Soquete CPU ↔ Placa-mãe** - um `Ryzen5` (AM4) não pode usar uma placa
   `Z790` (LGA1700).
2. **Memória DDR ↔ Placa-mãe** - uma placa `B550` exige DDR4; DDR5 é rejeitada.
3. **Potência da fonte** - soma o TDP do processador e da placa de vídeo, mais
   ~50W de base (placa-mãe, RAM, fans, discos), aplica uma **margem de segurança
   de 20%** e avisa se a fonte declarada é insuficiente.
4. **Gabinete ↔ Formato da placa-mãe** - verifica se o gabinete comporta o
   formato da placa.

Se algo estiver errado, o programa lista **todos** os problemas encontrados.

---

## Como funciona (estrutura de compilador)

O projeto segue a estrutura clássica de um compilador, usando o
**Lark**:

1. **Análise Léxica e Sintática** — a gramática formal (`grammar`, em `DSL.py`)
   define os tokens (`NOME`, `CAPACIDADE`, `UNIDADE`, `POTENCIA`, `FREQUENCIA`,
   `TIPO_ARMAZ`, `VRAM`, ...) e as regras de produção (`computador`,
   `processador`, `placa_mae`, `memoria`, ...).
2. **Geração da Árvore Sintática** — `parser.parse(texto)` constrói a árvore de
   sintaxe a partir do código `.dsl`.
3. **Tradução dirigida pela sintaxe** — a função `analisar()` percorre os nós da
   árvore (`match child.data`) e os traduz para uma estrutura interna
   (dicionário `config`).
4. **Análise Semântica** — `config` é validado contra tabelas de conhecimento
   (`socket_motherboard`, `socket_cpu`, `ddr_type`, `tdp_cpu`, `tdp_gpu`,
   `formato_case_suporta`), produzindo o laudo final.

---

## Como executar

### Pré-requisitos

- Python 3.10 ou superior (o código usa `match/case`)
- Biblioteca [`lark`](https://github.com/lark-parser/lark)

### Instalação

```bash
pip install lark
```

### Execução

```bash
python3 DSL.py <arquivo.dsl>
```

Exemplos prontos no repositório:

```bash
# Configuração válida
python3 DSL.py meu_pc.dsl

# Configuração com fonte insuficiente
python3 DSL.py pc_erro_fonte.dsl
```

---

## Exemplos de programas

### 1. Configuração válida — `meu_pc.dsl`

```text
computador MeuPC {
    processador Ryzen5 5600X
    placa_mae B550
    memoria 16 GB DDR4 3200MHz
    armazenamento SSD 1 TB
    fonte 650 W
    placa_video RTX3060 12GB
    gabinete ATX
}
```

**Saída esperada:**

```
Configuração válida!

cpu: Ryzen5
motherboard: B550
ram: {'capacidade': 16, 'unidade': 'GB', 'tipo': 'DDR4', 'frequencia': 3200}
storage: [{'tipo': 'SSD', 'capacidade': 1, 'unidade': 'TB'}]
psu: 650
gpu: {'nome': 'RTX3060', 'vram': 12}
case: ATX
```

### 2. Fonte insuficiente — `pc_erro_fonte.dsl`

```text
computador PC_Explosivo {
    processador Corei9 14900K
    placa_mae Z790
    memoria 32 GB DDR5 6000MHz
    armazenamento SSD 2 TB
    fonte 500 W
    placa_video RTX4090 24GB
    gabinete ATX
}
```

Aqui um Core i9 (250W) somado a uma RTX 4090 (450W) ultrapassa, com folga, os
500W declarados. O compilador acusa:

```
 Erros de validação:
- Fonte insuficiente! O PC consome aprox. 750W. Com margem de segurança, é
  recomendado no mín. 900W. Sua fonte atual é de 500W.
```

### 3. Soquete incompatível (exemplo livre)

```text
computador BuildErrada {
    processador Ryzen5 5600X
    placa_mae Z790
    memoria 16 GB DDR4 3200MHz
    armazenamento SSD 1 TB
    fonte 650 W
}
```

Um `Ryzen5` (soquete AM4) em uma placa `Z790` (soquete LGA1700) gera:

```
 Erros de validação:
- Soquete incompatível: Ryzen5 (AM4) ↔ Z790 (LGA1700)
- Memória DDR4 incompatível com Z790 (esperado DDR5)
```

---

## Componentes suportados (tabelas de referência)

**Placas-mãe / Soquete / DDR:**

| Soquete  | Placas-mãe                         | DDR        |
| -------- | ---------------------------------- | ---------- |
| AM4      | A320, B450, B550, X570             | DDR4       |
| AM5      | B650, X670                         | DDR5       |
| LGA1700  | H610, B660, Z690, Z790             | DDR4/DDR5  |
| LGA1200  | H410, B460, Z490                   | DDR4       |
| LGA1151  | H110, B360, Z390                   | DDR4       |
| LGA1155  | H61, B75                           | DDR3       |

**Processadores:** Ryzen3/5/7/9, Ryzen7000/9000, Corei3/5/7/9 (e variantes por
geração `_10G`, `_9G`, `_3G`).

**Placas de vídeo (com TDP):** GTX1060/1660, RTX2060/3060/3070/3080/4090,
RX580/6600/7600.

> As tabelas completas estão definidas no início de `DSL.py` e podem ser
> facilmente estendidas com novos modelos.
