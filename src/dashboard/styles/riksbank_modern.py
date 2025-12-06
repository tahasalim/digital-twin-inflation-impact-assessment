"""
Modern Riksbank-Inspired Design System for Swedish Inflation Energy Digital Twin.

DARK MODE THEME:
- Dark page background (#0a192f)
- White cards for content
- Primary: Deep Blue (#003366) - Authority, trust, accent fill
- Secondary: Royal Blue (#0066CC) - Action, links
"""

# =============================================================================
# COLOR PALETTE
# =============================================================================

COLORS = {
    # Dark mode backgrounds
    "dark_bg": "#0a192f",           # Page background
    "dark_surface": "#0d1b2a",      # Slightly lighter surface
    "dark_elevated": "#112240",     # Elevated cards
    "dark_border": "#233554",       # Borders on dark
    
    # Primary palette (Riksbank-inspired)
    "primary_dark": "#002855",      # Deep navy - headers, primary elements
    "primary": "#003366",           # Riksbank blue - MAIN ACCENT COLOR
    "primary_light": "#004488",     # Lighter blue for hovers
    
    # Secondary palette
    "secondary": "#0066CC",         # Action blue - buttons, links
    "secondary_light": "#3399FF",   # Light action blue
    
    # Accent colors
    "accent_teal": "#00A3A3",       # Modern teal accent
    "accent_gold": "#B8860B",       # Swedish gold
    
    # Semantic colors
    "success": "#00B894",           # Nordic green
    "warning": "#F39C12",           # Amber warning
    "danger": "#E74C3C",            # Alert red
    "info": "#3498DB",              # Info blue
    
    # Neutral palette
    "white": "#FFFFFF",
    "gray_50": "#F8F9FA",           # Light card background
    "gray_100": "#F1F3F5",          # Cards
    "gray_200": "#E9ECEF",          # Borders
    "gray_300": "#DEE2E6",          # Dividers
    "gray_500": "#6C757D",          # Muted text
    "gray_700": "#495057",          # Secondary text
    "gray_900": "#212529",          # Primary text
    
    # Zone colors (Swedish grid)
    "zone_se1": "#00B894",          # North - Green (hydro)
    "zone_se2": "#00CEC9",          # Mid-north - Teal
    "zone_se3": "#0984E3",          # Central - Blue
    "zone_se4": "#6C5CE7",          # South - Purple
}


def get_main_css() -> str:
    """Generate the main CSS for the entire application - DARK THEME."""
    return f"""
<style>
    /* =========================================================================
       GLOBAL STYLES - DARK MODE
       ========================================================================= */
    
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables */
    :root {{
        --dark-bg: {COLORS["dark_bg"]};
        --dark-surface: {COLORS["dark_surface"]};
        --dark-elevated: {COLORS["dark_elevated"]};
        --dark-border: {COLORS["dark_border"]};
        --primary-dark: {COLORS["primary_dark"]};
        --primary: {COLORS["primary"]};
        --primary-light: {COLORS["primary_light"]};
        --secondary: {COLORS["secondary"]};
        --accent: {COLORS["accent_teal"]};
        --success: {COLORS["success"]};
        --warning: {COLORS["warning"]};
        --danger: {COLORS["danger"]};
        --white: {COLORS["white"]};
        --gray-50: {COLORS["gray_50"]};
        --gray-100: {COLORS["gray_100"]};
        --gray-200: {COLORS["gray_200"]};
        --gray-500: {COLORS["gray_500"]};
        --gray-700: {COLORS["gray_700"]};
        --gray-900: {COLORS["gray_900"]};
        --zone-se1: {COLORS["zone_se1"]};
        --zone-se2: {COLORS["zone_se2"]};
        --zone-se3: {COLORS["zone_se3"]};
        --zone-se4: {COLORS["zone_se4"]};
    }}
    
    /* Base styles - DARK BACKGROUND */
    .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background-color: var(--dark-bg) !important;
        color: var(--gray-100);
    }}
    
    /* Sidebar dark mode */
    section[data-testid="stSidebar"] {{
        background-color: var(--dark-surface) !important;
    }}
    
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label {{
        color: var(--gray-100) !important;
    }}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: var(--dark-surface);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: var(--gray-500);
        border-radius: 8px;
        padding: 10px 20px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: var(--primary) !important;
        color: var(--white) !important;
    }}
    
    /* =========================================================================
       HEADER & BRANDING
       ========================================================================= */
    
    .riksbank-header {{
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
        color: white;
        padding: 2rem 2.5rem;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 20px rgba(0, 40, 85, 0.15);
    }}
    
    .riksbank-header h1 {{
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }}
    
    .riksbank-header .tagline {{
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
        font-weight: 400;
    }}
    
    .riksbank-logo {{
        display: flex;
        align-items: center;
        gap: 1rem;
    }}
    
    .riksbank-logo .logo-icon {{
        font-size: 2.5rem;
    }}
    
    /* =========================================================================
       NAVIGATION TABS
       ========================================================================= */
    
    .stTabs [data-baseweb="tab-list"] {{
        background-color: white;
        padding: 0.5rem;
        border-radius: 12px;
        gap: 0.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        margin-bottom: 1.5rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        color: var(--gray-700);
        border: none;
        transition: all 0.2s ease;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: var(--gray-100);
        color: var(--primary);
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: var(--primary) !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(0, 51, 102, 0.3);
    }}
    
    /* =========================================================================
       CARDS & CONTAINERS - WHITE CARDS ON DARK BACKGROUND
       ========================================================================= */
    
    .modern-card {{
        background: var(--white);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        border: none;
        transition: all 0.2s ease;
        color: var(--gray-900);
    }}
    
    .modern-card:hover {{
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        transform: translateY(-2px);
    }}
    
    .modern-card-header {{
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--gray-900);
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid var(--gray-200);
    }}
    
    .stat-card {{
        background: #0A0A0A;
        border-radius: 0;
        padding: 1.5rem;
        border-left: 4px solid var(--primary);
        box-shadow: none;
        border: 1px solid #1A1A1A;
    }}
    
    .stat-card.success {{ border-left-color: var(--success); }}
    .stat-card.warning {{ border-left-color: var(--warning); }}
    .stat-card.danger {{ border-left-color: var(--danger); }}
    .stat-card.zone-1 {{ border-left-color: var(--zone-se1); }}
    .stat-card.zone-2 {{ border-left-color: var(--zone-se2); }}
    .stat-card.zone-3 {{ border-left-color: var(--zone-se3); }}
    .stat-card.zone-4 {{ border-left-color: var(--zone-se4); }}
    
    .stat-card .stat-value {{
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        color: #FFFFFF;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    
    .stat-card .stat-label {{
        font-family: 'Roboto Mono', monospace;
        font-size: 0.75rem;
        color: #B0B0B0;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }}
    
    /* =========================================================================
       BUTTONS
       ========================================================================= */
    
    .stButton > button {{
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0, 51, 102, 0.2);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 51, 102, 0.3);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    /* Primary action button */
    .primary-action .stButton > button {{
        background: linear-gradient(135deg, var(--success) 0%, #00D9A5 100%);
        padding: 1rem 2rem;
        font-size: 1.1rem;
    }}
    
    /* =========================================================================
       METRICS & KPIs - WHITE CARDS
       ========================================================================= */
    
    .stMetric {{
        background-color: var(--white) !important;
        padding: 1.25rem !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
    }}
    
    .stMetric label {{
        font-size: 0.875rem !important;
        color: var(--gray-500) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }}
    
    .stMetric [data-testid="stMetricValue"] {{
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: var(--primary) !important;
    }}
    
    /* Streamlit elements on dark background */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: var(--gray-100) !important;
    }}
    
    .stMarkdown p {{
        color: var(--gray-300) !important;
    }}
    
    /* =========================================================================
       ZONE-SPECIFIC STYLING
       ========================================================================= */
    
    .zone-indicator {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    
    .zone-se1 {{ 
        background-color: rgba(0, 184, 148, 0.15);
        color: {COLORS["zone_se1"]};
        border-left: 4px solid {COLORS["zone_se1"]} !important;
    }}
    
    .zone-se2 {{
        background-color: rgba(0, 206, 201, 0.15);
        color: {COLORS["zone_se2"]};
        border-left: 4px solid {COLORS["zone_se2"]} !important;
    }}
    
    .zone-se3 {{
        background-color: rgba(9, 132, 227, 0.15);
        color: {COLORS["zone_se3"]};
        border-left: 4px solid {COLORS["zone_se3"]} !important;
    }}
    
    .zone-se4 {{
        background-color: rgba(108, 92, 231, 0.15);
        color: {COLORS["zone_se4"]};
        border-left: 4px solid {COLORS["zone_se4"]} !important;
    }}
    
    /* =========================================================================
       ALERTS & STATUS - WHITE CARDS
       ========================================================================= */
    
    .alert-banner {{
        background: var(--white);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }}
    
    .alert-success {{
        border-left: 4px solid var(--success);
        color: #00875A;
    }}
    
    .alert-warning {{
        border-left: 4px solid var(--warning);
        color: #B7791F;
    }}
    
    .alert-danger {{
        border-left: 4px solid var(--danger);
        color: #C53030;
    }}
    
    .alert-info {{
        border-left: 4px solid var(--primary);
        color: var(--primary);
    }}
    
    /* =========================================================================
       TIMELINE & SIMULATION - WHITE CARDS
       ========================================================================= */
    
    .timeline-container {{
        background: var(--white);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        color: var(--gray-900);
    }}
    
    .timeline-event {{
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 1rem;
        border-left: 3px solid var(--primary);
        background: var(--gray-50);
        border-radius: 0 10px 10px 0;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
        color: var(--gray-900);
    }}
    
    .timeline-event:hover {{
        background: var(--gray-100);
        border-left-color: var(--secondary);
    }}
    
    .timeline-event.critical {{
        border-left-color: var(--danger);
        background: rgba(231, 76, 60, 0.05);
    }}
    
    .domino-chain {{
        background: var(--white);
        border-radius: 12px;
        padding: 1.5rem;
        border: none;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        color: var(--gray-900);
    }}
    
    .domino-step {{
        background: var(--gray-50);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 4px solid var(--danger);
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: var(--gray-900);
    }}
    
    .domino-step::before {{
        content: "→";
        color: var(--danger);
        font-weight: bold;
    }}
    
    /* =========================================================================
       AGENT CARDS
       ========================================================================= */
    
    .agent-card {{
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        border: 1px solid var(--gray-200);
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }}
    
    .agent-card:hover {{
        border-color: var(--primary);
        box-shadow: 0 4px 16px rgba(0, 51, 102, 0.1);
    }}
    
    .agent-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }}
    
    .agent-icon {{
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        background: var(--gray-100);
    }}
    
    .agent-status {{
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    
    .agent-status.active {{
        background: rgba(0, 184, 148, 0.15);
        color: var(--success);
    }}
    
    .agent-status.pending {{
        background: rgba(243, 156, 18, 0.15);
        color: var(--warning);
    }}
    
    /* =========================================================================
       SIDEBAR
       ========================================================================= */
    
    section[data-testid="stSidebar"] {{
        background-color: white;
        border-right: 1px solid var(--gray-200);
    }}
    
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {{
        color: var(--primary);
    }}
    
    /* =========================================================================
       FORMS & INPUTS
       ========================================================================= */
    
    .stSelectbox > div > div {{
        border-radius: 10px;
        border-color: var(--gray-200);
    }}
    
    .stSelectbox > div > div:focus-within {{
        border-color: var(--primary);
        box-shadow: 0 0 0 2px rgba(0, 51, 102, 0.1);
    }}
    
    .stSlider > div > div > div {{
        background-color: var(--primary);
    }}
    
    .stTextInput > div > div > input {{
        border-radius: 10px;
    }}
    
    /* =========================================================================
       EXPANDERS
       ========================================================================= */
    
    .streamlit-expanderHeader {{
        background-color: var(--gray-50);
        border-radius: 10px;
        font-weight: 600;
        color: var(--gray-700);
    }}
    
    .streamlit-expanderContent {{
        background-color: white;
        border-radius: 0 0 10px 10px;
    }}
    
    /* =========================================================================
       FOOTER
       ========================================================================= */
    
    .riksbank-footer {{
        background: var(--primary-dark);
        color: white;
        padding: 2rem;
        margin-top: 3rem;
        border-radius: 20px 20px 0 0;
        text-align: center;
    }}
    
    .riksbank-footer a {{
        color: var(--secondary-light);
        text-decoration: none;
    }}
    
    .riksbank-footer .footer-text {{
        font-size: 0.875rem;
        opacity: 0.8;
    }}
    
    /* =========================================================================
       RESPONSIVE ADJUSTMENTS
       ========================================================================= */
    
    @media (max-width: 768px) {{
        .riksbank-header {{
            padding: 1.5rem;
        }}
        
        .riksbank-header h1 {{
            font-size: 1.5rem;
        }}
        
        .modern-card {{
            padding: 1rem;
        }}
    }}
    
    /* =========================================================================
       ANIMATIONS
       ========================================================================= */
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .animate-in {{
        animation: fadeIn 0.3s ease-out forwards;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.6; }}
    }}
    
    .pulse {{
        animation: pulse 2s infinite;
    }}
</style>
"""


def render_header():
    """Render the modern header with Inflation → Energy / Digital Twin."""
    return """
    <div style="margin-bottom: 2rem;">
        <div style="font-family: 'Roboto Mono', monospace; font-size: 0.875rem; color: #B0B0B0; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Inflation → Energy</div>
        <h1 style="font-family: 'Inter', sans-serif; font-size: 5rem; font-weight: 900; color: #FFFFFF; margin: 0; letter-spacing: -0.03em; line-height: 1;">Digital Twin</h1>
        <p style="font-size: 1rem; color: #B0B0B0; margin-top: 0.5rem;">AI-Powered Inflation Impact Assessment</p>
    </div>
    """


def render_key_metrics_header(inflation_rate: float = 1.8, policy_rate: float = 1.75, 
                               electricity_price: float = 45.2, grid_balance: str = "Stable"):
    """Render the key metrics bar inspired by Riksbank's styrränta display."""
    return f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; margin-bottom: 2rem;">
        <div class="stat-card">
            <div class="stat-label">Current Inflation (CPIF)</div>
            <div class="stat-value" style="font-family: 'Inter', sans-serif; font-size: 4rem; font-weight: 900; color: #FFFFFF; letter-spacing: -0.02em; line-height: 1;">{inflation_rate}<span style="font-size: 1.5rem; font-weight: 500; color: #808080; margin-left: 0.125rem;">%</span></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Policy Rate</div>
            <div class="stat-value" style="font-family: 'Inter', sans-serif; font-size: 4rem; font-weight: 900; color: #FFFFFF; letter-spacing: -0.02em; line-height: 1;">{policy_rate}<span style="font-size: 1.5rem; font-weight: 500; color: #808080; margin-left: 0.125rem;">%</span></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Avg. Electricity Price</div>
            <div class="stat-value" style="font-family: 'Inter', sans-serif; font-size: 4rem; font-weight: 900; color: #FFFFFF; letter-spacing: -0.02em; line-height: 1;">{electricity_price}<span style="font-size: 1.5rem; font-weight: 500; color: #808080; margin-left: 0.25rem;">€/MWh</span></div>
        </div>
        <div class="stat-card" style="border-left-color: {'var(--success)' if grid_balance == 'Stable' else 'var(--warning)'};">
            <div class="stat-label">Grid Balance</div>
            <div class="stat-value" style="font-family: 'Inter', sans-serif; font-size: 4rem; font-weight: 900; color: #FFFFFF; letter-spacing: -0.02em; line-height: 1;">{grid_balance}</div>
        </div>
    </div>
    """


def render_info_banner(message: str, banner_type: str = "info"):
    """Render an information banner."""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "danger": "🚨"
    }
    return f"""
    <div class="alert-banner alert-{banner_type}">
        <span>{icons.get(banner_type, 'ℹ️')}</span>
        <span>{message}</span>
    </div>
    """


def render_section_header(title: str, subtitle: str = None, icon: str = None):
    """Render a section header."""
    subtitle_html = f'<div style="font-size: 0.9rem; color: var(--gray-500); margin-top: 0.25rem;">{subtitle}</div>' if subtitle else ''
    icon_html = f'<span style="margin-right: 0.5rem;">{icon}</span>' if icon else ''
    return f"""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="color: var(--primary); font-size: 1.5rem; font-weight: 600; margin: 0;">
            {icon_html}{title}
        </h2>
        {subtitle_html}
    </div>
    """


def render_footer():
    """Render the footer."""
    return """
    <div class="riksbank-footer">
        <div style="font-weight: 600; margin-bottom: 0.5rem;">Swedish Inflation Energy Digital Twin</div>
        <div class="footer-text">
            Built for Riksbanken Hackathon • AI-Powered Economic Forecasting
        </div>
        <div class="footer-text" style="margin-top: 0.5rem;">
            Data Sources: Nord Pool • SCB • SMHI • Konjunkturinstitutet
        </div>
    </div>
    """
