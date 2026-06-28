import streamlit as st


def render_about() -> None:
    """Renderiza o bloco 'Sobre o Observatório'."""

    st.markdown("### 🦉 Sobre o Observatório das Emendas RS")

    st.markdown(
        """
O **Observatório das Emendas RS** é uma plataforma acadêmica de análise territorial desenvolvida para organizar, visualizar e interpretar informações públicas sobre a destinação de emendas parlamentares no Estado do Rio Grande do Sul.

Ao integrar dados orçamentários, eleitorais e indicadores de prioridade social, o Observatório transforma informações públicas em visualizações e indicadores que apoiam a compreensão da distribuição territorial dos recursos públicos.
"""
    )

    st.markdown("### 🎯 Objetivo")

    st.markdown(
        """
O Observatório tem como objetivo ampliar a transparência e facilitar o acesso a informações sobre a destinação de emendas parlamentares por meio de uma interface interativa, baseada em dados públicos oficiais e procedimentos metodológicos documentados.

A plataforma não busca emitir juízos de valor sobre a atuação parlamentar. Seu propósito é disponibilizar evidências, indicadores e visualizações que auxiliem pesquisadores, estudantes, jornalistas, gestores públicos e cidadãos na formulação de análises e interpretações fundamentadas.
"""
    )

    st.markdown("### 🔍 O que é analisado?")

    st.markdown(
        """
- distribuição territorial das emendas parlamentares;
- votação municipal dos parlamentares;
- prioridade social dos municípios (IPS);
- Índice de Correspondência Territorial (ICT).
"""
    )

    st.markdown("### 🗂 Fontes dos dados")

    st.markdown(
        """
- Tribunal Regional Eleitoral do Rio Grande do Sul (TRE-RS);
- Portal da Transparência do Governo Federal;
- Instituto Brasileiro de Geografia e Estatística (IBGE);
- Indicadores de Prioridade Social (IPS).
"""
    )

    st.markdown("### 📖 Metodologia")

    st.markdown(
        """
Os procedimentos metodológicos adotados pelo projeto encontram-se documentados no arquivo:

`docs/metodologia.md`
"""
    )

    st.markdown("### 🎓 Instituição")

    st.markdown(
        """
Universidade Federal do Rio Grande do Sul (UFRGS)

Disciplina de Sociologia I

Projeto acadêmico em desenvolvimento.
"""
    )

    st.markdown("### 🚀 Versão")

    st.markdown("**Versão 1.0**")

    st.markdown("### 🌱 Desenvolvimento")

    st.markdown(
        """
O Observatório das Emendas RS é um projeto em desenvolvimento contínuo.

Novas funcionalidades e análises poderão ser incorporadas conforme a evolução da pesquisa, o amadurecimento metodológico e a disponibilidade de novas bases de dados públicas.

**O conhecimento científico avança quando dados públicos são transformados em evidências acessíveis. O Observatório das Emendas RS nasce como uma contribuição, ainda em construção, para esse esforço coletivo.**
"""
    )