import logging
from llama_cpp import Llama

logger = logging.getLogger(__name__)

class LLMFallbackService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            logger.info("Loading Gemma 3 1B LLM into memory...")
            try:
                cls._model = Llama(
                    model_path="gemma-3-1b-it-Q4_K_M.gguf",
                    n_gpu_layers=-1, # Automatically uses GPU if available, CPU if not
                    n_threads=4, # Based on CPU benchmarks for this environment
                    verbose=False
                )
            except Exception as e:
                logger.error(f"Failed to load LLM model: {e}")
                raise
        return cls._model

    @classmethod
    def generate_with_context(cls, system_prompt_context, session_history, user_message):
        try:
            model = cls.get_model()
        except Exception:
            return "I apologize, but I am currently experiencing a technical issue loading my brain. Please try again later or contact our live support."
        
        # Build chat payload for gemma chat template
        messages = [
            {"role": "system", "content": system_prompt_context}
        ]
        
        for msg in session_history:
            role = "user" if msg.role == "USER" else "assistant"
            messages.append({"role": role, "content": msg.content})
            
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = model.create_chat_completion(
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            return "I apologize, but I am currently experiencing a technical issue and cannot answer right now. Please try again later or contact our live support."
