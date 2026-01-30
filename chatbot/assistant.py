"""
AI Assistant for Parkview CMA methodology questions.

Uses Claude Haiku for fast, cost-effective responses.
"""

import streamlit as st
import os
from typing import Generator

# Try to import anthropic, handle if not installed
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# System prompt with methodology knowledge
SYSTEM_PROMPT = """You are a helpful assistant for the Parkview Capital Market Assumptions (CMA) Tool. You help users understand the methodology, calculations, assumptions, and how to use overrides.

## Your Knowledge Base

### Overview
The Parkview CMA methodology produces 10-year expected returns for major asset classes using a building block approach. Key principles:
- Returns are decomposed into fundamental components (yield, growth, valuation changes)
- Valuations and spreads mean-revert to fair value over time
- Forward-looking macro forecasts drive rate expectations
- All asset classes use consistent underlying macro assumptions

### Macro Models

**GDP Growth Model:**
E[Real GDP Growth] = E[Output-per-Capita Growth] + E[Population Growth]
- Population Growth: UN Population Database forecasts
- Productivity Growth: EWMA of historical data (5-year half-life)
- Demographic Effect: Sigmoid function of MY (Middle/Young) ratio

**Inflation Model:**
E[Inflation] = 30% × Current Headline Inflation + 70% × Long-Term Inflation
- Current Headline: Latest YoY CPI reading
- Long-Term: Central bank target or EWMA of core inflation

**T-Bill Rate Model:**
E[T-Bill] = 30% × Current T-Bill + 70% × Long-Term T-Bill
Long-Term T-Bill = max(-0.75%, Country Factor + E[Real GDP] + E[Inflation])

### Asset Class Models

**Liquidity (Cash):**
E[Return] = E[T-Bill Rate]

**Bonds (Global, HY, EM):**
E[Return] = Yield + Roll Return + Valuation Return - Credit Losses + FX Return
- Yield: E[T-Bill] + Term Premium (+ Credit Spread for HY/EM)
- Roll Return: (Term Premium / Maturity) × Duration
- Valuation: -Duration × (ΔTerm Premium / Horizon)
- Credit Loss: Default Rate × (1 - Recovery Rate)

**Equity (US, Europe, Japan, EM):**
E[Real Return] = Dividend Yield + Real EPS Growth + Valuation Change
- EPS Growth: 50% Country + 50% Regional, capped at Global GDP
- Valuation: CAEY (1/CAPE) mean reversion over 20 years

**Absolute Return (Hedge Funds):**
E[Return] = E[T-Bill] + Σ(βᵢ × Factor Premiumᵢ) + Trading Alpha
- Factors: Market, Size, Value, Profitability, Investment, Momentum
- Alpha: 50% of historical alpha (accounts for decay)

### FX Adjustments
E[FX Return] = 30% × (Home T-Bill - Foreign T-Bill) + 70% × (Home Inflation - Foreign Inflation)
- Positive FX return = home currency depreciates, adds to foreign asset returns
- Applied when base currency differs from asset's local currency

### Default Values (Key Inputs)

**Macro - US:** Inflation 2.29%, GDP 1.20%, T-Bill 3.79%, MY Ratio 2.1
**Macro - Eurozone:** Inflation 2.06%, GDP 0.80%, MY Ratio 2.3
**Macro - Japan:** Inflation 1.65%, GDP 0.30%, MY Ratio 2.5
**Macro - EM:** Inflation 3.80%, GDP 3.00%, MY Ratio 1.5

**Bonds Global:** Yield 3.5%, Duration 7.0 yrs, Term Premium 1.0% (fair: 1.5%)
**Bonds HY:** Yield 7.5%, Duration 4.0 yrs, Default 5.5%, Recovery 40%
**Bonds EM:** Yield 5.77%, Duration 5.5 yrs, Default 2.8%, Recovery 55%

**Equity US:** Div Yield 1.13%, CAEY 2.48% (fair: 5.0%), EPS Growth 1.8%
**Equity Europe:** Div Yield 3.0%, CAEY 5.5% (fair: 5.5%), EPS Growth 1.2%
**Equity Japan:** Div Yield 2.2%, CAEY 5.5% (fair: 5.0%), EPS Growth 0.8%
**Equity EM:** Div Yield 3.0%, CAEY 6.5% (fair: 6.0%), EPS Growth 3.0%

**Absolute Return:** Alpha 1.0%, Market β 0.30, Size β 0.10, Value β 0.05

### Using Overrides
- Basic Mode: Override final forecasts directly (E[Inflation], E[GDP], E[T-Bill])
- Advanced Mode: Override building blocks (population growth, productivity, MY ratio, etc.)
- Overrides appear with yellow "OVERRIDE" badge; defaults show gray "DEFAULT" badge
- Computed values show blue "COMPUTED" badge and cannot be directly changed

### Mean Reversion
- Bond Term Premium: Partial reversion over 10 years (~3% per month)
- Credit Spread (HY): 50% reversion over 10 years
- Equity CAEY: Full reversion over 20 years

### EWMA Parameters
- Productivity/Inflation (DM): 5-year half-life
- Inflation (EM): 2-year half-life (faster adjustment)
- Term Premium/CAEY Fair Values: 20-year half-life, 50-year window

## Response Guidelines
- Be concise but thorough
- Use specific numbers from the methodology when relevant
- Explain formulas step-by-step when asked
- Help users understand how changing inputs affects outputs
- If asked about something outside your knowledge, say so clearly
"""


def get_anthropic_client():
    """Get Anthropic client if API key is available."""
    # Try environment variable first (local .env)
    api_key = os.getenv('ANTHROPIC_API_KEY')

    # Fallback to Streamlit secrets (for Streamlit Cloud deployment)
    if not api_key:
        try:
            api_key = st.secrets.get('ANTHROPIC_API_KEY')
        except Exception:
            pass

    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def stream_response(client, messages: list) -> Generator[str, None, None]:
    """Stream response from Claude Haiku."""
    with client.messages.stream(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages
    ) as stream:
        for text in stream.text_stream:
            yield text


def get_response(client, messages: list) -> str:
    """Get non-streaming response from Claude Haiku."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages
    )
    return response.content[0].text


def render_chatbot():
    """Render the floating chatbot in the bottom right corner."""

    # Check if anthropic is available
    if not ANTHROPIC_AVAILABLE:
        return  # Silently skip if not installed

    # Check for API key
    client = get_anthropic_client()
    if not client:
        return  # Silently skip if no API key

    # Initialize chat state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'chat_open' not in st.session_state:
        st.session_state.chat_open = False

    # CSS for floating chat widget
    st.markdown("""
    <style>
    .chat-toggle-btn {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background-color: #1E3A5F;
        color: white;
        border: none;
        cursor: pointer;
        font-size: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .chat-toggle-btn:hover {
        background-color: #2E5A8F;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create a container for the chat in the sidebar or as expander
    # Using Streamlit's native components for better compatibility

    # Chat toggle in sidebar
    with st.sidebar:
        st.divider()
        st.markdown("### 🤖 AI Assistant")

        # Toggle chat
        if st.button(
            "💬 Open Chat" if not st.session_state.chat_open else "✖️ Close Chat",
            use_container_width=True,
            key="chat_toggle"
        ):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()

        if st.session_state.chat_open:
            st.caption("Ask about methodology, calculations, or assumptions")

            # Display chat messages
            chat_container = st.container(height=300)
            with chat_container:
                for msg in st.session_state.chat_messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # Chat input
            if prompt := st.chat_input("Ask a question...", key="chat_input"):
                # Add user message
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": prompt
                })

                # Get AI response
                try:
                    # Convert to API format
                    api_messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_messages
                    ]

                    # Get response
                    response = get_response(client, api_messages)

                    # Add assistant message
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": response
                    })
                except Exception as e:
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"Sorry, I encountered an error: {str(e)}"
                    })

                st.rerun()

            # Clear chat button
            if st.session_state.chat_messages:
                if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
                    st.session_state.chat_messages = []
                    st.rerun()


def render_chatbot_main_area():
    """Alternative: Render chatbot in the main content area as an expander."""

    if not ANTHROPIC_AVAILABLE:
        return

    client = get_anthropic_client()
    if not client:
        return

    # Initialize chat state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

    with st.expander("🤖 AI Assistant - Ask about methodology", expanded=False):
        st.caption("Get help with calculations, assumptions, and how to use overrides")

        # Display chat messages
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        col1, col2 = st.columns([5, 1])
        with col1:
            prompt = st.text_input(
                "Your question",
                key="chat_input_main",
                placeholder="e.g., How is US equity return calculated?",
                label_visibility="collapsed"
            )
        with col2:
            send = st.button("Send", key="send_btn", use_container_width=True)

        if send and prompt:
            # Add user message
            st.session_state.chat_messages.append({
                "role": "user",
                "content": prompt
            })

            # Get AI response
            try:
                api_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_messages
                ]

                response = get_response(client, api_messages)

                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": response
                })
            except Exception as e:
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {str(e)}"
                })

            st.rerun()

        # Clear chat
        if st.session_state.chat_messages:
            if st.button("Clear conversation", key="clear_main"):
                st.session_state.chat_messages = []
                st.rerun()
