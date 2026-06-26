import sys

from lark import Lark, Token, Tree

# ========== GRAMÁTICA ==========
grammar = r"""
?start: computador

computador: "computador" NOME "{" (processador | placa_mae | memoria | armazenamento | fonte | placa_video | gabinete)+ "}" -> computador

processador: "processador" NOME GERACAO? -> cpu
placa_mae: "placa_mae" NOME -> motherboard
memoria: "memoria" CAPACIDADE UNIDADE NOME FREQUENCIA? -> ram
armazenamento: "armazenamento" TIPO_ARMAZ CAPACIDADE UNIDADE -> storage
fonte: "fonte" POTENCIA "W" -> psu
placa_video: "placa_video" NOME VRAM? -> gpu
gabinete: "gabinete" NOME -> case

NOME: /[A-Za-z0-9_]+/
GERACAO: /[A-Za-z0-9_]+/
CAPACIDADE: /[0-9]+/
UNIDADE: "GB" | "TB"
POTENCIA: /[0-9]+/
FREQUENCIA: /[0-9]+MHz/
TIPO_ARMAZ: "SSD" | "HDD"
VRAM: /[0-9]+GB/

%ignore /\s+/
"""

# ========== TABELAS DE VALIDAÇÃO ==========
socket_motherboard = {
    # AMD
    "A320": "AM4", "B450": "AM4", "B550": "AM4", "X570": "AM4",
    "B650": "AM5", "X670": "AM5",
    # Intel LGA1700 (12ª a 14ª Geração)
    "H610": "LGA1700", "B660": "LGA1700", "Z690": "LGA1700", "Z790": "LGA1700",
    # Intel LGA1200 (10ª e 11ª Geração)
    "H410": "LGA1200", "B460": "LGA1200", "Z490": "LGA1200",
    # Intel LGA1151 (6ª a 9ª Geração)
    "H110": "LGA1151", "B360": "LGA1151", "Z390": "LGA1151",
    # Intel LGA1155 (2ª e 3ª Geração)
    "H61": "LGA1155", "B75": "LGA1155"
}

socket_cpu = {
    "Ryzen3": "AM4", "Ryzen5": "AM4", "Ryzen7": "AM4", "Ryzen9": "AM4",
    "Ryzen7000": "AM5", "Ryzen9000": "AM5", 
    "Corei3": "LGA1700", "Corei5": "LGA1700", "Corei7": "LGA1700", "Corei9": "LGA1700",
    "Corei5_10G": "LGA1200", "Corei7_10G": "LGA1200",
    "Corei5_9G": "LGA1151", "Corei7_9G": "LGA1151",
    "Corei5_3G": "LGA1155", "Corei7_3G": "LGA1155"
}

ddr_type = {
    # DDR3
    "H61": "DDR3", "B75": "DDR3",
    # DDR4
    "H110": "DDR4", "B360": "DDR4", "Z390": "DDR4",
    "H410": "DDR4", "B460": "DDR4", "Z490": "DDR4",
    "A320": "DDR4", "B450": "DDR4", "B550": "DDR4", "X570": "DDR4",
    # DDR5
    "B650": "DDR5", "X670": "DDR5",
    "Z790": "DDR5"
}

# Consumo estimado em Watts (TDP)
tdp_cpu = {
    "Ryzen3": 65, "Ryzen5": 65, "Ryzen7": 105, "Ryzen9": 170,
    "Ryzen7000": 105, "Ryzen9000": 170,
    "Corei3": 60, "Corei5": 65, "Corei7": 125, "Corei9": 250,
    "Corei5_10G": 65, "Corei7_10G": 125,
    "Corei5_9G": 65, "Corei7_9G": 95,
    "Corei5_3G": 77, "Corei7_3G": 77
}

tdp_gpu = {
    "GTX1060": 120, "GTX1660": 120,
    "RTX2060": 160, "RTX3060": 170, "RTX3070": 220, "RTX3080": 320, "RTX4090": 450,
    "RX580": 185, "RX6600": 132, "RX7600": 165
}

formato_case_suporta = {
    "ATX": ["ATX", "MicroATX", "MiniITX"],
    "MicroATX": ["MicroATX", "MiniITX"],
    "MiniITX": ["MiniITX"],
}


# ========== FUNÇÃO DE ANÁLISE ==========
def analisar(texto):
    parser = Lark(grammar, parser="lalr")
    arvore = parser.parse(texto)

    config = {
        "cpu": None,
        "motherboard": None,
        "ram": None,
        "storage": [],
        "psu": None,
        "gpu": None,
        "case": None,
    }
    erros = []

    for child in arvore.children:
        if not isinstance(child, Tree):
            continue

        try:
            match child.data:
                case "cpu":
                    # filhos: [NOME, GERACAO?]
                    if len(child.children) >= 1:
                        config["cpu"] = str(child.children[0])
                    else:
                        erros.append("Processador sem nome.")
                case "motherboard":
                    # filhos: [NOME]
                    if len(child.children) >= 1:
                        config["motherboard"] = str(child.children[0])
                    else:
                        erros.append("Placa-mãe sem nome.")
                case "ram":
                    # filhos: [CAPACIDADE, UNIDADE, NOME, FREQUENCIA?]
                    if len(child.children) < 3:
                        erros.append("Memória RAM com campos insuficientes.")
                    else:
                        cap = int(child.children[0])
                        unidade = str(child.children[1])
                        tipo = str(child.children[2])
                        freq = None
                        if len(child.children) >= 4:
                            freq_str = str(child.children[3])  # ex: "3200MHz"
                            freq = int(freq_str.replace("MHz", ""))
                        config["ram"] = {
                            "capacidade": cap,
                            "unidade": unidade,
                            "tipo": tipo,
                            "frequencia": freq,
                        }
                case "storage":
                    # filhos: [TIPO_ARMAZ, CAPACIDADE, UNIDADE]
                    if len(child.children) < 3:
                        erros.append("Armazenamento com campos insuficientes.")
                    else:
                        tipo = str(child.children[0])
                        cap = int(child.children[1])
                        unidade = str(child.children[2])
                        config["storage"].append(
                            {"tipo": tipo, "capacidade": cap, "unidade": unidade}
                        )
                case "psu":
                    # filhos: [POTENCIA]
                    if len(child.children) >= 1:
                        config["psu"] = int(child.children[0])
                    else:
                        erros.append("Fonte sem potência.")
                case "gpu":
                    # filhos: [NOME, VRAM?]
                    if len(child.children) >= 1:
                        nome = str(child.children[0])
                        vram = None
                        if len(child.children) >= 2:
                            vram_str = str(child.children[1])  # ex: "12GB"
                            vram = int(vram_str.replace("GB", ""))
                        config["gpu"] = {"nome": nome, "vram": vram}
                    else:
                        erros.append("Placa de vídeo sem nome.")
                case "case":
                    # filhos: [NOME]
                    if len(child.children) >= 1:
                        config["case"] = str(child.children[0])
                    else:
                        erros.append("Gabinete sem nome.")
        except (IndexError, ValueError) as ex:
            erros.append(f"Erro ao processar '{child.data}': {ex}")

    # --- Validações de obrigatoriedade ---
    if not config["cpu"]:
        erros.append("Processador obrigatório")
    if not config["motherboard"]:
        erros.append("Placa-mãe obrigatória")
    if not config["ram"]:
        erros.append("Memória RAM obrigatória")
    if not config["storage"]:
        erros.append("Pelo menos 1 armazenamento obrigatório")
    if not config["psu"]:
        erros.append("Fonte obrigatória")

    # --- Compatibilidade CPU ↔ Placa-mãe (soquete) ---
    if config["cpu"] and config["motherboard"]:
        cpu_model = config["cpu"].split()[0]
        mobo = config["motherboard"]
        if mobo not in socket_motherboard:
            erros.append(f"Placa-mãe '{mobo}' não reconhecida")
        elif cpu_model not in socket_cpu:
            erros.append(f"Processador '{config['cpu']}' não reconhecido")
        elif socket_motherboard[mobo] != socket_cpu[cpu_model]:
            erros.append(
                f"Soquete incompatível: {cpu_model} ({socket_cpu[cpu_model]}) ↔ {mobo} ({socket_motherboard[mobo]})"
            )

    # --- Compatibilidade memória (DDR) ---
    if config["motherboard"] and config["ram"]:
        mobo = config["motherboard"]
        if mobo in ddr_type:
            if ddr_type[mobo] != config["ram"]["tipo"]:
                erros.append(
                    f"Memória {config['ram']['tipo']} incompatível com {mobo} (esperado {ddr_type[mobo]})"
                )
        else:
            erros.append(f"Placa-mãe '{mobo}' sem informação de DDR")

# --- Cálculo Robusto de Potência da Fonte ---
    if config["psu"]:
        # 50W base para placa-mãe, RAM, fans e armazenamento
        consumo_total = 50 

        # Adiciona o consumo do Processador
        if config["cpu"]:
            cpu_model = config["cpu"].split()[0]
            # Se não achar o CPU na lista, assume 65W por padrão
            consumo_total += tdp_cpu.get(cpu_model, 65) 

        # Adiciona o consumo da Placa de Vídeo
        if config["gpu"]:
            gpu_name = config["gpu"]["nome"]
            # Se não achar a GPU na lista, assume 150W por padrão
            consumo_total += tdp_gpu.get(gpu_name, 150)

        # Margem de segurança de 20%  para picos de consumo e futuras atualizações 
        fonte_recomendada = consumo_total * 1.2

        if config["psu"] < fonte_recomendada:
            erros.append(
                f"Fonte insuficiente! O PC consome aprox. {consumo_total}W. "
                f"Com margem de segurança, é recomendado no mín. {int(fonte_recomendada)}W. "
                f"Sua fonte atual é de {config['psu']}W."
            )

    # --- Gabinete x Formato da placa-mãe ---
    if config["case"] and config["motherboard"]:
        formato_mobo = "ATX"
        case = config["case"]
        if case in formato_case_suporta:
            if formato_mobo not in formato_case_suporta[case]:
                erros.append(f"Gabinete {case} não suporta placas {formato_mobo}")
        else:
            erros.append(f"Gabinete '{case}' não cadastrado")

    if erros:
        raise Exception("Erros de validação:\n- " + "\n- ".join(erros))

    return config


# ========== EXECUÇÃO PRINCIPAL ==========
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 DSL.py <arquivo.dsl>")
        sys.exit(1)

    arquivo = sys.argv[1]
    try:
        with open(arquivo, "r") as f:
            texto = f.read()
        resultado = analisar(texto)
        print("\nConfiguração válida!\n")
        for k, v in resultado.items():
            print(f"{k}: {v}")
    except Exception as e:
        print("\n", e)
