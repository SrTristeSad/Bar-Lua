# Bar-Lua — BarbarQ 1.0.1811 no Windows (reconstrução fiel em Lua)

**Objetivo:** estudar um APK original do BarbarQ e reproduzir sua experiência no PC com **Lua e LÖVE2D**, sem emulador Android. Isto **não** é um jogo inspirado no BarbarQ. Os recursos recuperados servem de referência, mas portar a lógica original exige engenharia reversa adicional.

## Fase 12 — fluxo estático de funções ARM64 (não jogável)

A ferramenta **`tools/analisar_fluxo.py`** usa `llvm-objdump` para examinar **10 funções** com endereços e tamanhos identificados na Fase 11. Confere o SHA-256 da `libcocos2dcpp.so` antes de analisar e produz `reports/native_flow.json` e `reports/native_flow.lua`, contendo **somente metadados** (quantidade de instruções, chamadas diretas `BL`, indiretas `BLR`, desvios condicionais e nomes de alvos). Os relatórios não contêm bytes de executável nem instruções copiadas.

- **1.576 instruções** de 10 funções ARM64 verificadas nos endereços originais.
- `Hero::setStickDir(int)` contém apenas `str` seguido de `ret`, o que é evidência de armazenamento de um argumento numa posição da estrutura (não demonstra a escala ou regra do movimento).
- `GameScene::updateStick()` referencia a construção de `COperateMessage__ThumbnailMove` e `BattleNet::SendCmd` com esse tipo de mensagem, mostrando uma ligação entre controle e envio de operações.
- `GameScene::updateLogicFrame(float)` tem chamadas para `BattleManager`, `BattleNet`, `ReplaySystem` e `SpectatorSystem`. Um alvo estático **não comprova** que a chamada é executada em todas as partidas.
- `CSkill::Update(float)` nesta biblioteca específica contém **uma única instrução de retorno**; isso não significa que o sistema de habilidades inteiro seja vazio.
- **F8 Fluxo ARM64:** aba somente leitura para consultar os alvos estáticos e contadores por função; F1–F7 preservadas. Não executa instruções nativas.

Para reproduzir o relatório com a **mesma versão 1.0.1811** do APK (Windows: LLVM instalado no PATH ou WSL):

```powershell
py tools/analisar_fluxo.py --apk "C:\caminho\BarbarQ-1.0.1811.apk" --symbols reports/native_symbols.csv --manifest reports/native_arm64.json --out reports
py -m unittest discover -s tests -v
```

**Limitações:** a listagem identifica transferências de controle no código compilado, não é rastreamento dinâmico, não identifica destinos de chamadas indiretas por vtables, não reconstrói variáveis, protocolos completos, IA, colisões, fórmulas ou gameplay. Nenhuma funcionalidade jogável foi reivindicada. Não foi realizado teste gráfico real no Windows.

## Estado atual — Fase 11: símbolos do motor nativo ARM64

O projeto ainda é **um laboratório de visualização; não é uma versão jogável**.

### Investigação da biblioteca nativa (Fase 11)

- `tools/auditar_elf.py`: audita exclusivamente arquivos ELF64 AArch64 dentro do **APK local**. Usa `readelf` e `c++filt`, sem carregar ou executar bibliotecas. Valida cabeçalho, tamanho máximo e diretórios permitidos antes de analisar.
- `libcocos2dcpp.so` (aprox. 38,1 MiB) é marcado como *stripped*, mas preserva **83.660 entradas anunciadas** de `.dynsym` (83.658 entradas com nome interpretáveis pelo leitor), incluindo funções C++ nomeadas do jogo. Isso fornece pontos de partida para análise dirigida; não equivale à recuperação de código-fonte ou algoritmos.
- O relatório extrai e classifica **586 símbolos de métodos** em 12 classes de interesse (`GameScene`, `BattleNet`, `BattleManager`, `BattleFieldController`, `GameLayer`, `Hero`, `CSkill`, `CSkillEntity`, `CMoveEdge`, `ViewMoveEdge`, `BattleDataManager`, `UILayer`). Exemplos efetivamente presentes: `BattleNet::processFrameUpdate`, `GameScene::processPursueFrame`, `Hero::setStickDir`, `CSkill::Update`, `BattleManager::createEntity`.
- `reports/native_arm64.json`, `reports/native_symbols.csv` e `reports/native_findings.lua` contêm **apenas nomes de símbolos, endereços virtuais, contagens e hashes**, sem redistribuir bibliotecas nem outras partes do APK.
- **F7 — ELF ARM64:** mostra os nomes de classes, contagens e amostras de funções do relatório para navegação no LÖVE2D. É ferramenta de pesquisa, não uma mecânica jogável.
- A presença de nomes como `processFrameUpdate`, `setStickDir` e `CreateSkillBySkillConfigId` **não demonstra** qual algoritmo, frame rate, regra de sincronização ou fórmula de combate o BarbarQ usa. Isso exigirá análise de fluxo e testes com o cliente original.

Executar a auditoria numa máquina com Python 3.10+ e Binutils/LLVM (no Windows pode usar WSL):

```powershell
python tools/auditar_elf.py "C:\caminho\para\BarbarQ.apk" --out reports
python -m unittest discover -s tests -v
```

Os relatórios que acompanham esta versão foram gerados **do APK BarbarQ 1.0.1811 enviado pelo usuário**. Para outra versão, gere relatórios novamente; endereços não são portáveis entre versões.

- **Fase 10 — subcenas:** o CSB declara 1.005 nós `ProjectNode`; 985 apontam para cenas que estão presentes no próprio APK e 20 não contêm nome válido. A aba F6 permite selecionar um `ProjectNode` e pressionar `Enter` para inspecionar a cena referenciada, e `Backspace` para retornar. Há bloqueio de ciclos, caminhos inválidos, ambiguidades e profundidade acima de 16. Isto **não** corresponde à navegação real do jogador entre menus; são referências de composição de cena.
- **Fase 10 — botões:** recuperadas 2.313 imagens de estado normal, 612 de estado pressionado e 956 de estado desabilitado dos 2.909 botões encontrados. `H` alterna somente os estados declarados para o botão selecionado, como ferramenta de inspeção visual; não executa cliques ou callbacks do jogo. Quatro nós em toda a coleção apresentam callback textual `Click`, insuficiente para reconstruir a lógica.
- **Auditoria:** `cache/summary.json` registra contagens de cenas, referências, skins e callbacks. O parser original continua defensivo contra referências malformadas.

- **VISPACK:** extrator de arquivos do APK 1.0.1811 (ARM64).
- **Cenas Cocos Studio:** 560 arquivos `.csb` FlatBuffers decodificados, com 26.612 nós de interface recuperados, incluindo 6.820 `ImageView`, 6.099 `Text`, 5.449 `Panel` e 2.909 `Button`. Nomes, caminhos de imagem, `actionTag`, posições, escalas, âncoras, dimensões e hierarquia são convertidos para `cache/scenes.lua`.
- **Aba F6 aprimorada:** inspeção de hierarquia, geometria e imagens reais dos atlas/PNGs quando presentes. Regras de layout, fontes e ações do Cocos ainda não são reconstruídas integralmente.
- **Mapas:** lê 32 mapas TMX base64/zlib e suas texturas; a câmera e o retículo são apenas ferramentas de investigação.
- **Atlas:** lê 171 `.bplist` FlatBuffers e 2 `.plist` XML; **13.875 recortes de sprites** catalogados. Uma textura referenciada não está presente no APK.
- **Animações:** lê os **1.079 `.bexportjson` binários (FlatBuffers)** e reconstrói os metadados de **1.079 armaduras, 2.657 movimentos, 7.452 trilhas de ossos e 38.727 keyframes**.
- **F5 atualizado:** leitura da pose-base, interpolação linear de keyframes, matrizes afins e composição de parentesco **somente quando informado nos dados**.
- **Troca real de imagens:** `bone[2]` fornece o display inicial; `frame[0]` seleciona o display por keyframe (índice baseado em zero, com `-1` = invisível). Os índices de **2.552 ossos** e **38.727 quadros-chave** foram conferidos contra suas próprias listas de displays: nenhum índice fora dos limites. Uma posição vazia é mantida no vetor para não deslocar índices posteriores.
- **Ordem de renderização:** `bone[5]` contém a ordem numérica de camada observada (em 1.022/1.079 armaduras, sequência contínua de 1 a N); renderização estável de trás para frente, mantendo a ordem original quando há empate. Sua semântica ainda depende de comparação visual com o motor original.
- **Busca de sprites melhorada:** dá prioridade aos atlas `.plist` declarados na própria animação (mapeando-os aos `.bplist` existentes), depois ao diretório da animação; somente usa nomes globais quando a associação é inequívoca.
- **Comparação A/B:** teclas `I` (interpolação ligada/desligada) e `B` (pose-base ligada/desligada) para inspecionar hipóteses de transformação sem confundir a prévia com o motor Cocos.
- **Correção do leitor:** a antiga hipótese de usar `frame[11]` como `display_index` continua descartada. A Fase 6 confirma o verdadeiro índice em `frame[0]` e usa `bone[2]` como display inicial.
- **F1/F2/F3/F4:** painéis de mapa, imagens, atlas e configurações preservados.

### Fase 8: reconstrução dos metadados de interfaces

- O leitor `tools/csb.py` decodifica o contêiner `CSParseBinary` e a árvore `NodeTree` de 560 cenas sem executar nenhum arquivo binário como código. A estrutura dos campos usa como referência o esquema público do Cocos Studio, **não** a lógica proprietária do jogo.
- Recuperados **26.612 nós** com verificação de limites, contagens máximas, validade UTF-8, profundidade da árvore e transformações finitas. Recurso e texto são extraídos apenas de tipos identificados.
- `tools/preparar_recursos.py` gera `cache/scenes.lua` e atualiza `summary.json` com número de cenas, nós e classes.
- A aba **F6** apresenta um retângulo de layout por componente, sua hierarquia, origem, tamanho e `z` declarados. Tenta exibir uma textura original **somente** quando ela existe como arquivo avulso no APK. A busca compara caminhos sem diferenciar maiúsculas/minúsculas, como no Android.
- Inspeção disponível por `Tab`/`Shift+Tab` (nó seguinte/anterior), `G` (guias) e `V` (exibir nós ocultos).
- **Limitações:** a geometria é uma projeção de depuração. Não implementa escalonamento responsivo do Cocos, `scale9`, fontes customizadas, sprites de atlas, clipping de painéis, rotação completa, blend, fluxo de eventos ou ações de botões. Um botão exibido em F6 **não funciona** como um botão de jogo. O cache local não deve ser publicado no GitHub público por conter dados originais.

### Fase 7: geometria dos sprites corrigida

- **Orientação das imagens:** cada textura recortada agora é desenhada com a inversão vertical correta entre o atlas (+Y para baixo) e as coordenadas locais Cocos (+Y para cima). A implementação antiga podia apresentar sprites invertidos.
- **Alinhamento do trim:** `offset_x`/`offset_y`, `source_w`/`source_h` e dimensões reais do recorte são considerados de forma uniforme em F3 e F5. O recorte não é esticado artificialmente para o tamanho original.
- **Referência visual F3:** quadro amarelo indica a área da imagem original; quadro verde indica os limites da parte visível do sprite. A origem usada é o centro do quadro original (âncora 0,5 × 0,5, uma **hipótese explícita**).
- **Depuração F5:** a tecla `P` alterna as guias amarelas (imagem original), verdes (recorte) e cruz vermelha (origem do osso). As guias acompanham a transformação local e a pose do osso.
- **Interpolação subquadro:** F5 passa o tempo fracionário ao avaliador de poses; anteriormente arredondava antes da interpolação, ocultando as transições.
- **Quadros rotacionados:** o módulo Lua tem um caminho condicional de desrotação para futuros recursos `rotated=true`, mas a auditoria desta versão do APK identificou **0/13.875 sprites rotacionados**. A convenção de rotação é **não validada** com dados reais deste jogo; não reivindicamos uma correção de recurso que não existe no material atual.
- **Auditoria de atlas:** 13.875 sprites dos 173 atlas; 9.181 têm dimensões recortadas, 9.108 apresentam offsets, e os recortes permanecem dentro dos retângulos de origem declarados.

**Limites da prévia F7:** os cálculos de pose-base + deltas e a decomposição de skew são **hipóteses de reconstrução**. A interpolação atual é linear e não replica easing Cocos; os assets analisados não expuseram nenhum `parent` textual não vazio para os ossos, então composição de pais está implementada e testada artificialmente, **mas não validada num esqueleto real do APK**. Ainda faltam: cor/blending, prova dos pivôs/âncoras de displays, easing, temporização original e reconciliação com captura do BarbarQ original. Não foram encontrados dados de ancoragem explícita nos displays comuns desta versão; a origem no centro é uma hipótese de visualização. A prioridade atual de atlas, a inversão vertical e a ordem das camadas precisam ser confrontadas visualmente com o jogo para confirmar o resultado. São usados 30 quadros/s **apenas para investigação**. Não apresentar o resultado como fiel 1:1 até comparação real.

**Não implementados:** controles de jogador, colisões, combate, IA, itens, menus operacionais, progressão, lobby e partidas online/offline. Ainda será necessária investigação do executável nativo e testes comparativos para uma portabilidade 1:1.

## Fase 9 — Atlas e componentes reais das cenas

- **Resolução de recursos:** `src/scene_resources.lua` mapeia caminhos virtuais dos arquivos `.csb` aos sprites dos atlas `.bplist` (`Gui/gui/Ver_6/...` → `gui/gui.bplist`) e texturas avulsas. Busca exata sem distinção entre maiúsculas/minúsculas e rejeição de nomes ambíguos; nenhuma substituição aleatória.
- **Auditoria:** nas 11.933 referências de imagens dos 560 arquivos `.csb`, há 10.868 referências apontam para nomes presentes nos atlas (10.866 resolvidas sem ambiguidades), 524 imagens avulsas e 541 referências não resolvidas. São ocorrências de referência (não imagens únicas); parte das ausências são placeholders do Cocos.
- **Transformação visual:** `src/scene_layout.lua` compõe âncora, posição, escala, flip, aproximação de `skew`/rotação e ordem z estável entre irmãos; permite selecionar um nó por posição usando matrizes inversas.
- **Aba F6:** desenha subtexturas com tamanho original e deslocamentos dos recortes, respeita opacidade herdada, oferece picking por clique e anotações textuais de depuração alternáveis (`T`). Menus ainda não são jogáveis; clicar seleciona componentes para inspeção, não aciona botões do BarbarQ.
- **Limitações:** layout responsivo, widgets `scale9`, fonts e eventos originais, ações, blending e renderização Cocos completa não estão implementados. As propriedades de `skew` são aproximadas e exigem comparação com capturas reais. Nenhum teste gráfico no Windows foi executado neste ambiente.

## Validação da Fase 10

Executado `python -m unittest discover -s tests -v`: **22 testes, sem falhas; 5 testes de integração antigos ficaram opcionais/skipped** por esperarem outro layout de diretórios. O novo teste audita os 560 CSBs reais, suas referências e os estados dos botões. `luatex --luaonly` cobre a navegação, ciclos, ida/volta e troca de skins. Cache regenerado e arquivos ZIP verificados. O teste gráfico real do LÖVE2D no Windows **ainda precisa ser feito**.

A maior parte da lógica de clique e de navegação do BarbarQ não está codificada nos CSB. Não há garantia de que um `ProjectNode` seja uma tela acessível por botão; ele pode representar apenas um fragmento visual reutilizado. A versão 1:1 exigirá engenharia reversa da biblioteca nativa original, validação de eventos e comparação em execução.

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
| `F1` a `F8` | Mapas, imagens, atlas, configurações, animações, cenas CSB, símbolos nativos e fluxo ARM64 |
| `↑` / `↓` e clique | Selecionar um arquivo na lista lateral (F2–F5) |
| Digitar / `Esc` | Filtrar ou limpar a lista (F2–F5) |
| `WASD` e roda do mouse | Câmara e zoom na inspeção de mapas |
| `[` / `]` | Trocar sprite na aba de atlas F3 |
| `Espaço` | Pausar/continuar prévia F5 |
| `←` / `→` | Voltar/avançar um quadro F5 (pausa automaticamente) |
| `Tab` / `Shift+Tab` | Trocar de movimento F5 |
| `I` | Alternar interpolação linear e quadros discretos F5 |
| `B` | Alternar inclusão da pose-base F5 |
| `P` | Exibir/ocultar caixas do recorte, canvas original e origem F5 |
| `Tab` / `Shift+Tab` | Navegar entre nós da cena F6 |
| `G` / `V` | Alternar guias / nós ocultos na cena F6 |
| `T` / clique na cena | Mostrar/ocultar textos de referência / selecionar nó da cena F6 |
| `Enter` em ProjectNode | Abrir a cena `.csb` referenciada, somente para inspeção |
| `Backspace` em subcena | Retornar à cena anterior sem perder o nó selecionado |
| `H` em botão | Alternar entre imagens de estados declarados no CSB |

## Estrutura

| Diretório/arquivo | Papel |
|---|---|
| `tools/extrair_barbarq.py` | Extrai recursos do VISPACK |
| `tools/bplist.py` | Decodifica atlas `.bplist` com validação de limites |
| `tools/bexport.py` | Decodifica animações `.bexportjson` sem executar dados externos |
| `tools/csb.py` | Leitor FlatBuffers das cenas do Cocos Studio, com limites e validações |
| `src/scene_view.lua` | Visualizador F6 de hierarquias, recortes e seleção |
| `src/scene_resources.lua` | Resolver de recursos das cenas para atlas ou PNGs avulsos |
| `src/scene_layout.lua` | Matrizes de hierarquia 2D, ordem z e picking |
| `tools/auditar_elf.py` | Auditoria estática dos ELF AArch64, nomes de símbolos, hashes e endereços virtuais |
| `tools/analisar_fluxo.py` | Desmontagem estática dirigida a funções da Fase 11; publica somente os metadados de fluxo |
| `src/flow_view.lua` | Painel F8 somente leitura de referências de fluxo ARM64 |
| `src/native_view.lua` | Painel F7 com metadados de funções C++ exportadas; não executa código Android |
| `src/scene_links.lua` | Resolução exata de referências ProjectNode com proteção contra caminhos ambíguos |
| `tools/preparar_recursos.py` | Converte mapas, atlas e animações para cache Lua local |
| `src/animation_view.lua` | Visualizador F5 de poses, seleção de displays e sobreposição |
| `src/sprite_resolver.lua` | Resolução contextual de nomes de sprites e prevenção de colisões |
| `src/pose.lua` | Interpolação e matrizes afins, sem dependência gráfica |
| `src/sprite_geometry.lua` | Cálculo de recortes, origem, offsets e conversão de eixo, com suporte experimental para atlas rotacionados |
| `tests/test_sprite_geometry.lua`, `tests/test_animation_view.lua` | Testes Lua do posicionamento, orientação e integração da prévia |
| `tests/test_pose.lua` | Testes Lua de poses, transições discretas de display e ordem de camadas |
| `tests/test_sprite_resolver.lua` | Teste Lua de atlas explícitos, locais, globais e colisões |
| `main.lua`, `conf.lua` | Interface LÖVE2D |
| `tests/` | Testes Python; casos malformados e integração opcional |
| `assets_original/` | Recursos locais do APK; **ignorado pelo Git** |
| `cache/` | Dados locais gerados; **ignorado pelo Git** |

## Auditoria da Fase 7

```powershell
py -m unittest discover -s tests -v
py tools/preparar_recursos.py --assets assets_original --out cache
```

Os **15 testes Python passaram**, incluindo as suítes Lua de pose, resolução de sprites, geometria e desenho da aba F5 com Lua via `luatex --luaonly`. Os **1.079 arquivos binários foram novamente decodificados sem falhas**, inclusive todas as 38.727 poses-chave. Há 18 keyframes que ocultam a imagem com display `-1`. O cache local completo foi regenerado a partir do APK. Sintaxe Lua dos módulos conferida. **Ainda não houve teste visual no LÖVE2D/Windows neste ambiente**; nenhuma fidelidade visual está certificada.

## Próximas frentes

1. Executar a Fase 7 no LÖVE2D para Windows e comparar imagens e ordem de camadas com capturas do BarbarQ original; investigar âncoras, curvas de easing, cor e taxa de reprodução sem pressupor semântica não confirmada.
2. Decodificar cenas `.csb`, modelos `.c3b` e informações de configuração pertinentes à jogabilidade.
3. Reconstruir a movimentação, entidades, física e combate com testes de referência 1:1.
4. Investigar e, se viável, substituir serviços de rede por uma infraestrutura independente.

Este repositório público distribui somente o código-fonte da investigação. **Não publica** o APK, texturas, áudio, modelos ou outros recursos protegidos do jogo. Use sua própria cópia autorizada do APK para extrair os arquivos localmente.

### Referência de formato para CSB

O mapeamento dos campos comuns `.csb` foi confrontado com o projeto público [csb-flatbuffers-schema](https://github.com/halx99/csb-flatbuffers-schema) e com os arquivos fornecidos do APK. O leitor é uma implementação independente: não inclui nem redistribui o esquema ou binários de terceiros.