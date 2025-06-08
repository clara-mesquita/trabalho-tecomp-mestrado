import re 
from typing import List, Tuple, Set, Optional
from collections import defaultdict, deque

def tratar_linhas_arquivo(caminho_arquivo):
    primeira_linha = None
    linhas = []

    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        for raw in f:
            conteudo = raw.strip()
            if not conteudo:
                continue

            if primeira_linha is None:
                primeira_linha = conteudo
                continue

            if conteudo.startswith('#'):
                continue

            linhas.append(conteudo)

    return primeira_linha, linhas


def parser_gramatica(caminho):
    primeira_linha, linhas = tratar_linhas_arquivo(caminho)
    print(f'primeira linha: {primeira_linha}')

    padrao = re.compile(
        r"""
        Gramática      
        \s*:\s*        
        G              
        \s*=\s*\(      
            \{\s*([^}]*)\s*\}         # grupo(1) = não-terminais entre chaves
            \s*,\s*\{\s*([^}]*)\s*\}  # grupo(2) = terminais entre chaves
            \s*,\s*P\s*,\s*           # descarta o “P”
            ([^\s\)]+)                # grupo(3) = símbolo/estado inicial
        \s*\)

        """,
        re.VERBOSE
    )
    match = padrao.search(primeira_linha)
    if not match:
        raise ValueError(
            f"Formato inesperado no cabeçalho da gramática: {primeira_linha!r}\n"
            "Use: Gramática: G = ({nao_terminais}, {terminais}, P, estado_inicial)"
        )
    
    nao_terminais: Set[str] = set()
    for x in match.group(1).split(','):
        sym = x.strip()
        if sym:
            nao_terminais.add(sym)

    terminais: Set[str] = set()
    for x in match.group(2).split(','):
        sym = x.strip()
        if sym:
            terminais.add(sym)

    estado_ini = match.group(3)

    return estado_ini, terminais, nao_terminais, linhas 

def parse_afn(file_path):
    """
    states: lista de todos os estados do AFN.

    alphabet: o alfabeto (Σ) desse AFN, embora nem seja usado diretamente nesta etapa.

    initial_state: o estado inicial (q0) do AFN.

    final_states: conjunto de estados finais.

    nfa_table: um dicionário que mapeia cada estado para outro dicionário de transições.
    Ou seja, nfa_table[q][a] = lista de estados alcançáveis a partir de q via símbolo a.

    """
    nfa_table = defaultdict(lambda: defaultdict(list))
    states = set()
    alphabet = set()
    initial_state = None
    final_states = set()

    _, linhas = tratar_linhas_arquivo(file_path)

    reading_transitions = False
    for line in linhas:
        if line.startswith("Q:"):
            states = {s.strip() for s in line.split(":", 1)[1].split(",")}
            continue

        if line.startswith("∑"):
            alphabet = {s.strip() for s in line.split(":", 1)[1].split(",")}
            continue

        if line.startswith("δ:"):
            reading_transitions = True
            continue

        if reading_transitions and "->" in line:
            left, right = line.split("->")
            left = left.strip()
            right = right.strip()
            state, symbol = (s.strip() for s in left.split(","))
            # Aqui mantemos 'ε' como símbolo especial:
            dest_state = right
            nfa_table[state][symbol].append(dest_state)
            continue

        if ": inicial" in line:
            initial_state = line.split(":", 1)[0].strip()
            continue

        if line.startswith("F:"):
            final_states = {s.strip() for s in line.split(":", 1)[1].split(",")}
            continue

    return states, alphabet, initial_state, final_states, nfa_table