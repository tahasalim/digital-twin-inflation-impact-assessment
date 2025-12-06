"""
Swedish Inflation Energy Digital Twin - Design System

DARK MODE THEME:
- Dark page background (#0a192f / #0d1b2a)
- White/light cards for content
- Primary blue (#003366) as accent/fill color
- Proper contrast throughout
"""

# =============================================================================
# COLOR PALETTE - Dark Mode Theme
# =============================================================================

COLORS = {
    # Primary palette (Riksbank-inspired blues)
    "primary_900": "#001A33",       # Darkest
    "primary_800": "#002244",       # Very dark
    "primary_700": "#002855",       # Dark - headers
    "primary_600": "#003366",       # PRIMARY BRAND COLOR
    "primary_500": "#004488",       # Medium
    "primary_400": "#0066AA",       # Light
    "primary_300": "#3388CC",       # Lighter
    "primary_200": "#66AADD",       # Very light
    "primary_100": "#CCE0F0",       # Background tint
    "primary_50": "#E8F4FC",        # Lightest background
    
    # Dark mode backgrounds
    "dark_900": "#0a192f",          # Darkest - page background
    "dark_800": "#0d1b2a",          # Slightly lighter
    "dark_700": "#112240",          # Card hover/active
    "dark_600": "#1a2f4a",          # Elevated surfaces
    "dark_500": "#233554",          # Borders on dark
    "dark_400": "#2d4a6a",          # Lighter borders
    
    # Neutral palette
    "white": "#FFFFFF",
    "gray_50": "#F8FAFC",           # Light card background
    "gray_100": "#F1F5F9",          # Card background
    "gray_200": "#E2E8F0",          # Borders
    "gray_300": "#CBD5E1",          # Dividers
    "gray_400": "#94A3B8",          # Placeholder text
    "gray_500": "#64748B",          # Muted text
    "gray_600": "#475569",          # Secondary text
    "gray_700": "#334155",          # Primary text
    "gray_800": "#1E293B",          # Headings
    "gray_900": "#0F172A",          # Darkest text
    
    # Semantic colors - with light/dark variants for proper contrast
    "success_50": "#ECFDF5",        # Light success bg
    "success_100": "#D1FAE5",       # Success bg
    "success_500": "#10B981",       # Success main
    "success_700": "#047857",       # Success text on light
    "success_900": "#064E3B",       # Dark success text
    
    "warning_50": "#FFFBEB",        # Light warning bg
    "warning_100": "#FEF3C7",       # Warning bg
    "warning_500": "#F59E0B",       # Warning main
    "warning_700": "#B45309",       # Warning text on light (dark amber)
    "warning_900": "#78350F",       # Dark warning text
    
    "danger_50": "#FEF2F2",         # Light danger bg
    "danger_100": "#FEE2E2",        # Danger bg
    "danger_500": "#EF4444",        # Danger main
    "danger_700": "#B91C1C",        # Danger text on light
    "danger_900": "#7F1D1D",        # Dark danger text
    
    "info_50": "#EFF6FF",           # Light info bg
    "info_100": "#DBEAFE",          # Info bg
    "info_500": "#3B82F6",          # Info main
    "info_700": "#1D4ED8",          # Info text on light
    "info_900": "#1E3A8A",          # Dark info text
    
    # Swedish electricity zones
    "zone_se1": "#059669",          # North - Emerald
    "zone_se2": "#0891B2",          # Mid-north - Cyan
    "zone_se3": "#2563EB",          # Central - Blue  
    "zone_se4": "#7C3AED",          # South - Violet
}


def get_main_css() -> str:
    """Generate the comprehensive CSS design system."""
    return f"""
<style>
    /* =========================================================================
       CSS VARIABLES & ROOT SETUP
       ========================================================================= */
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {{
        /* Primary colors */
        --primary-900: {COLORS["primary_900"]};
        --primary-800: {COLORS["primary_800"]};
        --primary-700: {COLORS["primary_700"]};
        --primary-600: {COLORS["primary_600"]};
        --primary-500: {COLORS["primary_500"]};
        --primary-400: {COLORS["primary_400"]};
        --primary-300: {COLORS["primary_300"]};
        --primary-100: {COLORS["primary_100"]};
        --primary-50: {COLORS["primary_50"]};
        
        /* Neutrals */
        --white: {COLORS["white"]};
        --gray-50: {COLORS["gray_50"]};
        --gray-100: {COLORS["gray_100"]};
        --gray-200: {COLORS["gray_200"]};
        --gray-300: {COLORS["gray_300"]};
        --gray-400: {COLORS["gray_400"]};
        --gray-500: {COLORS["gray_500"]};
        --gray-600: {COLORS["gray_600"]};
        --gray-700: {COLORS["gray_700"]};
        --gray-800: {COLORS["gray_800"]};
        --gray-900: {COLORS["gray_900"]};
        
        /* Semantic */
        --success-50: {COLORS["success_50"]};
        --success-100: {COLORS["success_100"]};
        --success-500: {COLORS["success_500"]};
        --success-700: {COLORS["success_700"]};
        --warning-50: {COLORS["warning_50"]};
        --warning-100: {COLORS["warning_100"]};
        --warning-500: {COLORS["warning_500"]};
        --warning-700: {COLORS["warning_700"]};
        --danger-50: {COLORS["danger_50"]};
        --danger-100: {COLORS["danger_100"]};
        --danger-500: {COLORS["danger_500"]};
        --danger-700: {COLORS["danger_700"]};
        --info-50: {COLORS["info_50"]};
        --info-100: {COLORS["info_100"]};
        --info-500: {COLORS["info_500"]};
        --info-700: {COLORS["info_700"]};
        
        /* Dark mode backgrounds */
        --dark-900: {COLORS["dark_900"]};
        --dark-800: {COLORS["dark_800"]};
        --dark-700: {COLORS["dark_700"]};
        --dark-600: {COLORS["dark_600"]};
        --dark-500: {COLORS["dark_500"]};
        --dark-400: {COLORS["dark_400"]};
        
        /* Zones */
        --zone-se1: {COLORS["zone_se1"]};
        --zone-se2: {COLORS["zone_se2"]};
        --zone-se3: {COLORS["zone_se3"]};
        --zone-se4: {COLORS["zone_se4"]};
        
        /* Typography */
        --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        --font-size-xs: 0.75rem;
        --font-size-sm: 0.875rem;
        --font-size-base: 1rem;
        --font-size-lg: 1.125rem;
        --font-size-xl: 1.25rem;
        --font-size-2xl: 1.5rem;
        --font-size-3xl: 1.875rem;
        --font-size-4xl: 2.25rem;
        
        /* Spacing */
        --space-1: 0.25rem;
        --space-2: 0.5rem;
        --space-3: 0.75rem;
        --space-4: 1rem;
        --space-5: 1.25rem;
        --space-6: 1.5rem;
        --space-8: 2rem;
        --space-10: 2.5rem;
        
        /* Border radius */
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 14px;
        --radius-xl: 20px;
        
        /* Shadows - enhanced for dark mode */
        --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.3);
        --shadow-glow: 0 0 20px rgba(0, 51, 102, 0.3);
    }}
    
    /* =========================================================================
       BASE STYLES - DARK MODE
       ========================================================================= */
    
    .stApp {{
        font-family: var(--font-family);
        background-color: var(--dark-900) !important;
        color: var(--gray-100);
    }}
    
    /* Override Streamlit's default backgrounds */
    .stApp > header {{
        background-color: transparent !important;
    }}
    
    section[data-testid="stSidebar"] {{
        background-color: var(--dark-800) !important;
    }}
    
    section[data-testid="stSidebar"] .stMarkdown {{
        color: var(--gray-200);
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background-color: var(--dark-800);
        border-radius: var(--radius-lg);
        padding: var(--space-1);
        gap: var(--space-1);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: var(--gray-400);
        border-radius: var(--radius-md);
        padding: var(--space-3) var(--space-5);
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: var(--primary-600) !important;
        color: var(--white) !important;
    }}
    
    /* =========================================================================
       TYPOGRAPHY - Dark mode optimized
       ========================================================================= */
    
    .ds-h1 {{
        font-size: var(--font-size-4xl);
        font-weight: 800;
        color: var(--white);
        line-height: 1.2;
        margin: 0 0 var(--space-4) 0;
        letter-spacing: -0.025em;
    }}
    
    .ds-h2 {{
        font-size: var(--font-size-3xl);
        font-weight: 700;
        color: var(--white);
        line-height: 1.25;
        margin: 0 0 var(--space-3) 0;
        letter-spacing: -0.02em;
    }}
    
    .ds-h3 {{
        font-size: var(--font-size-2xl);
        font-weight: 600;
        color: var(--gray-100);
        line-height: 1.3;
        margin: 0 0 var(--space-3) 0;
    }}
    
    .ds-h4 {{
        font-size: var(--font-size-xl);
        font-weight: 600;
        color: var(--gray-100);
        line-height: 1.35;
        margin: 0 0 var(--space-2) 0;
    }}
    
    .ds-h5 {{
        font-size: var(--font-size-lg);
        font-weight: 600;
        color: var(--gray-200);
        line-height: 1.4;
        margin: 0 0 var(--space-2) 0;
    }}
    
    .ds-h6 {{
        font-size: var(--font-size-base);
        font-weight: 600;
        color: var(--gray-300);
        line-height: 1.4;
        margin: 0 0 var(--space-2) 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Dark text for use inside white cards */
    .ds-h1-dark, .ds-h2-dark, .ds-h3-dark, .ds-h4-dark {{
        color: var(--gray-900);
    }}
    
    .ds-text {{
        font-size: var(--font-size-base);
        color: var(--gray-300);
        line-height: 1.6;
    }}
    
    .ds-text-sm {{
        font-size: var(--font-size-sm);
        color: var(--gray-400);
        line-height: 1.5;
    }}
    
    .ds-text-muted {{
        font-size: var(--font-size-sm);
        color: var(--gray-500);
    }}
    
    .ds-label {{
        font-size: var(--font-size-xs);
        font-weight: 600;
        color: var(--gray-400);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* =========================================================================
       PAGE HEADER - Primary blue fill
       ========================================================================= */
    
    .ds-page-header {{
        background: linear-gradient(135deg, var(--primary-700) 0%, var(--primary-600) 100%);
        padding: var(--space-8) var(--space-10);
        margin: -1rem -1rem var(--space-6) -1rem;
        border-radius: 0 0 var(--radius-xl) var(--radius-xl);
        box-shadow: var(--shadow-lg), var(--shadow-glow);
    }}
    
    .ds-page-header h1 {{
        font-size: var(--font-size-3xl);
        font-weight: 700;
        color: var(--white);
        margin: 0;
    }}
    
    .ds-page-header .ds-tagline {{
        font-size: var(--font-size-base);
        color: rgba(255, 255, 255, 0.85);
        margin-top: var(--space-2);
    }}
    
    /* =========================================================================
       CARDS - White background, dark text (contrasts with dark page bg)
       ========================================================================= */
    
    .ds-card {{
        background: var(--white);
        border-radius: var(--radius-lg);
        padding: var(--space-6);
        border: none;
        box-shadow: var(--shadow-md);
        transition: all 0.2s ease;
        color: var(--gray-800);
    }}
    
    .ds-card:hover {{
        box-shadow: var(--shadow-md);
        border-color: var(--gray-300);
    }}
    
    .ds-card-header {{
        font-size: var(--font-size-lg);
        font-weight: 600;
        color: var(--gray-800);
        margin-bottom: var(--space-4);
        padding-bottom: var(--space-3);
        border-bottom: 2px solid var(--gray-100);
    }}
    
    /* Stat card with colored left border - BIG numbers */
    .ds-stat-card {{
        background: #0A0A0A;
        border-radius: 0;
        padding: 1.5rem;
        border: 1px solid #1A1A1A;
        border-left: 4px solid var(--primary-600);
        box-shadow: none;
    }}
    
    .ds-stat-card .ds-stat-value {{
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        color: #FFFFFF;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    
    .ds-stat-card .ds-stat-label {{
        font-family: 'Roboto Mono', monospace;
        font-size: 0.75rem;
        font-weight: 500;
        color: #B0B0B0;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }}
    
    /* Stat card variants */
    .ds-stat-card.success {{ border-left-color: var(--success-500); }}
    .ds-stat-card.warning {{ border-left-color: var(--warning-500); }}
    .ds-stat-card.danger {{ border-left-color: var(--danger-500); }}
    .ds-stat-card.info {{ border-left-color: var(--info-500); }}
    
    /* Zone-specific stat cards */
    .ds-stat-card.zone-se1 {{ border-left-color: var(--zone-se1); }}
    .ds-stat-card.zone-se2 {{ border-left-color: var(--zone-se2); }}
    .ds-stat-card.zone-se3 {{ border-left-color: var(--zone-se3); }}
    .ds-stat-card.zone-se4 {{ border-left-color: var(--zone-se4); }}
    
    /* =========================================================================
       ALERTS - Proper contrast with dark text on light backgrounds
       ========================================================================= */
    
    .ds-alert {{
        padding: var(--space-4) var(--space-5);
        border-radius: var(--radius-md);
        display: flex;
        align-items: flex-start;
        gap: var(--space-3);
        margin: var(--space-4) 0;
    }}
    
    .ds-alert-icon {{
        font-size: var(--font-size-xl);
        flex-shrink: 0;
    }}
    
    .ds-alert-content {{
        flex: 1;
    }}
    
    .ds-alert-title {{
        font-weight: 600;
        margin-bottom: var(--space-1);
    }}
    
    .ds-alert-message {{
        font-size: var(--font-size-sm);
    }}
    
    /* Info alert - Blue tones, dark text */
    .ds-alert-info {{
        background: var(--info-50);
        border: 1px solid var(--info-500);
    }}
    .ds-alert-info .ds-alert-title {{ color: var(--info-700); }}
    .ds-alert-info .ds-alert-message {{ color: var(--gray-700); }}
    
    /* Success alert - Green tones, dark text */
    .ds-alert-success {{
        background: var(--success-50);
        border: 1px solid var(--success-500);
    }}
    .ds-alert-success .ds-alert-title {{ color: var(--success-700); }}
    .ds-alert-success .ds-alert-message {{ color: var(--gray-700); }}
    
    /* Warning alert - Amber tones, DARK BROWN text (not yellow!) */
    .ds-alert-warning {{
        background: var(--warning-50);
        border: 1px solid var(--warning-500);
    }}
    .ds-alert-warning .ds-alert-title {{ color: var(--warning-700); }}
    .ds-alert-warning .ds-alert-message {{ color: var(--gray-700); }}
    
    /* Danger alert - Red tones, dark text */
    .ds-alert-danger {{
        background: var(--danger-50);
        border: 1px solid var(--danger-500);
    }}
    .ds-alert-danger .ds-alert-title {{ color: var(--danger-700); }}
    .ds-alert-danger .ds-alert-message {{ color: var(--gray-700); }}
    
    /* =========================================================================
       EMPTY STATE - For "No Data" messages
       ========================================================================= */
    
    .ds-empty-state {{
        background: var(--gray-100);
        border: 2px dashed var(--gray-300);
        border-radius: var(--radius-lg);
        padding: var(--space-10);
        text-align: center;
        margin: var(--space-6) 0;
    }}
    
    .ds-empty-state-icon {{
        font-size: 3rem;
        margin-bottom: var(--space-4);
    }}
    
    .ds-empty-state-title {{
        font-size: var(--font-size-xl);
        font-weight: 600;
        color: var(--gray-700);
        margin-bottom: var(--space-2);
    }}
    
    .ds-empty-state-message {{
        font-size: var(--font-size-base);
        color: var(--gray-600);
        max-width: 400px;
        margin: 0 auto var(--space-4) auto;
        line-height: 1.6;
    }}
    
    .ds-empty-state-list {{
        text-align: left;
        max-width: 350px;
        margin: var(--space-4) auto;
        padding-left: var(--space-6);
    }}
    
    .ds-empty-state-list li {{
        color: var(--gray-600);
        margin-bottom: var(--space-2);
    }}
    
    /* =========================================================================
       BADGES & CHIPS
       ========================================================================= */
    
    .ds-badge {{
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        padding: var(--space-1) var(--space-3);
        border-radius: 9999px;
        font-size: var(--font-size-xs);
        font-weight: 600;
    }}
    
    .ds-badge-primary {{
        background: var(--primary-100);
        color: var(--primary-700);
    }}
    
    .ds-badge-success {{
        background: var(--success-100);
        color: var(--success-700);
    }}
    
    .ds-badge-warning {{
        background: var(--warning-100);
        color: var(--warning-700);
    }}
    
    .ds-badge-danger {{
        background: var(--danger-100);
        color: var(--danger-700);
    }}
    
    .ds-badge-info {{
        background: var(--info-100);
        color: var(--info-700);
    }}
    
    /* =========================================================================
       BUTTONS
       ========================================================================= */
    
    .stButton > button {{
        background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-500) 100%);
        color: var(--white);
        border: none;
        border-radius: var(--radius-md);
        padding: var(--space-3) var(--space-6);
        font-weight: 600;
        font-size: var(--font-size-sm);
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }}
    
    /* Primary action button - larger, green */
    .ds-btn-primary {{
        background: linear-gradient(135deg, var(--success-500) 0%, #059669 100%) !important;
        padding: var(--space-4) var(--space-8) !important;
        font-size: var(--font-size-base) !important;
    }}
    
    /* =========================================================================
       TABS - Clean design
       ========================================================================= */
    
    .stTabs [data-baseweb="tab-list"] {{
        background-color: var(--white);
        padding: var(--space-2);
        border-radius: var(--radius-lg);
        gap: var(--space-2);
        box-shadow: var(--shadow-sm);
        margin-bottom: var(--space-6);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        border-radius: var(--radius-md);
        padding: var(--space-3) var(--space-5);
        font-weight: 500;
        color: var(--gray-600);
        border: none;
        transition: all 0.2s ease;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: var(--gray-100);
        color: var(--primary-600);
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: var(--primary-600) !important;
        color: var(--white) !important;
        box-shadow: var(--shadow-sm);
    }}
    
    /* =========================================================================
       METRICS (Streamlit native)
       ========================================================================= */
    
    .stMetric {{
        background-color: var(--white) !important;
        padding: var(--space-5) !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--gray-200) !important;
        box-shadow: var(--shadow-sm) !important;
    }}
    
    .stMetric label {{
        font-size: var(--font-size-xs) !important;
        color: var(--gray-500) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-weight: 600 !important;
    }}
    
    .stMetric [data-testid="stMetricValue"] {{
        font-size: var(--font-size-2xl) !important;
        font-weight: 700 !important;
        color: var(--gray-900) !important;
    }}
    
    /* =========================================================================
       SECTION HEADER
       ========================================================================= */
    
    .ds-section-header {{
        margin-bottom: var(--space-5);
    }}
    
    .ds-section-header h2 {{
        font-size: var(--font-size-xl);
        font-weight: 600;
        color: var(--gray-800);
        margin: 0;
    }}
    
    .ds-section-header .ds-subtitle {{
        font-size: var(--font-size-sm);
        color: var(--gray-500);
        margin-top: var(--space-1);
    }}
    
    /* =========================================================================
       SIDEBAR
       ========================================================================= */
    
    section[data-testid="stSidebar"] {{
        background-color: var(--white);
        border-right: 1px solid var(--gray-200);
    }}
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: var(--primary-700) !important;
    }}
    
    /* =========================================================================
       ZONE INDICATORS
       ========================================================================= */
    
    .ds-zone-badge {{
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-2) var(--space-4);
        border-radius: var(--radius-md);
        font-size: var(--font-size-sm);
        font-weight: 600;
    }}
    
    .ds-zone-se1 {{
        background: rgba(5, 150, 105, 0.1);
        color: #047857;
        border: 1px solid rgba(5, 150, 105, 0.3);
    }}
    
    .ds-zone-se2 {{
        background: rgba(8, 145, 178, 0.1);
        color: #0E7490;
        border: 1px solid rgba(8, 145, 178, 0.3);
    }}
    
    .ds-zone-se3 {{
        background: rgba(37, 99, 235, 0.1);
        color: #1D4ED8;
        border: 1px solid rgba(37, 99, 235, 0.3);
    }}
    
    .ds-zone-se4 {{
        background: rgba(124, 58, 237, 0.1);
        color: #6D28D9;
        border: 1px solid rgba(124, 58, 237, 0.3);
    }}
    
    /* =========================================================================
       TIMELINE
       ========================================================================= */
    
    .ds-timeline-event {{
        display: flex;
        align-items: flex-start;
        gap: var(--space-4);
        padding: var(--space-4);
        background: var(--white);
        border-left: 4px solid var(--primary-500);
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
        margin-bottom: var(--space-3);
        box-shadow: var(--shadow-sm);
    }}
    
    .ds-timeline-event.critical {{
        border-left-color: var(--danger-500);
        background: var(--danger-50);
    }}
    
    .ds-timeline-event.warning {{
        border-left-color: var(--warning-500);
        background: var(--warning-50);
    }}
    
    /* =========================================================================
       DOMINO CHAIN
       ========================================================================= */
    
    .ds-domino-step {{
        background: var(--white);
        padding: var(--space-4);
        margin: var(--space-2) 0;
        border-radius: var(--radius-md);
        border-left: 4px solid var(--danger-500);
        box-shadow: var(--shadow-sm);
        display: flex;
        align-items: center;
        gap: var(--space-3);
        color: var(--gray-700);
    }}
    
    .ds-domino-step::before {{
        content: "→";
        color: var(--danger-500);
        font-weight: bold;
        font-size: var(--font-size-lg);
    }}
    
    /* =========================================================================
       FOOTER
       ========================================================================= */
    
    .ds-footer {{
        background: var(--primary-800);
        color: var(--white);
        padding: var(--space-8);
        margin-top: var(--space-10);
        border-radius: var(--radius-xl) var(--radius-xl) 0 0;
        text-align: center;
    }}
    
    .ds-footer-title {{
        font-weight: 600;
        margin-bottom: var(--space-2);
    }}
    
    .ds-footer-text {{
        font-size: var(--font-size-sm);
        color: rgba(255, 255, 255, 0.75);
    }}
    
    /* =========================================================================
       UTILITIES
       ========================================================================= */
    
    .ds-mt-4 {{ margin-top: var(--space-4); }}
    .ds-mb-4 {{ margin-bottom: var(--space-4); }}
    .ds-p-4 {{ padding: var(--space-4); }}
    .ds-text-center {{ text-align: center; }}
    .ds-flex {{ display: flex; }}
    .ds-gap-4 {{ gap: var(--space-4); }}
    
    /* Grid layout */
    .ds-grid-4 {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: var(--space-4);
    }}
    
    @media (max-width: 768px) {{
        .ds-grid-4 {{
            grid-template-columns: repeat(2, 1fr);
        }}
    }}
</style>
"""


# =============================================================================
# REUSABLE COMPONENT FUNCTIONS
# =============================================================================

def render_page_header(title: str, tagline: str = None) -> str:
    """Render a page header with dark background and light text."""
    tagline_html = f'<div class="ds-tagline">{tagline}</div>' if tagline else ''
    return f"""
    <div class="ds-page-header">
        <h1>🇸🇪 {title}</h1>
        {tagline_html}
    </div>
    """


def render_section_header(title: str, subtitle: str = None, icon: str = None) -> str:
    """Render a section header with dark text."""
    icon_html = f'{icon} ' if icon else ''
    subtitle_html = f'<div class="ds-subtitle">{subtitle}</div>' if subtitle else ''
    return f"""
    <div class="ds-section-header">
        <h2>{icon_html}{title}</h2>
        {subtitle_html}
    </div>
    """


def render_alert(message: str, title: str = None, alert_type: str = "info", icon: str = None) -> str:
    """
    Render an alert with proper contrast.
    
    Args:
        message: Alert message text
        title: Optional title
        alert_type: One of 'info', 'success', 'warning', 'danger'
        icon: Optional emoji icon
    """
    default_icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "danger": "🚨"
    }
    icon = icon or default_icons.get(alert_type, "ℹ️")
    title_html = f'<div class="ds-alert-title">{title}</div>' if title else ''
    
    return f"""
    <div class="ds-alert ds-alert-{alert_type}">
        <span class="ds-alert-icon">{icon}</span>
        <div class="ds-alert-content">
            {title_html}
            <div class="ds-alert-message">{message}</div>
        </div>
    </div>
    """


def render_empty_state(title: str, message: str, icon: str = "📭", list_items: list = None) -> str:
    """
    Render an empty state placeholder with proper dark text.
    
    Args:
        title: Main title
        message: Description message
        icon: Emoji icon
        list_items: Optional list of instruction items
    """
    list_html = ""
    if list_items:
        items = "".join([f"<li>{item}</li>" for item in list_items])
        list_html = f'<ul class="ds-empty-state-list">{items}</ul>'
    
    return f"""
    <div class="ds-empty-state">
        <div class="ds-empty-state-icon">{icon}</div>
        <div class="ds-empty-state-title">{title}</div>
        <div class="ds-empty-state-message">{message}</div>
        {list_html}
    </div>
    """


def render_stat_card(label: str, value: str, variant: str = None) -> str:
    """
    Render a stat card with label and value.
    
    Args:
        label: Metric label
        value: Metric value
        variant: Color variant - 'success', 'warning', 'danger', 'info', 'zone-se1', etc.
    """
    variant_class = f" {variant}" if variant else ""
    return f"""
    <div class="ds-stat-card{variant_class}">
        <div class="ds-stat-value">{value}</div>
        <div class="ds-stat-label">{label}</div>
    </div>
    """


def render_badge(text: str, variant: str = "primary") -> str:
    """Render a badge/chip with proper contrast."""
    return f'<span class="ds-badge ds-badge-{variant}">{text}</span>'


def render_key_metrics_bar(inflation: float = 1.8, policy_rate: float = 1.75, 
                           electricity_price: float = 45.2, grid_status: str = "Stable") -> str:
    """Render the key metrics bar with 4 stat cards."""
    status_variant = "success" if grid_status == "Stable" else "warning"
    
    return f"""
    <div class="ds-grid-4">
        <div class="ds-stat-card">
            <div class="ds-stat-value">{inflation}%</div>
            <div class="ds-stat-label">Current Inflation (CPIF)</div>
        </div>
        <div class="ds-stat-card">
            <div class="ds-stat-value">{policy_rate}%</div>
            <div class="ds-stat-label">Policy Rate</div>
        </div>
        <div class="ds-stat-card">
            <div class="ds-stat-value">{electricity_price} €</div>
            <div class="ds-stat-label">Avg. Electricity Price</div>
        </div>
        <div class="ds-stat-card {status_variant}">
            <div class="ds-stat-value">{grid_status}</div>
            <div class="ds-stat-label">Grid Balance</div>
        </div>
    </div>
    """


def render_footer() -> str:
    """Render the page footer."""
    return """
    <div class="ds-footer">
        <div class="ds-footer-title">Swedish Inflation Energy Digital Twin</div>
        <div class="ds-footer-text">
            Built for Riksbanken Hackathon • AI-Powered Economic Forecasting
        </div>
        <div class="ds-footer-text" style="margin-top: 0.5rem;">
            Data Sources: Nord Pool • SCB • SMHI • Konjunkturinstitutet
        </div>
    </div>
    """
