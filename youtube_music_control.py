from livekit.agents import function_tool, RunContext

@function_tool
async def youtube_music_control(
    context: RunContext,
    track_name: str,
    open_in_browser: bool = True
) -> str:
    """
    Play music via YouTube for free users.

    Parameters:
    - track_name: Name of the song to play
    - open_in_browser: If True, opens the video URL in the default web browser

    Returns:
    - A string indicating the result
    """
    import requests
    import webbrowser
    import urllib.parse

    if not track_name:
        return "Please provide a track name to play."

    try:
        # Prepare search query
        query = urllib.parse.quote(track_name)
        url = f"https://www.youtube.com/results?search_query={query}"

        # Fetch search results page
        response = requests.get(url)
        if response.status_code != 200:
            return "Failed to search YouTube."

        # Find the first video link
        import re
        video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
        if not video_ids:
            return f"Could not find a YouTube video for '{track_name}'."

        video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"

        # Optionally open in browser
        if open_in_browser:
            webbrowser.open(video_url)

        return f"🎵 Playing '{track_name}' on YouTube: {video_url}"

    except Exception as e:
        return f"An error occurred while playing music: {str(e)}"
