from io_utils.parser import parser_gramatica
from typing import List, Tuple, Set, Optional

def producoes_gramatica(caminho):
    estado_ini, terminais, nao_terminais, linhas  = parser_gramatica(caminho)
    producoes: List[Tuple[str, str, Optional[str]]] = []

    for linha in linhas:
        if '->' not in linha:
            raise ValueError(f"Produção sem '->' ou formato inválido: '{linha}'")

        esquerda, corpo = linha.split('->', 1)
        esquerda = esquerda.strip()  
        corpo    = corpo.strip()     # ex.: "aB" ou "b" ou "ε"

        # Verifica se a cabeça foi declarada em Q:{…}
        if esquerda not in nao_terminais:
            raise ValueError(f"Não-terminal (esquerda) não declarado em Q")

        # Caso 1: produção A -> ε
        if corpo == 'ε':
            producoes.append((esquerda, 'ε', None))

        # Caso 2: produção A -> a  
        elif len(corpo) == 1:
            sym = corpo
            if sym not in terminais:
                raise ValueError(f"Terminal '{sym}' não contido em Σ")
            producoes.append((esquerda, sym, None))

        # Caso 3: produção A -> aB  
        elif len(corpo) == 2:
            sym, prox_nt = corpo[0], corpo[1]
            if sym not in terminais:
                raise ValueError(f"Terminal '{sym}' não contido em Σ")
            if prox_nt not in nao_terminais:
                raise ValueError(f"Não-terminal não contido em Q")
            producoes.append((esquerda, sym, prox_nt))

        # Qualquer outro comprimento é inválido
        else:
            raise ValueError(f"Produção fora do padrão GLUD")

    return estado_ini, terminais, nao_terminais, producoes

def produzir_afn(estado_ini, terminais, nao_terminais, producoes):
    estados = nao_terminais.union({'qf'})
    estado_fin = 'qf'
    transicoes = []

    for esq, simbolo, dir in producoes:
        if simbolo == 'ε':
            transicoes.append((esq, 'ε', estado_fin))
        elif dir is None:
            transicoes.append((esq, simbolo, estado_fin))
        else:
            transicoes.append((esq, simbolo, dir))

    return estados, terminais, transicoes, estado_ini, estado_fin

def renomear_estados_afn(estados, nao_terminais, transicoes, estado_ini, estado_fin):
    lista_estados = sorted(nao_terminais)
    mapeamento = {}

    lista_estados = sorted(estados)
    mapeamento = {}
    for idx, est in enumerate(lista_estados):
        mapeamento[est] = f"q{idx}"
    novos_estados = set(mapeamento.values())

    novas_transicoes = []
    for origem, simbolo, destino in transicoes:
        nova_origem = mapeamento[origem]
        if (destino == None):
            novo_destino = None
        else:
            novo_destino = mapeamento[destino]
        novas_transicoes.append((nova_origem, simbolo, novo_destino))

    novo_inicial = mapeamento[estado_ini]
    novo_final = mapeamento[estado_fin]

    return novos_estados, novas_transicoes, novo_inicial, novo_final

def converter_glud_para_afn(arquivo_entrada):
    estado_ini, terminais, nao_terminais, producoes = producoes_gramatica(arquivo_entrada)

    estados, terminais, transicoes, estado_ini, estado_fin = produzir_afn(estado_ini, terminais, nao_terminais, producoes)
    print("Autômato finito gerado a partir da GLUD:")
    print(f"Estado inicial: {estado_ini}")
    print(f"Estado final: {estado_fin}")
    for origem, simbolo, destino in transicoes:
        print(f"{origem}, {simbolo} -> {destino}")   

    novos_estados, novas_producoes, novo_inicial, novo_fin = renomear_estados_afn(estados, nao_terminais, transicoes, estado_ini, estado_fin)
    print("Autômato finito com novos estados:")
    print(f"Estado inicial: {novo_inicial}")
    print(f"Estado final: {novo_fin}")
    for origem, simbolo, destino in novas_producoes:
        print(f"{origem}, {simbolo} -> {destino}")   

    return novos_estados, terminais, novas_producoes, novo_inicial, novo_fin



