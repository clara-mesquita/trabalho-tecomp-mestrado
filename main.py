import sys
from io_utils.output import salvar_afn
from conversores.glud_afn import converter_glud
from conversores.afn_dfa import converter_afn

def main():
    if len(sys.argv) < 4:
        print("Erro: algum dos 3 argumentos não foi fornecido: <operacao> <arquivo_entrada.txt> <cadeia>")
        sys.exit(1)

    operacao = sys.argv[1] 
    arquivo_entrada = sys.argv[2]

    if (operacao == 'glud'):
        
        cadeia = sys.argv[3]

        arquivo_afn_saida = './arquivos/afn_saida2.txt'

        converter_glud(arquivo_entrada)
    

    if (operacao == 'afn'):
        converter_afn(arquivo_entrada)



if __name__ == "__main__":
    main()