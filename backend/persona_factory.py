import json
import uuid
import logging
from typing import List, Dict, Any
from backend.config import settings
from backend.models import PersonaSchema


logger = logging.getLogger("popusim.persona_factory")

def get_fallback_personas(url: str, title: str, num_personas: int) -> List[Dict[str, Any]]:
    """
    Generates tailored mock personas when Anthropic API is not configured or fails.
    Analyzes the URL and title to customize goals.
    """
    domain = url.split("//")[-1].split("/")[0]
    site_type = "SaaS Platform"
    
    if any(k in url.lower() or k in title.lower() for k in ["shop", "store", "buy", "cart", "product", "checkout"]):
        site_type = "E-Commerce Store"
    elif any(k in url.lower() or k in title.lower() for k in ["blog", "news", "read", "article"]):
        site_type = "Content/Blog Site"
    elif any(k in url.lower() or k in title.lower() for k in ["doc", "help", "guide", "learn", "api"]):
        site_type = "Documentation Portal"

    # Define base archetypes
    archetypes = [
        {
            "name": "Sarah Jenkins",
            "archetype": "Impatient Scanner",
            "traits": {"impatience": 0.9, "tech_savviness": 0.7, "price_sensitivity": 0.4, "support_reliance": 0.1},
            "goals_map": {
                "E-Commerce Store": ["Quickly find a popular item, add it to the cart, and proceed to checkout.", "Verify shipping options."],
                "Content/Blog Site": ["Find the latest article, read the first few paragraphs, and look for an email newsletter sign-up."],
                "Documentation Portal": ["Search for a specific API endpoint or setup guide, copy a code block, and leave."],
                "SaaS Platform": ["Find the feature list, check for a 'Sign Up Free' or 'Get Started' button, and register within 1 minute."]
            }
        },
        {
            "name": "David Miller",
            "archetype": "Price-Sensitive Skeptic",
            "traits": {"impatience": 0.5, "tech_savviness": 0.6, "price_sensitivity": 0.95, "support_reliance": 0.3},
            "goals_map": {
                "E-Commerce Store": ["Find the pricing or sales section, look for discount codes, and compare items before adding to cart."],
                "Content/Blog Site": ["Look for pricing info, subscription options, or check if there is a paywall barrier."],
                "Documentation Portal": ["Check if the API usage is free, search for pricing limits or tier restrictions."],
                "SaaS Platform": ["Navigate directly to the pricing page, compare plans, look for hidden charges or free tiers, and evaluate cost."]
            }
        },
        {
            "name": "Arthur Pendelton",
            "archetype": "Confused Novice",
            "traits": {"impatience": 0.4, "tech_savviness": 0.2, "price_sensitivity": 0.5, "support_reliance": 0.9},
            "goals_map": {
                "E-Commerce Store": ["Browse the catalog slowly, look for contact details or live chat, and try to purchase a gift card."],
                "Content/Blog Site": ["Navigate between topics, try to adjust text size or search for basic information."],
                "Documentation Portal": ["Look for 'Getting Started' or 'FAQs', look for a contact support link because technical docs are confusing."],
                "SaaS Platform": ["Look for a customer support, FAQ, or contact page, find a product demo video, and try to sign up."]
            }
        },
        {
            "name": "Alex Riviera",
            "archetype": "Tech-Savvy Power User",
            "traits": {"impatience": 0.3, "tech_savviness": 0.95, "price_sensitivity": 0.3, "support_reliance": 0.1},
            "goals_map": {
                "E-Commerce Store": ["Examine technical specifications of a product, check security features, look for API integration logs."],
                "Content/Blog Site": ["Search the articles using advanced keywords, check RSS feed availability, or inspect page layout."],
                "Documentation Portal": ["Navigate deep into advanced configurations, check code snippet languages, look for git repository links."],
                "SaaS Platform": ["Look for developer API docs, third-party integrations, advanced settings, and create a developer account."]
            }
        },
        {
            "name": "Emily Watson",
            "archetype": "Feature Hunter",
            "traits": {"impatience": 0.6, "tech_savviness": 0.75, "price_sensitivity": 0.6, "support_reliance": 0.2},
            "goals_map": {
                "E-Commerce Store": ["Look for product reviews, customer ratings, compare product features and return policy details."],
                "Content/Blog Site": ["Find recommended reading list, share an article on social media, search for specialized tags."],
                "Documentation Portal": ["Compare different integration libraries, search for guides on specific advanced features."],
                "SaaS Platform": ["Search for product tours, comparison sheets against competitors, check list of integrations, and click sign up."]
            }
        }
    ]
    
    selected_personas = archetypes[:num_personas]
    result_list = []
    
    for i, p in enumerate(selected_personas):
        goals = p["goals_map"].get(site_type, p["goals_map"]["SaaS Platform"])
        result_list.append({
            "id": f"pers_{uuid.uuid4().hex[:8]}",
            "name": p["name"],
            "archetype": p["archetype"],
            "goals": goals,
            "impatience": p["traits"]["impatience"],
            "tech_savviness": p["traits"]["tech_savviness"],
            "price_sensitivity": p["traits"]["price_sensitivity"],
            "support_reliance": p["traits"]["support_reliance"],
            "status": "pending"
        })
        
    return result_list

async def generate_personas(simulation_id: str, url: str, site_data: dict, num_personas: int) -> List[Dict[str, Any]]:
    """
    Generates a set of personas for the simulation.
    Calls Anthropic if key is set, otherwise generates fallback personas.
    """
    title = site_data.get("title", "Target Website")
    description = site_data.get("meta_description", "")
    headings = ", ".join(site_data.get("headings", [])[:5])
    
    if not settings.GEMINI_API_KEY:
        logger.info("No GEMINI_API_KEY found. Generating mock personas.")
        raw_personas = get_fallback_personas(url, title, num_personas)
    else:
        logger.info("Generating personas using Google Gemini.")
        prompt = f"""
        You are a UX research scientist. Based on the website details below, create {num_personas} diverse, realistic user personas that represent different target segments (e.g. tech comfort, price sensitivity, impatience, goals) that would visit this site.

        Website URL: {url}
        Website Title: {title}
        Description: {description}
        Key Headings: {headings}

        Each persona MUST have:
        1. A realistic Name (e.g. John Doe)
        2. Archetype (e.g. Skeptical Buyer, Confused Novice, Impatient Browser, Feature Hunter)
        3. 2-3 specific navigation goals on this website (e.g. 'find the pricing plans and see if there is a free trial', 'register for an account and check the feature list')
        4. Behavioral traits (floats between 0.0 and 1.0):
           - impatience: how quickly they abandon a page if they hit friction, wait too long, or can't find what they need
           - tech_savviness: comfort using complex interfaces, reading documentation
           - price_sensitivity: focus on cost, searching for price or comparisons
           - support_reliance: willingness to seek contact/support rather than exploring

        Return ONLY a valid JSON array matching this structure:
        [
          {{
            "name": "Sarah Jenkins",
            "archetype": "Impatient Scanner",
            "goals": ["Find the signup page", "Register a new free trial account"],
            "impatience": 0.9,
            "tech_savviness": 0.7,
            "price_sensitivity": 0.4,
            "support_reliance": 0.1
          }}
        ]
        """
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            async with client.aio as aclient:
                response = await aclient.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
            
            text_content = response.text
            # Try to parse JSON block if output is wrapped
            if "```json" in text_content:
                text_content = text_content.split("```json")[1].split("```")[0].strip()
            elif "```" in text_content:
                text_content = text_content.split("```")[1].split("```")[0].strip()
            
            raw_personas = json.loads(text_content.strip())
            
            # Add IDs and status
            for idx, p in enumerate(raw_personas):
                p["id"] = f"pers_{uuid.uuid4().hex[:8]}_{idx}"
                p["status"] = "pending"
                
        except Exception as e:
            logger.error(f"Gemini persona generation failed: {e}. Falling back to mock personas.")
            raw_personas = get_fallback_personas(url, title, num_personas)
            
    # Populate simulation_id
    for p in raw_personas:
        p["simulation_id"] = simulation_id
        
    return raw_personas
