import logging
from livekit.agents import function_tool
from datetime import datetime
from datetime import date

@function_tool()
async def get_current_date_time() -> str:
    """
    Get the current date and time.
    """
    from datetime import datetime
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Current date and time: {current_time}")
    return current_time