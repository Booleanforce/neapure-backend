import logging
from pathlib import Path

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


logger = logging.getLogger(__name__)


# neapure-backend/
BASE_DIR = Path(__file__).resolve().parents[3]

# neapure-backend/models/gemma-3-1b-it-Q4_K_M.gguf
MODEL_PATH = BASE_DIR / "models" / "gemma-3-1b-it-Q4_K_M.gguf"


class LLMFallbackService:
    _model = None

    @classmethod
    def get_model(cls):
        """
        Load the local Gemma model only when llama-cpp-python
        is available and the GGUF model exists.
        """

        # ---------------------------------------------------------
        # llama_cpp is not installed
        # ---------------------------------------------------------
        if Llama is None:
            logger.warning(
                "llama-cpp-python is not installed. "
                "Local LLM fallback is unavailable."
            )

            raise RuntimeError(
                "Local LLM is unavailable because "
                "llama-cpp-python is not installed."
            )

        # ---------------------------------------------------------
        # Return already-loaded model
        # ---------------------------------------------------------
        if cls._model is not None:
            return cls._model

        # ---------------------------------------------------------
        # Check model file
        # ---------------------------------------------------------
        logger.info(
            "Looking for Gemma model at: %s",
            MODEL_PATH,
        )

        if not MODEL_PATH.exists():
            logger.error(
                "Gemma model file not found: %s",
                MODEL_PATH,
            )

            raise FileNotFoundError(
                f"Gemma model not found at: {MODEL_PATH}"
            )

        # ---------------------------------------------------------
        # Load model
        # ---------------------------------------------------------
        logger.info(
            "Loading Gemma 3 1B LLM into memory..."
        )

        try:
            cls._model = Llama(
                model_path=str(MODEL_PATH),
                n_threads=4,
                n_gpu_layers=0,
                verbose=False,
            )

            logger.info(
                "Gemma 3 1B LLM loaded successfully."
            )

            return cls._model

        except Exception as e:
            logger.exception(
                "Failed to load LLM model: %s",
                e,
            )

            cls._model = None

            raise

    @classmethod
    def generate_with_context(
        cls,
        system_prompt_context,
        session_history,
        user_message,
    ):
        """
        Generate a response using the local Gemma model.

        If the local model is unavailable, return a safe
        fallback message instead of crashing Django.
        """

        # ---------------------------------------------------------
        # Get model
        # ---------------------------------------------------------
        try:
            model = cls.get_model()

        except Exception as e:
            logger.warning(
                "Local LLM unavailable: %s",
                e,
            )

            return (
                "I apologize, but I am currently "
                "experiencing a technical issue loading "
                "my AI service. Please try again later "
                "or contact our live support."
            )

        # ---------------------------------------------------------
        # Build chat messages
        # ---------------------------------------------------------
        messages = [
            {
                "role": "system",
                "content": system_prompt_context,
            }
        ]

        # ---------------------------------------------------------
        # Add conversation history
        # ---------------------------------------------------------
        for msg in session_history:
            role = (
                "user"
                if msg.role == "USER"
                else "assistant"
            )

            messages.append(
                {
                    "role": role,
                    "content": msg.content,
                }
            )

        # ---------------------------------------------------------
        # Add current user message
        # ---------------------------------------------------------
        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        # ---------------------------------------------------------
        # Generate response
        # ---------------------------------------------------------
        try:
            response = model.create_chat_completion(
                messages=messages,
                max_tokens=200,
                temperature=0.3,
            )

            content = (
                response
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content")
            )

            if not content:
                logger.warning(
                    "LLM returned an empty response."
                )

                return (
                    "I apologize, but I could not "
                    "generate a response right now. "
                    "Please try again later."
                )

            return content.strip()

        except Exception as e:
            logger.exception(
                "LLM generation failed: %s",
                e,
            )

            return (
                "I apologize, but I am currently "
                "experiencing a technical issue and "
                "cannot answer right now. Please try "
                "again later or contact our live support."
            )