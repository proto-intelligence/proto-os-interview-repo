import json
import logging

logger = logging.getLogger(__name__)

def parse_structured_output(response: dict) -> dict:
    """
    Safely extracts and parses the structured JSON content from a chat completion response.
    
    :param response: The response dict returned from OpenRouter API.
    :return: Parsed JSON content as dict or empty dict if failed.
    """
    try:
        message = response.get("choices", [{}])[0].get("message", {})
        content = message.get("content", "").strip()

        if not content:
            logger.warning("Response content is empty.")
            return {}

        # Optional: Handle markdown-wrapped JSON (```json ... ```)
        if content.startswith("```json"):
            content = content.strip("```json").strip("```").strip()

        # Attempt to parse JSON
        return {"choices": message,"content":content}

    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decode error: {json_err}")
        logger.debug(f"Raw content: {content}")
        return {}
    except Exception as e:
        logger.exception("Unexpected error while parsing structured output.")
        return {}