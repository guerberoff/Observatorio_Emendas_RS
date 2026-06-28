\# Metodologia do Observatório das Emendas RS



\## 1. Apresentação



O Observatório das Emendas RS é uma plataforma analítica desenvolvida para organizar, visualizar e interpretar dados sobre a destinação de emendas parlamentares no Rio Grande do Sul.



O projeto busca tornar informações públicas mais acessíveis por meio de visualizações territoriais, indicadores sintéticos e textos descritivos automatizados.



\## 2. Objetivo analítico



O objetivo central do Observatório é analisar a relação territorial entre três dimensões:



1\. votação parlamentar nos municípios;

2\. destinação de recursos de emendas parlamentares;

3\. faixa de prioridade social dos municípios.



A análise não tem como objetivo atribuir intenção, motivação ou causalidade à atuação parlamentar. O Observatório descreve padrões territoriais observáveis a partir dos dados disponíveis.



\## 3. Fontes de dados



O Observatório utiliza bases consolidadas contendo informações sobre:



\- localidade de aplicação dos recursos;

\- valores pagos de emendas parlamentares;

\- parlamentar autor da emenda;

\- votos obtidos por município;

\- código IBGE;

\- faixa de prioridade social;

\- geometria municipal do Rio Grande do Sul em formato GeoJSON.



As bases são previamente organizadas para permitir o cruzamento entre dados orçamentários, eleitorais e territoriais.



\## 4. Tratamento dos dados



Antes da visualização, os dados passam por etapas de padronização e validação.



Entre os principais procedimentos estão:



\- verificação da existência dos arquivos de dados;

\- validação das colunas obrigatórias;

\- padronização dos nomes dos municípios;

\- separação entre emendas destinadas a municípios e emendas destinadas à Unidade Federativa;

\- agregação dos valores pagos por município;

\- agregação dos votos por município;

\- associação dos dados tabulares à base geográfica municipal.



A padronização dos nomes dos municípios é necessária para garantir a correspondência entre a base de emendas e o arquivo geográfico utilizado no mapa.



\## 5. Emendas municipais e emendas estaduais/UF



O Observatório distingue dois tipos de destinação:



\- \*\*MUNICÍPIO\*\*: quando a localidade de aplicação do recurso corresponde a um município específico;

\- \*\*UF\*\*: quando a destinação está associada ao Estado do Rio Grande do Sul como unidade federativa.



As emendas municipais são utilizadas nas análises territoriais e no mapa municipal. As emendas classificadas como UF são tratadas separadamente e apresentadas como indicador próprio, evitando sua distribuição artificial entre municípios.



\## 6. Faixa de prioridade social



Cada município é associado a uma faixa de prioridade social, utilizada para analisar a distribuição dos recursos em relação às condições sociais dos territórios.



As faixas utilizadas são:



\- Alta Prioridade;

\- Média Prioridade;

\- Baixa Prioridade.



Essa classificação permite observar se os recursos destinados aos municípios se concentram em localidades de maior, média ou menor prioridade social, sem produzir juízo de valor automático sobre a adequação da destinação.



\## 7. Mapa territorial



O mapa do Observatório combina duas camadas principais:



1\. \*\*Mapa coroplético de emendas\*\*  

&#x20;  A intensidade da cor vermelha representa o volume de recursos pagos em emendas destinadas a cada município.



2\. \*\*Marcadores eleitorais\*\*  

&#x20;  Os marcadores azuis representam os votos obtidos pelo parlamentar nos municípios.



Essa composição permite observar, em uma mesma visualização, a relação territorial entre votação e destinação de recursos.



\## 8. Indicadores gerais



O painel apresenta indicadores sintéticos para o parlamentar selecionado, incluindo:



\- número de municípios contemplados;

\- total de recursos destinados diretamente aos municípios;

\- total de recursos destinados à Unidade Federativa;

\- total de votos considerados na base municipal.



Esses indicadores têm função descritiva e ajudam a contextualizar a leitura do mapa e dos gráficos.



\## 9. Distribuição por prioridade social



O gráfico de prioridade social apresenta a soma dos valores pagos em emendas segundo a faixa de prioridade social dos municípios.



Essa visualização permite observar a distribuição dos recursos entre municípios classificados como de Alta, Média ou Baixa Prioridade Social.



\## 10. Narrativa automática



O Observatório gera textos descritivos automáticos com base nos resultados agregados.



Essas narrativas têm caráter exclusivamente descritivo. Elas não avaliam a conduta parlamentar, não produzem julgamento político e não inferem causalidade.



A interpretação sociológica e política dos resultados permanece como tarefa do pesquisador.



\## 11. Índice de Correspondência Territorial (ICT)



O Índice de Correspondência Territorial mede a sobreposição entre:



\- os municípios onde o parlamentar obteve maior votação;

\- os municípios que mais receberam recursos de emendas.



O ICT busca descrever o grau de correspondência territorial entre base eleitoral e destinação de recursos.



\## 12. Fórmula do ICT



O ICT é calculado pela razão entre o número de municípios coincidentes nas duas listas e o número de municípios considerados no ranking.



```text

ICT = número de municípios coincidentes / número de municípios considerados no ranking

