# Conciliação — o que falta

Fonte: `conciliacao-mapa.md`. Sem chamada. Sem senha.

O mapa do processo está fechado. O gabarito numérico da 1200 não.

## Já fechado

- Só Valen Lubrificantes. Atlas sinaliza. Não baixa, não estorna, não entra no banco, não chama POST.
- D-1. Segunda olha a sexta. Sem extrato, para.
- 1305, 1104 e 1200 existem. Ata de 28/09. Caixa 4 é Bradesco, não filial.
- Subcontas: 30060001 tarifa, 30060005 aplicação, 30060006 resgate.
- `X-Tenant` é a chave do mgerencia, não o domínio. O valor não entra em arquivo.
- Login da tela autentica na REST. `idUsuario` 82. Filial 1 é MATRIZ. Não é o caixa 4.
- Pix e BOL apareceram na baixa do 25. Cielo não veio nesse GET.

## Ainda bloqueia

1. Credencial no cofre. Sem ela, a leitura diária do Query não roda daqui. O teste de 29/09 foi só arquivo.
2. Segundo dia no mesmo pacote: OFX, PDF, CSV Cielo, relatório Query.
3. Nome do campo de NSU na API.
4. Planilha Fluxo de Caixa LUB. Não vista.
5. Telas 1111 e 1100. A ata não cravou.
6. 36,01 com o contas a receber. No OFX do 25 é um Pix, não tarifa e não é os 36,08 da Cielo.

API da Cielo não bloqueia. Enquanto não existir, entra CSV.
