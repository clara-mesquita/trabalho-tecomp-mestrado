from collections import defaultdict

def remover_caracteres_extra(s):
    """
    Dado algo como '{A}, {B}, ∅' ou '{{X}, {Y}}, {Z}', retorna:
      ['{A}', '{B}', '∅'] ou ['{{X}, {Y}}', '{Z}']
    """
    elementos = []
    it = 0
    atual = []
    for ch in s:
        if ch == '{':
            it += 1
            atual.append(ch)
        elif ch == '}':
            it -= 1
            atual.append(ch)
        elif ch == ',' and it == 0:
            elementos.append("".join(atual).strip())
            atual = []
        else:
            atual.append(ch)
    if atual:
        elementos.append("".join(atual).strip())
    return elementos

def extrair_afn_arquivo(caminho_arqiuvo):
    """
    Lê um AFD (completo e determinístico) de um arquivo de texto no formato:

    Q: {A}, {QF_S}, ∅
    Σ: a, b
    Δ:
    {A}, a -> ∅
    {A}, b -> {QF_S}
    {QF_S}, a -> {A}
    {QF_S}, b -> ∅
    ∅, a -> ∅
    ∅, b -> ∅
    q0: {QF_S}
    F: {{QF_S}}

    """
    estados = set()
    alfabeto = set()
    transicoes = defaultdict(lambda: defaultdict(set))
    inicial = ""
    finais = set()

    with open(caminho_arqiuvo, "r", encoding="utf-8") as f:
        linhas = [linha.strip() for linha in f if linha.strip() and not linha.startswith("#")]

    lendo_trans = False
    for linha in linhas:
        if linha.startswith("Q:"):
            rhs = linha.split(":", 1)[1].strip()
            # remove o 'Q:' e pega a parte à direita
            for item in remover_caracteres_extra(rhs):
                estados.add(item)
            continue

        # Σ: a, b
        if linha.startswith("Σ") or linha.startswith("S"):
            linha_trans = linha.split(":", 1)[1].strip()
            for simb in [tok.strip() for tok in linha_trans.split(",")]:
                alfabeto.add(simb)
            continue

        # δ:
        if linha.startswith("Δ:") or linha.startswith("δ:"):
            lendo_trans = True
            continue

        # Linhas de transição: "{A}, a -> ∅"
        if lendo_trans and "->" in linha:
            esquerda, direita = linha.split("->")
            esquerda = esquerda.strip()
            direita = direita.strip()

            parte_estado, parte_simb = (s.strip() for s in esquerda.split(",", 1))
            estado = parte_estado
            simbolo = parte_simb

            prox_estado = direita
            transicoes[estado][simbolo].add(prox_estado)
            continue

        # q0: {QF_S}
        if ": " in linha and "inicial" not in linha and "F:" not in linha:
            # Detecta a linha que especifica estado inicial,
            # pode vir como "q0: {QF_S}" ou "{algum}: {BLA}"
            # mas no nosso caso, esperamos algo na forma “q0: {ESTADO}”.
            a = linha.split(":", 1)[1].strip()
            inicial = a
            continue

        # F: {{QF_S}}
        if linha.startswith("F:"):
            linha_finais = linha.split(":", 1)[1].strip()
            if linha_finais.startswith("{") and linha_finais.endswith("}"):
                inner = linha_finais[1:-1].strip()     # << correção aqui
                for item in remover_caracteres_extra(inner):
                    finais.add(item)

    return estados, alfabeto, transicoes, inicial, finais

def reverter_afd_para_afn(estados, alfabeto, transicoes, inicial, finais):
    """
    Dado um DFA (full, deterministic), constrói um NFA-λ que reconhece a linguagem inversa:
      • Novo alfabeto = mesmo alfabeto original.
      • Transições invertidas: se no DFA havia p --a--> q, no NFA teremos q --a--> p.
      • Criamos um novo estado inicial "I_rev" (string fixa) que faz ε-> sobre cada
        antigo estado final. (I_rev é só string, não pertencia a states ainda.)
      • O(s) novo(s) estado(s) final(is) do NFA-reverso é(ão) { initial_original }.
      • Retornamos (new_states, alphabet, new_transitions, new_initial, new_finals).
    """
    novos_estados = set(estados)  
    novas_transicoes = defaultdict(lambda: defaultdict(set))

    # inverte todas as transições originais:
    for p, mapa in transicoes.items():
        for a, dests in mapa.items():
            for q in dests:
                # p --a--> q  vira  q --a--> p
                novas_transicoes[q][a].add(p)

    # cria um novo estado inicial “I_rev” que faz ε -> cada final original
    I_rev = "I_rev"
    novos_estados.add(I_rev)
    for f in finais:
        novas_transicoes[I_rev]["ε"].add(f)

    # nó final do NFA reverso é o inicial original
    novos_finais = {inicial}

    return novos_estados, alfabeto, novas_transicoes, I_rev, novos_finais

def simular_afd(transicoes, inicial, finais, w):
    """
    Simula uma cadeia w num DFA determinístico completo:
      • transicoes: dict de forma transicoes[state][symbol] → set(next_states)
      • inicia em 'inicial'
      • pra cada símbolo c em w, faz:
          proximo = qualquer elemento de transicoes[current][c]
      • retorna True se, ao final, current ∈ finais
    """
    atual = inicial
    for simb in w:
        # pega o conjunto de destinos; se não existir, falha
        destinos = transicoes.get(atual, {}).get(simb)
        if not destinos:
            return False
        # como é determinístico, deve haver exatamente um destino
        atual = next(iter(destinos))   
    return atual in finais

def fechamento_afd(transicoes_afn, estados):
    fecho = set(estados)
    for estado in estados:
        changed = True
        while changed:
            changed = False
            for q in list(fecho):
                for r in transicoes_afn[q].get("ε", []):  
                    if r not in fecho:
                        fecho.add(r)
                        changed = True
    return fecho

def simular_afn(transicoes_afn, inicial, finais, w):
    """
    Simula cadeia w num NFA com transições vazias
    """
    estados_atuais = fechamento_afd(transicoes_afn, {inicial})

    for c in w:
        prox_cadeia = set()
        for p in estados_atuais:
            prox_cadeia |= transicoes_afn[p].get(c, set()) 
        estados_atuais = fechamento_afd(transicoes_afn, prox_cadeia)

    return bool(estados_atuais & finais)


def aplicar_reverso_complemento_afd(caminho_afd, cadeia):
    estados, alfabeto, transicoes, inicial, finais = extrair_afn_arquivo(caminho_afd)

    print("\n— AFD de Entrada —")

    novos_finais = estados - finais
    print("\n--- AFD COMPLEMENTO ---")
    print("Estados AFD:", estados)
    print("Estado inicial AFD:", inicial)
    print("Estados finais AFD:", novos_finais)
    print("Transições AFD:")
    for p, mapa in transicoes.items():
        for a, dests in mapa.items():
            print(f"{p}, {a} -> {dests}")

    # 3) Gera o reverso do AFD (como um NFA-λ):
    estados_rev, rev_alpha, transicoes_rev, inicial_rev, finais_rev = reverter_afd_para_afn(estados, alfabeto, transicoes, inicial, finais)
    print("\n--- AFN-ε REVERSO ---")
    print("Estados AFN:", sorted(estados_rev))
    print("Estado inicial AFN:", inicial_rev)
    print("Estados finais AFN:", finais_rev)
    print("Transições AFN:")
    for p, mapa in transicoes_rev.items():
        for a, dests in mapa.items():
            print(f"{p}, {a} -> {dests}")

    # 4) Simula w:
    print(f"\nSimulação da cadeia w = '{cadeia}':")
    aceita_comp = simular_afd(transicoes, inicial, novos_finais, cadeia)
    print(f"  • Em AFD Complemento: {'ACEITA' if aceita_comp else 'REJEITA'}")

    aceita_rev = simular_afn(transicoes_rev, inicial_rev, finais_rev, cadeia)
    print(f"  • Em AFN-λ Reverso: {'ACEITA' if aceita_rev else 'REJEITA'}")
