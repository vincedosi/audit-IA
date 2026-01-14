import streamlit as st
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from mistralai import Mistral
from urllib.parse import urljoin, urlparse
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from datetime import datetime
import xml.etree.ElementTree as ET
import re

# =============================================================================
# 1. CONFIGURATION & STYLE
# =============================================================================
st.set_page_config(page_title="Seorux AIO", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp { background-color: #F8F9FA; color: #1A202C; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #2D3748; font-family: 'Inter', sans-serif; }
    
    /* Cards métriques */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] { color: #3182CE; font-size: 28px; }
    
    /* Dashboard Grid */
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    
    /* File Status Card - Nouveau Design */
    .status-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .status-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }
    .status-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
    }
    .status-card.success::before { background: linear-gradient(90deg, #38A169, #68D391); }
    .status-card.warning::before { background: linear-gradient(90deg, #DD6B20, #F6AD55); }
    .status-card.error::before { background: linear-gradient(90deg, #E53E3E, #FC8181); }
    .status-card.info::before { background: linear-gradient(90deg, #3182CE, #63B3ED); }
    
    .card-icon {
        font-size: 2.5em;
        margin-bottom: 12px;
    }
    .card-title {
        font-size: 1.1em;
        font-weight: 700;
        color: #2D3748;
        margin-bottom: 4px;
    }
    .card-desc {
        font-size: 0.85em;
        color: #718096;
        margin-bottom: 16px;
    }
    .card-status {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 600;
    }
    .card-status.present { background: #C6F6D5; color: #22543D; }
    .card-status.missing { background: #FED7D7; color: #822727; }
    .card-status.optimize { background: #FEEBC8; color: #744210; }
    
    .card-score {
        position: absolute;
        top: 20px;
        right: 20px;
        font-size: 1.4em;
        font-weight: 800;
    }
    
    /* Score Central */
    .score-hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
    }
    .score-hero-value {
        font-size: 5em;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 10px;
    }
    .score-hero-label {
        font-size: 1.2em;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .score-hero-sub {
        font-size: 1em;
        opacity: 0.7;
        margin-top: 10px;
    }
    
    /* Progress Ring */
    .progress-ring {
        display: flex;
        justify-content: center;
        gap: 30px;
        flex-wrap: wrap;
        margin: 30px 0;
    }
    .progress-item {
        text-align: center;
    }
    .progress-circle {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5em;
        font-weight: 700;
        margin: 0 auto 8px;
        border: 4px solid #E2E8F0;
    }
    .progress-circle.good { border-color: #38A169; color: #38A169; background: #F0FFF4; }
    .progress-circle.medium { border-color: #DD6B20; color: #DD6B20; background: #FFFAF0; }
    .progress-circle.bad { border-color: #E53E3E; color: #E53E3E; background: #FFF5F5; }
    .progress-label { font-size: 0.85em; color: #718096; }
    
    /* Checklist Visuelle */
    .checklist-container {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    .checklist-item {
        display: flex;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid #EDF2F7;
        transition: background 0.2s;
    }
    .checklist-item:hover { background: #F7FAFC; }
    .checklist-item:last-child { border-bottom: none; }
    .checklist-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3em;
        margin-right: 16px;
    }
    .checklist-icon.success { background: #C6F6D5; }
    .checklist-icon.error { background: #FED7D7; }
    .checklist-icon.warning { background: #FEEBC8; }
    .checklist-content { flex: 1; }
    .checklist-title { font-weight: 600; color: #2D3748; }
    .checklist-subtitle { font-size: 0.85em; color: #718096; }
    .checklist-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75em;
        font-weight: 600;
    }
    .checklist-badge.ok { background: #C6F6D5; color: #22543D; }
    .checklist-badge.ko { background: #FED7D7; color: #822727; }
    .checklist-badge.warn { background: #FEEBC8; color: #744210; }
    
    /* Code Diff */
    .code-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        font-size: 0.9em;
        padding: 10px 14px;
        border-radius: 8px 8px 0 0;
    }
    .code-header.before { background: #FFF5F5; color: #C53030; }
    .code-header.after { background: #F0FFF4; color: #276749; }
    
    /* Insight Box */
    .insight-box {
        background: linear-gradient(135deg, #EBF8FF 0%, #BEE3F8 100%);
        border-radius: 10px;
        padding: 16px 20px;
        margin: 16px 0;
        border-left: 4px solid #3182CE;
    }
    .insight-box p { margin: 0; color: #2C5282; font-size: 0.95em; }
    
    /* Button */
    .stButton>button {
        background: linear-gradient(135deg, #3182CE 0%, #2B6CB0 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.7rem 1.2rem;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2B6CB0 0%, #2C5282 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.4);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        color: #718096;
        border-radius: 8px 8px 0 0;
        font-weight: 500;
        padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        color: #3182CE;
        border-top: 3px solid #3182CE;
        border-bottom: none;
    }
    
    /* Action Cards */
    .action-card {
        background: linear-gradient(135deg, #FFF5F5 0%, #FED7D7 100%);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border-left: 4px solid #E53E3E;
    }
    .action-card.priority-high { 
        background: linear-gradient(135deg, #FFF5F5 0%, #FED7D7 100%);
        border-left-color: #E53E3E;
    }
    .action-card.priority-medium { 
        background: linear-gradient(135deg, #FFFAF0 0%, #FEEBC8 100%);
        border-left-color: #DD6B20;
    }
    .action-card.priority-low { 
        background: linear-gradient(135deg, #F0FFF4 0%, #C6F6D5 100%);
        border-left-color: #38A169;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. FICHIERS IA - DEFINITIONS & ANALYSEURS
# =============================================================================

AI_FILES = {
    "robots.txt": {
        "icon": "🤖",
        "name": "robots.txt",
        "path": "/robots.txt",
        "description": "Contrôle l'accès des crawlers IA",
        "importance": "Critique",
        "ai_crawlers": ["GPTBot", "ChatGPT-User", "Google-Extended", "Googlebot", "Bingbot", 
                       "anthropic-ai", "ClaudeBot", "PerplexityBot", "CCBot", "Bytespider"]
    },
    "sitemap.xml": {
        "icon": "🗺️",
        "name": "sitemap.xml",
        "path": "/sitemap.xml",
        "description": "Plan du site pour l'indexation",
        "importance": "Haute"
    },
    "llms.txt": {
        "icon": "📄",
        "name": "llms.txt",
        "path": "/llms.txt",
        "description": "Instructions pour les LLMs",
        "importance": "Haute"
    },
    "llm-policy.json": {
        "icon": "📋",
        "name": "llm-policy.json", 
        "path": "/.well-known/llm-policy.json",
        "description": "Politique d'utilisation IA",
        "importance": "Moyenne"
    },
    "ai-plugin.json": {
        "icon": "🔌",
        "name": "ai-plugin.json",
        "path": "/.well-known/ai-plugin.json",
        "description": "Manifeste plugin ChatGPT",
        "importance": "Moyenne"
    },
    "security.txt": {
        "icon": "🔒",
        "name": "security.txt",
        "path": "/.well-known/security.txt",
        "description": "Contact sécurité",
        "importance": "Basse"
    },
    "humans.txt": {
        "icon": "👥",
        "name": "humans.txt",
        "path": "/humans.txt",
        "description": "Crédits équipe",
        "importance": "Basse"
    },
    "json-ld": {
        "icon": "🏷️",
        "name": "JSON-LD Schema.org",
        "path": "embedded",
        "description": "Données structurées",
        "importance": "Critique"
    }
}


def fetch_file(base_url: str, path: str, timeout: int = 10) -> dict:
    """Récupère un fichier et retourne son contenu avec métadonnées."""
    try:
        parsed = urlparse(base_url)
        full_url = f"{parsed.scheme}://{parsed.netloc}{path}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(full_url, headers=headers, timeout=timeout)
        
        return {
            "exists": response.status_code == 200,
            "status_code": response.status_code,
            "content": response.text if response.status_code == 200 else None,
            "url": full_url,
            "content_type": response.headers.get('Content-Type', ''),
            "size": len(response.content) if response.status_code == 200 else 0
        }
    except requests.RequestException as e:
        return {
            "exists": False,
            "status_code": None,
            "content": None,
            "url": f"{parsed.scheme}://{parsed.netloc}{path}" if 'parsed' in dir() else path,
            "error": str(e)
        }


def analyze_robots_txt(content: str) -> dict:
    """Analyse le robots.txt pour les accès IA."""
    if not content:
        return {"status": "missing", "ai_access": {}, "issues": ["Fichier robots.txt manquant"]}
    
    lines = content.strip().split('\n')
    current_agent = None
    rules = {}
    sitemaps = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        
        if line.lower().startswith('user-agent:'):
            current_agent = line.split(':', 1)[1].strip()
            if current_agent not in rules:
                rules[current_agent] = {"allow": [], "disallow": []}
        elif line.lower().startswith('disallow:') and current_agent:
            path = line.split(':', 1)[1].strip()
            rules[current_agent]["disallow"].append(path)
        elif line.lower().startswith('allow:') and current_agent:
            path = line.split(':', 1)[1].strip()
            rules[current_agent]["allow"].append(path)
        elif line.lower().startswith('sitemap:'):
            sitemaps.append(line.split(':', 1)[1].strip())
    
    ai_access = {}
    ai_crawlers = AI_FILES["robots.txt"]["ai_crawlers"]
    
    for crawler in ai_crawlers:
        if crawler in rules:
            disallows = rules[crawler]["disallow"]
            if "/" in disallows or "/*" in disallows:
                ai_access[crawler] = "blocked"
            elif disallows:
                ai_access[crawler] = "partial"
            else:
                ai_access[crawler] = "allowed"
        elif "*" in rules:
            disallows = rules["*"]["disallow"]
            if "/" in disallows or "/*" in disallows:
                ai_access[crawler] = "blocked"
            elif disallows:
                ai_access[crawler] = "partial"
            else:
                ai_access[crawler] = "allowed"
        else:
            ai_access[crawler] = "allowed"
    
    issues = []
    blocked = [k for k, v in ai_access.items() if v == "blocked"]
    if blocked:
        issues.append(f"Crawlers IA bloqués : {', '.join(blocked)}")
    if not sitemaps:
        issues.append("Aucun sitemap déclaré dans robots.txt")
    
    return {
        "status": "present",
        "rules": rules,
        "ai_access": ai_access,
        "sitemaps": sitemaps,
        "issues": issues,
        "blocked_count": len(blocked),
        "allowed_count": len([k for k, v in ai_access.items() if v == "allowed"])
    }


def analyze_sitemap(content: str, url: str) -> dict:
    """Analyse le sitemap.xml."""
    if not content:
        return {"status": "missing", "issues": ["Sitemap manquant"]}
    
    try:
        root = ET.fromstring(content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        urls = []
        if 'sitemapindex' in root.tag.lower():
            sitemaps = root.findall('.//sm:loc', ns) or root.findall('.//loc')
            return {
                "status": "present",
                "type": "index",
                "sitemap_count": len(sitemaps),
                "sitemaps": [s.text for s in sitemaps[:10]],
                "issues": []
            }
        else:
            url_elements = root.findall('.//sm:url', ns) or root.findall('.//url')
            for url_elem in url_elements[:100]:
                loc = url_elem.find('sm:loc', ns) or url_elem.find('loc')
                lastmod = url_elem.find('sm:lastmod', ns) or url_elem.find('lastmod')
                priority = url_elem.find('sm:priority', ns) or url_elem.find('priority')
                changefreq = url_elem.find('sm:changefreq', ns) or url_elem.find('changefreq')
                
                urls.append({
                    "loc": loc.text if loc is not None else None,
                    "lastmod": lastmod.text if lastmod is not None else None,
                    "priority": priority.text if priority is not None else None,
                    "changefreq": changefreq.text if changefreq is not None else None
                })
        
        issues = []
        urls_without_lastmod = sum(1 for u in urls if not u["lastmod"])
        urls_without_priority = sum(1 for u in urls if not u["priority"])
        
        if urls_without_lastmod > len(urls) * 0.5:
            issues.append(f"{urls_without_lastmod}/{len(urls)} URLs sans date de modification")
        if urls_without_priority > len(urls) * 0.8:
            issues.append("Peu d'URLs avec priorité définie")
        
        return {
            "status": "present",
            "type": "urlset",
            "url_count": len(urls),
            "urls_sample": urls[:10],
            "has_lastmod": urls_without_lastmod < len(urls) * 0.5,
            "has_priority": urls_without_priority < len(urls) * 0.8,
            "issues": issues
        }
    except ET.ParseError as e:
        return {"status": "invalid", "issues": [f"XML invalide : {str(e)}"]}


def analyze_llms_txt(content: str) -> dict:
    """Analyse le fichier llms.txt."""
    if not content:
        return {"status": "missing", "issues": ["Fichier llms.txt manquant"]}
    
    lines = content.strip().split('\n')
    sections = {}
    current_section = "intro"
    sections[current_section] = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            current_section = line.lstrip('#').strip().lower()
            sections[current_section] = []
        elif line:
            sections[current_section].append(line)
    
    issues = []
    recommendations = []
    
    key_sections = ["about", "contact", "usage", "restrictions", "data"]
    present_sections = [s for s in key_sections if s in sections]
    
    if len(present_sections) < 2:
        issues.append("Peu de sections structurées détectées")
        recommendations.append("Ajouter des sections : # About, # Usage, # Restrictions")
    
    word_count = sum(len(' '.join(v).split()) for v in sections.values())
    if word_count < 50:
        issues.append("Contenu trop court pour être informatif")
        recommendations.append("Enrichir le contenu avec plus de contexte")
    
    return {
        "status": "present",
        "sections": list(sections.keys()),
        "word_count": word_count,
        "line_count": len(lines),
        "issues": issues,
        "recommendations": recommendations
    }


def analyze_llm_policy(content: str) -> dict:
    """Analyse le fichier llm-policy.json."""
    if not content:
        return {"status": "missing", "issues": ["Fichier llm-policy.json manquant"]}
    
    try:
        data = json.loads(content)
        
        recommended_fields = ["name", "policy_version", "allow_training", "allow_indexing", 
                             "allow_inference", "restrictions", "contact"]
        present_fields = [f for f in recommended_fields if f in data]
        missing_fields = [f for f in recommended_fields if f not in data]
        
        issues = []
        if missing_fields:
            issues.append(f"Champs manquants : {', '.join(missing_fields)}")
        
        return {
            "status": "present",
            "data": data,
            "present_fields": present_fields,
            "missing_fields": missing_fields,
            "allow_training": data.get("allow_training"),
            "allow_indexing": data.get("allow_indexing"),
            "issues": issues
        }
    except json.JSONDecodeError as e:
        return {"status": "invalid", "issues": [f"JSON invalide : {str(e)}"]}


def analyze_ai_plugin(content: str) -> dict:
    """Analyse le fichier ai-plugin.json."""
    if not content:
        return {"status": "missing", "issues": ["Fichier ai-plugin.json manquant"]}
    
    try:
        data = json.loads(content)
        
        required_fields = ["schema_version", "name_for_model", "name_for_human", 
                          "description_for_model", "description_for_human", "api"]
        present = [f for f in required_fields if f in data]
        missing = [f for f in required_fields if f not in data]
        
        return {
            "status": "present",
            "data": data,
            "name": data.get("name_for_human", "N/A"),
            "description": data.get("description_for_human", "")[:200],
            "missing_fields": missing,
            "issues": [f"Champs requis manquants : {', '.join(missing)}"] if missing else []
        }
    except json.JSONDecodeError as e:
        return {"status": "invalid", "issues": [f"JSON invalide : {str(e)}"]}


def analyze_json_ld(url: str) -> dict:
    """Analyse le JSON-LD présent sur une page."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        scripts = soup.find_all('script', type='application/ld+json')
        
        if not scripts:
            return {
                "status": "missing",
                "count": 0,
                "schemas": [],
                "issues": ["Aucun JSON-LD détecté sur la page"]
            }
        
        schemas = []
        issues = []
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        schemas.append({
                            "type": item.get("@type", "Unknown"),
                            "data": item
                        })
                else:
                    schemas.append({
                        "type": data.get("@type", "Unknown"),
                        "data": data
                    })
            except json.JSONDecodeError:
                issues.append("JSON-LD mal formé détecté")
        
        types_found = [s["type"] for s in schemas]
        recommended_types = ["Organization", "WebSite", "WebPage", "BreadcrumbList"]
        missing_types = [t for t in recommended_types if t not in types_found]
        
        if missing_types:
            issues.append(f"Types recommandés manquants : {', '.join(missing_types)}")
        
        return {
            "status": "present",
            "count": len(schemas),
            "schemas": schemas,
            "types": types_found,
            "missing_types": missing_types,
            "issues": issues
        }
    except Exception as e:
        return {
            "status": "error",
            "count": 0,
            "schemas": [],
            "issues": [f"Erreur d'analyse : {str(e)}"]
        }


# =============================================================================
# 3. CRAWL MULTI-PAGES
# =============================================================================

def crawl_links(start_url: str, pattern: str, limit: int, deep_mode: bool) -> list:
    """Crawle les liens d'une page selon un pattern."""
    if not deep_mode:
        return [start_url]
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(start_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        domain = urlparse(start_url).netloc
        links = set([start_url])
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            if pattern and pattern not in href:
                continue
            
            full_url = urljoin(start_url, href)
            parsed = urlparse(full_url)
            
            if parsed.netloc == domain and full_url not in links:
                links.add(full_url)
            
            if len(links) >= limit:
                break
        
        return list(links)[:limit]
    
    except requests.RequestException as e:
        st.warning(f"⚠️ Erreur lors du crawl : {str(e)}")
        return [start_url]


def analyze_page_json_ld(url: str) -> dict:
    """Analyse le JSON-LD d'une page spécifique."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Récupérer titre
        title = soup.title.string if soup.title else "Sans titre"
        
        # Récupérer JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        schemas = []
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    schemas.extend(data)
                else:
                    schemas.append(data)
            except:
                pass
        
        return {
            "url": url,
            "title": title,
            "has_json_ld": len(schemas) > 0,
            "schemas": schemas,
            "types": [s.get("@type", "Unknown") for s in schemas]
        }
    except Exception as e:
        return {
            "url": url,
            "title": "Erreur",
            "has_json_ld": False,
            "schemas": [],
            "types": [],
            "error": str(e)
        }


# =============================================================================
# 4. GÉNÉRATEUR D'OPTIMISATIONS (MISTRAL)
# =============================================================================

def get_optimization_prompt(file_type: str, current_content: str, analysis: dict, context: dict) -> str:
    """Génère le prompt pour Mistral selon le type de fichier."""
    
    domain = urlparse(context.get('url', '')).netloc
    
    prompts = {
        "robots.txt": f"""Tu es un expert en SEO technique et accessibilité IA. Analyse ce robots.txt et propose une version optimisée.

## ROBOTS.TXT ACTUEL
```
{current_content or "Fichier absent"}
```

## ANALYSE
- Crawlers IA bloqués : {analysis.get('blocked_count', 'N/A')}
- Crawlers IA autorisés : {analysis.get('allowed_count', 'N/A')}
- Problèmes : {', '.join(analysis.get('issues', []))}

## MISSION
Génère un robots.txt optimisé qui :
1. Autorise les crawlers IA majeurs (GPTBot, ChatGPT-User, Google-Extended, ClaudeBot, PerplexityBot)
2. Référence le sitemap
3. Protège les zones sensibles (/admin, /api, /private)

Réponds en JSON :
{{
    "analysis_summary": "<résumé en 2 phrases>",
    "score": <1-10>,
    "optimized_content": "<nouveau robots.txt complet>",
    "changes": ["<changement 1>", "<changement 2>"]
}}""",

        "sitemap.xml": f"""Tu es un expert SEO. Analyse ce sitemap et propose des améliorations.

## SITEMAP ACTUEL
- Type : {analysis.get('type', 'N/A')}
- Nombre d'URLs : {analysis.get('url_count', 'N/A')}
- Dates de modif : {'Présentes' if analysis.get('has_lastmod') else 'Absentes'}
- Problèmes : {', '.join(analysis.get('issues', []))}

## MISSION
Propose des améliorations structurelles pour le sitemap.

Réponds en JSON :
{{
    "analysis_summary": "<résumé en 2 phrases>",
    "score": <1-10>,
    "recommendations": ["<reco 1>", "<reco 2>"],
    "example_entry": "<exemple d'entrée sitemap optimisée>"
}}""",

        "llms.txt": f"""Tu es un expert en AI Optimization. Analyse ce llms.txt et propose une version optimisée.

## CONTENU ACTUEL
```
{current_content or "Fichier absent"}
```

## CONTEXTE DU SITE
- URL : {context.get('url', 'N/A')}
- Secteur : {context.get('sector', 'N/A')}

## MISSION
Crée un llms.txt complet et professionnel avec :
1. Section About (présentation claire)
2. Section Usage (ce que les IA peuvent faire)
3. Section Restrictions (limites d'usage)
4. Contact

Réponds en JSON :
{{
    "analysis_summary": "<résumé en 2 phrases>",
    "score": <1-10>,
    "optimized_content": "<nouveau llms.txt complet>",
    "sections_added": ["<section 1>", "<section 2>"]
}}""",

        "llm-policy.json": f"""Tu es un expert en AI Governance. Crée ou optimise ce llm-policy.json.

## CONTENU ACTUEL
```json
{current_content or "Fichier absent"}
```

## CONTEXTE
- URL : {context.get('url', 'N/A')}
- Secteur : {context.get('sector', 'N/A')}

## MISSION
Génère un llm-policy.json complet selon les meilleures pratiques.

Réponds en JSON :
{{
    "analysis_summary": "<résumé>",
    "score": <1-10>,
    "optimized_content": {{
        "name": "{domain}",
        "policy_version": "1.0",
        "allow_training": true,
        "allow_indexing": true,
        "allow_inference": true,
        "restrictions": [],
        "contact": "contact@{domain}",
        "effective_date": "2025-01-01"
    }}
}}""",

        "ai-plugin.json": f"""Tu es un expert en développement de plugins IA. Crée un ai-plugin.json pour ce site.

## CONTEXTE
- URL : {context.get('url', 'N/A')}
- Secteur : {context.get('sector', 'N/A')}
- Domaine : {domain}

## MISSION
Génère un ai-plugin.json complet pour ChatGPT/assistants IA selon le standard OpenAI.
Adapte le contenu au secteur d'activité ({context.get('sector', 'N/A')}).

Réponds en JSON :
{{
    "analysis_summary": "<résumé de ce que fait le plugin>",
    "score": <1-10>,
    "optimized_content": {{
        "schema_version": "v1",
        "name_for_model": "<nom_technique_sans_espaces_ni_accents>",
        "name_for_human": "<Nom Lisible du Site>",
        "description_for_model": "<description technique détaillée pour l'IA expliquant ce que le plugin permet de faire, 100-200 mots, adapté au secteur {context.get('sector', 'N/A')}>",
        "description_for_human": "<description courte et attrayante pour les utilisateurs, 1-2 phrases>",
        "auth": {{
            "type": "none"
        }},
        "api": {{
            "type": "openapi",
            "url": "{context.get('url', '')}/openapi.yaml"
        }},
        "logo_url": "{context.get('url', '')}/logo.png",
        "contact_email": "contact@{domain}",
        "legal_info_url": "{context.get('url', '')}/legal"
    }}
}}""",

        "json-ld": f"""Tu es un expert Schema.org. Analyse les JSON-LD et propose des améliorations.

## JSON-LD DÉTECTÉS
Types : {', '.join(analysis.get('types', []))}
Nombre : {analysis.get('count', 0)}

## PROBLÈMES
{', '.join(analysis.get('issues', []))}

## CONTEXTE
- URL : {context.get('url', 'N/A')}
- Secteur : {context.get('sector', 'N/A')}
- Domaine : {domain}

## MISSION
Propose des JSON-LD optimisés avec Organization, WebSite et BreadcrumbList adaptés au secteur.

Réponds en JSON :
{{
    "analysis_summary": "<résumé>",
    "score": <1-10>,
    "optimized_schemas": [
        {{"@context": "https://schema.org", "@type": "Organization", "name": "...", "url": "{context.get('url', '')}", ...}},
        {{"@context": "https://schema.org", "@type": "WebSite", "name": "...", "url": "{context.get('url', '')}", ...}}
    ],
    "recommendations": ["<reco 1>", "<reco 2>"]
}}"""
    }
    
    return prompts.get(file_type, "Analyse ce fichier et propose des améliorations.")


def get_optimization(file_type: str, content: str, analysis: dict, context: dict, api_key: str) -> dict:
    """Appelle Mistral pour obtenir des optimisations."""
    if not api_key:
        return {"error": "Clé API Mistral manquante. Ajoutez votre clé dans la sidebar pour générer des optimisations."}
    
    try:
        client = Mistral(api_key=api_key)
        prompt = get_optimization_prompt(file_type, content, analysis, context)
        
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# 5. AUDIT COMPLET
# =============================================================================

def run_full_audit(url: str, api_key: str, sector: str) -> dict:
    """Exécute l'audit complet de tous les fichiers IA."""
    results = {
        "url": url,
        "sector": sector,
        "timestamp": datetime.now().isoformat(),
        "files": {}
    }
    
    context = {"url": url, "sector": sector}
    
    # 1. robots.txt
    robots_data = fetch_file(url, "/robots.txt")
    robots_analysis = analyze_robots_txt(robots_data.get("content"))
    results["files"]["robots.txt"] = {
        "raw": robots_data,
        "analysis": robots_analysis,
        "optimization": None
    }
    
    # 2. sitemap.xml
    sitemap_data = fetch_file(url, "/sitemap.xml")
    sitemap_analysis = analyze_sitemap(sitemap_data.get("content"), url)
    results["files"]["sitemap.xml"] = {
        "raw": sitemap_data,
        "analysis": sitemap_analysis,
        "optimization": None
    }
    
    # 3. llms.txt
    llms_data = fetch_file(url, "/llms.txt")
    llms_analysis = analyze_llms_txt(llms_data.get("content"))
    results["files"]["llms.txt"] = {
        "raw": llms_data,
        "analysis": llms_analysis,
        "optimization": None
    }
    
    # 4. llm-policy.json
    policy_data = fetch_file(url, "/.well-known/llm-policy.json")
    policy_analysis = analyze_llm_policy(policy_data.get("content"))
    results["files"]["llm-policy.json"] = {
        "raw": policy_data,
        "analysis": policy_analysis,
        "optimization": None
    }
    
    # 5. ai-plugin.json
    plugin_data = fetch_file(url, "/.well-known/ai-plugin.json")
    plugin_analysis = analyze_ai_plugin(plugin_data.get("content"))
    results["files"]["ai-plugin.json"] = {
        "raw": plugin_data,
        "analysis": plugin_analysis,
        "optimization": None
    }
    
    # 6. security.txt
    security_data = fetch_file(url, "/.well-known/security.txt")
    results["files"]["security.txt"] = {
        "raw": security_data,
        "analysis": {"status": "present" if security_data.get("exists") else "missing"},
        "optimization": None
    }
    
    # 7. humans.txt
    humans_data = fetch_file(url, "/humans.txt")
    results["files"]["humans.txt"] = {
        "raw": humans_data,
        "analysis": {"status": "present" if humans_data.get("exists") else "missing"},
        "optimization": None
    }
    
    # 8. JSON-LD
    jsonld_analysis = analyze_json_ld(url)
    results["files"]["json-ld"] = {
        "raw": {"exists": jsonld_analysis.get("count", 0) > 0},
        "analysis": jsonld_analysis,
        "optimization": None
    }
    
    # Calculer le score global
    score = calculate_global_score(results)
    results["global_score"] = score
    
    return results


def calculate_global_score(results: dict) -> dict:
    """Calcule le score global de l'audit."""
    weights = {
        "robots.txt": 20,
        "sitemap.xml": 15,
        "llms.txt": 20,
        "llm-policy.json": 15,
        "ai-plugin.json": 10,
        "json-ld": 20
    }
    
    scores = {}
    total_score = 0
    total_weight = 0
    
    for file_key, weight in weights.items():
        file_data = results.get("files", {}).get(file_key, {})
        analysis = file_data.get("analysis", {})
        status = analysis.get("status", "missing")
        
        if status == "present":
            issues = len(analysis.get("issues", []))
            file_score = max(0, 100 - (issues * 15))
        elif status == "missing":
            file_score = 0
        else:
            file_score = 30
        
        scores[file_key] = file_score
        total_score += file_score * weight
        total_weight += weight
    
    overall = round(total_score / total_weight) if total_weight > 0 else 0
    
    return {
        "overall": overall,
        "by_file": scores,
        "grade": get_grade(overall),
        "files_present": sum(1 for s in scores.values() if s > 0),
        "files_optimized": sum(1 for s in scores.values() if s >= 70),
        "files_total": len(weights)
    }


def get_grade(score: float) -> str:
    """Convertit un score en note lettre."""
    if score >= 90: return "A"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "F"


# =============================================================================
# 6. INTERFACE STREAMLIT
# =============================================================================

# --- SESSION STATE ---
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None
if "optimizations" not in st.session_state:
    st.session_state.optimizations = {}
if "pages_analysis" not in st.session_state:
    st.session_state.pages_analysis = []

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🔍 Seorux AIO v3")
    st.caption("Audit complet d'accessibilité IA")
    st.markdown("---")
    
    api_key = st.text_input(
        "🔑 Clé API Mistral",
        type="password",
        help="Pour les recommandations d'optimisation"
    )
    
    st.markdown("### ⚙️ Configuration")
    sector = st.selectbox(
        "Secteur d'activité",
        ["E-commerce", "RH / Recrutement", "Immobilier", "SaaS / Tech", "Média / Contenu", "Autre"]
    )
    
    url_target = st.text_input(
        "🔗 URL du site à auditer",
        value="https://www.exemple.com",
        help="URL de la page d'accueil du site"
    )
    
    # Options de scan multi-pages
    with st.expander("🔧 Options avancées", expanded=False):
        deep_mode = st.checkbox(
            "📑 Scanner plusieurs pages",
            value=False,
            help="Crawle les liens internes pour analyser les JSON-LD de chaque page"
        )
        pattern = st.text_input(
            "Filtre URL (contient)",
            value="",
            help="Ne scanne que les URLs contenant ce texte (ex: /blog/, /product/)"
        )
        limit = st.slider(
            "Nombre max de pages",
            min_value=1,
            max_value=20,
            value=5
        )
    
    st.markdown("---")
    start_audit = st.button("🚀 LANCER L'AUDIT", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.caption("v3.0 • Audit IA Complet")

# --- LANCEMENT AUDIT ---
if start_audit:
    if not url_target or not url_target.startswith("http"):
        st.error("❌ Veuillez entrer une URL valide (commençant par http:// ou https://)")
    else:
        with st.status("🔍 Audit en cours...", expanded=True) as status:
            st.write("📡 Analyse des fichiers IA...")
            
            results = run_full_audit(url_target, api_key, sector)
            st.session_state.audit_results = results
            st.session_state.optimizations = {}
            
            files_found = sum(1 for f in results["files"].values() 
                            if f.get("raw", {}).get("exists") or 
                            f.get("analysis", {}).get("status") == "present")
            
            st.write(f"✅ {files_found}/{len(results['files'])} fichiers détectés")
            
            # Scan multi-pages si activé
            if deep_mode:
                st.write("🔗 Crawl des pages internes...")
                pages = crawl_links(url_target, pattern, limit, deep_mode)
                st.write(f"📄 {len(pages)} pages trouvées")
                
                pages_analysis = []
                for i, page_url in enumerate(pages):
                    st.write(f"  → Analyse : {page_url[:50]}...")
                    page_data = analyze_page_json_ld(page_url)
                    pages_analysis.append(page_data)
                
                st.session_state.pages_analysis = pages_analysis
            else:
                st.session_state.pages_analysis = []
            
            st.write(f"📊 Score global : {results['global_score']['overall']}/100")
            
            status.update(label="✅ Audit terminé !", state="complete", expanded=False)

# --- AFFICHAGE RÉSULTATS ---
if st.session_state.audit_results:
    results = st.session_state.audit_results
    score = results["global_score"]
    
    st.markdown(f"## 📊 Audit IA : {urlparse(results['url']).netloc}")
    
    # === ONGLETS ===
    tab_names = [
        "📋 Résumé Global",
        "🤖 robots.txt",
        "🗺️ sitemap.xml", 
        "📄 llms.txt",
        "📋 llm-policy.json",
        "🔌 ai-plugin.json",
        "🏷️ JSON-LD",
        "📁 Autres"
    ]
    
    # Ajouter l'onglet pages si scan multi-pages
    if st.session_state.pages_analysis:
        tab_names.append("📑 Pages scannées")
    
    tabs = st.tabs(tab_names)
    
    # --- TAB 0: RÉSUMÉ GLOBAL (DESIGN AVEC COMPOSANTS STREAMLIT) ---
    with tabs[0]:
        # === SCORE CENTRAL ===
        grade_colors = {"A": "🟢", "B": "🟢", "C": "🟠", "D": "🟠", "F": "🔴"}
        grade_emoji = grade_colors.get(score["grade"], "🔴")
        
        # Score principal avec colonnes Streamlit
        col_score, col_stats = st.columns([1, 2])
        
        with col_score:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 20px; padding: 30px; text-align: center; color: white;">
                <div style="font-size: 4em; font-weight: 800; line-height: 1;">{score['grade']}</div>
                <div style="font-size: 1.5em; opacity: 0.9;">{score['overall']}/100</div>
                <div style="font-size: 0.9em; opacity: 0.7; margin-top: 10px;">Score d'Accessibilité IA</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stats:
            st.markdown("#### 📈 Résumé rapide")
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                st.metric("Fichiers présents", f"{score['files_present']}/{score['files_total']}")
            with stat_col2:
                st.metric("Fichiers optimisés", f"{score['files_optimized']}/{score['files_total']}")
            with stat_col3:
                priority_label = "Critique" if score["overall"] < 40 else ("Moyen" if score["overall"] < 70 else "Bon")
                st.metric("Niveau", f"{grade_emoji} {priority_label}")
            
            # Message selon le score
            if score["overall"] >= 70:
                st.success("✅ Votre site est bien configuré pour les IA !")
            elif score["overall"] >= 40:
                st.warning("⚠️ Des améliorations sont recommandées pour optimiser l'accessibilité IA.")
            else:
                st.error("🔴 Actions urgentes requises pour améliorer la visibilité IA.")
        
        st.markdown("---")
        
        # === CARTOGRAPHIE DES FICHIERS (Grille avec colonnes Streamlit) ===
        st.markdown("### 🗺️ Cartographie des fichiers IA")
        
        file_order = ["robots.txt", "sitemap.xml", "llms.txt", "llm-policy.json", "ai-plugin.json", "json-ld"]
        
        # Première ligne : 3 fichiers
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        # Deuxième ligne : 3 fichiers
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        
        all_cols = [row1_col1, row1_col2, row1_col3, row2_col1, row2_col2, row2_col3]
        
        for i, file_key in enumerate(file_order):
            file_info = AI_FILES.get(file_key, {})
            file_data = results["files"].get(file_key, {})
            analysis = file_data.get("analysis", {})
            status = analysis.get("status", "missing")
            file_score = score["by_file"].get(file_key, 0)
            
            # Déterminer le style
            if status == "present" and file_score >= 70:
                bg_color = "#F0FFF4"
                border_color = "#38A169"
                status_icon = "✅"
                status_text = "OK"
            elif status == "present":
                bg_color = "#FFFAF0"
                border_color = "#DD6B20"
                status_icon = "⚠️"
                status_text = "À optimiser"
            else:
                bg_color = "#FFF5F5"
                border_color = "#E53E3E"
                status_icon = "❌"
                status_text = "Manquant"
            
            with all_cols[i]:
                st.markdown(f"""
                <div style="background: {bg_color}; border: 2px solid {border_color}; 
                            border-radius: 12px; padding: 20px; text-align: center; 
                            margin-bottom: 10px; min-height: 140px;">
                    <div style="font-size: 2em; margin-bottom: 8px;">{file_info.get('icon', '📄')}</div>
                    <div style="font-weight: 700; color: #2D3748; font-size: 0.9em;">{file_info.get('name', file_key)}</div>
                    <div style="margin-top: 8px;">
                        <span style="background: {border_color}; color: white; padding: 4px 12px; 
                                     border-radius: 20px; font-size: 0.75em; font-weight: 600;">
                            {status_icon} {status_text} • {file_score}/100
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # === CHAÎNE D'ACCESSIBILITÉ IA (avec colonnes) ===
        st.markdown("### 🔄 Chaîne d'accessibilité IA")
        st.markdown("*Comment les IA accèdent et comprennent votre site :*")
        
        flow_items = [
            {"icon": "🤖", "name": "1. Accès", "file": "robots.txt", "desc": "robots.txt autorise les crawlers"},
            {"icon": "🗺️", "name": "2. Découverte", "file": "sitemap.xml", "desc": "sitemap.xml liste les pages"},
            {"icon": "📄", "name": "3. Instructions", "file": "llms.txt", "desc": "llms.txt guide les LLMs"},
            {"icon": "🏷️", "name": "4. Compréhension", "file": "json-ld", "desc": "JSON-LD structure les données"},
        ]
        
        flow_cols = st.columns(4)
        
        for i, item in enumerate(flow_items):
            file_score = score["by_file"].get(item["file"], 0)
            if file_score >= 70:
                circle_style = "background: #C6F6D5; border-color: #38A169; color: #22543D;"
            elif file_score > 0:
                circle_style = "background: #FEEBC8; border-color: #DD6B20; color: #744210;"
            else:
                circle_style = "background: #FED7D7; border-color: #E53E3E; color: #822727;"
            
            with flow_cols[i]:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="width: 60px; height: 60px; {circle_style} border: 3px solid; 
                                border-radius: 50%; display: flex; align-items: center; 
                                justify-content: center; margin: 0 auto 10px; font-size: 1.5em;">
                        {item['icon']}
                    </div>
                    <div style="font-weight: 700; color: #2D3748; font-size: 0.9em;">{item['name']}</div>
                    <div style="font-size: 0.75em; color: #718096; margin-top: 4px;">{item['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # === ACTIONS PRIORITAIRES ===
        st.markdown("### 🎯 Actions Prioritaires")
        
        priorities = []
        
        for file_key in ["robots.txt", "json-ld", "llms.txt", "sitemap.xml", "llm-policy.json", "ai-plugin.json"]:
            file_data = results["files"].get(file_key, {})
            analysis = file_data.get("analysis", {})
            file_score = score["by_file"].get(file_key, 0)
            
            if analysis.get("status") == "missing":
                priorities.append({
                    "text": f"Créer le fichier **{file_key}**",
                    "priority": "high" if file_key in ["robots.txt", "json-ld", "llms.txt"] else "medium",
                    "file": file_key,
                    "impact": "+20 pts" if file_key in ["robots.txt", "json-ld", "llms.txt"] else "+15 pts"
                })
            elif file_score < 70 and analysis.get("issues"):
                priorities.append({
                    "text": f"Optimiser **{file_key}** : {analysis['issues'][0]}",
                    "priority": "medium",
                    "file": file_key,
                    "impact": "+10 pts"
                })
        
        if priorities:
            for p in priorities[:5]:
                if p['priority'] == 'high':
                    st.error(f"🔴 **{p['text']}** — Impact estimé : {p['impact']}")
                else:
                    st.warning(f"🟠 **{p['text']}** — Impact estimé : {p['impact']}")
        else:
            st.success("✅ Aucune action prioritaire ! Votre site est bien configuré pour les IA.")
        
        st.markdown("---")
        
        # === DÉTAIL DES SCORES (Barres de progression) ===
        st.markdown("### 📊 Détail des scores par fichier")
        
        for file_key in ["robots.txt", "sitemap.xml", "llms.txt", "llm-policy.json", "ai-plugin.json", "json-ld"]:
            file_info = AI_FILES.get(file_key, {})
            file_score = score["by_file"].get(file_key, 0)
            
            col_label, col_bar = st.columns([1, 3])
            
            with col_label:
                st.markdown(f"**{file_info.get('icon', '📄')} {file_info.get('name', file_key)}**")
            
            with col_bar:
                # Utiliser la progress bar native de Streamlit
                st.progress(file_score / 100, text=f"{file_score}/100")
    
    # --- TAB 1: ROBOTS.TXT ---
    with tabs[1]:
        file_data = results["files"].get("robots.txt", {})
        analysis = file_data.get("analysis", {})
        raw = file_data.get("raw", {})
        
        st.markdown("### 🤖 Analyse du robots.txt")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if analysis.get("status") == "present":
                st.success(f"✅ Fichier présent : {raw.get('url', '')}")
                
                st.markdown("#### Accès des crawlers IA")
                ai_access = analysis.get("ai_access", {})
                
                cols = st.columns(2)
                for i, (crawler, access) in enumerate(ai_access.items()):
                    with cols[i % 2]:
                        if access == "allowed":
                            st.markdown(f"✅ **{crawler}**")
                        elif access == "blocked":
                            st.markdown(f"🔴 **{crawler}** (bloqué)")
                        else:
                            st.markdown(f"🟠 **{crawler}** (partiel)")
                
                sitemaps = analysis.get("sitemaps", [])
                if sitemaps:
                    st.markdown("#### Sitemaps déclarés")
                    for sm in sitemaps:
                        st.code(sm)
            else:
                st.error("❌ Fichier robots.txt manquant")
        
        with col2:
            st.markdown("#### Contenu actuel")
            content = raw.get("content", "")
            if content:
                st.code(content, language="text")
            else:
                st.info("Aucun contenu")
        
        st.markdown("---")
        st.markdown("#### 🔧 Optimisation")
        
        if st.button("Générer une version optimisée", key="opt_robots"):
            with st.spinner("Génération en cours..."):
                opt = get_optimization("robots.txt", raw.get("content"), analysis, 
                                      {"url": results["url"], "sector": results["sector"]}, api_key)
                st.session_state.optimizations["robots.txt"] = opt
        
        if "robots.txt" in st.session_state.optimizations:
            opt = st.session_state.optimizations["robots.txt"]
            if "error" not in opt:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="code-header before">❌ AVANT</div>', unsafe_allow_html=True)
                    st.code(raw.get("content", "Fichier absent"), language="text")
                with col2:
                    st.markdown('<div class="code-header after">✅ APRÈS</div>', unsafe_allow_html=True)
                    st.code(opt.get("optimized_content", ""), language="text")
                
                st.download_button(
                    "📥 Télécharger robots.txt optimisé",
                    opt.get("optimized_content", ""),
                    file_name="robots.txt",
                    mime="text/plain"
                )
            else:
                st.error(f"Erreur : {opt.get('error')}")
    
    # --- TAB 2: SITEMAP.XML ---
    with tabs[2]:
        file_data = results["files"].get("sitemap.xml", {})
        analysis = file_data.get("analysis", {})
        raw = file_data.get("raw", {})
        
        st.markdown("### 🗺️ Analyse du sitemap.xml")
        
        if analysis.get("status") == "present":
            st.success(f"✅ Sitemap présent : {raw.get('url', '')}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Type", analysis.get("type", "N/A"))
            with col2:
                st.metric("URLs", analysis.get("url_count", analysis.get("sitemap_count", 0)))
            with col3:
                st.metric("Dates de modif", "✅" if analysis.get("has_lastmod") else "❌")
            
            issues = analysis.get("issues", [])
            if issues:
                st.warning("⚠️ Problèmes détectés")
                for issue in issues:
                    st.markdown(f"- {issue}")
            
            st.markdown("#### Aperçu des URLs")
            urls_sample = analysis.get("urls_sample", [])
            if urls_sample:
                df = pd.DataFrame(urls_sample)
                st.dataframe(df, use_container_width=True)
        else:
            st.error("❌ Sitemap manquant ou invalide")
            st.info("💡 Un sitemap aide les IA à découvrir vos pages importantes.")
    
    # --- TAB 3: LLMS.TXT ---
    with tabs[3]:
        file_data = results["files"].get("llms.txt", {})
        analysis = file_data.get("analysis", {})
        raw = file_data.get("raw", {})
        
        st.markdown("### 📄 Analyse du llms.txt")
        
        st.markdown("""
        <div class="insight-box">
            <p>Le fichier <strong>llms.txt</strong> permet de donner des instructions directes aux LLMs sur comment utiliser le contenu de votre site.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if analysis.get("status") == "present":
            st.success(f"✅ Fichier présent")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Mots", analysis.get("word_count", 0))
            with col2:
                st.metric("Sections", len(analysis.get("sections", [])))
            
            st.markdown("#### Contenu actuel")
            st.code(raw.get("content", ""), language="markdown")
        else:
            st.error("❌ Fichier llms.txt manquant")
        
        st.markdown("---")
        if st.button("Générer un llms.txt", key="opt_llms"):
            with st.spinner("Génération en cours..."):
                opt = get_optimization("llms.txt", raw.get("content"), analysis,
                                      {"url": results["url"], "sector": results["sector"]}, api_key)
                st.session_state.optimizations["llms.txt"] = opt
        
        if "llms.txt" in st.session_state.optimizations:
            opt = st.session_state.optimizations["llms.txt"]
            if "error" not in opt:
                st.markdown("#### Version optimisée")
                st.code(opt.get("optimized_content", ""), language="markdown")
                st.download_button(
                    "📥 Télécharger llms.txt",
                    opt.get("optimized_content", ""),
                    file_name="llms.txt",
                    mime="text/plain"
                )
            else:
                st.error(f"Erreur : {opt.get('error')}")
    
    # --- TAB 4: LLM-POLICY.JSON ---
    with tabs[4]:
        file_data = results["files"].get("llm-policy.json", {})
        analysis = file_data.get("analysis", {})
        raw = file_data.get("raw", {})
        
        st.markdown("### 📋 Analyse du llm-policy.json")
        
        st.markdown("""
        <div class="insight-box">
            <p>Le fichier <strong>llm-policy.json</strong> définit votre politique d'utilisation par les IA (entraînement, indexation, inférence).</p>
        </div>
        """, unsafe_allow_html=True)
        
        if analysis.get("status") == "present":
            st.success("✅ Politique LLM définie")
            
            data = analysis.get("data", {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                allow_training = data.get("allow_training")
                st.metric("Entraînement", "✅ Oui" if allow_training else ("❌ Non" if allow_training is False else "❓"))
            with col2:
                allow_indexing = data.get("allow_indexing")
                st.metric("Indexation", "✅ Oui" if allow_indexing else ("❌ Non" if allow_indexing is False else "❓"))
            with col3:
                st.metric("Champs présents", f"{len(analysis.get('present_fields', []))}/7")
            
            st.markdown("#### Contenu")
            st.json(data)
            
            missing = analysis.get("missing_fields", [])
            if missing:
                st.warning(f"⚠️ Champs recommandés manquants : {', '.join(missing)}")
        else:
            st.error("❌ Fichier llm-policy.json manquant")
        
        st.markdown("---")
        if st.button("Générer un llm-policy.json", key="opt_policy"):
            with st.spinner("Génération en cours..."):
                opt = get_optimization("llm-policy.json", raw.get("content"), analysis,
                                      {"url": results["url"], "sector": results["sector"]}, api_key)
                st.session_state.optimizations["llm-policy.json"] = opt
        
        if "llm-policy.json" in st.session_state.optimizations:
            opt = st.session_state.optimizations["llm-policy.json"]
            if "error" not in opt:
                st.markdown("#### Version optimisée")
                optimized = opt.get("optimized_content", {})
                st.json(optimized)
                st.download_button(
                    "📥 Télécharger llm-policy.json",
                    json.dumps(optimized, indent=2),
                    file_name="llm-policy.json",
                    mime="application/json"
                )
            else:
                st.error(f"Erreur : {opt.get('error')}")
    
    # --- TAB 5: AI-PLUGIN.JSON ---
    with tabs[5]:
        file_data = results["files"].get("ai-plugin.json", {})
        analysis = file_data.get("analysis", {})
        raw = file_data.get("raw", {})
        
        st.markdown("### 🔌 Analyse du ai-plugin.json")
        
        st.markdown("""
        <div class="insight-box">
            <p>Le fichier <strong>ai-plugin.json</strong> est le manifeste pour les plugins ChatGPT et autres assistants IA. Il permet à votre site d'être intégré comme plugin.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if analysis.get("status") == "present":
            st.success("✅ Plugin IA configuré")
            st.markdown(f"**Nom** : {analysis.get('name', 'N/A')}")
            st.markdown(f"**Description** : {analysis.get('description', 'N/A')}")
            
            st.markdown("#### Contenu actuel")
            st.json(analysis.get("data", {}))
            
            missing = analysis.get("missing_fields", [])
            if missing:
                st.warning(f"⚠️ Champs requis manquants : {', '.join(missing)}")
        else:
            st.warning("ℹ️ Fichier ai-plugin.json non présent")
            st.markdown("""
            Ce fichier est optionnel mais recommandé si vous souhaitez :
            - Créer un plugin pour ChatGPT
            - Permettre aux assistants IA d'interagir avec votre site
            - Exposer une API aux LLMs
            """)
        
        st.markdown("---")
        st.markdown("#### 🔧 Générer un ai-plugin.json")
        
        if st.button("🔌 Générer un ai-plugin.json", key="opt_plugin"):
            with st.spinner("Génération en cours..."):
                opt = get_optimization("ai-plugin.json", raw.get("content"), analysis,
                                      {"url": results["url"], "sector": results["sector"]}, api_key)
                st.session_state.optimizations["ai-plugin.json"] = opt
        
        if "ai-plugin.json" in st.session_state.optimizations:
            opt = st.session_state.optimizations["ai-plugin.json"]
            if "error" not in opt:
                st.markdown("#### Version générée")
                st.markdown(f"*{opt.get('analysis_summary', '')}*")
                
                optimized = opt.get("optimized_content", {})
                st.json(optimized)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📥 Télécharger ai-plugin.json",
                        json.dumps(optimized, indent=2),
                        file_name="ai-plugin.json",
                        mime="application/json"
                    )
                with col2:
                    st.info("📍 Placer dans : `/.well-known/ai-plugin.json`")
            else:
                st.error(f"Erreur : {opt.get('error')}")
    
    # --- TAB 6: JSON-LD ---
    with tabs[6]:
        file_data = results["files"].get("json-ld", {})
        analysis = file_data.get("analysis", {})
        
        st.markdown("### 🏷️ Analyse des JSON-LD (Schema.org)")
        
        if analysis.get("status") == "present":
            st.success(f"✅ {analysis.get('count', 0)} schema(s) détecté(s)")
            
            st.markdown(f"**Types trouvés** : {', '.join(analysis.get('types', []))}")
            
            missing_types = analysis.get("missing_types", [])
            if missing_types:
                st.warning(f"⚠️ Types recommandés manquants : {', '.join(missing_types)}")
            
            st.markdown("#### Schemas détectés")
            for i, schema in enumerate(analysis.get("schemas", [])):
                with st.expander(f"Schema {i+1} : {schema.get('type', 'Unknown')}"):
                    st.json(schema.get("data", {}))
        else:
            st.error("❌ Aucun JSON-LD détecté sur la page d'accueil")
        
        st.markdown("---")
        if st.button("Générer des JSON-LD optimisés", key="opt_jsonld"):
            with st.spinner("Génération en cours..."):
                opt = get_optimization("json-ld", None, analysis,
                                      {"url": results["url"], "sector": results["sector"]}, api_key)
                st.session_state.optimizations["json-ld"] = opt
        
        if "json-ld" in st.session_state.optimizations:
            opt = st.session_state.optimizations["json-ld"]
            if "error" not in opt:
                st.markdown("#### Schemas optimisés")
                schemas = opt.get("optimized_schemas", [])
                for i, schema in enumerate(schemas):
                    st.markdown(f"**Schema {i+1}** : {schema.get('@type', 'Unknown')}")
                    code = json.dumps(schema, indent=2, ensure_ascii=False)
                    st.code(code, language="json")
                    st.download_button(
                        f"📥 Télécharger schema {i+1}",
                        code,
                        file_name=f"schema_{schema.get('@type', 'unknown').lower()}.json",
                        mime="application/json",
                        key=f"dl_schema_{i}"
                    )
            else:
                st.error(f"Erreur : {opt.get('error')}")
    
    # --- TAB 7: AUTRES ---
    with tabs[7]:
        st.markdown("### 📁 Autres fichiers")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔒 security.txt")
            security = results["files"].get("security.txt", {})
            if security.get("raw", {}).get("exists"):
                st.success("✅ Présent")
                st.code(security.get("raw", {}).get("content", "")[:500])
            else:
                st.info("ℹ️ Non présent (optionnel mais recommandé)")
                st.markdown("Créez un fichier `/.well-known/security.txt` avec vos contacts de sécurité.")
        
        with col2:
            st.markdown("#### 👥 humans.txt")
            humans = results["files"].get("humans.txt", {})
            if humans.get("raw", {}).get("exists"):
                st.success("✅ Présent")
                st.code(humans.get("raw", {}).get("content", "")[:500])
            else:
                st.info("ℹ️ Non présent (optionnel)")
                st.markdown("Créez un fichier `/humans.txt` pour créditer votre équipe.")
    
    # --- TAB 8: PAGES SCANNÉES (si activé) ---
    if st.session_state.pages_analysis and len(tabs) > 8:
        with tabs[8]:
            st.markdown("### 📑 Analyse JSON-LD par page")
            
            pages = st.session_state.pages_analysis
            
            # Résumé
            pages_with_jsonld = sum(1 for p in pages if p.get("has_json_ld"))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pages scannées", len(pages))
            with col2:
                st.metric("Avec JSON-LD", pages_with_jsonld)
            with col3:
                st.metric("Sans JSON-LD", len(pages) - pages_with_jsonld)
            
            st.markdown("---")
            
            # Tableau des pages
            for page in pages:
                status_icon = "✅" if page.get("has_json_ld") else "❌"
                types = ", ".join(page.get("types", [])) if page.get("types") else "Aucun"
                
                with st.expander(f"{status_icon} {page.get('title', 'Sans titre')[:50]}"):
                    st.markdown(f"**URL** : {page.get('url')}")
                    st.markdown(f"**Types JSON-LD** : {types}")
                    
                    if page.get("schemas"):
                        for i, schema in enumerate(page.get("schemas", [])):
                            st.json(schema)
                    else:
                        st.warning("Aucun JSON-LD détecté sur cette page")

else:
    # === ÉTAT INITIAL ===
    st.markdown("## 🔍 Bienvenue sur Seorux AIO v3")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Audit complet d'accessibilité IA
        
        Seorux AIO analyse **tous les fichiers** que les IA génératives utilisent pour comprendre votre site :
        
        | Fichier | Rôle | Importance |
        |---------|------|------------|
        | 🤖 **robots.txt** | Contrôle l'accès des crawlers IA | Critique |
        | 🗺️ **sitemap.xml** | Plan du site pour l'indexation | Haute |
        | 📄 **llms.txt** | Instructions pour les LLMs | Haute |
        | 📋 **llm-policy.json** | Politique d'usage IA | Moyenne |
        | 🔌 **ai-plugin.json** | Manifeste plugin ChatGPT | Moyenne |
        | 🏷️ **JSON-LD** | Données structurées Schema.org | Critique |
        
        **🚀 Pour commencer :**
        1. Entrez votre clé API Mistral (recommandé pour les optimisations)
        2. Entrez l'URL de votre site
        3. Activez le scan multi-pages si besoin
        4. Cliquez sur "Lancer l'audit"
        """)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; padding: 40px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 3.5em; color: white;">AIO</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1em;">AI Optimization</p>
            <p style="margin: 5px 0 0 0; opacity: 0.7; font-size: 0.9em;">Version 3.0</p>
        </div>
        """, unsafe_allow_html=True)