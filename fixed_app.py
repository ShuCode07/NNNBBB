import streamlit as st
import pandas as pd
import plotly.express as px

# 设置页面标题
st.set_page_config(page_title="企业数字化转型指数查询", layout="wide")

def load_data():
    """简化的数据加载函数"""
    try:
        # 读取主要数据文件
        data_path = r"APP ALL\两版合并后的年报数据_完整版.xlsx"
        df = pd.read_excel(data_path, engine='openpyxl')
        
        # 处理股票代码
        if '股票代码' in df.columns:
            df['股票代码'] = df['股票代码'].astype(str).str.zfill(6)
        
        # 读取行业数据文件
        try:
            industry_path = r"APP ALL\最终数据dta格式-上市公司年度行业代码至2021.xlsx"
            df_industry = pd.read_excel(industry_path, engine='openpyxl')
            
            # 处理行业数据的股票代码和年份
            if '股票代码全称' in df_industry.columns:
                df_industry['股票代码'] = df_industry['股票代码全称'].astype(str).str.zfill(6)
            
            if '年度' in df_industry.columns:
                df_industry.rename(columns={'年度': '年份'}, inplace=True)
            
            # 合并数据
            if '股票代码' in df_industry.columns and '年份' in df_industry.columns:
                merge_columns = ['股票代码', '年份']
                if '行业名称' in df_industry.columns:
                    merge_columns.append('行业名称')
                elif '行业代码' in df_industry.columns:
                    merge_columns.append('行业代码')
                
                df = pd.merge(df, df_industry[merge_columns], on=['股票代码', '年份'], how='left')
                
        except Exception:
            st.warning("读取行业数据失败，仅使用主要数据")
        
        return df
        
    except Exception as e:
        st.error(f"数据加载错误: {str(e)}")
        return None

# 加载数据
df = load_data()

if df is not None:
    st.title("企业数字化转型指数查询系统")
    
    # 侧边栏查询条件
    st.sidebar.header("查询条件")
    
    # 股票代码选择
    stock_codes = sorted(df['股票代码'].unique())
    
    # 获取企业名称映射
    stock_name_map = {}
    if '企业名称' in df.columns:
        for code in stock_codes:
            names = df[df['股票代码'] == code]['企业名称'].dropna().unique()
            if len(names) > 0:
                stock_name_map[code] = names[0]
    
    selected_stock = st.sidebar.selectbox(
        "选择股票代码",
        options=stock_codes,
        format_func=lambda x: f"{x} - {stock_name_map.get(x, '')}"
    )
    
    # 年份选择
    stock_years = sorted(df[df['股票代码'] == selected_stock]['年份'].unique())
    
    # 添加"全部显示"选项
    year_options = ['全部显示'] + stock_years
    selected_year = st.sidebar.selectbox("选择年份", options=year_options)
    
    # 获取所选数据
    if selected_year == '全部显示':
        selected_data = df[df['股票代码'] == selected_stock]
    else:
        selected_data = df[(df['股票代码'] == selected_stock) & (df['年份'] == selected_year)]
    
    if not selected_data.empty:
        # 显示企业基本信息
        st.header("企业基本信息")
        
        if '企业名称' in selected_data.columns:
            stock_name = selected_data['企业名称'].iloc[0]
            st.subheader(f"{stock_name} ({selected_stock})")
        else:
            st.subheader(f"{selected_stock}")
        
        # 显示行业信息
        if '行业名称' in selected_data.columns:
            industry_name = selected_data['行业名称'].iloc[0]
            if pd.notna(industry_name):
                st.write(f"行业: {industry_name}")
        elif '行业代码' in selected_data.columns:
            industry_code = selected_data['行业代码'].iloc[0]
            if pd.notna(industry_code):
                st.write(f"行业代码: {industry_code}")
        
        # 显示数字化转型指数相关数据
        st.header("数字化转型指数")
        index_cols = [col for col in selected_data.columns if '指数' in col or '词频' in col]
        
        if index_cols:
            company_info = selected_data[index_cols].iloc[0]
            col1, col2, col3 = st.columns(3)
            cols = [col1, col2, col3, col1, col2, col3]
            
            for i, col in enumerate(index_cols[:6]):
                if pd.notna(company_info[col]):
                    cols[i % 3].metric(label=col, value=round(company_info[col], 4))
        else:
            st.warning("未找到数字化转型指数相关数据")
        
        # 绘制趋势图
        st.header("数字化转型指数趋势")
        
        if len(selected_data) > 1 and index_cols:
            fig_data = selected_data.sort_values('年份')
            
            fig = px.line(
                fig_data,
                x='年份',
                y=index_cols,
                title=f"{stock_name_map.get(selected_stock, selected_stock)} 数字化转型指数趋势",
                markers=True,
                labels={'value': '指数值', '年份': '年份'}
            )
            
            fig.update_layout(
                template='plotly_white',
                hovermode='x unified',
                legend_title='指数类型'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("数据不足，无法绘制趋势图")
            
        # 显示原始数据
        st.header("原始数据")
        
        # 确保所有数据都能显示
        st.dataframe(selected_data, use_container_width=True, height=800)
        
        # 添加数据下载功能
        st.header("数据下载")
        
        # 生成文件名
        if '企业名称' in selected_data.columns:
            company_name = selected_data['企业名称'].iloc[0] if pd.notna(selected_data['企业名称'].iloc[0]) else selected_stock
        else:
            company_name = selected_stock
        
        if selected_year == '全部显示':
            file_name = f"{company_name}_全部年份_数字化转型数据.csv"
        else:
            file_name = f"{company_name}_{selected_year}_数字化转型数据.csv"
        
        st.download_button(
            label="下载原始数据（CSV）",
            data=selected_data.to_csv(index=False, encoding='utf-8-sig'),
            file_name=file_name,
            mime="text/csv"
        )
    else:
        st.warning("未找到所选条件的数据")
    
    # 数据概览
    st.header("数据概览")
    col1, col2, col3 = st.columns(3)
    col1.metric("总股票数", len(stock_codes))
    col2.metric("年份范围", f"{df['年份'].min()} - {df['年份'].max()}")
    col3.metric("数据总量", len(df))
else:
    st.error("无法加载数据，请检查文件路径和格式")