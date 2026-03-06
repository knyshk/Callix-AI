# app/core/config_loader.py

def load_brand_config(brand_id: str) -> dict:
    """
    For now, simple hardcoded config.
    Later this will load JSON or DB.
    """

    return {
        "supported_intents": [
            "check_balance",
            "refund_status",
            "talk_to_agent"
        ]
    }