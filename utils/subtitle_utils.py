"""
Subtitle utilities for SRT file processing.
Provides functions to parse, format, and compose SRT subtitle files.
"""

import datetime


class SubtitleItem:
    """Represents a single subtitle item with timing and content."""

    def __init__(self, index=0, start=None, end=None, content="", proprietary=""):
        self.index = index
        self.start = start or datetime.timedelta()
        self.end = end or datetime.timedelta()
        self.content = content
        self.proprietary = proprietary

    def __str__(self):
        return f"Subtitle(index={self.index}, start={self.start}, end={self.end}, content='{self.content}')"


def parse_srt(srt_content):
    """
    Parse SRT file content and return list of SubtitleItem objects.

    Args:
        srt_content (str): Raw SRT file content

    Returns:
        list: List of SubtitleItem objects
    """
    try:
        subs = []
        blocks = srt_content.strip().replace('\r\n', '\n').split('\n\n')

        for block in blocks:
            if not block.strip():
                continue

            lines = block.split('\n')
            if len(lines) < 3:
                continue

            # Parse index
            try:
                index = int(lines[0])
            except ValueError:
                print(f"Debug: Invalid subtitle index: {lines[0]}")
                continue

            # Parse time range
            time_line = lines[1]
            try:
                start_time, end_time = time_line.split(' --> ')
                start = parse_time(start_time)
                end = parse_time(end_time)
            except (ValueError, IndexError) as e:
                print(f"Debug: Invalid time format in subtitle {index}: {time_line} - {str(e)}")
                continue

            # Parse content
            content = '\n'.join(lines[2:])

            # Create SubtitleItem
            sub = SubtitleItem(index=index, start=start, end=end, content=content)
            subs.append(sub)

        print(f"Debug: Successfully parsed {len(subs)} subtitles")
        return subs

    except Exception as e:
        print(f"Debug: Error parsing SRT content: {str(e)}")
        return []


def parse_time(time_str):
    """
    Parse SRT time format to datetime.timedelta.

    Args:
        time_str (str): Time string in format "HH:MM:SS,mmm"

    Returns:
        datetime.timedelta: Parsed time duration
    """
    try:
        hours, minutes, seconds = time_str.replace(',', '.').split(':')
        hours = int(hours)
        minutes = int(minutes)
        seconds_parts = seconds.split('.')
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

        return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
    except Exception as e:
        print(f"Debug: Error parsing time string '{time_str}': {str(e)}")
        return datetime.timedelta()


def format_time(td):
    """
    Format datetime.timedelta to SRT time format.

    Args:
        td (datetime.timedelta): Time duration

    Returns:
        str: Formatted time string "HH:MM:SS,mmm"
    """
    try:
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = td.microseconds // 1000

        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    except Exception as e:
        print(f"Debug: Error formatting time: {str(e)}")
        return "00:00:00,000"


def compose_srt(subs):
    """
    Compose SubtitleItem list back to SRT format string.

    Args:
        subs (list): List of SubtitleItem objects

    Returns:
        str: SRT formatted content
    """
    try:
        result = []

        for i, sub in enumerate(subs, 1):
            # Index
            result.append(str(i))

            # Time range
            result.append(f"{format_time(sub.start)} --> {format_time(sub.end)}")

            # Content
            result.append(sub.content)

            # Empty line
            result.append("")

        srt_content = "\n".join(result)
        print(f"Debug: Successfully composed SRT with {len(subs)} subtitles")
        return srt_content

    except Exception as e:
        print(f"Debug: Error composing SRT: {str(e)}")
        return ""