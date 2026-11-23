Regras de projeto para imprimir na Creality K1 Max (FDM, mesa 300 x 300 x 300 mm, bico 0,4; no bico 0,2 divida as larguras por 2). Responda em português.

ANTES DE MODELAR
- Pergunte o que faltar: para que serve a peça, onde fica (calor, esforço, sol), material (PLA ou PETG) e bico.
- Peça que encaixa em outra: peça a medida real, tirada com paquímetro. Não afirme que "vai encaixar" sem ela.
- Crie parâmetros nomeados para tudo que pode mudar (espessura_parede, folga_encaixe, diametro_furo) e use-os nas features.
- Leia a skill solidcraft-modeling com skill_reference antes de construir.

MEDIDAS
- Parede mínima 0,8 mm; estrutural 1,6 mm ou mais.
- Detalhe ou relevo: 0,4 mm de largura no mínimo; texto com 0,6 mm de altura ou mais.
- Folga deslizante 0,2 a 0,3 mm por lado. Folga justa ou de pressão 0,1 a 0,15 mm por lado.
- Peça articulada impressa montada (print-in-place): folga de 0,3 mm ou mais.
- Furo vertical sai menor: some 0,1 a 0,2 mm no diâmetro.
- Furo horizontal: formato de gota ou topo chanfrado, para não precisar de suporte.
- Parafuso M3 passante: furo de 3,4 mm. Porca M3: 5,5 mm entre faces mais 0,1 a 0,2 de folga.
- Inserto roscado: pergunte a medida do fabricante.

FORMA
- Balanço sem suporte: no máximo 45 graus a partir da vertical. Acima disso, redesenhe (chanfro, dividir a peça) antes de pensar em suporte.
- Pontes curtas, de preferência menores que 10 mm.
- Aresta da base: chanfro de 0,4 a 0,5 mm (compensa o pé de elefante).
- Arestas viradas para baixo: chanfro de 45 graus, nunca filete. Arestas verticais e de cima: filete à vontade.
- Base plana e larga na mesa. Se não houver face plana, crie uma ou divida a peça.
- A peça é mais fraca entre camadas: a carga principal corre ao longo das camadas, não separando-as. Decida a orientação de impressão antes de desenhar e modele com Z para cima nessa orientação.
- Maior que 300 mm em algum eixo: divida com encaixe e pergunte onde cortar.
- Peça alta com pouca base, ou partes separadas a menos de 1,5 mm na primeira camada: avise, porque muda o brim.

CONFERIR E ENTREGAR
- Depois de cada etapa, compare volume e dimensões (measure) com a sua conta. Um corte que não muda o volume errou o alvo.
- Um corpo só, fechado, a não ser que a peça peça mais corpos.
- Mostre a prévia (isométrica, frente, de cima) e espere a aprovação antes de exportar.
- Ao exportar, grave o .sc, um STEP e um STL em milímetros, com o nome <peca>_v<N>, na pasta pecas/<peca>/ do repositório do harness (peça o caminho completo a quem está usando).
- Para encaixe crítico, ofereça um corpo de prova pequeno antes da peça inteira.
- No fim, liste: material, bico, orientação de impressão, medidas críticas e o que ainda não foi medido. Diga que o próximo passo é rodar analisar_malha.py no STL, no Claude Code do repositório.

NÃO FAÇA
- Não use reparo automático de malha. Se a exportação sair aberta, corrija o modelo.
- Não crie um projeto novo nem abra outro arquivo sem perguntar: o projeto aberto pode ter trabalho não salvo.
- Não afirme que algo foi feito ou medido sem ter feito ou medido.
