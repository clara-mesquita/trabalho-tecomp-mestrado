#!/usr/bin/env python3
import sys
from conversores.glud_afn import converter_glud
from conversores.afn_afd import converter_afn
from conversores.rev_comp import aplicar_reverso_complemento_afd

USO = """
Uso:
  script.py glud <entrada> <saida>
  script.py afn  <entrada> <saida>
  script.py afd  <entrada> <saida_complemento> <saida_reverso> <cadeia>
"""

def main():
    args = sys.argv[1:]
    if not args:
        print(USO)
        sys.exit(1)

    operacao = args[0]

    if operacao == 'glud':
        _, entrada, saida = args
        converter_glud(entrada, saida)

    elif operacao == 'afn':
        sys.exit(1)
        _, entrada, saida = args
        converter_afn(entrada, saida)

    elif operacao == 'afd':
        _, entrada, comp, rev, cadeia = args
        aplicar_reverso_complemento_afd(entrada, comp, rev, cadeia)

if __name__ == "__main__":
    main()
