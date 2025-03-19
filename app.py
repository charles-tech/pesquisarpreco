import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO

# Função para obter dados do ativo e calcular diferenças e porcentagens
def check_price_near_target(ticker, target_price):
    try:
        # Obter os dados históricos dos últimos 5 anos
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5 * 365)
        data = yf.download(ticker, start=start_date, end=end_date)
        
        st.write("Dados brutos baixados:")
        st.dataframe(data)

        if data.empty:
            st.warning("Os dados retornados estão vazios. Pode ser um problema com o ticker ou com a fonte dos dados.")
            return None, None, None

        # Obter preço atual
        stock_data = yf.Ticker(ticker)
        current_price = stock_data.info.get('regularMarketPrice')

        # Calcular diferença e porcentagem entre preço atual e preço alvo
        diff = current_price - target_price
        percent_diff = (diff / target_price) * 100

        # Ajustar diferença e porcentagem para incluir sinal
        diff_sign = '+' if target_price > current_price else '-'
        diff_signed = f"{diff_sign}{abs(diff):.2f}"
        percent_diff_signed = f"{diff_sign}{abs(percent_diff):.2f}%"

        # Criar tabela com os dados necessários
        comparison_data = pd.DataFrame({
            'Preço Atual': [current_price],
            'Preço Alvo': [target_price],
            'Diferença em relação ao Alvo': [diff_signed],
            'Diferença (%) em relação ao Alvo': [percent_diff_signed]
        })

        st.write("Comparação entre Preço Atual e Alvo:")
        st.dataframe(comparison_data)

        # Verificar os preços de fechamento que estão próximos do alvo
        is_near = data[(data['Close'] >= target_price - 0.99) & (data['Close'] <= target_price + 0.99)]

        # Encontrar o fechamento mais próximo, caso nenhum esteja no intervalo
        closest_idx = (data['Close'] - target_price).abs().idxmin()
        closest = data.loc[closest_idx]

        st.write("Fechamento mais próximo encontrado:")
        st.write(closest)

        return data, is_near, closest
    except Exception as e:
        st.error(f"Erro ao buscar os dados do ticker. Detalhes do erro: {e}")
        return None, None, None

# Função para converter DataFrame em Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=True, sheet_name='Dados')
        writer.close()
    return output.getvalue()

# Configuração do layout do Streamlit
st.title("Verificador de Preços de Ativos da B3")
st.write("Digite o código do ativo e o preço alvo para verificar.")

# Entrada do usuário
ticker_input = st.text_input("Código do ativo (ex: BOVA11.SA):")
price_input = st.number_input("Preço alvo (em R$):", min_value=0.0, format="%.2f")

# Botão para processar a consulta
if st.button("Verificar"):
    if ticker_input and price_input:
        # Verificar os dados
        data_bruta, result, closest = check_price_near_target(ticker_input, price_input)
        if data_bruta is not None:
            # Preparação do download do arquivo Excel para dados brutos
            excel_data = to_excel(data_bruta)
            st.download_button(
                label="Baixar dados brutos como Excel",
                data=excel_data,
                file_name='dados_brutos.xls',
                mime='application/vnd.ms-excel'
            )

        if result is not None:
            if not result.empty:
                st.success(f"O preço fechou próximo de R${price_input:.2f} nas datas e valores encontrados.")
            else:
                st.warning(f"Nenhum fechamento encontrado próximo de R${price_input:.2f} nos últimos 5 anos.")
                if closest is not None:
                    st.info(f"O fechamento mais próximo foi em {closest.name.date()} com preço de R${closest['Close']:.2f}.")
        else:
            st.error("Não foi possível recuperar os dados. Verifique se o código do ativo está correto.")
    else:
        st.warning("Por favor, insira tanto o código do ativo quanto o preço alvo.")