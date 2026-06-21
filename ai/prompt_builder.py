import yaml
import os
from typing import List, Dict
from ai.language_detect import get_language_instruction

class PromptBuilder:
    def __init__(self, config_path: str = None):
        if config_path is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            config_path = os.path.join(base_dir, "config.yaml")
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            print(f"Config file not found: {self.config_path}")
            return {}
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def build_system_prompt(self, customer_info: Dict) -> str:
        """
        Assembles the system prompt with business rules, pricing, and language instructions.
        """
        bot_settings = self.config.get("bot_settings", {})
        packages = self.config.get("packages", {})
        payment_methods = self.config.get("payment_methods", [])
        
        # Format pricing info for the AI
        pricing_info = "\n".join([
            f"- {p['name']}: 1 month {p.get('price_1month', 'N/A')}, 1 year {p.get('price_1year', 'N/A')}"
            for p in packages.values()
        ])

        # Format payment info
        payment_info = "\n".join([f"- {m}" for m in payment_methods])

        language_instruction = get_language_instruction(customer_info.get("language", "mixed"))

        system_prompt = f"""
You are a WhatsApp sales agent for {bot_settings.get('name', 'Premium Stream Bot')}.
You sell premium subscriptions like Netflix, Spotify, and YouTube.

BUSINESS RULES:
- Never share the full price list at once. Reveal prices conversationally when asked.
- Never mention you are an AI or a bot.
- Keep replies very short (1-3 sentences) unless explaining a process.
- Use a friendly, human-like sales tone.
- If the customer asks for a manager/owner, say they are busy and offer to help them yourself.
- ALWAYS try to move the conversation towards a sale.

PRICING & SERVICES:
{pricing_info}

PAYMENT METHODS:
{payment_info}

LANGUAGE INSTRUCTION:
{language_instruction}

CUSTOMER CONTEXT:
- Phone: {customer_info.get('phone')}
- Current Sales Stage: {customer_info.get('stage', 'new')}
- Interested in: {customer_info.get('selected_package', 'Not yet identified')}
"""
        return system_prompt.strip()

    def build_full_prompt(self, system_prompt: str, history: List[Dict], rag_examples: List[str] = None) -> List[Dict]:
        """
        Combines system prompt, RAG examples, and history into the final messages list for Groq.
        """
        messages = [{"role": "system", "content": system_prompt}]

        if rag_examples:
            examples_text = "\n\n".join([f"Example {i+1}:\n{ex}" for i, ex in enumerate(rag_examples)])
            messages.append({
                "role": "system", 
                "content": f"Here are examples of successful past conversations for inspiration:\n{examples_text}"
            })

        # Add history (last 10 messages)
        # History format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        messages.extend(history)

        return messages
