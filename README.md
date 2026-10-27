# Bar-Lua — BarbarQ 1.0.1811 no Windows (reconstrução fiel em Lua)

**Objetivo:** estudar um APK original do BarbarQ e reproduzir sua experiência no PC com **Lua e LÖVE2D**, sem emulador Android. Isto **não** é um jogo inspirado no BarbarQ. Os recursos recuperados servem de referência, mas portar a lógica original exige engenharia reversa adicional.

## Estado atual — Fase 4: animações originais

O projeto ainda é **um laboratório de visualização; não é uma versão jogável**.

- **VISPACK:** extrator de arquivos do APK 1.0.1811 (ARM64).
- **Mapas:** lê 32 mapas TMX base64/zlib e suas texturas; a câmera e o retículo são apenas ferramentas de investigação.
- **Atlas:** lê 171 `.bplist` FlatBuffers e 2 `.plist` XML; **13.875 recortes de sprites** catalogados. Uma textura referenciada não está presente no APK.
- **Animações:** lê os **1.079 `.bexportjson` binários (FlatBuffers)** e reconstrói os metadados de **1.079 armaduras, 2.657 movimentos, 7.452 trilhas de ossos e 38.727 keyframes**.
- **Nova aba F5:** seleção de animação e movimento, controle quadro a quadro, pausa/reprodução e prévia experimental com os sprites originais vinculados por nome ao atlas.
- **F1/F2/F3/F4:** painéis de mapa, imagens, atlas e configurações preservados.

**Limites da prévia F5:** a pose é um visualizador de dados (amostragem por último keyframe conhecido), não a animação final de Cocos. Ainda faltam composição hierárquica dos ossos, interpolações, rotações/skew, índices de display alternativos, ordem de desenho exata, coordenadas de referência, blending e velocidade original. A prévia usa 30 quadros/s **apenas como convenção de inspeção**. Uma pose visualmente diferente do jogo original **não** deve ser tomada como evidência de que o sprite ou a fonte estão errados.

**Não implementados:** controles de jogador, colisões, combate, IA, itens, menus operacionais, progressão, lobby e partidas online/offline. Ainda será necessária investigação do executável nativo e testes comparativos para uma portabilidade 1:1.

## Rodar o visualizador no Windows

Requisitos: [LÖVE2D 11.x](https://love2d.org/) e Python 3.10+.

```powershell
py tools/extrair_barbarq.py "C:\caminho\para\BarbarQ-1.0.1811.apk" --out assets_original
py tools/preparar_recursos.py --assets assets_original --out cache
& "C:\Program Files\LOVE\love.exe" .
```

Os ZIPs de teste **com recursos** já incluem `assets_original/` e `cache/`, então basta abrir a pasta com LÖVE2D. O ZIP **só com código** exige a extração a partir do APK local.

### Navegação

| Atalho | Operação |
|---|---|
| `F1` a `F5` | Mapas, imagens, atlas, configurações, animações |
| `↑` / `↓` e clique | Selecionar um arquivo na lista lateral (F2–F5) |
| Digitar / `Esc` | Filtrar ou limpar a lista (F2–F5) |
| `WASD` e roda do mouse | Câmara e zoom na inspeção de mapas |
| `[` / `]` | Trocar sprite na aba de atlas F3 |
| `Espaço` | Pausar/continuar prévia F5 |
| `←` / `→` | Voltar/avançar um quadro F5 (pausa automaticamente) |
| `Tab` / `Shift+Tab` | Trocar de movimento F5 |

## Estrutura

| Diretório/arquivo | Papel |
|---|---|
| `tools/extrair_barbarq.py` | Extrai recursos do VISPACK |
| `tools/bplist.py` | Decodifica atlas `.bplist` com validação de limites |
| `tools/bexport.py` | Decodifica animações `.bexportjson` sem executar dados externos |
| `tools/preparar_recursos.py` | Converte mapas, atlas e animações para cache Lua local |
| `src/animation_view.lua` | Inspeção experimental de poses e keyframes |
| `main.lua`, `conf.lua` | Interface LÖVE2D |
| `tests/` | Testes Python; casos malformados e integração opcional |
| `assets_original/` | Recursos locais do APK; **ignorado pelo Git** |
| `cache/` | Dados locais gerados; **ignorado pelo Git** |

## Auditoria da Fase 4

```powershell
py -m unittest discover -s tests -v
py tools/preparar_recursos.py --assets assets_original --out cache
```

Os **9 testes Python passaram**, inclusive a validação de todos os 1.079 arquivos binários e dos atlas do APK fornecido. A sintaxe dos arquivos Lua é verificada separadamente. **Ainda não houve teste visual no LÖVE2D/Windows neste ambiente**, então é necessário validar as prévias na execução real antes de declarar fidelidade gráfica.

## Próximas frentes

1. Confirmar layout e transformações de ossos (Cocos Studio), índices alternativos de displays, z-order, interpolação, curvas e taxa real de reprodução.
2. Decodificar cenas `.csb`, modelos `.c3b` e informações de configuração pertinentes à jogabilidade.
3. Reconstruir a movimentação, entidades, física e combate com testes de referência 1:1.
4. Investigar e, se viável, substituir serviços de rede por uma infraestrutura independente.

Este repositório público distribui somente o código-fonte da investigação. **Não publica** o APK, texturas, áudio, modelos ou outros recursos protegidos do jogo. Use sua própria cópia autorizada do APK para extrair os arquivos localmente.