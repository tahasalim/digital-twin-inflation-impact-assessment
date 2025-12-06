"""
Swedish Inflation Energy Digital Twin - Modern Professional Design System

Design Philosophy:
- High contrast, pure black background with white text
- Sharp edges - no rounded corners
- Inter for headings, Roboto Mono for body text
- Minimal, institutional aesthetic for Riksbank economists
- Data should be the hero, not the UI

Typography:
- Headings: Inter (clean, modern sans-serif)
- Body: Roboto Mono (technical, precise, monospace)
- All text white, subtext slightly muted white

Color Strategy:
- Background: Pure black (#000000)
- Surface: Near black (#0A0A0A) - cards and elevated content
- Border: Dark gray (#1A1A1A) - subtle separation
- Text: Pure white (#FFFFFF) - all primary text
- Subtext: Muted white (#B0B0B0) - secondary information
- Primary: Riksbank Blue (#003366) - accent, CTAs
"""

# =============================================================================
# REFINED COLOR PALETTE - HIGH CONTRAST BLACK/WHITE
# =============================================================================

COLORS = {
    # Background layers (pure black base)
    "bg_base": "#000000",           # Page background - pure black
    "bg_surface": "#0A0A0A",        # Cards, modals - near black
    "bg_elevated": "#111111",       # Hover states, nested cards
    "bg_overlay": "#1A1A1A",        # Dropdowns, tooltips
    
    # Border & dividers
    "border_subtle": "#1A1A1A",     # Default borders
    "border_default": "#2A2A2A",    # Emphasized borders
    "border_strong": "#3A3A3A",     # Focus states
    
    # Text hierarchy - WHITE based
    "text_primary": "#FFFFFF",      # Headlines, important text - pure white
    "text_secondary": "#B0B0B0",    # Body text, descriptions - muted white
    "text_tertiary": "#808080",     # Captions, placeholders
    "text_inverse": "#000000",      # Text on light backgrounds
    
    # Primary accent (Riksbank Blue) - THE ONLY accent
    "primary_900": "#001a33",       # Darkest
    "primary_800": "#002244",
    "primary_700": "#002855",       # Dark
    "primary_600": "#003366",       # DEFAULT PRIMARY
    "primary_500": "#004080",       
    "primary_400": "#0066cc",       # Hover, links
    "primary_300": "#3399ff",       # Active states
    "primary_200": "#66b3ff",       # Light accent
    "primary_100": "#cce5ff",       # Very light tint
    
    # Semantic - MUTED versions (use sparingly)
    "success": "#1a4d2e",           # Muted green
    "success_text": "#4ade80",      # Green text
    "warning": "#5c4a0a",           # Muted amber  
    "warning_text": "#fbbf24",      # Amber text
    "danger": "#5c1a1a",            # Muted red
    "danger_text": "#f87171",       # Red text
    "critical": "#dc2626",          # Bright red for CRITICAL
    
    # Supply & Demand - ALWAYS consistent
    "supply": "#3b82f6",            # Blue - ALWAYS for supply
    "demand": "#ef4444",            # Red - ALWAYS for demand
    
    # Zone colors - vibrant for visibility on black
    "zone_se1": "#10b981",          # Emerald
    "zone_se2": "#06b6d4",          # Cyan
    "zone_se3": "#3b82f6",          # Blue
    "zone_se4": "#8b5cf6",          # Violet
}

# Convenient zone color mapping
ZONE_COLORS = {
    "SE1": COLORS["zone_se1"],
    "SE2": COLORS["zone_se2"],
    "SE3": COLORS["zone_se3"],
    "SE4": COLORS["zone_se4"],
}

# Zone colors as list (for index-based access)
ZONE_COLOR_LIST = [
    COLORS["zone_se1"],  # SE1
    COLORS["zone_se2"],  # SE2
    COLORS["zone_se3"],  # SE3
    COLORS["zone_se4"],  # SE4
]

# Typography settings - Inter for headings, Roboto Mono for body
TYPOGRAPHY = {
    "font_heading": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "font_body": "'Roboto Mono', 'SF Mono', 'Monaco', 'Consolas', monospace",
    "font_family": "'Roboto Mono', 'SF Mono', 'Monaco', 'Consolas', monospace",
    "font_size_base": "14px",
    "font_size_sm": "12px",
    "font_size_lg": "16px",
    "font_size_xl": "20px",
    "font_size_2xl": "24px",
    "font_size_3xl": "30px",
    "font_weight_normal": "400",
    "font_weight_medium": "500",
    "font_weight_semibold": "600",
    "font_weight_bold": "700",
    "line_height": "1.5",
}


def get_main_css() -> str:
    """Generate modern, professional CSS with sharp edges and high contrast."""
    return f"""
<style>
    /* =========================================================================
       CSS CUSTOM PROPERTIES
       ========================================================================= */
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Roboto+Mono:wght@400;500;600;700&display=swap');
    
    :root {{
        /* Backgrounds */
        --bg-base: {COLORS["bg_base"]};
        --bg-surface: {COLORS["bg_surface"]};
        --bg-elevated: {COLORS["bg_elevated"]};
        --bg-overlay: {COLORS["bg_overlay"]};
        
        /* Borders */
        --border-subtle: {COLORS["border_subtle"]};
        --border-default: {COLORS["border_default"]};
        --border-strong: {COLORS["border_strong"]};
        
        /* Text */
        --text-primary: {COLORS["text_primary"]};
        --text-secondary: {COLORS["text_secondary"]};
        --text-tertiary: {COLORS["text_tertiary"]};
        
        /* Primary */
        --primary: {COLORS["primary_600"]};
        --primary-hover: {COLORS["primary_400"]};
        --primary-muted: {COLORS["primary_800"]};
        
        /* Semantic */
        --success: {COLORS["success"]};
        --success-text: {COLORS["success_text"]};
        --warning: {COLORS["warning"]};
        --warning-text: {COLORS["warning_text"]};
        --danger: {COLORS["danger"]};
        --danger-text: {COLORS["danger_text"]};
        
        /* Zones */
        --zone-1: {COLORS["zone_se1"]};
        --zone-2: {COLORS["zone_se2"]};
        --zone-3: {COLORS["zone_se3"]};
        --zone-4: {COLORS["zone_se4"]};
        
        /* Typography - Inter for headings, Roboto Mono for body */
        --font-heading: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-body: 'Roboto Mono', 'SF Mono', 'Monaco', 'Consolas', monospace;
        --font-mono: 'Roboto Mono', 'SF Mono', 'Monaco', monospace;
        
        /* Sizing - SHARP EDGES */
        --radius-sm: 0px;
        --radius-md: 0px;
        --radius-lg: 0px;
        
        /* Shadows - minimal for flat design */
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.5);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.6);
        --shadow-lg: 0 8px 24px rgba(0,0,0,0.7);
    }}
    
    /* =========================================================================
       BASE STYLES - Pure black background, white text
       ========================================================================= */
    
    .stApp {{
        background: var(--bg-base) !important;
        font-family: var(--font-body);
        color: var(--text-primary);
    }}
    
    /* All text white by default */
    .stApp, .stApp * {{
        color: var(--text-primary) !important;
    }}
    
    /* Secondary text - muted white */
    .stApp p, .stApp span, .stApp label {{
        color: var(--text-secondary) !important;
    }}
    
    /* Headings - Inter font, pure white */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
        font-family: var(--font-heading) !important;
        color: var(--text-primary) !important;
        font-weight: 600;
    }}
    
    /* Remove default Streamlit backgrounds */
    .stApp > header {{
        background: transparent !important;
    }}
    
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}
    
    /* Main content area */
    .main .block-container {{
        padding: 2rem 3rem !important;
        max-width: 1400px !important;
    }}
    
    /* Remove ALL border-radius throughout the app */
    .stApp * {{
        border-radius: 0 !important;
    }}
    
    /* =========================================================================
       SIDEBAR - Clean, minimal, sharp edges
       ========================================================================= */
    
    section[data-testid="stSidebar"] {{
        background: var(--bg-surface) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }}
    
    section[data-testid="stSidebar"] > div {{
        padding: 1.5rem 1rem !important;
    }}
    
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {{
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
    }}
    
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }}
    
    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton button {{
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        font-size: 0.8125rem !important;
        padding: 0.5rem 1rem !important;
        border-radius: var(--radius-md) !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
        justify-content: flex-start !important;
    }}
    
    section[data-testid="stSidebar"] .stButton button:hover {{
        background: var(--primary-muted) !important;
        border-color: var(--primary) !important;
    }}
    
    /* =========================================================================
       TABS - White text buttons on black background, clean minimal
       ========================================================================= */
    
    .stTabs {{
        background: #000000 !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background: #000000 !important;
        border-radius: 0 !important;
        padding: 1rem 0 !important;
        gap: 1rem !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: #FFFFFF !important;
        color: #000000 !important;
        font-family: var(--font-body) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        padding: 1rem 2rem !important;
        border-radius: 0 !important;
        border: none !important;
        transition: all 0.15s ease !important;
    }}
    
    .stTabs [data-baseweb="tab"] * {{
        color: #000000 !important;
    }}
    
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] div {{
        color: #000000 !important;
        font-weight: 500 !important;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        color: #000000 !important;
        background: #E0E0E0 !important;
    }}
    
    .stTabs [data-baseweb="tab"]:hover * {{
        color: #000000 !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: #FFFFFF !important;
        color: #000000 !important;
        font-weight: 500 !important;
        border: none !important;
    }}
    
    .stTabs [aria-selected="true"] * {{
        color: #000000 !important;
        font-weight: 500 !important;
    }}
    
    /* Remove any underline/indicator */
    .stTabs [data-baseweb="tab-highlight"] {{
        display: none !important;
        background: transparent !important;
    }}
    
    .stTabs [data-baseweb="tab-border"] {{
        display: none !important;
        background: transparent !important;
    }}
    
    /* Tab panel content */
    .stTabs [data-baseweb="tab-panel"] {{
        padding-top: 2rem !important;
        background: #000000 !important;
    }}
    
    /* =========================================================================
       TYPOGRAPHY - BOLD hierarchy with HUGE headings
       ========================================================================= */
    
    /* Main page title - HUGE */
    .stMarkdown h1 {{
        color: var(--text-primary) !important;
        font-family: var(--font-heading) !important;
        font-size: 4rem !important;
        font-weight: 900 !important;
        letter-spacing: -0.03em !important;
        margin-bottom: 1rem !important;
        line-height: 1.1 !important;
    }}
    
    /* Section headers - Medium */
    .stMarkdown h2 {{
        color: var(--text-primary) !important;
        font-family: var(--font-heading) !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        margin-top: 2.5rem !important;
        margin-bottom: 1rem !important;
        line-height: 1.2 !important;
    }}
    
    /* Subsection headers */
    .stMarkdown h3 {{
        color: var(--text-primary) !important;
        font-family: var(--font-heading) !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }}
    
    /* H4 - smaller section headers */
    .stMarkdown h4 {{
        color: var(--text-secondary) !important;
        font-family: var(--font-heading) !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }}
    
    /* Body text */
    .stMarkdown p {{
        color: var(--text-secondary) !important;
        font-size: 0.9375rem !important;
        line-height: 1.6 !important;
    }}
    
    /* Lists */
    .stMarkdown ul, .stMarkdown ol {{
        color: var(--text-secondary) !important;
    }}
    
    .stMarkdown li {{
        margin-bottom: 0.375rem !important;
    }}
    
    /* =========================================================================
       CARDS - Sharp edges, HUGE numbers
       ========================================================================= */
    
    .modern-card {{
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: 0;
        padding: 1.5rem;
        transition: border-color 0.15s ease;
    }}
    
    .modern-card:hover {{
        border-color: var(--border-default);
    }}
    
    .modern-card-header {{
        font-family: var(--font-body);
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-secondary);
        margin-bottom: 0.75rem;
    }}
    
    .modern-card-value {{
        font-family: var(--font-heading);
        font-size: 3rem;
        font-weight: 900;
        color: var(--text-primary);
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    
    .modern-card-sublabel {{
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-top: 0.5rem;
    }}
    
    /* Hero number variant - extra large */
    .hero-number {{
        font-family: var(--font-heading);
        font-size: 5rem;
        font-weight: 900;
        color: var(--text-primary);
        letter-spacing: -0.03em;
        line-height: 1;
    }}
    
    /* Large insight number */
    .insight-number {{
        font-family: var(--font-heading);
        font-size: 3.5rem;
        font-weight: 900;
        color: var(--text-primary);
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    
    /* =========================================================================
       METRICS - HUGE numbers for impact
       ========================================================================= */
    
    .stMetric {{
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0.5rem 0 !important;
    }}
    
    .stMetric label {{
        color: var(--text-secondary) !important;
        font-family: var(--font-body) !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        margin-bottom: 0.5rem !important;
    }}
    
    .stMetric [data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-size: 2rem !important;
        font-weight: 900 !important;
        font-family: var(--font-heading) !important;
        letter-spacing: -0.02em !important;
        line-height: 1.1 !important;
    }}
    
    .stMetric [data-testid="stMetricDelta"] {{
        font-size: 0.875rem !important;
        font-weight: 600 !important;
    }}
    
    /* Large metric variant for hero numbers */
    .metric-huge [data-testid="stMetricValue"] {{
        font-size: 4.5rem !important;
        font-weight: 900 !important;
    }}
    
    /* =========================================================================
       ALERTS & STATUS - Muted, professional
       ========================================================================= */
    
    .status-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.25rem 0.625rem;
        border-radius: 0;
        font-size: 0.75rem;
        font-weight: 500;
    }}
    
    .status-badge.success {{
        background: var(--success);
        color: var(--success-text);
    }}
    
    .status-badge.warning {{
        background: var(--warning);
        color: var(--warning-text);
    }}
    
    .status-badge.danger {{
        background: var(--danger);
        color: var(--danger-text);
    }}
    
    .status-badge.neutral {{
        background: var(--bg-elevated);
        color: var(--text-secondary);
    }}
    
    /* Alert boxes */
    .alert-box {{
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-left: 3px solid var(--primary);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        margin: 1rem 0;
    }}
    
    .alert-box.warning {{
        border-left-color: var(--warning-text);
    }}
    
    .alert-box.danger {{
        border-left-color: var(--danger-text);
    }}
    
    .alert-box.success {{
        border-left-color: var(--success-text);
    }}
    
    .alert-box-title {{
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }}
    
    .alert-box-message {{
        font-size: 0.8125rem;
        color: var(--text-secondary);
        line-height: 1.5;
    }}
    
    /* =========================================================================
       DATA TABLE STYLING
       ========================================================================= */
    
    .stDataFrame {{
        background: var(--bg-surface) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-lg) !important;
    }}
    
    .stDataFrame thead th {{
        background: var(--bg-elevated) !important;
        color: var(--text-tertiary) !important;
        font-size: 0.6875rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}
    
    .stDataFrame tbody td {{
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        border-color: var(--border-subtle) !important;
    }}
    
    /* =========================================================================
       BUTTONS - Subtle, professional
       ========================================================================= */
    
    .stButton > button {{
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        padding: 0.625rem 1.25rem !important;
        transition: all 0.15s ease !important;
    }}
    
    .stButton > button:hover {{
        background: var(--primary-hover) !important;
        transform: translateY(-1px) !important;
    }}
    
    /* Secondary button style */
    .stButton > button[kind="secondary"] {{
        background: transparent !important;
        border: 1px solid var(--border-default) !important;
        color: var(--text-primary) !important;
    }}
    
    .stButton > button[kind="secondary"]:hover {{
        background: var(--bg-elevated) !important;
        border-color: var(--primary) !important;
    }}
    
    /* =========================================================================
       FORM ELEMENTS - Sharp edges, high contrast
       ========================================================================= */
    
    /* Text inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: var(--bg-surface) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 0 !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--primary) !important;
        box-shadow: none !important;
    }}
    
    .stSelectbox > div > div,
    .stMultiSelect > div > div {{
        background: var(--bg-surface) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 0 !important;
        color: var(--text-primary) !important;
    }}
    
    .stSelectbox label,
    .stMultiSelect label,
    .stSlider label,
    .stTextInput label,
    .stTextArea label {{
        color: var(--text-secondary) !important;
        font-size: 0.8125rem !important;
        font-weight: 500 !important;
        font-family: var(--font-body) !important;
    }}
    
    .stSlider > div > div > div {{
        background: var(--primary) !important;
    }}
    
    /* Number inputs */
    .stNumberInput > div > div > input {{
        background: var(--bg-surface) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 0 !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
    }}
    
    /* =========================================================================
       EXPANDERS - Clean accordions, sharp edges
       ========================================================================= */
    
    .streamlit-expanderHeader {{
        background: var(--bg-surface) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 0 !important;
        color: var(--text-primary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        border-color: var(--border-default) !important;
    }}
    
    .streamlit-expanderContent {{
        background: var(--bg-surface) !important;
        border: 1px solid var(--border-subtle) !important;
        border-top: none !important;
        border-radius: 0 !important;
    }}
    
    /* =========================================================================
       PLOTLY CHARTS - Dark theme compatible
       ========================================================================= */
    
    .js-plotly-plot .plotly {{
        background: transparent !important;
    }}
    
    /* =========================================================================
       CUSTOM COMPONENTS
       ========================================================================= */
    
    /* Page header */
    .page-header {{
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-subtle);
    }}
    
    .page-header-title {{
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.02em;
    }}
    
    .page-header-subtitle {{
        font-size: 1rem;
        color: var(--text-secondary);
        margin-top: 0.5rem;
    }}
    
    /* KPI bar - HUGE numbers */
    .kpi-bar {{
        display: flex;
        gap: 3rem;
        padding: 2rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid var(--border-subtle);
    }}
    
    .kpi-item {{
        display: flex;
        flex-direction: column;
    }}
    
    .kpi-label {{
        font-family: var(--font-body);
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }}
    
    .kpi-value {{
        font-family: var(--font-heading);
        font-size: 3rem;
        font-weight: 900;
        color: var(--text-primary);
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    
    /* Extra large KPI variant */
    .kpi-value-xl {{
        font-family: var(--font-heading);
        font-size: 4.5rem;
        font-weight: 900;
        color: var(--text-primary);
        letter-spacing: -0.03em;
        line-height: 1;
    }}
    
    /* Section wrapper */
    .section {{
        margin-bottom: 2rem;
    }}
    
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }}
    
    .section-title {{
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
    }}
    
    .section-icon {{
        font-size: 1rem;
        opacity: 0.7;
    }}
    
    /* Grid layouts */
    .grid-2 {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
    }}
    
    .grid-3 {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
    }}
    
    .grid-4 {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
    }}
    
    /* Empty state */
    .empty-state {{
        background: var(--bg-surface);
        border: 1px dashed var(--border-default);
        border-radius: var(--radius-lg);
        padding: 3rem 2rem;
        text-align: center;
    }}
    
    .empty-state-icon {{
        font-size: 2rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }}
    
    .empty-state-title {{
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }}
    
    .empty-state-message {{
        font-size: 0.875rem;
        color: var(--text-secondary);
        max-width: 320px;
        margin: 0 auto;
    }}
    
    /* Zone indicators - subtle chips */
    .zone-chip {{
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.25rem 0.5rem;
        border-radius: var(--radius-sm);
        font-size: 0.75rem;
        font-weight: 500;
        background: var(--bg-elevated);
    }}
    
    .zone-chip.se1 {{ color: var(--zone-1); }}
    .zone-chip.se2 {{ color: var(--zone-2); }}
    .zone-chip.se3 {{ color: var(--zone-3); }}
    .zone-chip.se4 {{ color: var(--zone-4); }}
    
    .zone-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }}
    
    .zone-dot.se1 {{ background: var(--zone-1); }}
    .zone-dot.se2 {{ background: var(--zone-2); }}
    .zone-dot.se3 {{ background: var(--zone-3); }}
    .zone-dot.se4 {{ background: var(--zone-4); }}
    
    /* Timeline items */
    .timeline-item {{
        display: flex;
        gap: 1rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid var(--border-subtle);
    }}
    
    .timeline-item:last-child {{
        border-bottom: none;
    }}
    
    .timeline-time {{
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-tertiary);
        font-family: var(--font-mono);
        min-width: 3rem;
    }}
    
    .timeline-content {{
        flex: 1;
    }}
    
    .timeline-title {{
        font-size: 0.875rem;
        color: var(--text-primary);
        margin-bottom: 0.125rem;
    }}
    
    .timeline-description {{
        font-size: 0.8125rem;
        color: var(--text-secondary);
    }}
    
    /* Subsystem status cards */
    .status-card {{
        background: transparent;
        border: none;
        padding: 1rem 1.25rem;
        text-align: center;
    }}
    
    .status-name {{
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }}
    
    .status-state {{
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 900;
        color: var(--text-secondary);
    }}
    
    .status-state.ready {{
        color: var(--success-text);
    }}
    
    .status-state.pending {{
        color: var(--text-tertiary);
    }}
    
    /* Insight cards - no background, no border */
    .insight-card {{
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 1.25rem;
    }}
    
    .insight-icon {{
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }}
    
    .insight-value {{
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 900;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }}
    
    .insight-label {{
        font-size: 0.6875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-tertiary);
    }}
    
    .insight-label-top {{
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }}
    
    .insight-card-icon {{
        font-size: 1.25rem;
        margin-bottom: 0.75rem;
    }}
    
    .insight-card-value {{
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 900;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }}
    
    .insight-card-label {{
        font-size: 0.6875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-tertiary);
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--bg-base);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--border-default);
        border-radius: 0;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--border-strong);
    }}
</style>
"""


# =============================================================================
# COMPONENT FUNCTIONS
# =============================================================================

def render_page_header(title: str, subtitle: str = None) -> str:
    """Render a clean page header."""
    subtitle_html = f'<div class="page-header-subtitle">{subtitle}</div>' if subtitle else ''
    return f"""
    <div class="page-header">
        <div class="page-header-title">{title}</div>
        {subtitle_html}
    </div>
    """


def render_kpi_bar(kpis: list) -> str:
    """
    Render a horizontal KPI bar.
    kpis: list of dicts with 'label' and 'value' keys
    """
    items = ""
    for kpi in kpis:
        items += f"""
        <div class="kpi-item">
            <span class="kpi-label">{kpi['label']}</span>
            <span class="kpi-value">{kpi['value']}</span>
        </div>
        """
    return f'<div class="kpi-bar">{items}</div>'


def render_section_header(title: str, icon: str = None) -> str:
    """Render a section header."""
    icon_html = f'<span class="section-icon">{icon}</span>' if icon else ''
    return f"""
    <div class="section-header">
        {icon_html}
        <span class="section-title">{title}</span>
    </div>
    """


def render_card(header: str, value: str, sublabel: str = None) -> str:
    """Render a metric card."""
    sublabel_html = f'<div class="modern-card-sublabel">{sublabel}</div>' if sublabel else ''
    return f"""
    <div class="modern-card">
        <div class="modern-card-header">{header}</div>
        <div class="modern-card-value">{value}</div>
        {sublabel_html}
    </div>
    """


def render_alert(title: str, message: str, variant: str = "info") -> str:
    """Render an alert box. variant: info, warning, danger, success"""
    return f"""
    <div class="alert-box {variant}">
        <div class="alert-box-title">{title}</div>
        <div class="alert-box-message">{message}</div>
    </div>
    """


def render_empty_state(title: str, message: str, icon: str = "📭") -> str:
    """Render an empty state placeholder."""
    return f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-message">{message}</div>
    </div>
    """


def render_status_badge(text: str, variant: str = "neutral") -> str:
    """Render a status badge. variant: success, warning, danger, neutral"""
    return f'<span class="status-badge {variant}">{text}</span>'


def render_zone_chip(zone: str) -> str:
    """Render a zone indicator chip."""
    zone_lower = zone.lower()
    return f"""
    <span class="zone-chip {zone_lower}">
        <span class="zone-dot {zone_lower}"></span>
        {zone.upper()}
    </span>
    """


def render_insight_card(icon: str, value: str, label: str) -> str:
    """Render an insight/metric card."""
    return f"""
    <div class="insight-card">
        <div class="insight-card-icon">{icon}</div>
        <div class="insight-card-value">{value}</div>
        <div class="insight-card-label">{label}</div>
    </div>
    """


def render_timeline_item(time: str, title: str, description: str = None) -> str:
    """Render a timeline item."""
    desc_html = f'<div class="timeline-description">{description}</div>' if description else ''
    return f"""
    <div class="timeline-item">
        <div class="timeline-time">{time}</div>
        <div class="timeline-content">
            <div class="timeline-title">{title}</div>
            {desc_html}
        </div>
    </div>
    """
