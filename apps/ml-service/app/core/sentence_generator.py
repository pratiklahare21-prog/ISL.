"""
Open-Weight AI Integration for Natural Sentence Generation

Uses a small local LLM (Phi-3 or fallback to rule-based) to convert
ISL sign sequences into natural English sentences.

This is the CRITICAL missing component identified in the QA audit.
"""

import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import transformers (for open-weight LLM)
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
    logger.info("✓ Transformers available - will use open-weight LLM")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠ Transformers not available - using rule-based fallback")


class SentenceGenerator:
    """
    Converts ISL sign sequences into natural English sentences.
    
    Priority order:
    1. Phi-3-mini (fast, efficient, good quality)
    2. TinyLlama (very fast, lower quality)
    3. Rule-based fallback (no LLM required)
    """
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm and TRANSFORMERS_AVAILABLE
        self.model = None
        self.tokenizer = None
        
        if self.use_llm:
            try:
                self._initialize_llm()
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                logger.warning("Falling back to rule-based generation")
                self.use_llm = False
    
    def _initialize_llm(self):
        """Initialize the open-weight LLM model"""
        logger.info("Initializing open-weight AI model...")
        
        # Try Phi-3-mini first (Microsoft, very efficient)
        model_options = [
            "microsoft/Phi-3-mini-4k-instruct",
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        ]
        
        for model_name in model_options:
            try:
                logger.info(f"Attempting to load: {model_name}")
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True
                )
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,  # CPU compatible
                    device_map="cpu",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
                
                logger.info(f"✓ Successfully loaded: {model_name}")
                return
                
            except Exception as e:
                logger.warning(f"Could not load {model_name}: {e}")
                continue
        
        raise RuntimeError("Could not load any LLM model")
    
    def generate_sentence(self, signs: List[str]) -> dict:
        """
        Convert sign sequence to natural English sentence.
        
        Args:
            signs: List of recognized signs (e.g., ["HELLO", "I", "NEED", "HELP"])
        
        Returns:
            dict with:
                - raw_signs: Original sign list
                - natural_sentence: AI-generated natural sentence
                - method: "llm" or "rule-based"
                - confidence: Generation confidence (if available)
        """
        if not signs:
            return {
                "raw_signs": [],
                "natural_sentence": "",
                "method": "none",
                "confidence": 0.0
            }
        
        # Use LLM if available
        if self.use_llm and self.model is not None:
            return self._generate_with_llm(signs)
        else:
            return self._generate_with_rules(signs)
    
    def _generate_with_llm(self, signs: List[str]) -> dict:
        """Generate sentence using open-weight LLM"""
        try:
            # Create prompt for the LLM
            signs_text = " ".join(signs)
            
            prompt = f"""Convert these Indian Sign Language signs into a natural English sentence with proper grammar and punctuation.

Signs: {signs_text}

Natural sentence:"""
            
            # Generate
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=50,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the sentence (after "Natural sentence:")
            if "Natural sentence:" in generated_text:
                sentence = generated_text.split("Natural sentence:")[-1].strip()
            else:
                sentence = generated_text.split(signs_text)[-1].strip()
            
            # Clean up
            sentence = sentence.split('\n')[0].strip()
            sentence = self._clean_sentence(sentence)
            
            return {
                "raw_signs": signs,
                "natural_sentence": sentence,
                "method": "llm",
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_with_rules(signs)
    
    def _generate_with_rules(self, signs: List[str]) -> dict:
        """
        Rule-based sentence generation (fallback when LLM unavailable).
        
        This is NOT as good as LLM but provides basic functionality.
        """
        # Convert signs to lowercase words
        words = [self._sign_to_word(sign) for sign in signs]
        
        # Apply basic grammar rules
        sentence = self._apply_grammar_rules(words)
        
        return {
            "raw_signs": signs,
            "natural_sentence": sentence,
            "method": "rule-based",
            "confidence": 0.6
        }
    
    def _sign_to_word(self, sign: str) -> str:
        """Convert sign label to English word"""
        # Handle special cases
        word_mapping = {
            "THANK_YOU": "thank you",
            "HOW_ARE_YOU": "how are you",
            "NOT_UNDERSTAND": "don't understand",
        }
        
        if sign in word_mapping:
            return word_mapping[sign]
        
        # Handle underscore-separated words
        if "_" in sign:
            return sign.replace("_", " ").lower()
        
        # Regular words/letters
        return sign.lower()
    
    def _apply_grammar_rules(self, words: List[str]) -> str:
        """Apply basic grammar rules to word list"""
        if not words:
            return ""
        
        # Join words
        sentence = " ".join(words)
        
        # Capitalize first letter
        sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 0 else sentence
        
        # Add period if missing
        if not sentence.endswith(('.', '!', '?')):
            sentence += '.'
        
        # Fix common patterns
        sentence = re.sub(r'\bi\b', 'I', sentence)  # Capitalize "I"
        sentence = re.sub(r'\s+', ' ', sentence)    # Remove extra spaces
        
        return sentence
    
    def _clean_sentence(self, sentence: str) -> str:
        """Clean up generated sentence"""
        # Remove extra whitespace
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        
        # Ensure first letter is capitalized
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
        
        # Ensure proper punctuation
        if sentence and not sentence[-1] in '.!?':
            sentence += '.'
        
        # Fix common issues
        sentence = re.sub(r'\bi\b', 'I', sentence)
        
        return sentence


# Global instance (initialized once)
_generator_instance: Optional[SentenceGenerator] = None


def get_sentence_generator() -> SentenceGenerator:
    """Get or create the global sentence generator instance"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = SentenceGenerator(use_llm=TRANSFORMERS_AVAILABLE)
    return _generator_instance
